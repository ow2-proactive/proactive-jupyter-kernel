from ipykernel.kernelbase import Kernel
from subprocess import check_output
import os
import re
import ast
import configparser as cp
import random
import proactive

from notebook import notebookapp
import urllib
import json
import ipykernel

import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import write_dot, graphviz_layout

from .images import display_data_for_image

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


class PragmaError(ValueError):
    def __init__(self, arg):
        self.strerror = arg
        self.args = {arg}


class ParsingError(ValueError):
    def __init__(self, arg):
        self.strerror = arg
        self.args = {arg}


class ConfigError(ValueError):
    def __init__(self, arg):
        self.strerror = arg
        self.args = {arg}


class ResultError(ValueError):
    def __init__(self, arg):
        self.strerror = arg
        self.args = {arg}


class ProActiveKernel(Kernel):
    implementation = 'ProActive'
    implementation_version = __version__

    _banner = "A ProActive Kernel - as useful as a parrot"

    language_info = {'name': 'python',
                     'codemirror_mode': 'ProActive',
                     'mimetype': 'text/x-python',
                     'file_extension': '.py'}

    @property
    def banner(self):
        if self._banner is None:
            self._banner = check_output(['python', '--version']).decode('utf-8')
        return self._banner

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        self.gateway = None
        self.proactive_tasks = []
        self.proactive_job = None
        self.job_created = False
        self.job_up_to_date = False
        self.job_name = None
        self.submitted_jobs_names = []
        self.submitted_jobs_ids = {}
        self.tasks_names = []
        self.tasks_count = 0
        self.proactive_config = None
        self.proactive_connected = False
        self.proactive_default_connection = False
        self.proactive_failed_connection = False
        self.error_message = ''
        self.graph_created = False
        self.G = None
        self.labels = {}

        try:
            self._start_proactive()

        except Exception as e:
            self.proactive_failed_connection = True
            self.error_message = str(e)

    def _start_proactive(self):
        if notebook_path() is not None:
            config_file = str(notebook_path().rsplit('/', 1)[0]) + '/proactive_config.ini'

            exists = os.path.isfile(config_file)

            if exists:
                # raise Exception(self.config)
                self.proactive_config = cp.ConfigParser()
                self.proactive_config.read(config_file)

                proactive_host = self.proactive_config['proactive_server']['host']
                proactive_port = self.proactive_config['proactive_server']['port']

                proactive_url = "http://" + proactive_host + ":" + proactive_port
                javaopts = []
                # uncomment for detailed logs
                # javaopts.append('-Dlog4j.configuration=file:'+os.path.join(os.getcwd(),'log4j.properties'))
                redirectJVMOutput = False
                self.gateway = proactive.ProActiveGateway(proactive_url, javaopts, redirectJVMOutput)

                if 'user' in self.proactive_config and 'login' in self.proactive_config['user'] and 'password' in \
                        self.proactive_config['user']:
                    if self.proactive_config['user']['login'] != '' and self.proactive_config['user']['password'] != '':
                        self.gateway.connect(username=self.proactive_config['user']['login'],
                                             password=self.proactive_config['user']['password'])
                        assert self.gateway.isConnected() is True
                        self.proactive_connected = True

                return

        proactive_host = 'try.activeeon.com'
        proactive_port = '8080'
        proactive_url = "http://" + proactive_host + ":" + proactive_port
        javaopts = []
        # uncomment for detailed logs
        # javaopts.append('-Dlog4j.configuration=file:'+os.path.join(os.getcwd(),'log4j.properties'))
        redirectJVMOutput = False
        self.gateway = proactive.ProActiveGateway(proactive_url, javaopts, redirectJVMOutput)
        self.proactive_default_connection = True

    @staticmethod
    def __is_valid_pragma__(data, sep_lines):
        pattern_path_cars = r"^[a-zA-Z0-9_\/\\:\.-]*$"
        pattern_generic = r"^( *[a-zA-Z]* *= *[a-zA-Z_]\w* *, *)*([a-zA-Z]* *= *[a-zA-Z_]\w* *)?$"
        pattern_with_name = r"^( *name *= *[a-zA-Z_]\w*)( *, *[a-zA-Z]* *= *[a-zA-Z_]\w* *)*$"
        pattern_with_path = pattern_with_name.strip('$)') + r"( *, *path *= *" + \
                            pattern_path_cars.strip("^$") + r" *)?$"
        pattern_connect = r"^( *host *= *(www.)?[a-z0-9]+(\.[a-z]+(\/[a-zA-Z0-9#]+)*)*(\.[a-z]+) *, *" \
                          r"port *= *\d+ *, *)?(login *= *[a-zA-Z_][a-zA-Z0-9_]*) *, *(password *= *[^ ]*)$"
        pattern_connect_with_path = r"^( *path *= *" + pattern_path_cars.strip("^$") + r" *)$"
        pattern_with_name_and_list_dep = r"^( *name *= *[a-zA-Z_]\w*)( *, *dep *= *\[ *[a-zA-Z_]\w*" \
                                         r"( *, *[a-zA-Z_]\w*)* *\] *)?( *, *[a-zA-Z]* *= *[a-zA-Z_]\w* *)*$"
        pattern_with_path_and_list_dep = pattern_with_name_and_list_dep.strip('$)') + r"( *, *path *= *" + \
                                         pattern_path_cars.strip("^$") + r" *)?$"
        pattern_with_name_only = r"^( *name *= *[a-zA-Z_]\w* *)$"
        pattern_with_id_only = r"^( *id *= *\d+ *)$"

        pragmas_generic = ['draw_job']
        pragmas_with_name = ['job', 'selection_script', 'fork_env']
        pragmas_with_name_and_path = ['selection_script', 'fork_env']
        pragmas_with_name_only = ['submit_job', 'write_dot']
        pragmas_with_id_or_name_only = ['get_result']
        pragmas_empty = ['submit_job', 'draw_job']

        invalid_generic = not re.match(pattern_generic, sep_lines[1]) and data['trigger'] in pragmas_generic
        invalid_with_name = not re.match(pattern_with_name, sep_lines[1]) and not \
            re.match(pattern_with_path, sep_lines[1]) and data['trigger'] in pragmas_with_name
        invalid_with_path = not re.match(pattern_with_path, sep_lines[1]) and \
                                data['trigger'] in pragmas_with_name_and_path
        invalid_task = not re.match(pattern_with_name_and_list_dep, sep_lines[1]) and not \
            re.match(pattern_with_path_and_list_dep, sep_lines[1]) and data['trigger'] == 'task'
        invalid_connect = not (re.match(pattern_connect, sep_lines[1]) or
                               re.match(pattern_connect_with_path, sep_lines[1])) and data['trigger'] == 'connect'
        invalid_with_name_only = (not re.match(pattern_with_name_only, sep_lines[1]) and data['trigger'] in
                                  pragmas_with_name_only)
        invalid_with_name_or_id = not (re.match(pattern_with_name_only, sep_lines[1]) or
                                       re.match(pattern_with_id_only, sep_lines[1])) and data['trigger'] in \
                                  pragmas_with_id_or_name_only
        valid_empty = sep_lines[1] == "" and data['trigger'] in pragmas_empty

        if (invalid_connect or invalid_generic or invalid_with_name or invalid_with_path or invalid_with_name_only
            or invalid_with_name_or_id or invalid_task) and not valid_empty:
            raise ParsingError('Invalid parameters')

    def __parse_pragma__(self, pragma):
        pragmas = ['job', 'task', 'selection_script', 'fork_env', 'connect', 'write_dot', 'get_result']
        pragmas_empty = ['submit_job', 'draw_job']
        pragma = pragma.strip(" #%)")
        sep_lines = pragma.split('(', 1)

        data = dict(trigger=sep_lines[0].strip(" "), name='')

        if len(sep_lines) == 2:
            self.__is_valid_pragma__(data, sep_lines)

            # if data['trigger'] == 'draw_job':
            #     if sep_lines[1] != '':
            #         self.__kernel_print_ok_message__('WARNING: The parameters \'' + str(sep_lines[1])
            #                                          + '\' are ignored.\n\n')
            #     return data

            # TODO: improve by saying if there is ignored parameters
            if data['trigger'] == 'task' and 'dep' in sep_lines[1]:
                draft = re.split(r'[\]\[]', sep_lines[1])
                sep_lines = draft[0] + 'TEMP' + draft[2]
                sep_lines = sep_lines.split(',')
                dep_list = draft[1].split(',')
                for line in sep_lines:
                    params = line.split('=')
                    data[params[0].strip(" ")] = params[1].strip(" ")

                data['dep'] = dep_list

            elif data['trigger'] in pragmas or (data['trigger'] in pragmas_empty and '=' in sep_lines[1]):
                sep_lines = sep_lines[1].split(',')
                for line in sep_lines:
                    params = line.split('=')
                    data[params[0].strip(" ")] = params[1].strip(" ")

        return data

    def __kernel_print_ok_message__(self, text):
        message = dict(name='stdout', text=text)
        self.send_response(self.iopub_socket, 'stream', message)

    def __kernel_print_error_message(self, error_data):
        error_content = {'execution_count': self.execution_count,
                         'ename': error_data['ename'], 'evalue': error_data['evalue'],
                         'traceback': []}
        self.send_response(self.iopub_socket, 'error', error_content)
        return error_content

    def __get_unique_task_name__(self):
        name = 'DT' + str(self.tasks_count)
        while name in self.tasks_names:
            name = 'DT' + str(random.randint(100, 9999999))
        return name

    def __trigger_pragma__(self, pragma_info):
        if pragma_info['trigger'] == 'task':
            return self.__create_task__
        elif pragma_info['trigger'] == 'draw_job':
            return self.__draw_job__
        elif pragma_info['trigger'] == 'connect':
            return self.__connect__
        elif pragma_info['trigger'] == 'submit_job':
            return self.__submit_job__
        elif pragma_info['trigger'] == 'get_result':
            return self.__get_result__
        elif pragma_info['trigger'] == 'job':
            return self.__create_job__
        elif pragma_info['trigger'] == 'write_dot':
            return self.__write_dot__
        elif pragma_info['trigger'] == 'selection_script':
            return self.__set_selection_script_from_name__
        elif pragma_info['trigger'] == 'fork_env':
            return self.__create_fork_environment_from_name__
        else:
            raise PragmaError('Directive \'' + pragma_info['trigger'] + '\' not known.')

    def draw_graph(self, input_data):
        pos = graphviz_layout(self.G, prog='dot')

        # nodes
        nx.draw_networkx_nodes(self.G, pos,
                               node_color='orange',
                               node_size=3000,
                               alpha=0.5)

        # edges
        nx.draw_networkx_edges(self.G, pos,
                               arrowstyle='->',
                               arrowsize=50,
                               edge_color='green',
                               width=2,
                               alpha=0.5)

        nx.draw_networkx_labels(self.G, pos,
                                self.labels,
                                font_size=13)

        plt.axis('off')

        if 'name' in input_data and input_data['name'] != '':
            title = input_data['name']
        elif self.job_created:
            title = self.job_name
        elif notebook_path() is not None:
            title = str(notebook_path().rsplit('/', 1)[1].split('.', 1)[0])
        else:
            title = 'Unnamed_job'

        plt.title(title)
        filename = './' + title + '.png'

        if 'inline' in input_data and input_data['inline'] == 'off':
            if 'save' in input_data and input_data['save'] == 'on':
                self.__kernel_print_ok_message__('Saving the job workflow into a png file...\n')
                plt.savefig(filename)  # save as png
                self.__kernel_print_ok_message__('\'' + filename + '\' file created.\n')

            self.__kernel_print_ok_message__('Plotting...\n')
            plt.show()  # display
            self.__kernel_print_ok_message__('End.\n')

        else:
            if 'save' in input_data and input_data['save'] == 'on':
                self.__kernel_print_ok_message__('Saving the job workflow into a png file...\n')
                plt.savefig(filename)  # save as png
                self.__kernel_print_ok_message__('\'' + filename + '\' file created.\n')
                save_file = True
            else:
                plt.savefig(filename)  # save as png
                save_file = False

            try:
                self.__kernel_print_ok_message__('Plotting...\n')
                data = display_data_for_image(filename, save_file)
            except ValueError as e:
                message = {'name': 'stdout', 'text': str(e)}
                self.send_response(self.iopub_socket, 'stream', message)
            else:
                self.send_response(self.iopub_socket, 'display_data', data)

            plt.close()

    def __draw_job__(self, input_data):
        if not self.graph_created or not self.job_up_to_date:
            self.__kernel_print_ok_message__('Creating the job workflow...\n')
            self.G = nx.DiGraph()

            # nodes
            nodes_ids = [i for i in range(len(self.proactive_tasks))]
            self.G.add_nodes_from(nodes_ids)

            # edges
            for index_son in range(len(self.proactive_tasks)):
                dependencies = self.proactive_tasks[index_son].getDependencesList()
                for parent_task in dependencies:
                    for index_parent in range(len(self.proactive_tasks)):
                        if parent_task.getTaskName() == self.proactive_tasks[index_parent].getTaskName():
                            self.G.add_edge(index_parent, index_son)

            # labels
            for i in nodes_ids:
                # some math labels
                self.labels[i] = r'$' + self.proactive_tasks[i].getTaskName() + '$'

            self.graph_created = True
            self.__kernel_print_ok_message__('Workflow created.\n')

        self.draw_graph(input_data)

        return 0

    def __write_dot__(self, input_data):
        self.__kernel_print_ok_message__('Creating the job workflow (dot format) ...\n')
        g_dot = nx.DiGraph()

        # nodes
        tasks_names = []
        for task in self.proactive_tasks:
            tasks_names.append(task.getTaskName())
        g_dot.add_nodes_from(tasks_names)

        # edges
        for son_task in self.proactive_tasks:
            dependencies = son_task.getDependencesList()
            for parent_task in dependencies:
                g_dot.add_edge(parent_task.getTaskName(), son_task.getTaskName())

        g_dot.name = self.job_name

        self.__kernel_print_ok_message__('Writing the dot file...\n')
        write_dot(g_dot, './' + input_data['name'] + '.dot')
        self.__kernel_print_ok_message__('\'' + input_data['name'] + '.dot\' file created.\n')

        return 0

    def __connect__(self, input_data):
        if self.proactive_connected:
            self.__kernel_print_ok_message__('WARNING: Proactive is already connected.\n')
            self.__kernel_print_ok_message__('Disconnecting from server: ' + self.gateway.base_url + ' ...\n')
            self.gateway.disconnect()
            self.proactive_connected = False

        if 'path' in input_data:
            exists = os.path.isfile(input_data['path'])

            if exists:
                try:
                    # raise Exception(self.config)
                    self.proactive_config = cp.ConfigParser()
                    self.proactive_config.read(input_data['path'])

                    proactive_host = self.proactive_config['proactive_server']['host']
                    proactive_port = self.proactive_config['proactive_server']['port']

                    proactive_url = "http://" + proactive_host + ":" + proactive_port
                    javaopts = []
                    # uncomment for detailed logs
                    # javaopts.append('-Dlog4j.configuration=file:'+os.path.join(os.getcwd(),'log4j.properties'))
                    redirectJVMOutput = False
                    self.gateway = proactive.ProActiveGateway(proactive_url, javaopts, redirectJVMOutput)
                    self.gateway.connect(username=self.proactive_config['user']['login'],
                                         password=self.proactive_config['user']['password'])

                    self.__kernel_print_ok_message__('Connecting to server ...\n')

                    assert self.gateway.isConnected() is True

                    self.__kernel_print_ok_message__('Connected as \'' + self.proactive_config['user']['login']
                                                     + '\'!\n')

                    self.proactive_connected = True

                    return 0

                except AssertionError as ae:
                    raise AssertionError(ae)
                except Exception as e:
                    raise ConfigError(str(e))

            else:
                raise ConfigError(input_data['path'] + ': No such a file.\n')

        if 'host' in input_data and 'port' in input_data:
            proactive_host = input_data['host']
            proactive_port = input_data['port']
            self.proactive_default_connection = False

            proactive_url = "http://" + proactive_host + ":" + proactive_port
            javaopts = []
            # uncomment for detailed logs
            # javaopts.append('-Dlog4j.configuration=file:'+os.path.join(os.getcwd(),'log4j.properties'))
            redirectJVMOutput = False
            self.gateway = proactive.ProActiveGateway(proactive_url, javaopts, redirectJVMOutput)

        self.__kernel_print_ok_message__('Connecting to server ...\n')

        self.gateway.connect(username=input_data['login'], password=input_data['password'])
        assert self.gateway.isConnected() is True

        self.__kernel_print_ok_message__('Connected as \'' + input_data['login'] + '\'!\n')

        self.proactive_connected = True

        return 0

    def __set_selection_script_from_task__(self, input_data):
        proactive_selection_script = self.gateway.createDefaultSelectionScript()
        if 'path' in input_data:
            exists = os.path.isfile(input_data['path'])
            if exists:
                proactive_selection_script.setImplementationFromFile(input_data['path'])
                if input_data['code'] != '':
                    self.__kernel_print_ok_message__('WARNING: The code written is ignored.\n')
            else:
                raise Exception('The file \'' + input_data['path'] + '\' does not exist')
        else:
            proactive_selection_script.setImplementation(input_data['code'])

        input_data['task'].setSelectionScript(proactive_selection_script)

    def __set_selection_script_from_name__(self, input_data):
        for value in self.proactive_tasks:
            if value.getTaskName() == input_data['name']:
                self.__kernel_print_ok_message__('Adding a selection script to the proactive task...\n')
                input_data['task'] = value
                self.__set_selection_script_from_task__(input_data)
                self.__kernel_print_ok_message__('Selection script added to \'' + input_data['name'] + '\'.\n')
                self.job_up_to_date = False
                return 0
        raise Exception('The task named \'' + input_data['name'] + '\' does not exist.')

    def __create_fork_environment_from_task__(self, input_data):
        proactive_fork_env = self.gateway.createDefaultForkEnvironment()
        if 'path' in input_data:
            exists = os.path.isfile(input_data['path'])
            if exists:
                proactive_fork_env.setImplementationFromFile(input_data['path'])
                if input_data['code'] != '':
                    self.__kernel_print_ok_message__('WARNING: The code written is ignored.\n')
            else:
                raise Exception('The file \'' + input_data['path'] + '\' does not exist')
        else:
            proactive_fork_env.setImplementation(input_data['code'])

        input_data['task'].setForkEnvironment(proactive_fork_env)

    def __create_fork_environment_from_name__(self, input_data):
        for value in self.proactive_tasks:
            if value.getTaskName() == input_data['name']:
                self.__kernel_print_ok_message__('Adding a fork environment to the proactive task...\n')
                input_data['task'] = value
                self.__create_fork_environment_from_task__(input_data)
                self.__kernel_print_ok_message__('Fork environment added to \'' + input_data['name'] + '\'.\n')
                self.job_up_to_date = False
                return 0
        raise Exception('The task named \'' + input_data['name'] + '\' does not exist.')

    def __get_task_from_name__(self, name):
        for task in self.proactive_tasks:
            if task.getTaskName() == name:
                return task
        return None

    def __add_dependency__(self, proactive_task, input_data):
        for task_name in input_data['dep']:
            task = self.__get_task_from_name__(task_name)
            if task is not None:
                proactive_task.addDependence(task)
                self.__kernel_print_ok_message__('Dependence \'' + task_name + '\'==>\'' + input_data['name'] +
                                                 '\' added.\n')
            else:
                self.__kernel_print_ok_message__('WARNING: Task \'' + task_name + '\' does not exist, '
                                                                                  'dependence ignored.\n')

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
        if 'path' in input_data:
            proactive_task.setTaskImplementationFromFile(input_data['path'])
            if input_data['code'] != '':
                self.__kernel_print_ok_message__('WARNING: The code written is ignored.\n')

        else:
            proactive_task.setTaskImplementation(input_data['code'])

        self.__kernel_print_ok_message__('Adding a selection script to the proactive task...\n')
        self.__set_selection_script_from_task__({'code': 'selected = True', 'task': proactive_task})
        self.__kernel_print_ok_message__('Task \'' + input_data['name'] + '\' created.\n')

        if 'dep' in input_data:
            self.__add_dependency__(proactive_task, input_data)

        self.proactive_tasks.append(proactive_task)

        self.tasks_names.append(input_data['name'])
        self.tasks_count += 1

        self.job_up_to_date = False

        return 0

    def __create_job__(self, input_data):
        if self.job_created and self.job_up_to_date:
            self.__set_job_name__(input_data['name'])
            self.__kernel_print_ok_message__('Job renamed to \'' + input_data['name'] + '\'.\n')
            return 0

        if self.job_created:
            self.__kernel_print_ok_message__('Re-creating the proactive job due to tasks changes ...\n')
        else:
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
        self.job_up_to_date = True

        return 0

    def __set_job_name__(self, name):
        self.proactive_job.setJobName(name)
        self.job_name = name
        return 0

    def __get_result__(self, input_data):
        job_id = 0

        if 'id' in input_data:
            job_id = int(input_data['id'])
            self.__kernel_print_ok_message__('Getting job ' + str(job_id) + ' output...\n')

        elif 'name' in input_data and input_data['name'] != '':
            if input_data['name'] not in self.submitted_jobs_ids:
                raise ResultError("The job named \'" + input_data['name'] + "\' does not exist.")
            job_id = self.submitted_jobs_ids[input_data['name']]
            self.__kernel_print_ok_message__('Getting job \'' + input_data['name'] + '\' output...\n')

        try:
            job_result = self.gateway.getJobResult(job_id)
        except Exception:
            raise ResultError("Results unreachable for job: " + str(job_id))

        self.__kernel_print_ok_message__('Result:\n')
        self.__kernel_print_ok_message__(job_result)

    def __submit_job__(self, input_data):
        if not self.job_created:
            if input_data['name'] == '':
                if notebook_path() is not None:
                    input_data['name'] = notebook_path().rsplit('/', 1)[1].split('.', 1)[0]
                else:
                    input_data['name'] = 'DefaultJob_' + str(random.randint(1000, 9999))

            self.__create_job__(input_data)

        elif not self.job_up_to_date:
            if input_data['name'] == '':
                input_data['name'] = self.job_name
            self.__create_job__(input_data)

        elif input_data['name'] != '':
            self.__kernel_print_ok_message__('Job renamed to \'' + input_data['name'] + '\'.\n')
            self.__set_job_name__(input_data['name'])

        else:
            input_data['name'] = self.job_name

        self.__kernel_print_ok_message__('Submitting the job to the proactive scheduler...\n')

        self.submitted_jobs_names.append(self.job_name)
        self.submitted_jobs_ids[self.job_name] = self.gateway.submitJob(self.proactive_job, debug=False)

        self.__kernel_print_ok_message__('job_id: ' + str(self.submitted_jobs_ids[self.job_name]) + '\n')

        return 0

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        self.silent = silent
        if not code.strip():
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

        interrupted = False

        if interrupted:
            return {'status': 'abort', 'execution_count': self.execution_count}

        if self.proactive_failed_connection:
            self.__kernel_print_error_message({'ename': 'Proactive connexion error',
                                               'evalue': 'Please, reconfigure proactive connection and restart kernel'})

            return self.__kernel_print_error_message({'ename': 'Error', 'evalue': self.error_message})

        pattern = r"^#%"

        func = self.__create_task__

        pragma_info = {'name': '', 'trigger': 'task'}

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

                except ParsingError as pe:
                    return self.__kernel_print_error_message({'ename': 'Parsing error', 'evalue': pe.strerror})

                if self.proactive_connected:
                    try:
                        func = self.__trigger_pragma__(pragma_info)
                    except PragmaError as pe:
                        return self.__kernel_print_error_message({'ename': 'Pragma error', 'evalue': pe.strerror})

                elif pragma_info['trigger'] == 'connect':
                    func = self.__connect__
                elif pragma_info['trigger'] in ['task', 'selection_script', 'fork_env', 'job', 'submit_job',
                                                'draw_job']:
                    return self.__kernel_print_error_message({'ename': 'Proactive error',
                                                              'evalue': 'Use #%connect() to connect to server first.'})
                else:
                    return self.__kernel_print_error_message({'ename': 'Pragma error', 'evalue':
                        'Directive \'' + pragma_info['trigger']
                        + '\' not known.'})

            try:
                ast.parse(code)
            except SyntaxError as e:
                return self.__kernel_print_error_message({'ename': 'Syntax error', 'evalue': str(e)})

            try:
                if not self.proactive_connected and not pragma_info['trigger'] == 'connect':
                    return self.__kernel_print_error_message({'ename': 'Proactive error',
                                                              'evalue': 'Use \'#%connect()\' to '
                                                                        'connect to proactive server first.'})

                pragma_info['code'] = code

                if self.proactive_default_connection and pragma_info['trigger'] != 'connect':
                    self.__kernel_print_ok_message__('WARNING: Proactive is connected by default on \''
                                                     + self.gateway.base_url + '\'.\n')
                try:
                    exitcode = func(pragma_info)
                except ConfigError as ce:
                    return self.__kernel_print_error_message({'ename': 'Proactive config error', 'evalue': ce.strerror})
                except ResultError as rer:
                    return self.__kernel_print_error_message(
                        {'ename': 'Proactive result error', 'evalue': rer.strerror})
                except AssertionError as ae:
                    return self.__kernel_print_error_message({'ename': 'Proactive connexion error', 'evalue': str(ae)})

            except Exception as e:
                return self.__kernel_print_error_message({'ename': 'Proactive error', 'evalue': str(e)})

        except Exception as e:
            exitcode = e

        if exitcode:
            error_content = self.__kernel_print_error_message({'ename': 'Error', 'evalue': str(exitcode)})
            error_content['status'] = 'error'
            return error_content

        else:
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

    def do_shutdown(self, restart):
        self.gateway.disconnect()
        self.gateway.terminate()
        return {'status': 'ok', 'restart': restart}
