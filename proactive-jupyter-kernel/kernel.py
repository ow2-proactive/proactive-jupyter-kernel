from ipykernel.kernelbase import Kernel
from subprocess import check_output
import os
import ast
import configparser as cp
import random
import tempfile
import proactive

from notebook import notebookapp
import urllib
import json
import ipykernel

from proactive.model.ProactiveScriptLanguage import *

import matplotlib.pyplot as plt
import networkx as nx
import pygraphviz as pgv
from networkx.drawing.nx_agraph import write_dot, graphviz_layout

from IPython.display import IFrame

from .images import display_data_for_image
from .pragma import *

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

    language_info = {'name': 'python',
                     'codemirror_mode': 'python',
                     'mimetype': 'text/x-python',
                     'file_extension': '.py'}

    pattern_pragma = r"^#%"

    @property
    def banner(self):
        if self._banner is None:
            self._banner = check_output(['python', '--version']).decode('utf-8')
        return self._banner

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        self.gateway = None
        self.proactive_tasks = []
        self.proactive_script_languages = None
        self.proactive_job = None
        self.job_created = False
        self.job_up_to_date = False
        self.job_name = None
        self.submitted_jobs_names = {}
        self.submitted_jobs_ids = {}
        self.tasks_names = []
        self.tasks_count = 0
        self.proactive_config = {}
        self.proactive_connected = False
        self.proactive_default_connection = True
        self.proactive_failed_connection = False
        self.error_message = ''
        self.graph_created = False
        self.G = None
        self.labels = {}
        self.pragma = Pragma()
        self.imports = {}
        self.default_selection_script = None
        self.default_fork_env = None
        self.multiblock_task_config = False

        self.previous_task_history = {}
        self.is_previous_pragma_task = False
        self.last_modified_task = None

        self.exported_vars = {}

        self.proactive_script_languages = ProactiveScriptLanguage().get_supported_languages()

        self.script_languages = ''
        for script_language in self.proactive_script_languages:
            self.script_languages += '   - ' + script_language + '\n'

        try:
            self.__start_proactive__()
        except Exception as e:
            self.proactive_failed_connection = True
            self.error_message = str(e)

    def __start_proactive__(self):
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

        self.proactive_config['proactive_server'] = {}

    def __kernel_print_ok_message__(self, text):
        message = dict(name='stdout', text=text)
        self.send_response(self.iopub_socket, 'stream', message)

    def __kernel_print_error_message(self, error_data):
        error_content = {'ename': error_data['ename'],
                         'evalue': error_data['evalue'],
                         'traceback': []}
        self.send_response(self.iopub_socket, 'error', error_content)
        error_content['execution_count'] = self.execution_count
        error_content['status'] = 'error'
        return error_content

    def __get_unique_task_name__(self, name_base = 'DT'):
        name = name_base + str(self.tasks_count)
        while name in self.tasks_names:
            name = name_base + str(random.randint(100, 9999999))
        return name

    def __trigger_pragma__(self, pragma_info):
        if pragma_info['trigger'] == 'task':
            return self.__create_task__
        elif pragma_info['trigger'] == 'help':
            return self.__help__
        elif pragma_info['trigger'] == 'import':
            return self.__import__
        elif pragma_info['trigger'] == 'draw_job':
            return self.__draw_job__
        elif pragma_info['trigger'] == 'connect':
            return self.__connect__
        elif pragma_info['trigger'] == 'submit_job':
            return self.__submit_job__
        elif pragma_info['trigger'] == 'get_job_result':
            return self.__get_job_result__
        elif pragma_info['trigger'] == 'get_task_result':
            return self.__get_task_result__
        elif pragma_info['trigger'] == 'print_job_output':
            return self.__print_job_output__
        elif pragma_info['trigger'] == 'print_task_output':
            return self.__print_task_output__
        elif pragma_info['trigger'] == 'configure':
            return self.__configure__
        elif pragma_info['trigger'] == 'delete_task':
            return self.__delete_task__
        elif pragma_info['trigger'] == 'list_submitted_jobs':
            return self.__list_submitted_jobs__
        elif pragma_info['trigger'] == 'split':
            return self.__create_split__
        elif pragma_info['trigger'] == 'runs':
            return self.__add_runs__
        elif pragma_info['trigger'] == 'process':
            return self.__create_process__
        elif pragma_info['trigger'] == 'merge':
            return self.__create_merge__
        elif pragma_info['trigger'] == 'job':
            return self.__create_job__
        elif pragma_info['trigger'] == 'export_xml':
            return self.__create_export_xml__
        elif pragma_info['trigger'] == 'write_dot':
            return self.__write_dot__
        elif pragma_info['trigger'] == 'import_dot':
            return self.__import_dot__
        elif pragma_info['trigger'] == 'pre_script':
            return self.__create_pre_script_from_name__
        elif pragma_info['trigger'] == 'post_script':
            return self.__create_post_script_from_name__
        elif pragma_info['trigger'] == 'selection_script':
            return self.__create_selection_script_from_name__
        elif pragma_info['trigger'] == 'job_selection_script':
            return self.__create_job_selection_script__
        elif pragma_info['trigger'] == 'fork_env':
            return self.__create_fork_environment_from_name__
        elif pragma_info['trigger'] == 'job_fork_env':
            return self.__create_job_fork_environment__
        elif pragma_info['trigger'] == 'show_resource_manager':
            return self.__show_resource_manager__
        elif pragma_info['trigger'] == 'show_scheduling_portal':
            return self.__show_scheduling_portal__
        elif pragma_info['trigger'] == 'show_workflow_automation':
            return self.__show_workflow_automation__
        else:
            raise PragmaError('Directive \'' + pragma_info['trigger'] + '\' not known.')

    def __configure__(self, input_data):
        if 'task' in input_data:
            self.__kernel_print_ok_message__('Switching to ' + input_data['task'] + ' mode...\n')
            if input_data['task'] == 'multiblock':
                self.multiblock_task_config = True
            else:
                self.multiblock_task_config = False
            self.__kernel_print_ok_message__('Done.')
        else:
            raise ParameterError('Task parameter \'' + input_data['task'] +
                                 '\' not supported!\n Supported values:\n\t-block\n\t-multiblock')

    def __show_portal__(self, input_data):
        if 'portal' not in input_data:
            input_data['portal'] = ""
        if 'host' in input_data:
            url = os.path.join('https://', input_data['host'], input_data['portal'])
        else:
            url = os.path.join('https://', self.proactive_config['proactive_server']['host'], input_data['portal'])

        if 'width' in input_data and 'height' in input_data:
            data = IFrame(url, width=input_data['width'], height=input_data['height'])
        else:
            data = IFrame(url, width=1200, height=750)

        content = {'data': {'text/html': data._repr_html_()},
                   'metadata': {}
                   }
        self.send_response(self.iopub_socket, 'display_data', content)

    def __show_resource_manager__(self, input_data):
        input_data['portal'] = 'rm'
        self.__show_portal__(input_data)

    def __show_scheduling_portal__(self, input_data):
        input_data['portal'] = 'scheduler'
        self.__show_portal__(input_data)

    def __show_workflow_automation__(self, input_data):
        input_data['portal'] = 'automation-dashboard/#/portal/workflow-automation'
        self.__show_portal__(input_data)

    def __get_saving_file_name__(self, input_data):
        if 'name' in input_data and input_data['name'] != '':
            title = input_data['name']
        elif self.job_created:
            title = self.job_name
        elif notebook_path() is not None:
            title = str(notebook_path().rsplit('/', 1)[1].split('.', 1)[0])
        else:
            title = 'Unnamed_job'
        return title

    def __draw_graph__(self, input_data):
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

        title = self.__get_saving_file_name__(input_data)

        plt.title(title)
        filename = './' + title + '.png'

        if 'inline' in input_data and input_data['inline'] == 'off':
            if 'save' in input_data and input_data['save'] == 'on':
                self.__kernel_print_ok_message__('Saving the job workflow into a png file ...\n')
                plt.savefig(filename)  # save as png
                self.__kernel_print_ok_message__('\'' + filename + '\' file created.\n')

            self.__kernel_print_ok_message__('Plotting ...\n')
            plt.show()  # display
            self.__kernel_print_ok_message__('End.\n')

        else:
            if 'save' in input_data and input_data['save'] == 'on':
                self.__kernel_print_ok_message__('Saving the job workflow into a png file ...\n')
                plt.savefig(filename)  # save as png
                self.__kernel_print_ok_message__('\'' + filename + '\' file created.\n')
                save_file = True
            else:
                plt.savefig(filename)  # save as png
                save_file = False

            try:
                self.__kernel_print_ok_message__('Plotting ...\n')
                data = display_data_for_image(filename, save_file)
            except ValueError as e:
                message = {'name': 'stdout', 'text': str(e)}
                self.send_response(self.iopub_socket, 'stream', message)
            else:
                self.send_response(self.iopub_socket, 'display_data', data)

            plt.close()

    def __draw_job__(self, input_data):
        if not self.graph_created or not self.job_up_to_date:
            self.__kernel_print_ok_message__('Creating the job workflow ...\n')
            self.G = nx.DiGraph()
            self.labels.clear()

            # nodes
            nodes_ids = [i for i in range(len(self.proactive_tasks))]
            self.G.add_nodes_from(nodes_ids)

            # edges
            for index_son in range(len(self.proactive_tasks)):
                dependencies = self.proactive_tasks[index_son].getDependencies()
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

        self.__draw_graph__(input_data)

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
            dependencies = son_task.getDependencies()
            for parent_task in dependencies:
                g_dot.add_edge(parent_task.getTaskName(), son_task.getTaskName())

        g_dot.name = self.job_name

        title = self.__get_saving_file_name__(input_data)

        self.__kernel_print_ok_message__('Writing the dot file ...\n')
        write_dot(g_dot, './' + title + '.dot')
        self.__kernel_print_ok_message__('\'' + title + '.dot\' file created.\n')

        return 0

    @staticmethod
    def __extract_dependencies_from_edges__(node, edges):
        dependencies = []
        for dependency in edges:
            if dependency[1] == node:
                dependencies.append(dependency[0])
        return dependencies

    @staticmethod
    def __extract_task_inputs_from_graph_data__(node, edges):
        input_map = {'trigger': 'task', 'name': node, 'code': ''}
        dependencies = ProActiveKernel.__extract_dependencies_from_edges__(node, edges)
        if len(dependencies):
            input_map['dep'] = dependencies
        return input_map

    @staticmethod
    def __extract_tasks_inputs_from_graph__(nodes_list, edges_list):
        inputs_list = []
        for node in nodes_list:
            inputs_list.append(ProActiveKernel.__extract_task_inputs_from_graph_data__(node, edges_list))
        return inputs_list

    def __import_dot__(self, input_data):
        if os.path.isfile(input_data['path']):
            Gtmp = pgv.AGraph(input_data['path'])
            nodes = Gtmp.nodes()
            edges = Gtmp.edges()

            inputs_data = ProActiveKernel.__extract_tasks_inputs_from_graph__(nodes, edges)
            for temp_input_data in inputs_data:
                self.__create_task__(temp_input_data)

        else:
            raise ConfigError(input_data['path'] + ': No such file.\n')

        return 0

    def __create_export_xml__(self, input_data):
        self.__kernel_print_ok_message__('Exporting the job workflow (xml format) ...\n')

        title = self.__get_saving_file_name__(input_data)

        filename = './' + title + '.xml'
        self.gateway.saveJob2XML(self.proactive_job, filename, debug=False)

        self.__kernel_print_ok_message__('\'' + title + '.xml\' file created.\n')

        return 0

    def __connect__(self, input_data):
        if self.proactive_connected:
            self.__kernel_print_ok_message__('WARNING: Proactive is already connected.\n')
            self.__kernel_print_ok_message__('Disconnecting from server: ' + self.gateway.base_url + ' ...\n')
            self.gateway.disconnect()
            self.gateway.terminate()
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
                    self.proactive_default_connection = False

                    return 0

                except AssertionError as ae:
                    raise AssertionError(ae)
                except Exception as e:
                    raise ConfigError(str(e))

            else:
                raise ConfigError(input_data['path'] + ': No such file.\n')

        if 'host' in input_data:
            self.proactive_config['proactive_server']['host'] = input_data['host']
            self.proactive_default_connection = False
        else:
            self.proactive_config['proactive_server']['host'] = 'try.activeeon.com'
            self.proactive_default_connection = True

        if 'port' in input_data:
            self.proactive_config['proactive_server']['port'] = input_data['port']
            self.proactive_default_connection = False
        else:
            self.proactive_config['proactive_server']['port'] = '8080'

        proactive_url = "http://" + self.proactive_config['proactive_server']['host'] + ":" + \
                        self.proactive_config['proactive_server']['port']

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

    def __print_usage_from_pragma__(self, pragma):
        trigger = pragma.strip(" #%)").split('(', 1)[0].strip(" ")
        self.__kernel_print_error_message({'ename': 'Usages', 'evalue': '\n' + get_usage(trigger)})

    def __help__(self, input_data):
        if 'pragma' in input_data:
            self.__kernel_print_ok_message__(get_help(input_data['pragma']))
        else:
            # TODO: automatize the help output and relate it more to pragma.py
            self.__kernel_print_ok_message__('\n#%connect(): connects to an ActiveEon server\n'
                                             + '#%import(): import specified libraries to all tasks of a same script language\n'
                                             + '#%configure(): configures the ProActive kernel\'s behavior\n'
                                             + '#%task(): creates/modifies a task\n'
                                             + '#%delete_task(): removes a task from the workflow\n'
                                             + "#%pre_script(): sets the pre-script of a task\n"
                                             + "#%post_script(): sets the post-script of a task\n"
                                             + '#%selection_script(): sets the selection script of a task\n'
                                             + '#%job_selection_script(): sets the default selection script of a job\n'
                                             + '#%fork_env(): sets the fork environment script\n'
                                             + '#%job_fork_env(): sets the default fork environment of a job\n'
                                             + '#%split(): creates/modifies a splitting task of a replicate control\n'
                                             + '#%runs(): creates/modifies the configuration script of a replicate control\n'
                                             + '#%process(): creates/modifies the script of a replicated processing task\n'
                                             + '#%merge(): creates/modifies a merging task of a replicate control\n'
                                             + '#%job(): creates/renames the job\n'
                                             + '#%draw_job(): plots the workflow\n'
                                             + '#%write_dot(): writes the workflow in .dot format\n'
                                             + '#%import_dot(): imports the workflow from a .dot file\n'
                                             + '#%submit_job(): submits the job to the scheduler\n'
                                             + '#%get_job_result(): gets and prints the job results\n'
                                             + '#%get_task_result(): gets and prints the results of a given task\n'
                                             + '#%print_job_output(): gets and prints the job outputs\n'
                                             + '#%print_task_output(): gets and prints the outputs of a given task\n'
                                             + '#%list_submitted_jobs(): gets and prints the ids and names of the submitted jobs\n'
                                             + '#%export_xml(): exports the workflow in .xml format\n'
                                             + '#%show_resource_manager(): opens the ActiveEon resource manager portal\n'
                                             + '#%show_scheduling_portal(): opens the ActiveEon scheduling portal\n'
                                             + '#%show_workflow_automation(): opens the ActiveEon workflow automation portal\n\n'
                                             + 'To know the usage of a pragma use: #%help(pragma=PRAGMA_NAME)\n\n'
                                             + 'For more information, please check: https://github.com/ow2-proactive/'
                                               'proactive-jupyter-kernel/blob/master/README.md\n')

    def __import__(self, input_data):
        # TODO: should we update old tasks to add new added imports?
        if 'language' in input_data:
            if input_data['language'] in self.proactive_script_languages:
                self.__kernel_print_ok_message__('Saving \'' + input_data['language'] + '\' imports ...\n')
                self.imports[input_data['language']] = input_data['code']
            else:
                raise ParameterError('Language \'' + input_data['language'] +
                                     '\' not supported!\n Supported Languages:\n' + self.script_languages)

        else:
            self.__kernel_print_ok_message__('Saving \'Python\' imports ...\n')
            self.imports['Python'] = input_data['code']

        self.__kernel_print_ok_message__('Saved.\n')

    def __create_pre_script_from_task__(self, input_data):
        if input_data['language'] in self.proactive_script_languages:
            pre_script = self.gateway.createPreScript(self.proactive_script_languages[input_data['language']])
        else:
            raise ParameterError('Language \'' + input_data['language'] +
                                 '\' not supported!\n Supported Languages:\n' + self.script_languages)
        if 'path' in input_data:
            exists = os.path.isfile(input_data['path'])
            if exists:
                pre_script.setImplementationFromFile(input_data['path'])
                if input_data['code'] != '':
                    self.__kernel_print_ok_message__('WARNING: The written code is ignored.\n')
            else:
                raise Exception('The file \'' + input_data['path'] + '\' does not exist')
        else:
            pre_script.setImplementation(input_data['code'])

        input_data['task'].setPreScript(pre_script)

    def __create_pre_script_from_name__(self, input_data):
        for value in self.proactive_tasks:
            if value.getTaskName() == input_data['name']:
                self.__kernel_print_ok_message__('Adding a pre-script to the proactive task ...\n')
                input_data['task'] = value
                self.__create_pre_script_from_task__(input_data)
                self.__kernel_print_ok_message__('Pre-script added to \'' + input_data['name'] + '\'.\n')
                self.job_up_to_date = False
                return 0
        raise Exception('The task named \'' + input_data['name'] + '\' does not exist.')

    def __create_post_script_from_task__(self, input_data):
        if input_data['language'] in self.proactive_script_languages:
            post_script = self.gateway.createPostScript(self.proactive_script_languages[input_data['language']])
        else:
            raise ParameterError('Language \'' + input_data['language'] +
                                 '\' not supported!\n Supported Languages:\n' + self.script_languages)
        if 'path' in input_data:
            exists = os.path.isfile(input_data['path'])
            if exists:
                post_script.setImplementationFromFile(input_data['path'])
                if input_data['code'] != '':
                    self.__kernel_print_ok_message__('WARNING: The written code is ignored.\n')
            else:
                raise Exception('The file \'' + input_data['path'] + '\' does not exist')
        else:
            post_script.setImplementation(input_data['code'])

        input_data['task'].setPostScript(post_script)

    def __create_post_script_from_name__(self, input_data):
        for value in self.proactive_tasks:
            if value.getTaskName() == input_data['name']:
                self.__kernel_print_ok_message__('Adding a post-script to the proactive task ...\n')
                input_data['task'] = value
                self.__create_post_script_from_task__(input_data)
                self.__kernel_print_ok_message__('Post-script added to \'' + input_data['name'] + '\'.\n')
                self.job_up_to_date = False
                return 0
        raise Exception('The task named \'' + input_data['name'] + '\' does not exist.')

    def __create_selection_script_from_task__(self, input_data):
        # TODO: add different script language handling
        proactive_selection_script = self.gateway.createDefaultSelectionScript()
        if 'path' in input_data:
            exists = os.path.isfile(input_data['path'])
            if exists:
                proactive_selection_script.setImplementationFromFile(input_data['path'])
                if input_data['code'] != '':
                    self.__kernel_print_ok_message__('WARNING: The written code is ignored.\n')
            else:
                raise Exception('The file \'' + input_data['path'] + '\' does not exist')
        else:
            proactive_selection_script.setImplementation(input_data['code'])

        input_data['task'].setSelectionScript(proactive_selection_script)

    def __create_selection_script_from_name__(self, input_data):
        for task in self.proactive_tasks:
            if task.getTaskName() == input_data['name']:
                self.__kernel_print_ok_message__('Adding a selection script to the proactive task ...\n')
                input_data['task'] = task
                self.__create_selection_script_from_task__(input_data)
                self.__kernel_print_ok_message__('Selection script added to \'' + input_data['name'] + '\'.\n')
                self.job_up_to_date = False
                return 0
        raise Exception('The task named \'' + input_data['name'] + '\' does not exist.')

    def __create_job_selection_script__(self, input_data):
        # TODO: add different script language handling
        proactive_selection_script = self.gateway.createDefaultSelectionScript()
        if 'path' in input_data:
            exists = os.path.isfile(input_data['path'])
            if exists:
                proactive_selection_script.setImplementationFromFile(input_data['path'])
                if input_data['code'] != '':
                    self.__kernel_print_ok_message__('WARNING: The written code is ignored.\n')
            else:
                raise Exception('The file \'' + input_data['path'] + '\' does not exist')
        else:
            proactive_selection_script.setImplementation(input_data['code'])

        self.__kernel_print_ok_message__('Saving selection script ...\n')
        self.default_selection_script = proactive_selection_script

        if 'force' in input_data and input_data['force'] == 'on':
            self.__kernel_print_ok_message__('Updating created tasks ...\n')
            for task in self.proactive_tasks:
                self.__kernel_print_ok_message__('Setting the selection script of the task \'' + task.getTaskName()
                                                 + '\' ...\n')
                task.setSelectionScript(self.default_selection_script)
                self.job_up_to_date = False

        self.__kernel_print_ok_message__('Done.\n')

    def __create_fork_environment_from_task__(self, input_data):
        # TODO: add different script language handling
        proactive_fork_env = self.gateway.createDefaultForkEnvironment()
        if 'path' in input_data:
            exists = os.path.isfile(input_data['path'])
            if exists:
                proactive_fork_env.setImplementationFromFile(input_data['path'])
                if input_data['code'] != '':
                    self.__kernel_print_ok_message__('WARNING: The written code is ignored.\n')
            else:
                raise Exception('The file \'' + input_data['path'] + '\' does not exist')
        else:
            proactive_fork_env.setImplementation(input_data['code'])

        input_data['task'].setForkEnvironment(proactive_fork_env)

    def __create_fork_environment_from_name__(self, input_data):
        for task in self.proactive_tasks:
            if task.getTaskName() == input_data['name']:
                self.__kernel_print_ok_message__('Adding a fork environment to the proactive task ...\n')
                input_data['task'] = task
                self.__create_fork_environment_from_task__(input_data)
                self.__kernel_print_ok_message__('Fork environment added to \'' + input_data['name'] + '\'.\n')
                self.job_up_to_date = False
                return 0
        raise Exception('The task named \'' + input_data['name'] + '\' does not exist.')

    def __create_job_fork_environment__(self, input_data):
        # TODO: add different script language handling
        proactive_fork_env = self.gateway.createDefaultForkEnvironment()
        if 'path' in input_data:
            exists = os.path.isfile(input_data['path'])
            if exists:
                proactive_fork_env.setImplementationFromFile(input_data['path'])
                if input_data['code'] != '':
                    self.__kernel_print_ok_message__('WARNING: The written code is ignored.\n')
            else:
                raise Exception('The file \'' + input_data['path'] + '\' does not exist')
        else:
            proactive_fork_env.setImplementation(input_data['code'])

        self.__kernel_print_ok_message__('Saving the fork environment ...\n')
        self.default_fork_env = proactive_fork_env

        if 'force' in input_data and input_data['force'] == 'on':
            self.__kernel_print_ok_message__('Updating created tasks ...\n')
            for task in self.proactive_tasks:
                self.__kernel_print_ok_message__('Setting the fork environment of the task \'' + task.getTaskName()
                                                 + '\' ...\n')
                task.setForkEnvironment(self.default_fork_env)
                self.job_up_to_date = False

        self.__kernel_print_ok_message__('Done.\n')

    def __get_task_from_name__(self, name):
        for task in self.proactive_tasks:
            if task.getTaskName() == name:
                return task
        return None

    def __print_all_dependencies(self):
        for son_task in self.proactive_tasks:
            self.__kernel_print_ok_message__('Task \'' + son_task.getTaskName() + '\':\n')
            dependencies = son_task.getDependencies()
            for parent_task in dependencies:
                self.__kernel_print_ok_message__('   ' + parent_task.getTaskName() +
                                                 ' -> ' + son_task.getTaskName() + '\n')

    def __add_dependency__(self, proactive_task, input_data):
        for task_name in input_data['dep']:
            if proactive_task.getTaskName() == task_name:
                continue
            task = self.__get_task_from_name__(task_name)
            if task is not None and task not in proactive_task.getDependencies():
                proactive_task.addDependency(task)
                self.__kernel_print_ok_message__('Dependence \'' + task_name + '\'==>\'' + input_data['name'] +
                                                 '\' added.\n')
            elif task is None:
                self.__kernel_print_ok_message__('WARNING: Task \'' + task_name + '\' does not exist, '
                                                                                  'dependence ignored.\n')

    def __isExported__(self, var_name):
        for task_name in self.exported_vars:
            if var_name in self.exported_vars[task_name]:
                return True
        return False

    def __set_default_selection_script__(self, proactive_task):
        if self.default_selection_script is not None:
            self.__kernel_print_ok_message__('Adding job selection script to the proactive task ...\n')
            proactive_task.setSelectionScript(self.default_selection_script)
        elif proactive_task.getSelectionScript() is None:
            self.__kernel_print_ok_message__('Adding default selection script to the proactive task ...\n')
            self.__create_selection_script_from_task__({'code': 'selected = True', 'task': proactive_task})

    def __set_default_fork_environment__(self, proactive_task):
        if self.default_fork_env is not None:
            self.__kernel_print_ok_message__('Adding job fork environment to the proactive task ...\n')
            proactive_task.setForkEnvironment(self.default_fork_env)

    def __set_dependencies_from_input_data__(self, proactive_task, input_data):
        if 'dep' in input_data:
            self.__add_dependency__(proactive_task, input_data)

    def __set_generic_information_from_input_data__(self, proactive_task, input_data):
        if 'generic_info' in input_data:
            self.__kernel_print_ok_message__('Adding generic information ...\n')
            for gen_info in input_data['generic_info']:
                proactive_task.addGenericInformation(gen_info[0], gen_info[1])

    def __add_importing_variables_to_implementation_script__(self, input_data):
        if 'import' in input_data:
            self.__kernel_print_ok_message__('Adding importing variables script ...\n')
            for var_name in input_data['import']:
                input_data['code'] = var_name + ' = variables.get("' + var_name + '")\n' + input_data['code']

    def __add_exporting_variables_to_implementation_script__(self, input_data):
        if 'export' in input_data:
            self.__kernel_print_ok_message__('Adding exporting variables script ...\n')
            self.exported_vars[input_data['name']] = []
            isAPythonTask = 'language' not in input_data \
                            or ('language' in input_data and input_data['language'] == 'Python')
            if isAPythonTask:
                input_data['code'] = input_data['code'] + '\ntry:'
            for var_name in input_data['export']:
                if isAPythonTask:
                    input_data['code'] = input_data['code'] + '\n' + \
                                         '\tvariables.put("' + var_name + '", ' + var_name + ')'
                else:
                    input_data['code'] = input_data['code'] + '\nvariables.put("' + var_name + '", ' + var_name + ')'
                self.exported_vars[input_data['name']].append(var_name)

            if isAPythonTask:
                input_data['code'] = input_data['code'] + \
                                     '\nexcept Exception:' \
                                     '\n\tprint("WARNING: Some exported variables are undefined. Please check.")'

    def __add_job_imports_to_implementation_script__(self, input_data):
        if 'language' in input_data:
            if input_data['language'] in self.imports:
                self.__kernel_print_ok_message__('Adding \'' + input_data['language'] + '\' library imports ...\n')
                input_data['code'] = self.imports[input_data['language']] + '\n' + input_data['code']
        else:
            if 'Python' in self.imports:
                self.__kernel_print_ok_message__('Adding \'Python\' library imports ...\n')
                input_data['code'] = self.imports['Python'] + '\n' + input_data['code']

    def __set_implementation_script_from_input_data__(self, proactive_task, input_data):
        if 'path' in input_data:
            proactive_task.setTaskImplementationFromFile(input_data['path'])
            if input_data['code'] != '':
                self.__kernel_print_ok_message__('WARNING: The written code is ignored.\n')
        else:
            proactive_task.setTaskImplementation(input_data['code'])

    def __create_task__(self, input_data):
        # Verifying if imported variables have been exported in other tasks
        if 'import' in input_data:
            for var_name in input_data['import']:
                if not self.__isExported__(var_name):
                    raise ParameterError('The variable \'' + var_name + '\' can\'t be imported.')

        if input_data['name'] in self.tasks_names:
            self.__kernel_print_ok_message__('WARNING: Task \'' + input_data['name'] + '\' already exists ...\n')
            proactive_task = self.__get_task_from_name__(input_data['name'])
            proactive_task.clearDependencies()
            proactive_task.clearGenericInformation()
            if input_data['name'] in self.exported_vars:
                del self.exported_vars[input_data['name']]

            if 'language' in input_data:
                if input_data['language'] in self.proactive_script_languages:
                    self.__kernel_print_ok_message__('Changing script language to \'' + input_data['language']
                                                     + '\' ...\n')
                    proactive_task.setScriptLanguage(self.proactive_script_languages[input_data['language']])
                else:
                    raise ParameterError('Language \'' + input_data['language'] +
                                         '\' not supported!\n Supported Languages:\n' + self.script_languages)
            else:
                self.__kernel_print_ok_message__('Changing script language to \'Python\' ...\n')
                proactive_task.setScriptLanguage(self.proactive_script_languages['Python'])

        else:
            if 'language' in input_data:
                if input_data['language'] in self.proactive_script_languages:
                    self.__kernel_print_ok_message__('Creating a proactive ' + input_data['language'] + ' task ...\n')
                    proactive_task = self.gateway.createTask(self.proactive_script_languages[input_data['language']])
                elif input_data['language'] == 'Python':
                    self.__kernel_print_ok_message__('Creating a proactive \'Python\' task ...\n')
                    proactive_task = self.gateway.createPythonTask()
                else:
                    raise ParameterError('Language \'' + input_data['language'] +
                                         '\' not supported!\n Supported Languages:\n' + self.script_languages)
            else:
                self.__kernel_print_ok_message__('Creating a proactive \'Python\' task ...\n')
                proactive_task = self.gateway.createPythonTask()

            if input_data['name'] == '':
                name = self.__get_unique_task_name__()
                self.__kernel_print_ok_message__('WARNING: Task \'' + input_data['name'] + '\' renamed to : '
                                                 + name + '\n')
                input_data['name'] = name

            proactive_task.setTaskName(input_data['name'])

            self.__kernel_print_ok_message__('Task \'' + input_data['name'] + '\' created.\n')

            self.proactive_tasks.append(proactive_task)
            self.tasks_names.append(input_data['name'])

            self.tasks_count += 1

        self.__set_default_selection_script__(proactive_task)
        self.__set_default_fork_environment__(proactive_task)
        self.__set_dependencies_from_input_data__(proactive_task, input_data)
        self.__set_generic_information_from_input_data__(proactive_task, input_data)

        # TODO: check how to import/export variables when a file path is provided
        self.__add_importing_variables_to_implementation_script__(input_data)
        self.__add_exporting_variables_to_implementation_script__(input_data)
        self.__add_job_imports_to_implementation_script__(input_data)
        self.__set_implementation_script_from_input_data__(proactive_task, input_data)

        self.previous_task_history = input_data
        self.is_previous_pragma_task = True
        self.last_modified_task = proactive_task

        self.__kernel_print_ok_message__('Done.\n')
        self.job_up_to_date = False

        return 0

    def __create_split__(self, input_data):
        input_data['trigger'] = 'task'
        if 'name' not in input_data or input_data['name'] == '':
            input_data['name'] = self.__get_unique_task_name__('split')
        self.__create_task__(input_data)
        self.__kernel_print_ok_message__('Setting the flow block ...\n')
        self.last_modified_task.setFlowBlock(self.gateway.getProactiveFlowBlockType().start())
        return 0

    def __add_runs__(self, input_data):
        self.__kernel_print_ok_message__('Adding the REPLICATE flow script ...\n')
        flow_script = self.gateway.createReplicateFlowScript(input_data['code'])
        self.last_modified_task.setFlowScript(flow_script)
        self.__kernel_print_ok_message__('Done.\n')
        return 0

    def __create_process__(self, input_data):
        input_data['trigger'] = 'task'
        if 'name' not in input_data or input_data['name'] == '':
            input_data['name'] = 'process' + re.findall(r'\d+', self.previous_task_history['name']).pop()
        if 'dep' not in input_data:
            input_data['dep'] = [self.last_modified_task.getTaskName()]
        self.__create_task__(input_data)
        return 0

    def __create_merge__(self, input_data):
        input_data['trigger'] = 'task'
        if 'name' not in input_data or input_data['name'] == '':
            input_data['name'] = 'merge' + re.findall(r'\d+', self.previous_task_history['name']).pop()
        if 'dep' not in input_data:
            input_data['dep'] = [self.last_modified_task.getTaskName()]
        self.__create_task__(input_data)
        self.__kernel_print_ok_message__('Setting the flow block ...\n')
        self.last_modified_task.setFlowBlock(self.gateway.getProactiveFlowBlockType().end())
        return 0

    def __clean_related_dependencies__(self, removed_task):
        for task in self.proactive_tasks:
            if removed_task in task.getDependencies():
                task.removeDependency(removed_task)

    def __delete_task__(self, input_data):
        if input_data['name'] in self.tasks_names:
            task_to_remove = self.__get_task_from_name__(input_data['name'])
        else:
            raise ParameterError('Task \'' + input_data['name'] + '\' does not exist.')

        if self.job_created:
            self.__kernel_print_ok_message__('Deleting task from the job...\n')
            self.proactive_job.removeTask(task_to_remove)

        self.__kernel_print_ok_message__('Deleting task from the tasks list...\n')
        self.proactive_tasks.remove(task_to_remove)
        self.tasks_names.remove(input_data['name'])

        self.__kernel_print_ok_message__('Cleaning dependencies...\n')
        self.__clean_related_dependencies__(task_to_remove)

        if input_data['name'] in self.exported_vars:
            del self.exported_vars[input_data['name']]

        self.__kernel_print_ok_message__('Done.\n')

        self.job_up_to_date = False

        return

    def __create_job__(self, input_data):
        if self.job_created and self.job_up_to_date:
            self.__set_job_name__(input_data['name'])
            self.__kernel_print_ok_message__('Job renamed to \'' + input_data['name'] + '\'.\n')
            return 0

        if self.job_created:
            self.__kernel_print_ok_message__('Re-creating the proactive job due to tasks changes ...\n')
        else:
            self.__kernel_print_ok_message__('Creating a proactive job ...\n')

        self.proactive_job = self.gateway.createJob()
        self.__set_job_name__(input_data['name'])

        self.__kernel_print_ok_message__('Job \'' + input_data['name'] + '\' created.\n')

        self.__kernel_print_ok_message__('Adding the created tasks to \'' + input_data['name'] + '\' ...\n')
        for task in self.proactive_tasks:
            self.proactive_job.addTask(task)

        # TODO:
        #  if input_data['input_folder'] is None, use the `tmpdir` variable
        #  same for input_data['output_folder']
        tmpdir = tempfile.mkdtemp(dir=tempfile.gettempdir())
        self.proactive_job.setInputFolder(tmpdir)
        self.proactive_job.setOutputFolder(tmpdir)

        self.__kernel_print_ok_message__('Done.\n')
        self.job_created = True
        self.job_up_to_date = True

        return 0

    def __set_job_name__(self, name):
        self.proactive_job.setJobName(name)
        self.job_name = name
        return 0

    def __get_job_id_from_inputs__(self, input_data):
        if 'job_id' in input_data:
            return input_data['job_id']
        if 'job_name' in input_data and input_data['job_name'] != '':
            if input_data['job_name'] not in self.submitted_jobs_ids:
                raise ResultError("The job named \'" + input_data['job_name'] + "\' does not exist.")
            return self.submitted_jobs_ids[input_data['job_name']]
        raise ParameterError('Invalid parameters and validation step. Please check.')

    def __get_job_result__(self, input_data):
        job_id = self.__get_job_id_from_inputs__(input_data)
        self.__kernel_print_ok_message__('Getting job ' + job_id + ' results ...\n')

        try:
            job_result = self.gateway.getJobResult(job_id)
        except Exception:
            raise ResultError("Results unreachable for job: " + job_id)

        self.__kernel_print_ok_message__('Results:\n')
        self.__kernel_print_ok_message__(job_result)

    def __get_task_result__(self, input_data):
        job_id = self.__get_job_id_from_inputs__(input_data)
        self.__kernel_print_ok_message__('Getting from job ' + job_id + ', task \'' + input_data['task_name']
                                         + '\' results ...\n')

        try:
            task_result = self.gateway.getTaskResult(job_id, input_data['task_name'])
        except Exception:
            raise ResultError("Results unreachable for job: " + job_id)

        self.__kernel_print_ok_message__('Result:\n')
        self.__kernel_print_ok_message__(str(task_result))

    def __print_job_output__(self, input_data):
        job_id = self.__get_job_id_from_inputs__(input_data)
        self.__kernel_print_ok_message__('Getting job ' + job_id + ' console outputs ...\n')

        try:
            job_result = self.gateway.printJobOutput(job_id)
        except Exception:
            raise ResultError("Results unreachable for job: " + job_id)

        self.__kernel_print_ok_message__('Outputs:\n')
        self.__kernel_print_ok_message__(job_result)

    def __print_task_output__(self, input_data):
        job_id = self.__get_job_id_from_inputs__(input_data)
        self.__kernel_print_ok_message__('Getting from job ' + job_id + ', task \'' + input_data['task_name']
                                         + '\' console output ...\n')

        try:
            task_result = self.gateway.printTaskOutput(job_id, input_data['task_name'])
        except Exception:
            raise ResultError("Results unreachable for job: " + job_id)

        self.__kernel_print_ok_message__('Output:\n')
        self.__kernel_print_ok_message__(str(task_result))

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

        self.__kernel_print_ok_message__('Submitting the job to the proactive scheduler ...\n')

        temp_id = self.gateway.submitJob(self.proactive_job, debug=False)
        self.submitted_jobs_names[temp_id] = self.job_name
        self.submitted_jobs_ids[self.job_name] = temp_id

        self.__kernel_print_ok_message__('job_id: ' + str(temp_id) + '\n')

        return 0

    def __list_submitted_jobs__(self, input_data):
        for job_id in self.submitted_jobs_names:
            self.__kernel_print_ok_message__('Id: ' + str(job_id) + ' , Name: ' + self.submitted_jobs_names[job_id]
                                             + '\n')

    @staticmethod
    def __merge_scripts__(code1, code2):
        _code = code1.split('\ntry:\n\tvariables.put')
        if len(_code) == 2:
            _code = _code[0] + '\n' + code2 + '\ntry:\n\tvariables.put' + _code[1]
        else:
            _code = _code[0] + '\n' + code2
        return _code

    def __preprocess_pragma_block__(self, pragma_info):
        pragma_string = pragma_info['code'].split("\n", 1)

        if len(pragma_string) == 2:
            pragma_info['code'] = pragma_string.pop(1)
        else:
            pragma_info['code'] = ''
        pragma_string = pragma_string[0]

        try:
            pragma_info.update(self.pragma.parse(pragma_string))
        except ParsingError as pe:
            errorValue = self.__kernel_print_error_message({'ename': 'Parsing error', 'evalue': pe.strerror})
            self.__print_usage_from_pragma__(pragma_string)
            return errorValue
        except ParameterError as pe:
            return self.__kernel_print_error_message({'ename': 'Parameter error', 'evalue': pe.strerror})

        if self.proactive_connected:
            try:
                pragma_info['func'] = self.__trigger_pragma__(pragma_info)
            except PragmaError as pe:
                return self.__kernel_print_error_message({'ename': 'Pragma error', 'evalue': pe.strerror})

        elif pragma_info['trigger'] == 'connect':
            pragma_info['func'] = self.__connect__
        elif pragma_info['trigger'] == 'help':
            pragma_info['func'] = self.__help__
        elif pragma_info['trigger'] == 'configure':
            pragma_info['func'] = self.__configure__
        elif pragma_info['trigger'] in Pragma.pragmas_connected_mode:
            return self.__kernel_print_error_message({'ename': 'Proactive error',
                                                      'evalue': 'Use #%connect() to connect to server first.'})
        else:
            return self.__kernel_print_error_message({'ename': 'Pragma error', 'evalue':
                'Directive \'' + pragma_info['trigger']
                + '\' not known.'})
        return pragma_info

    def __process_pragma_block__(self, pragma_info):

        # TODO: compile python code even when creating a task
        if 'language' in pragma_info and pragma_info['language'] == 'Python':
            try:
                ast.parse(pragma_info['code'])
            except SyntaxError as e:
                return self.__kernel_print_error_message({'ename': 'Syntax error', 'evalue': str(e)})

        try:
            if not self.proactive_connected and pragma_info['trigger'] not in Pragma.pragmas_not_connected_mode:
                return self.__kernel_print_error_message({'ename': 'Proactive error',
                                                          'evalue': 'Use \'#%connect()\' to '
                                                                    'connect to proactive server first.'})

            if self.proactive_default_connection and pragma_info['trigger'] not in Pragma.pragmas_not_connected_mode:
                self.__kernel_print_ok_message__('WARNING: Proactive is connected by default on \''
                                                 + self.gateway.base_url + '\'.\n')

            # TODO: use more functions to reduce do_execute size

            try:
                exitcode = pragma_info['func'](pragma_info)
            except ConfigError as ce:
                return self.__kernel_print_error_message({'ename': 'Proactive config error', 'evalue': ce.strerror})
            except ParameterError as pe:
                return self.__kernel_print_error_message({'ename': 'Parameter error', 'evalue': pe.strerror})
            except ResultError as rer:
                return self.__kernel_print_error_message(
                    {'ename': 'Proactive result error', 'evalue': rer.strerror})
            except AssertionError as ae:
                return self.__kernel_print_error_message({'ename': 'Proactive connexion error', 'evalue': str(ae)})

        except Exception as e:
            return self.__kernel_print_error_message({'ename': 'Proactive error', 'evalue': str(e)})

        return exitcode

    def __execute_block__(self, code):
        pragma_info = {'name': '', 'trigger': 'task', 'code': code, 'func': self.__create_task__}

        if re.match(self.pattern_pragma, code):
            pragma_info = self.__preprocess_pragma_block__(pragma_info)
            if 'execution_count' in pragma_info:
                return pragma_info

        return self.__process_pragma_block__(pragma_info)

    def __execute_multiblock__(self, code):
        pragma_info = {'name': '', 'trigger': 'task', 'code': code, 'func': self.__create_task__}

        if re.match(self.pattern_pragma, code):
            pragma_info = self.__preprocess_pragma_block__(pragma_info)
            if 'execution_count' in pragma_info:
                return pragma_info
            if pragma_info['trigger'] != 'task':
                self.is_previous_pragma_task = False
            exitcode = self.__process_pragma_block__(pragma_info)
        else:
            if self.is_previous_pragma_task:
                self.__kernel_print_ok_message__('Adding current script to task \'' +
                                                 self.previous_task_history['name'] + '\'.\n')
                updated_code = ProActiveKernel.__merge_scripts__(self.previous_task_history['code'],
                                                                 pragma_info['code'])
                pragma_info.update(self.previous_task_history)
                pragma_info['code'] = updated_code
                proactive_task = self.__get_task_from_name__(pragma_info['name'])
                proactive_task.setTaskImplementation(pragma_info['code'])
                self.previous_task_history.update(pragma_info)
                self.__kernel_print_ok_message__('Done.\n')
                exitcode = 0
            else:
                return self.__kernel_print_error_message({'ename': 'Pragma error',
                                                          'evalue': 'Blocks should be started by pragmas.'})
        return exitcode

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        self.silent = silent
        if not code.strip():
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

        interrupted = False

        if self.proactive_failed_connection:
            self.__kernel_print_error_message({'ename': 'Proactive connexion error',
                                               'evalue': 'Please, reconfigure proactive connection and restart kernel'})

            return self.__kernel_print_error_message({'ename': 'Error', 'evalue': self.error_message})

        try:
            if self.multiblock_task_config:
                exitcode = self.__execute_multiblock__(code)
            else:
                exitcode = self.__execute_block__(code)

            if exitcode:
                return exitcode

        except KeyboardInterrupt:
            interrupted = True
            exitcode = 134
        except Exception as e:
            exitcode = e

        if interrupted:
            self.__kernel_print_ok_message__('Interrupted!')
            return {'status': 'abort', 'execution_count': self.execution_count, 'evalue': exitcode}

        if exitcode:
            error_content = self.__kernel_print_error_message({'ename': 'Error', 'evalue': str(exitcode)})
            error_content['status'] = 'error'
            return error_content

        else:
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

    def do_shutdown(self, restart):
        if self.gateway is not None:
            self.gateway.disconnect()
            self.gateway.terminate()
        return {'status': 'ok', 'restart': restart}
