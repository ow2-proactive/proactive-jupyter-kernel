from ipykernel.kernelbase import Kernel
from subprocess import check_output
import os
import re
import ast
import random
import proactive

from traitlets import Any

from notebook import notebookapp
import urllib
import json
import ipykernel

__version__ = '0.1'


def notebook_path():
    """Returns the absolute path of the Notebook or None if it cannot be determined
    NOTE: works only when the security is token-based or there is also no password
    """
    connection_file = os.path.basename(ipykernel.get_connection_file())
    kernel_id = connection_file.split('-', 1)[1].split('.')[0]

    for srv in notebookapp.list_running_servers():
        try:
            if srv['token'] == '' and not srv['password']:  # No token and no password, ahem...
                req = urllib.request.urlopen(srv['url'] + 'api/sessions')
            else:
                req = urllib.request.urlopen(srv['url'] + 'api/sessions?token=' + srv['token'])
            sessions = json.load(req)
            for sess in sessions:
                if sess['kernel']['id'] == kernel_id:
                    return os.path.join(srv['notebook_dir'], sess['notebook']['path'])
        except:
            pass  # There may be stale entries in the runtime directory
    return None


class ProActiveKernel(Kernel):
    implementation = 'ProActive'
    implementation_version = __version__

    _banner = "A ProActive Kernel - as useful as a parrot"

    gateway = Any()

    language_info = {'name': 'python',
                     'codemirror_mode': 'ProActive',
                     'mimetype': 'text/x-python',
                     'file_extension': '.py'}

    proactive_tasks = []
    proactive_job = Any()

    job_created = False

    tasks_names = []
    tasks_count = 0

    proactive_connected = False

    @property
    def banner(self):
        if self._banner is None:
            self._banner = check_output(['python', '--version']).decode('utf-8')
        return self._banner

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        try:
            self._start_proactive()

        except AssertionError as ae:
            self.process_output("Initialization of the Gateway failed.")

    def _start_proactive(self):
        proactive_host = 'try.activeeon.com'
        proactive_port = '8080'
        proactive_url = "http://" + proactive_host + ":" + proactive_port
        javaopts = []
        # uncomment for detailed logs
        # javaopts.append('-Dlog4j.configuration=file:'+os.path.join(os.getcwd(),'log4j.properties'))
        redirectJVMOutput = False
        self.gateway = proactive.ProActiveGateway(proactive_url, javaopts, redirectJVMOutput)

    def __parse_pragma__(self, pragma):
        pragma = pragma.strip(" #%)")
        sep_lines = pragma.split('(', 1)

        # if len(data) == 2:
        #     data[1] = data[1].strip(")")

        data = dict(trigger=sep_lines[0], name='')

        if len(sep_lines) == 2:  # TODO: add blank character (regex support and stripping blanks)
            pattern_generic = r"^(name=[a-zA-Z_][a-zA-Z0-9_]*)(,[a-zA-Z]*=[a-zA-Z_][a-zA-Z0-9_]*)*$"
            pattern_connect = r"^(login=[a-zA-Z_][a-zA-Z0-9_]*) *, *(password=[^ ]*)$"

            if (not re.match(pattern_generic, sep_lines[1]) and data['trigger'] in ['job', 'task']) \
                    or (not re.match(pattern_connect, sep_lines[1]) and data['trigger'] == 'connect'):
                raise Exception('Not valid parameters')

            if data['trigger'] == 'submit_job':
                if sep_lines[1] != '':
                    self.__kernel_print_ok_message__('WARNING: The parameters ' + str(sep_lines)
                                                     + ' are ignored.\n\n')
                return data

            sep_lines = sep_lines[1].split(',')
            for line in sep_lines:
                params = line.split('=')
                data[params[0]] = params[1]

        return data

    def __kernel_print_ok_message__(self, text):
        message = dict(name='stdout', text=text)
        self.send_response(self.iopub_socket, 'stream', message)

    def __get_unique_task_name__(self):
        name = 'DT' + str(self.tasks_count)
        while name in self.tasks_names:
            name = 'DT' + str(random.randint(100, 9999999))
        return name

    def __connect__(self, input_data):
        self.__kernel_print_ok_message__('Connecting to server ...\n')
        try:
            self.gateway.connect(username=input_data['login'], password=input_data['password'])
            assert self.gateway.isConnected() is True

            self.__kernel_print_ok_message__('Connected!')

            self.proactive_connected = True

        except Exception as e:
            error_content = {'execution_count': self.execution_count,
                             'ename': 'Proactive connexion error', 'evalue': str(e), 'traceback': []}
            self.send_response(self.iopub_socket, 'error', error_content)
            return error_content
        return 0

    def __create_task__(self, input_data):
        self.__kernel_print_ok_message__('Creating a proactive task...\n')
        proactive_task = self.gateway.createPythonTask()

        if input_data['name'] == '':
            name = self.__get_unique_task_name__()
            self.__kernel_print_ok_message__('WARNING: Task \'' + input_data['name'] + '\' renamed to : '
                                             + name + '\n')
            input_data['name'] = name
        elif input_data['name'] in self.tasks_names:
            self.__kernel_print_ok_message__('Task name : ' + input_data['name'] + ' exists already...\n')

            name = self.__get_unique_task_name__()

            self.__kernel_print_ok_message__('WARNING: Task \'' + input_data['name'] + '\' renamed to : '
                                             + name + '\n')
            input_data['name'] = name

        proactive_task.setTaskName(input_data['name'])
        proactive_task.setTaskImplementation(input_data['code'])

        self.__kernel_print_ok_message__('Adding a selection script to the proactive task...\n')
        proactive_selection_script = self.gateway.createDefaultSelectionScript()
        proactive_selection_script.setImplementation("selected = True")
        # proactive_selection_script.setImplementationFromFile("scripts/selection_script.py")
        proactive_task.setSelectionScript(proactive_selection_script)

        self.__kernel_print_ok_message__('Task \'' + input_data['name'] + '\' created.\n')

        self.proactive_tasks.append(proactive_task)

        self.tasks_names.append(input_data['name'])
        self.tasks_count += 1

        return 0

    def __create_job__(self, input_data):
        if self.job_created:
            self.__set_job_name__(input_data['name'])
            self.__kernel_print_ok_message__('Job renamed to \'' + input_data['name'] + '\'.\n')
            return 0

        self.__kernel_print_ok_message__('Creating a proactive job...\n')
        self.proactive_job = self.gateway.createJob()
        self.__set_job_name__(input_data['name'])

        self.__kernel_print_ok_message__('Job \'' + input_data['name'] + '\' created.\n')

        self.__kernel_print_ok_message__('Adding the created tasks to \'' + input_data['name'] + '\' ...\n')
        for task in self.proactive_tasks:
            self.proactive_job.addTask(task)

        self.proactive_job.setInputFolder(os.getcwd())
        self.proactive_job.setOutputFolder(os.getcwd())

        self.job_created = True

        return 0

    def __set_job_name__(self, name):
        self.proactive_job.setJobName(name)
        return 0

    def __submit_job__(self, input_data):
        if not self.job_created:
            if input_data['name'] == '':
                input_data['name'] = notebook_path().rsplit('/', 1)[1].split('.', 1)[0]
            self.__create_job__(input_data)

        self.__kernel_print_ok_message__('Submitting the job to the proactive scheduler...\n')

        job_id = self.gateway.submitJob(self.proactive_job, debug=False)

        self.__kernel_print_ok_message__('job_id: ' + str(job_id) + '\n')

        self.__kernel_print_ok_message__('Getting job output...\n')
        job_result = self.gateway.getJobResult(job_id)

        self.__kernel_print_ok_message__(job_result)

        return 0

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        self.silent = silent
        if not code.strip():
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

        interrupted = False

        if interrupted:
            return {'status': 'abort', 'execution_count': self.execution_count}

        pattern = r"^#%"

        func = self.__create_task__

        pragma_info = {'name': ''}

        try:
            if re.match(pattern, code):
                pragma = code.split("\n", 1)

                if len(pragma) == 2:
                    code = pragma.pop(1)
                else:
                    code = ''
                pragma = pragma.pop(0)

                try:
                    pragma_info = self.__parse_pragma__(pragma)

                except Exception as e:
                    error_content = {'execution_count': self.execution_count,
                                     'ename': 'Parsing error', 'evalue': str(e), 'traceback': []}
                    self.send_response(self.iopub_socket, 'error', error_content)
                    return error_content

                if self.proactive_connected:
                    if pragma_info['trigger'] == 'job':
                        func = self.__create_job__
                    elif pragma_info['trigger'] == 'submit_job':
                        func = self.__submit_job__
                    elif pragma_info['trigger'] != 'task':
                        error_content = {'execution_count': self.execution_count,
                                         'ename': 'Pragma error', 'evalue': 'Directive \'' +
                                                                            pragma_info['trigger'] + '\' not known.',
                                         'traceback': []}
                        self.send_response(self.iopub_socket, 'error', error_content)
                        return error_content
                elif pragma_info['trigger'] in ['task', 'job', 'submit_job']:
                    error_content = {'execution_count': self.execution_count,
                                     'ename': 'Proactive error', 'evalue': 'Use #%connect() to connect to server '
                                                                           'first.', 'traceback': []}
                    self.send_response(self.iopub_socket, 'error', error_content)
                    return error_content
                elif pragma_info['trigger'] != 'connect':
                    error_content = {'execution_count': self.execution_count,
                                     'ename': 'Pragma error', 'evalue': 'Directive \'' +
                                                                        pragma_info['trigger'] + '\' not known.',
                                     'traceback': []}
                    self.send_response(self.iopub_socket, 'error', error_content)
                    return error_content
                else:
                    func = self.__connect__

            try:
                ast.parse(code)
            except SyntaxError as e:
                error_content = {'execution_count': self.execution_count,
                                 'ename': 'Syntax error', 'evalue': str(e), 'traceback': []}
                self.send_response(self.iopub_socket, 'error', error_content)
                return error_content

            try:
                if not self.proactive_connected and not pragma_info['trigger'] == 'connect':
                    error_content = {'execution_count': self.execution_count,
                                     'ename': 'Proactive error', 'evalue': 'Use \'#%connect()\' to connect to '
                                                                           'proactive server first.', 'traceback': []}
                    self.send_response(self.iopub_socket, 'error', error_content)
                    return error_content
                pragma_info['code'] = code
                exitcode = func(pragma_info)
            except Exception as e:
                error_content = {'execution_count': self.execution_count,
                                 'ename': 'Proactive error', 'evalue': str(e), 'traceback': []}
                self.send_response(self.iopub_socket, 'error', error_content)
                return error_content

        except Exception as e:
            exitcode = e

        if exitcode:
            error_content = {'execution_count': self.execution_count,
                             'ename': 'Error', 'evalue': str(exitcode), 'traceback': []}
            self.send_response(self.iopub_socket, 'error', error_content)
            error_content['status'] = 'error'
            return error_content

        else:
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

    def do_shutdown(self, restart):
        self.gateway.disconnect()
        self.gateway.terminate()
        return {'status': 'ok', 'restart': restart}
