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
        self.last_submitted_job_id = None
        self.tasks_names = []
        self.tasks_count = 0
        self.proactive_config = {}
        self.proactive_connected = False
        self.proactive_default_connection = True
        self.proactive_failed_connection = False
        self.error_message = ''
        self.graph_up_to_date = False
        self.graph = None
        self.node_labels = {}
        self.edge_labels = {}
        self.pragma = Pragma()
        self.imports = {}
        self.default_selection_script = None
        self.default_fork_env = None
        self.multiblock_task_config = False
        self.semaphore_controls = 0

        self.replicated_tasks = []

        self.previous_task_history = {}
        self.is_previous_pragma_task = False
        self.last_modified_task = None
        self.saved_flow_script = None
        self.saved_branch_task = None

        self.exported_vars = {}

        self.proactive_script_languages = ProactiveScriptLanguage().get_supported_languages()

        self.script_languages = ''
        for script_language in self.proactive_script_languages:
            self.script_languages += '   - ' + script_language + '\n'

        try:
            self.__start_proactive__()
        except ConfigError as ce:
            self.proactive_failed_connection = True
            self.error_message = str(ce)
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

                if 'host' in self.proactive_config['proactive_server']:
                    proactive_protocol = self.proactive_config['proactive_server']['protocol']
                    proactive_host = self.proactive_config['proactive_server']['host']
                    proactive_port = self.proactive_config['proactive_server']['port']
                    proactive_url = proactive_protocol + "://" + proactive_host + ":" + proactive_port
                    self.proactive_config['proactive_server']['url'] = proactive_url
                elif 'url' in self.proactive_config['proactive_server']:
                    proactive_url = self.proactive_config['proactive_server']['url']
                else:
                    raise ConfigError('Activeeon server host and url not found in the config file.')

                self.gateway = proactive.ProActiveGateway(proactive_url)

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

    def __get_unique_task_name__(self, name_base='DT'):
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
        elif pragma_info['trigger'] == 'start':
            return self.__create_start__
        elif pragma_info['trigger'] == 'loop':
            return self.__create_loop__
        elif pragma_info['trigger'] == 'condition':
            return self.__add_condition__
        elif pragma_info['trigger'] == 'branch':
            return self.__create_branch__
        elif pragma_info['trigger'] == 'if':
            return self.__create_if__
        elif pragma_info['trigger'] == 'else':
            return self.__create_else__
        elif pragma_info['trigger'] == 'continuation':
            return self.__create_continuation__
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
        elif pragma_info['trigger'] == 'runtime_env':
            return self.__create_runtime_environment__
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
            url = os.path.join(self.proactive_config['proactive_server']['url'], input_data['portal'])

        width = input_data['width'] if 'width' in input_data else 1200
        height = input_data['height'] if 'height' in input_data else 750
        data = IFrame(url, width=width, height=height)

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
        pos = graphviz_layout(self.graph, prog='dot')

        # nodes
        nx.draw_networkx_nodes(self.graph, pos,
                               node_color='orange',
                               node_size=3000,
                               alpha=0.5)

        # edges
        nx.draw_networkx_edges(self.graph, pos,
                               arrowstyle='->',
                               arrowsize=50,
                               edge_color='green',
                               width=2,
                               alpha=0.5)

        nx.draw_networkx_labels(self.graph, pos,
                                self.node_labels,
                                font_size=13)

        nx.draw_networkx_edge_labels(self.graph, pos,
                                     alpha=0.7,
                                     font_size=9,
                                     edge_labels=self.edge_labels)

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
        if not self.graph_up_to_date:
            self.__kernel_print_ok_message__('Creating the job workflow ...\n')
            self.graph = nx.DiGraph()
            self.node_labels.clear()
            self.edge_labels.clear()

            # nodes
            nodes_ids = [i for i in range(len(self.proactive_tasks))]
            self.graph.add_nodes_from(nodes_ids)

            # edges
            for index_son in range(len(self.proactive_tasks)):
                dependencies = self.proactive_tasks[index_son].getDependencies()
                for parent_task in dependencies:
                    index_parent = self.proactive_tasks.index(parent_task)
                    self.graph.add_edge(index_parent, index_son)
                    if parent_task.hasFlowScript():
                        if parent_task.getFlowScript().isReplicateFlowScript():
                            self.edge_labels[(index_parent, index_son)] = 'replicate'
                    if self.proactive_tasks[index_son].hasFlowScript():
                        if self.proactive_tasks[index_son].getFlowScript().isLoopFlowScript():
                            self.graph.add_edge(index_son, index_parent)
                            self.edge_labels[(index_son, index_parent)] = 'loop'

            # branching edges
            for index_parent in range(len(self.proactive_tasks)):
                parent_task = self.proactive_tasks[index_parent]
                if parent_task.hasFlowScript():
                    parent_flow_script = parent_task.getFlowScript()
                    if parent_flow_script.isBranchFlowScript():
                        if_task_index = self.__find_task_index_from_name__(parent_flow_script.getActionTarget())
                        else_task_index = self.__find_task_index_from_name__(parent_flow_script.getActionTargetElse())
                        continuation_task_index = self.__find_task_index_from_name__(parent_flow_script.getActionTargetContinuation())

                        self.graph.add_edge(index_parent, if_task_index)
                        self.graph.add_edge(index_parent, else_task_index)
                        self.graph.add_edge(index_parent, continuation_task_index)

                        self.edge_labels[(index_parent, if_task_index)] = 'if'
                        self.edge_labels[(index_parent, else_task_index)] = 'else'
                        self.edge_labels[(index_parent, continuation_task_index)] = 'continuation'

            # node labels
            for i in nodes_ids:
                # some math labels
                self.node_labels[i] = r'$' + self.proactive_tasks[i].getTaskName() + '$'

            self.graph_up_to_date = True
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

                    if 'host' in self.proactive_config['proactive_server']:
                        proactive_protocol = self.proactive_config['proactive_server']['protocol']
                        proactive_host = self.proactive_config['proactive_server']['host']
                        proactive_port = self.proactive_config['proactive_server']['port']
                        proactive_url = proactive_protocol + "://" + proactive_host + ":" + proactive_port
                        self.proactive_config['proactive_server']['url'] = proactive_url
                    elif 'url' in self.proactive_config['proactive_server']:
                        proactive_url = self.proactive_config['proactive_server']['url']
                    else:
                        raise ConfigError('Activeeon server host and url not found in the config file.')

                    self.gateway = proactive.ProActiveGateway(proactive_url)
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
            if 'port' in input_data:
                self.proactive_config['proactive_server']['port'] = input_data['port']
            else:
                self.proactive_config['proactive_server']['port'] = '8080'
            proactive_url = "http://" + self.proactive_config['proactive_server']['host'] + ":" + \
                            self.proactive_config['proactive_server']['port']
            self.proactive_default_connection = False
        elif 'port' in input_data:
            self.proactive_config['proactive_server']['port'] = input_data['port']
            self.proactive_config['proactive_server']['host'] = 'try.activeeon.com'
            proactive_url = "http://" + self.proactive_config['proactive_server']['host'] + ":" + \
                            self.proactive_config['proactive_server']['port']
            self.proactive_default_connection = False
        elif 'url' in input_data:
            proactive_url = input_data['url']
            self.proactive_default_connection = False
        else:
            self.proactive_config['proactive_server']['host'] = 'try.activeeon.com'
            self.proactive_config['proactive_server']['port'] = '8080'
            proactive_url = "http://" + self.proactive_config['proactive_server']['host'] + ":" + \
                            self.proactive_config['proactive_server']['port']
            self.proactive_default_connection = True

        self.proactive_config['proactive_server']['url'] = proactive_url

        self.gateway = proactive.ProActiveGateway(proactive_url)

        if 'login' not in input_data:
            input_data['login'] = self.raw_input("Login: ")

        if 'password' not in input_data:
            input_data['password'] = self.getpass("Password: ")

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
                                             + '#%runtime_env(): sets the default runtime environment of a job\n'
                                             + '#%split(): creates/modifies a splitting task of a replicate control\n'
                                             + '#%runs(): creates/modifies the configuration script of a replicate control\n'
                                             + '#%process(): creates/modifies the script of a replicated processing task\n'
                                             + '#%merge(): creates/modifies a merging task of a replicate control\n'
                                             + '#%start(): creates/modifies a start task of a loop control\n'
                                             + '#%loop(): creates/modifies a loop task of a loop control\n'
                                             + '#%condition(): creates/modifies the condition script of a branch/loop control\n'
                                             + '#%branch(): creates/modifies a branch task of a branching control\n'
                                             + '#%if(): creates/modifies an if task of a branching control\n'
                                             + '#%else(): creates/modifies an else task of a branching control\n'
                                             + '#%continuation(): creates/modifies a continuation task of a branching control\n'
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
            pre_script.setImplementation('\n' + input_data['code'])

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
            post_script.setImplementation('\n' + input_data['code'])

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
        if 'language' in input_data:
            if input_data['language'] in self.proactive_script_languages:
                proactive_selection_script = self.gateway.createSelectionScript(language=self.proactive_script_languages[input_data['language']])
            else:
                raise ParameterError('Language \'' + input_data['language'] +
                                     '\' not supported!\n Supported Languages:\n' + self.script_languages)
        else:
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
            proactive_selection_script.setImplementation('\n' + input_data['code'])

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
        if 'language' in input_data:
            if input_data['language'] in self.proactive_script_languages:
                proactive_selection_script = self.gateway.createSelectionScript(language=self.proactive_script_languages[input_data['language']])
            else:
                raise ParameterError('Language \'' + input_data['language'] +
                                     '\' not supported!\n Supported Languages:\n' + self.script_languages)
        else:
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
            proactive_selection_script.setImplementation('\n' + input_data['code'])

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
        if 'language' in input_data:
            if input_data['language'] in self.proactive_script_languages:
                proactive_fork_env = self.gateway.createForkEnvironment(language=self.proactive_script_languages[input_data['language']])
            else:
                raise ParameterError('Language \'' + input_data['language'] +
                                     '\' not supported!\n Supported Languages:\n' + self.script_languages)
        else:
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
            proactive_fork_env.setImplementation('\n' + input_data['code'])

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
        if 'language' in input_data:
            if input_data['language'] in self.proactive_script_languages:
                proactive_fork_env = self.gateway.createForkEnvironment(language=self.proactive_script_languages[input_data['language']])
            else:
                raise ParameterError('Language \'' + input_data['language'] +
                                     '\' not supported!\n Supported Languages:\n' + self.script_languages)
        else:
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
            proactive_fork_env.setImplementation('\n' + input_data['code'])

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

    def __build_runtime_environment__(self, input_data):
        from string import Template

        DEBUG = False
        VERBOSE = "false"

        DEFAULT_CONTAINER_PLATFORM = "docker"
        DEFAULT_CONTAINER_IMAGE = "docker://activeeon/dlm3"
        DEFAULT_CONTAINER_GPU_ENABLED = "false"
        DEFAULT_HOST_LOG_PATH = "null"
        DEFAULT_CONTAINER_LOG_PATH = "null"
        DEFAULT_CONTAINER_ROOTLESS_ENABLED = "false"
        DEFAULT_CONTAINER_ISOLATION_ENABLED = "false"
        DEFAULT_CONTAINER_NO_HOME_ENABLED = "false"
        DEFAULT_CONTAINER_HOST_NETWORK_ENABLED = "true"

        CONTAINER_PLATFORM = input_data['type'] if 'type' in input_data else DEFAULT_CONTAINER_PLATFORM
        CONTAINER_IMAGE = input_data['image'] if 'image' in input_data else DEFAULT_CONTAINER_IMAGE
        CONTAINER_GPU_ENABLED = input_data['nvidia_gpu'] if 'nvidia_gpu' in input_data else DEFAULT_CONTAINER_GPU_ENABLED
        HOST_LOG_PATH = input_data['mount_host_path'] if 'mount_host_path' in input_data else DEFAULT_HOST_LOG_PATH
        CONTAINER_LOG_PATH = input_data['mount_container_path'] if 'mount_container_path' in input_data else DEFAULT_CONTAINER_LOG_PATH
        CONTAINER_ROOTLESS_ENABLED = input_data['rootless'] if 'rootless' in input_data else DEFAULT_CONTAINER_ROOTLESS_ENABLED
        CONTAINER_ISOLATION_ENABLED = input_data['isolation'] if 'isolation' in input_data else DEFAULT_CONTAINER_ISOLATION_ENABLED
        CONTAINER_NO_HOME_ENABLED = input_data['no_home'] if 'no_home' in input_data else DEFAULT_CONTAINER_NO_HOME_ENABLED
        CONTAINER_HOST_NETWORK_ENABLED = input_data['host_network'] if 'host_network' in input_data else DEFAULT_CONTAINER_HOST_NETWORK_ENABLED

        if 'debug' in input_data and str.lower(input_data['debug']) == "true":
            DEBUG = True

        if 'verbose' in input_data and str.lower(input_data['verbose']) == "true":
            VERBOSE = "true"

        params = {
            'CONTAINER_PLATFORM': CONTAINER_PLATFORM,
            'CONTAINER_IMAGE': CONTAINER_IMAGE,
            'CONTAINER_GPU_ENABLED': CONTAINER_GPU_ENABLED,
            'HOST_LOG_PATH': HOST_LOG_PATH,
            'CONTAINER_LOG_PATH': CONTAINER_LOG_PATH,
            'CONTAINER_ROOTLESS_ENABLED': CONTAINER_ROOTLESS_ENABLED,
            'CONTAINER_ISOLATION_ENABLED': CONTAINER_ISOLATION_ENABLED,
            'CONTAINER_NO_HOME_ENABLED': CONTAINER_NO_HOME_ENABLED,
            'CONTAINER_HOST_NETWORK_ENABLED': CONTAINER_HOST_NETWORK_ENABLED,
            'VERBOSE': VERBOSE
        }

        if DEBUG:
            self.__kernel_print_ok_message__(str(params) + '\n')

        template = Template('''
/*
This template creates a runtime environment for containers-based jobs supporting docker, podman, and singularity.

Variables:
 - CONTAINER_PLATFORM: docker, podman, singularity or null/empty (none)
 - CONTAINER_IMAGE: container image name (default=activeeon/dlm3)
 - CONTAINER_GPU_ENABLED: true/false, set to false to disable gpu support (default=true)
 - HOST_LOG_PATH: optional host path to store logs
 - CONTAINER_LOG_PATH: mounting point of optional logs in the container
 - CONTAINER_ROOTLESS_ENABLED: true/false, set to false to disable rootless mode (default=false)

If used on windows:
 - currently, only linux containers are supported
 - make sure the drives containing the scheduler installation and TEMP folders are shared with docker containers
 - the container used must have java installed by default in the /usr folder. Change the value of the java home parameter to use a different installation path

On linux, the java installation used by the ProActive Node will be also used inside the container
*/

import org.ow2.proactive.utils.OperatingSystem
import org.ow2.proactive.utils.OperatingSystemFamily
import org.codehaus.groovy.runtime.StackTraceUtils

def VERBOSE = $VERBOSE
def CONTAINER_PLATFORM = "$CONTAINER_PLATFORM"
def CONTAINER_IMAGE = "$CONTAINER_IMAGE"
def CONTAINER_GPU_ENABLED = $CONTAINER_GPU_ENABLED
def HOST_LOG_PATH = "$HOST_LOG_PATH"
def CONTAINER_LOG_PATH = "$CONTAINER_LOG_PATH"
def CONTAINER_ROOTLESS_ENABLED = $CONTAINER_ROOTLESS_ENABLED
def CONTAINER_ISOLATION_ENABLED = $CONTAINER_ISOLATION_ENABLED
def CONTAINER_NO_HOME_ENABLED = $CONTAINER_NO_HOME_ENABLED
def CONTAINER_HOST_NETWORK_ENABLED = $CONTAINER_HOST_NETWORK_ENABLED

def SUPPORTED_PLATFORMS = ["docker", "podman", "singularity"]
def CONTAINER_ENABLED = SUPPORTED_PLATFORMS.any{it.equalsIgnoreCase(CONTAINER_PLATFORM)}

def CUDA_ENABLED = false
def CUDA_HOME = System.getenv('CUDA_HOME')
def CUDA_HOME_DEFAULT = "/usr/local/cuda"
if (CUDA_HOME && (new File(CUDA_HOME)).isDirectory()) {
    CUDA_ENABLED = true
} else if ((new File(CUDA_HOME_DEFAULT)).isDirectory()) {
    CUDA_ENABLED = true
}
if (!CUDA_ENABLED) {
    CONTAINER_GPU_ENABLED = false
}

if ((new File("/.dockerenv")).exists() && ! (new File("/var/run/docker.sock")).exists()) {
    println ("Already inside docker container, without host docker access")
    CONTAINER_ENABLED = false
}

if (CONTAINER_ENABLED) {
    try {
        def sout = new StringBuffer(), serr = new StringBuffer()
        def proc = (CONTAINER_PLATFORM + ' --help').execute()
        proc.consumeProcessOutput(sout, serr)
        proc.waitForOrKill(10000)
    } catch (Exception e) {
        println CONTAINER_PLATFORM + " does not exists : " + e.getMessage()
        CONTAINER_ENABLED = false
    }
}

if (VERBOSE) {
    println "Fork environment info..."
    println "CONTAINER_ENABLED:              " + CONTAINER_ENABLED
    println "CONTAINER_PLATFORM:             " + CONTAINER_PLATFORM
    println "CONTAINER_IMAGE:                " + CONTAINER_IMAGE
    println "CONTAINER_GPU_ENABLED:          " + CONTAINER_GPU_ENABLED
    println "CUDA_ENABLED:                   " + CUDA_ENABLED
    println "HOST_LOG_PATH:                  " + HOST_LOG_PATH
    println "CONTAINER_LOG_PATH:             " + CONTAINER_LOG_PATH
    println "CONTAINER_NO_HOME_ENABLED:      " + CONTAINER_NO_HOME_ENABLED
    println "CONTAINER_ROOTLESS_ENABLED:     " + CONTAINER_ROOTLESS_ENABLED
    println "CONTAINER_HOST_NETWORK_ENABLED: " + CONTAINER_HOST_NETWORK_ENABLED
}

String osName = System.getProperty("os.name")
if (VERBOSE) {
    println "Operating system : " + osName
}
OperatingSystem operatingSystem = OperatingSystem.resolveOrError(osName)
OperatingSystemFamily family = operatingSystem.getFamily()

// If docker or podman
if (CONTAINER_ENABLED && (
    "docker".equalsIgnoreCase(CONTAINER_PLATFORM) ||
    "podman".equalsIgnoreCase(CONTAINER_PLATFORM))) {

    if (CONTAINER_IMAGE.startsWith("docker://")) {
        CONTAINER_IMAGE = CONTAINER_IMAGE.substring(CONTAINER_IMAGE.indexOf("://") + 3)
    }

    // Prepare Docker parameters
    containerName = CONTAINER_IMAGE
    cmd = []
    cmd.add(CONTAINER_PLATFORM.toLowerCase())
    cmd.add("run")
    cmd.add("--rm")
    cmd.add("--shm-size=256M")

    if (CONTAINER_HOST_NETWORK_ENABLED) {
        cmd.add("--network=host")
    }

    if (CONTAINER_ROOTLESS_ENABLED) {
        cmd.add("--env")
        cmd.add("HOME=/tmp")
    }

    if (CUDA_ENABLED && CONTAINER_GPU_ENABLED) {
        if ("docker".equalsIgnoreCase(CONTAINER_PLATFORM)) {
            // Versions earlier than 19.03 require nvidia-docker2 and the --runtime=nvidia flag.
            // On versions including and after 19.03, you will use the nvidia-container-toolkit package
            // and the --gpus all flag.
            try {
                def sout = new StringBuffer(), serr = new StringBuffer()
                def proc = 'docker version -f "{{.Server.Version}}"'.execute()
                proc.consumeProcessOutput(sout, serr)
                proc.waitForOrKill(10000)
                docker_version = sout.toString()
                docker_version = docker_version.substring(1, docker_version.length()-2)
                docker_version_major = docker_version.split("\\\\.")[0].toInteger()
                docker_version_minor = docker_version.split("\\\\.")[1].toInteger()
                if (VERBOSE) {
                    println "Docker version: " + docker_version
                }
                if ((docker_version_major >= 19) && (docker_version_minor >= 3)) {
                    cmd.add("--gpus=all")
                } else {
                    cmd.add("--runtime=nvidia")
                }
            } catch (Exception e) {
                println "Error while getting the docker version: " + e.getMessage()
                println "DOCKER_GPU_ENABLED is off"
            }
        } else {
            cmd.add("--runtime=nvidia")
        }
        // rootless containers leveraging NVIDIA GPUs
        // needed when cgroups is disabled in nvidia-container-runtime
        // /etc/nvidia-container-runtime/config.toml => no-cgroups = true
        cmd.add("--privileged") // https://github.com/NVIDIA/nvidia-docker/issues/1171
    }
 
    isWindows = false
    isMac = false
    switch (family) {
        case OperatingSystemFamily.WINDOWS:
            isWindows = true
            break
        case OperatingSystemFamily.MAC:
            isMac = true
            break
    }
    forkEnvironment.setDockerWindowsToLinux(isWindows)

    paContainerName = System.getProperty("proactive.container.name")
    isPANodeInContainer = (paContainerName != null && !paContainerName.isEmpty())
    paContainerHostAddress = System.getProperty("proactive.container.host.address")

    if (isPANodeInContainer) {
        cmd.add("--volumes-from")
        cmd.add(paContainerName)
        cmd.add("--add-host")
        cmd.add("service-node:" + paContainerHostAddress)
    }

    // Prepare ProActive home volume
    paHomeHost = variables.get("PA_SCHEDULER_HOME")
    paHomeContainer = (isWindows ? forkEnvironment.convertToLinuxPath(paHomeHost) : paHomeHost)
    if (!isPANodeInContainer) {
        cmd.add("-v")
        cmd.add(paHomeHost + ":" + paHomeContainer)
    }
    // Prepare working directory (For Dataspaces and serialized task file)
    workspaceHost = localspace
    workspaceContainer = (isWindows ? forkEnvironment.convertToLinuxPath(workspaceHost) : workspaceHost)
    if (!isPANodeInContainer) {
        cmd.add("-v")
        cmd.add(workspaceHost + ":" + workspaceContainer)
    }

    cachespaceHost = cachespace
    cachespaceContainer = (isWindows ? forkEnvironment.convertToLinuxPath(cachespaceHost) : cachespaceHost)
    cachespaceHostFile = new File(cachespaceHost)
    if (cachespaceHostFile.exists() && cachespaceHostFile.canRead()) {
        if (!isPANodeInContainer) {
            cmd.add("-v")
            cmd.add(cachespaceHost + ":" + cachespaceContainer)
        }
    } else {
        println cachespaceHost + " does not exist or is not readable, access to cache space will be disabled in the container"
    }

    if (!isWindows && !isMac) {
        // when not on windows, mount and use the current JRE
        currentJavaHome = System.getProperty("java.home")
        forkEnvironment.setJavaHome(currentJavaHome)
        if (!isPANodeInContainer) {
            cmd.add("-v")
            cmd.add(currentJavaHome + ":" + currentJavaHome)
        }

        // when not on windows, mount a shared folder if it exists
        // sharedDirectory = new File("/shared")
        // if (sharedDirectory.isDirectory() && sharedDirectory.canWrite()) {
        //     cmd.add("-v")
        //     cmd.add("/shared:/shared")
        // }
    }

    // Prepare log directory
    if (HOST_LOG_PATH && CONTAINER_LOG_PATH) {
        cmd.add("-v")
        cmd.add(HOST_LOG_PATH + ":" + CONTAINER_LOG_PATH)
    }

    // Prepare container working directory
    cmd.add("-w")
    cmd.add(workspaceContainer)

    // linux on windows does not allow sharing identities (such as AD identities)
    if (!isWindows && CONTAINER_ROOTLESS_ENABLED) {
        sigar = new org.hyperic.sigar.Sigar()
        try {
            pid = sigar.getPid()
            creds = sigar.getProcCred(pid)
            uid = creds.getUid()
            gid = creds.getGid()
            cmd.add("--user=" + uid + ":" + gid)
        } catch (Exception e) {
            println "Cannot retrieve user or group id : " + e.getMessage()
        } finally {
            sigar.close()
        }
    }

    cmd.add(containerName)
    forkEnvironment.setPreJavaCommand(cmd)

    // Show the generated command
    if (VERBOSE) {
        println "CONTAINER COMMAND : " + forkEnvironment.getPreJavaCommand()
    }
}

// If singularity
if (CONTAINER_ENABLED &&
    "singularity".equalsIgnoreCase(CONTAINER_PLATFORM)) {

    userHome = System.getProperty("user.home")

    switch (family) {
        case OperatingSystemFamily.WINDOWS:
        throw new IllegalStateException("Singularity is not supported on Windows operating system")
        case OperatingSystemFamily.MAC:
        throw new IllegalStateException("Singularity is not supported on Mac operating system")
        default:
            isWindows = false;
    }

    if (CONTAINER_IMAGE.endsWith(".sif")) {
        sif_image_path = CONTAINER_IMAGE
    }
    else {
        try {
            imageUrl = CONTAINER_IMAGE
            imageName = imageUrl.substring(imageUrl.indexOf("://") + 3).replace("/","_").replace(":","_")
            imageLockFileName = imageName + ".lock"

            process = "singularity --version".execute()
            majorVersion = 0
            if (process.waitFor() == 0) {
                version = process.text
                version = version.replace("singularity version ", "").trim()
                if (VERBOSE) {
                    println "Singularity version: " + version
                }
                majorVersion = Integer.parseInt(version.substring(0, version.indexOf(".")))
            } else {
                throw new IllegalStateException("Cannot find singularity command")
            }

            if (majorVersion >= 3) {
                imageFile = imageName + ".sif"
            } else {
                imageFile = imageName + ".simg"
            }

            // synchronization to avoid concurrent NFS conflicts when creating the image
            imageLockPath = new File(userHome, imageLockFileName);
            if (!imageLockPath.exists()) {
                imageLockPath.createNewFile()
            } else {
                while (imageLockPath.exists()) {
                    Thread.sleep(1000)
                }
            }

            // pull the container inside the synchronization lock
            if (majorVersion >= 3) {
                pullCmd = "singularity pull --dir " + userHome + " " + imageFile + " " + imageUrl
                if (VERBOSE) {
                    println pullCmd
                }
                def env = System.getenv().collect { k, v -> "$$k=$$v" }
                env.push('XDG_RUNTIME_DIR=/run/user/$$UID')
                process = pullCmd.execute(env, new File(userHome))
            } else {
                pullCmd = "singularity pull --name " + imageFile + " " + imageUrl
                def env = System.getenv().collect { k, v -> "$$k=$$v" }
                env.push("SINGULARITY_PULLFOLDER=" + userHome)
                process = pullCmd.execute(env, new File(userHome))
            }
            
            if (VERBOSE) {
                process.in.eachLine { line ->
                    println line
                }
            }
            process.waitFor()

            (new File(userHome, imageFile)).setReadable(true, false)

            // release lock
            imageLockPath.delete()

            sif_image_path = (new File(userHome, imageFile)).getAbsolutePath()

        } catch (Exception e) {
            StackTraceUtils.deepSanitize(e)
            e.stackTrace.head().lineNumber
            throw e
        } finally {
            (new File(userHome, imageLockFileName)).delete()
        }
    }

    cmd = []
    cmd.add("singularity")
    cmd.add("exec")
    // cmd.add("--writable") // by default all singularity containers are available as read only. This option makes the file system accessible as read/write.
    cmd.add("--writable-tmpfs") // makes the file system accessible as read-write with non persistent data (with overlay support only)

    if (CONTAINER_NO_HOME_ENABLED) {
        cmd.add("--no-home") // do NOT mount users home directory if home is not the current working directory
    }

    // run a singularity image in an isolated manner
    if (CONTAINER_ISOLATION_ENABLED) {
        // cmd.add("--disable-cache") // dont use cache, and dont create cache
        // cmd.add("--cleanenv") // clean environment before running container
        // cmd.add("--contain") // use minimal /dev and empty other directories (e.g. /tmp and $$HOME) instead of sharing filesystems from your host
        cmd.add("--containall") // contain not only file systems, but also PID, IPC, and environment
    }

    if (CUDA_ENABLED && CONTAINER_GPU_ENABLED) {
        cmd.add("--nv") // enable experimental NVIDIA GPU support
    }

    // Prepare log directory
    if (HOST_LOG_PATH && CONTAINER_LOG_PATH) {
        cmd.add("-B")
        cmd.add(HOST_LOG_PATH + ":" + CONTAINER_LOG_PATH)
    }

    forkEnvironment.setDockerWindowsToLinux(isWindows)

    // Prepare ProActive home volume
    paHomeHost = variables.get("PA_SCHEDULER_HOME")
    paHomeContainer = (isWindows ? forkEnvironment.convertToLinuxPath(paHomeHost) : paHomeHost)
    cmd.add("-B")
    cmd.add(paHomeHost + ":" + paHomeContainer)
    // Prepare working directory (For Dataspaces and serialized task file)
    workspaceHost = localspace
    workspaceContainer = (isWindows ? forkEnvironment.convertToLinuxPath(workspaceHost) : workspaceHost)
    cmd.add("-B")
    cmd.add(workspaceHost + ":" + workspaceContainer)

    cachespaceHost = cachespace
    cachespaceContainer = (isWindows ? forkEnvironment.convertToLinuxPath(cachespaceHost) : cachespaceHost)
    cachespaceHostFile = new File(cachespaceHost)
    if (cachespaceHostFile.exists() && cachespaceHostFile.canRead()) {
        cmd.add("-B")
        cmd.add(cachespaceHost + ":" + cachespaceContainer)
    } else {
        println cachespaceHost + " does not exist or is not readable, access to cache space will be disabled in the container"
    }

    if (!isWindows) {
        // when not on windows, mount and use the current JRE
        currentJavaHome = System.getProperty("java.home")
        forkEnvironment.setJavaHome(currentJavaHome)
        cmd.add("-B")
        cmd.add(currentJavaHome + ":" + currentJavaHome)
    }

    // Prepare container working directory
    cmd.add("--pwd") // initial working directory for payload process inside the container
    cmd.add(workspaceContainer)
    cmd.add("--workdir") // working directory to be used for /tmp, /var/tmp and $$HOME (if -c/--contain was also used)
    cmd.add(workspaceContainer)

    // Directory containing the singularity image
    cmd.add(sif_image_path)

    forkEnvironment.setPreJavaCommand(cmd)
    forkEnvironment.addSystemEnvironmentVariable("XDG_RUNTIME_DIR",'/run/user/$$UID')

    // Show the generated command
    if (VERBOSE) {
        println "SINGULARITY COMMAND : " + forkEnvironment.getPreJavaCommand()
    }
}

if (!CONTAINER_ENABLED) {
    if (VERBOSE) {
        println "Fork environment disabled"
    }
}
        ''')
        runtime_code = str(template.substitute(**params))

        if DEBUG:
            self.__kernel_print_ok_message__(runtime_code + '\n')

        return runtime_code

    def __create_runtime_environment__(self, input_data):
        proactive_runtime_env = self.__build_runtime_environment__(input_data)
        proactive_fork_env = self.gateway.createForkEnvironment(language="groovy")
        proactive_fork_env.setImplementation(proactive_runtime_env)

        self.__kernel_print_ok_message__('Saving the runtime environment ...\n')
        self.default_fork_env = proactive_fork_env

        if 'force' in input_data and input_data['force'] == 'on':
            self.__kernel_print_ok_message__('Updating created tasks ...\n')
            for task in self.proactive_tasks:
                self.__kernel_print_ok_message__('Setting the runtime environment of the task \'' + task.getTaskName()
                                                 + '\' ...\n')
                task.setForkEnvironment(self.default_fork_env)
                self.job_up_to_date = False

        self.__kernel_print_ok_message__('Done.\n')

    def __find_task_index_from_name__(self, name):
        for task_index in range(len(self.proactive_tasks)):
            if self.proactive_tasks[task_index].getTaskName() == name:
                return task_index
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
            task_index = self.__find_task_index_from_name__(task_name)
            task = self.proactive_tasks[task_index] if task_index is not None else None
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
            self.__create_selection_script_from_task__({'code': 'selected = true', 'language': 'Groovy', 'task': proactive_task})

    def __set_default_fork_environment__(self, proactive_task):
        if self.default_fork_env is not None:
            self.__kernel_print_ok_message__('Adding job fork environment to the proactive task ...\n')
            proactive_task.setForkEnvironment(self.default_fork_env)

    def __set_dependencies_from_input_data__(self, proactive_task, input_data):
        if 'dep' in input_data:
            self.__add_dependency__(proactive_task, input_data)

    def __set_generic_information_from_input_data__(self, proactive_common, input_data):
        if 'generic_info' in input_data:
            self.__kernel_print_ok_message__('Adding generic information ...\n')
            for gen_info in input_data['generic_info']:
                proactive_common.addGenericInformation(gen_info[0], gen_info[1])

    def __set_variables_from_input_data__(self, proactive_common, input_data):
        if 'variables' in input_data:
            self.__kernel_print_ok_message__('Adding variables ...\n')
            for variable in input_data['variables']:
                proactive_common.addVariable(variable[0], variable[1])

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
            proactive_task.setTaskImplementation('\n' + input_data['code'])

    def __is_replicable_as_child__(self, task):
        task_dependencies = task.getDependencies()
        if len(task_dependencies) != 1:
            return False
        if len(task_dependencies[0].getDependencies()):
            return False
        return True

    def __find_all_children__(self, task):
        children = []
        for _task_child in self.proactive_tasks:
            _task_child_dependencies = _task_child.getDependencies()
            for _task_parent in _task_child_dependencies:
                if _task_parent == task:
                    children.append(_task_child)
        return children

    def __is_replicable_as_parent__(self, task):
        children = self.__find_all_children__(task)
        if len(children) != 1:
            return False
        return len(children[0].getDependencies()) == 1

    def __is_not_replicable__(self, task):
        if not self.__is_replicable_as_child__(task):
            return 1
        return 0 if self.__is_replicable_as_parent__(task) else 2

    def __add_replicate_control__(self, proactive_task, input_data):
        if 'runs' in input_data:
            self.__kernel_print_ok_message__('Adding REPLICATE control ...\n')
            if not self.__is_replicable_as_child__(proactive_task):
                raise ParameterError('The task \'' + input_data['name'] + '\' can\'t be replicated.\n')
            else:
                parent_task = proactive_task.getDependencies()[0]
                parent_task.setFlowBlock(self.gateway.getProactiveFlowBlockType().start())
                parent_task.setFlowScript(self.gateway.createReplicateFlowScript('runs=' + input_data['runs']))
                self.replicated_tasks.append(proactive_task)

    def __create_task__(self, input_data):
        # Verifying if imported variables have been exported in other tasks
        if 'import' in input_data:
            for var_name in input_data['import']:
                if not self.__isExported__(var_name):
                    raise ParameterError('The variable \'' + var_name + '\' can\'t be imported.')

        if input_data['name'] in self.tasks_names:
            self.__kernel_print_ok_message__('WARNING: Task \'' + input_data['name'] + '\' already exists ...\n')
            proactive_task = self.proactive_tasks[self.__find_task_index_from_name__(input_data['name'])]
            proactive_task.clearDependencies()
            proactive_task.clearGenericInformation()
            proactive_task.clearVariables()
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
        self.__set_variables_from_input_data__(proactive_task, input_data)

        # TODO: check how to import/export variables when a file path is provided
        self.__add_importing_variables_to_implementation_script__(input_data)
        self.__add_exporting_variables_to_implementation_script__(input_data)
        self.__add_job_imports_to_implementation_script__(input_data)
        self.__set_implementation_script_from_input_data__(proactive_task, input_data)

        self.__add_replicate_control__(proactive_task, input_data)

        self.previous_task_history = input_data
        self.is_previous_pragma_task = True
        self.last_modified_task = proactive_task

        self.__kernel_print_ok_message__('Done.\n')
        self.job_up_to_date = False
        self.graph_up_to_date = False
        return 0

    def __create_split__(self, input_data):
        input_data['trigger'] = 'task'
        if 'name' not in input_data or input_data['name'] == '':
            input_data['name'] = self.__get_unique_task_name__('split')
        self.__create_task__(input_data)
        self.__kernel_print_ok_message__('Setting the flow block ...\n')
        self.last_modified_task.setFlowBlock(self.gateway.getProactiveFlowBlockType().start())
        self.__kernel_print_ok_message__('Done.\n')
        self.semaphore_controls = 1
        self.job_up_to_date = False
        return 0

    def __add_runs__(self, input_data):
        self.__kernel_print_ok_message__('Adding the REPLICATE flow script ...\n')
        flow_script = self.gateway.createReplicateFlowScript(input_data['code'])
        self.last_modified_task.setFlowScript(flow_script)
        self.__kernel_print_ok_message__('Done.\n')
        self.semaphore_controls = 2
        self.job_up_to_date = False
        self.graph_up_to_date = False
        return 0

    def __create_process__(self, input_data):
        input_data['trigger'] = 'task'
        if 'name' not in input_data or input_data['name'] == '':
            input_data['name'] = 'process' + re.findall(r'\d+', self.previous_task_history['name']).pop()
        if 'dep' not in input_data:
            input_data['dep'] = [self.last_modified_task.getTaskName()]
        self.__create_task__(input_data)
        self.semaphore_controls = 3
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
        self.semaphore_controls = 0
        return 0

    def __create_start__(self, input_data):
        input_data['trigger'] = 'task'
        if 'name' not in input_data or input_data['name'] == '':
            input_data['name'] = self.__get_unique_task_name__('start')
        self.__create_task__(input_data)
        self.__kernel_print_ok_message__('Setting the flow block ...\n')
        self.last_modified_task.setFlowBlock(self.gateway.getProactiveFlowBlockType().start())
        self.__kernel_print_ok_message__('Done.\n')
        self.semaphore_controls = 11
        self.job_up_to_date = False
        return 0

    def __create_loop__(self, input_data):
        input_data['trigger'] = 'task'
        if 'name' not in input_data or input_data['name'] == '':
            input_data['name'] = 'loop' + re.findall(r'\d+', self.previous_task_history['name']).pop()
        if 'dep' not in input_data:
            input_data['dep'] = [self.last_modified_task.getTaskName()]
        self.__create_task__(input_data)
        self.__kernel_print_ok_message__('Adding the LOOP flow script ...\n')
        self.last_modified_task.setFlowScript(self.saved_flow_script)
        self.__kernel_print_ok_message__('Setting the flow block ...\n')
        self.last_modified_task.setFlowBlock(self.gateway.getProactiveFlowBlockType().end())
        self.__kernel_print_ok_message__('Done.\n')
        self.semaphore_controls = 0
        return 0

    def __add_condition_loop__(self, input_data):
        self.__kernel_print_ok_message__('Saving the LOOP flow script ...\n')
        self.saved_flow_script = self.gateway.createLoopFlowScript(input_data['code'],
                                                                   self.last_modified_task.getTaskName())
        self.__kernel_print_ok_message__('Done.\n')
        self.semaphore_controls = 12
        self.job_up_to_date = False
        self.graph_up_to_date = False
        return 0

    def __create_branch__(self, input_data):
        input_data['trigger'] = 'task'
        if 'name' not in input_data or input_data['name'] == '':
            input_data['name'] = self.__get_unique_task_name__('branch')
        self.__create_task__(input_data)
        self.saved_branch_task = self.last_modified_task
        self.semaphore_controls = 101
        self.job_up_to_date = False
        return 0

    def __add_condition_branch__(self, input_data):
        self.__kernel_print_ok_message__('Saving the BRANCHING flow script ...\n')
        self.saved_flow_script = self.gateway.createBranchFlowScript(input_data['code'], '', '', '')
        self.__kernel_print_ok_message__('Done.\n')
        self.semaphore_controls = 102
        self.job_up_to_date = False
        self.graph_up_to_date = False
        return 0

    def __create_if__(self, input_data):
        input_data['trigger'] = 'task'
        if 'name' not in input_data or input_data['name'] == '':
            input_data['name'] = self.__get_unique_task_name__('if')
        self.__create_task__(input_data)
        self.saved_flow_script.setActionTarget(self.last_modified_task.getTaskName())
        self.semaphore_controls = 103
        self.job_up_to_date = False
        return 0

    def __create_else__(self, input_data):
        input_data['trigger'] = 'task'
        if 'name' not in input_data or input_data['name'] == '':
            input_data['name'] = self.__get_unique_task_name__('else')
        self.__create_task__(input_data)
        self.saved_flow_script.setActionTargetElse(self.last_modified_task.getTaskName())
        self.semaphore_controls = 104
        self.job_up_to_date = False
        return 0

    def __create_continuation__(self, input_data):
        input_data['trigger'] = 'task'
        if 'name' not in input_data or input_data['name'] == '':
            input_data['name'] = self.__get_unique_task_name__('continuation')
        self.__create_task__(input_data)
        self.saved_flow_script.setActionTargetContinuation(self.last_modified_task.getTaskName())
        self.__kernel_print_ok_message__('Setting the BRANCHING flow script ...\n')
        self.saved_branch_task.setFlowScript(self.saved_flow_script)
        self.__kernel_print_ok_message__('Done.\n')
        self.semaphore_controls = 0
        self.job_up_to_date = False
        return 0

    def __add_condition__(self, input_data):
        if self.semaphore_controls == 11:
            self.__add_condition_loop__(input_data)
        else:
            self.__add_condition_branch__(input_data)

    def __clean_related_dependencies__(self, removed_task):
        for task in self.proactive_tasks:
            if removed_task in task.getDependencies():
                task.removeDependency(removed_task)

    def __clean_replicate_information__(self, removed_task):
        _parents = removed_task.getDependencies()
        for _parent in _parents:
            _parent.setFlowBlock(None)
            _parent.setFlowScript(None)
        _children = self.__find_all_children__(removed_task)
        for _child in _children:
            _child.setFlowBlock(None)

    def __delete_task__(self, input_data):
        if input_data['name'] in self.tasks_names:
            task_to_remove = self.proactive_tasks[self.__find_task_index_from_name__(input_data['name'])]
        else:
            raise ParameterError('Task \'' + input_data['name'] + '\' does not exist.')

        if self.job_created:
            if task_to_remove in self.proactive_job.job_tasks:
                self.__kernel_print_ok_message__('Deleting task from the job...\n')
                self.proactive_job.removeTask(task_to_remove)

        if task_to_remove in self.replicated_tasks:
            self.__kernel_print_ok_message__('Clearing REPLICATE control...\n')
            self.__clean_replicate_information__(task_to_remove)
            self.replicated_tasks.remove(task_to_remove)

        self.__kernel_print_ok_message__('Deleting task from the tasks list...\n')
        self.proactive_tasks.remove(task_to_remove)
        self.tasks_names.remove(input_data['name'])

        self.__kernel_print_ok_message__('Cleaning dependencies...\n')
        self.__clean_related_dependencies__(task_to_remove)

        if input_data['name'] in self.exported_vars:
            del self.exported_vars[input_data['name']]

        self.__kernel_print_ok_message__('Done.\n')

        self.job_up_to_date = False
        self.graph_up_to_date = False

        return

    def __restore_variables_and_generic_info_in_input_data__(self, input_data):
        self.__kernel_print_ok_message__('Saving job variables and generic information ...\n')
        input_data['generic_info'] = [(k, v) for k, v in self.proactive_job.getGenericInformation().items()]
        input_data['variables'] = [(k, v) for k, v in self.proactive_job.getVariables().items()]
        return

    def __create_job__(self, input_data):
        if self.job_created and self.job_up_to_date:
            self.__set_job_name__(input_data['name'])
            self.__kernel_print_ok_message__('Job renamed to \'' + input_data['name'] + '\'.\n')
            return 0

        if self.job_created:
            self.__kernel_print_ok_message__('Re-creating the proactive job due to tasks changes ...\n')
            if input_data['trigger'] == 'submit_job':
                self.__restore_variables_and_generic_info_in_input_data__(input_data)
        else:
            self.__kernel_print_ok_message__('Creating a proactive job ...\n')

        self.proactive_job = self.gateway.createJob()
        self.__set_job_name__(input_data['name'])

        self.__kernel_print_ok_message__('Job \'' + input_data['name'] + '\' created.\n')

        self.__kernel_print_ok_message__('Adding the created tasks to \'' + input_data['name'] + '\' ...\n')
        for task in self.proactive_tasks:
            self.proactive_job.addTask(task)

        self.__set_generic_information_from_input_data__(self.proactive_job, input_data)
        self.__set_variables_from_input_data__(self.proactive_job, input_data)

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
        job_id = self.last_submitted_job_id if self.last_submitted_job_id is not None \
                                               and 'job_id' not in input_data \
                                               and 'job_name' not in input_data \
                                               else self.__get_job_id_from_inputs__(input_data)
        self.__kernel_print_ok_message__('Getting job ' + str(job_id) + ' results ...\n')

        try:
            job_result = self.gateway.getJobResult(job_id)
        except Exception:
            raise ResultError("Results unreachable for job: " + job_id)

        self.__kernel_print_ok_message__('Results:\n')
        self.__kernel_print_ok_message__(job_result)

    def __get_task_result__(self, input_data):
        job_id = self.last_submitted_job_id if self.last_submitted_job_id is not None \
                                               and 'job_id' not in input_data \
                                               and 'job_name' not in input_data \
                                               else self.__get_job_id_from_inputs__(input_data)
        self.__kernel_print_ok_message__('Getting from job ' + str(job_id) + ', task \'' + input_data['task_name']
                                         + '\' results ...\n')

        try:
            task_result = self.gateway.getTaskResult(job_id, input_data['task_name'])
        except Exception:
            raise ResultError("Results unreachable for job: " + job_id)

        self.__kernel_print_ok_message__('Result:\n')
        self.__kernel_print_ok_message__(str(task_result))

    def __print_job_output__(self, input_data):
        job_id = self.last_submitted_job_id if self.last_submitted_job_id is not None \
                                               and 'job_id' not in input_data \
                                               and 'job_name' not in input_data \
                                               else self.__get_job_id_from_inputs__(input_data)
        self.__kernel_print_ok_message__('Getting job ' + str(job_id) + ' console outputs ...\n')

        try:
            job_result = self.gateway.printJobOutput(job_id)
        except Exception:
            raise ResultError("Results unreachable for job: " + job_id)

        self.__kernel_print_ok_message__('Outputs:\n')
        self.__kernel_print_ok_message__(job_result)

    def __print_task_output__(self, input_data):
        job_id = self.last_submitted_job_id if self.last_submitted_job_id is not None \
                                               and 'job_id' not in input_data \
                                               and 'job_name' not in input_data \
                                               else self.__get_job_id_from_inputs__(input_data)
        self.__kernel_print_ok_message__('Getting from job ' + str(job_id) + ', task \'' + input_data['task_name']
                                         + '\' console output ...\n')

        try:
            task_result = self.gateway.printTaskOutput(job_id, input_data['task_name'])
        except Exception:
            raise ResultError("Results unreachable for job: " + job_id)

        self.__kernel_print_ok_message__('Output:\n')
        self.__kernel_print_ok_message__(str(task_result))

    def __check_replicates_validity__(self):
        self.__kernel_print_ok_message__('Checking REPLICATE controls validity ...\n')
        for replicated_task in self.replicated_tasks:
            _is_not_validated = self.__is_not_replicable__(replicated_task)
            children = self.__find_all_children__(replicated_task)
            if _is_not_validated == 2:
                if len(children):
                    raise JobValidationError('The replicated task \'' + replicated_task.getTaskName() +
                                             '\' should not have more than one child task.')
                input_data = {'name': self.__get_unique_task_name__('DefaultMerge'),
                              'trigger': 'task',
                              'code': '',
                              'dep': [replicated_task.getTaskName()]}
                self.__kernel_print_error_message({'ename': 'WARNING',
                                                   'evalue': 'Adding an empty default merge task to complete \''
                                                             + replicated_task.getTaskName() + '\' REPLICATE control.'})
                self.__create_task__(input_data)
                self.last_modified_task.setFlowBlock(self.gateway.getProactiveFlowBlockType().end())

            elif _is_not_validated == 1:
                raise JobValidationError('The replicated task \'' + replicated_task.getTaskName() +
                                         '\' should not have more than one parent task.')

            else:
                children[0].setFlowBlock(self.gateway.getProactiveFlowBlockType().end())
        self.__kernel_print_ok_message__('Validated.\n')

    def __submit_job__(self, input_data):
        if len(self.replicated_tasks):
            self.__check_replicates_validity__()
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

        if 'input_path' in input_data or 'output_path' in input_data:
            input_path = input_data['input_path'] if 'input_path' in input_data else '.'
            output_path = input_data['output_path'] if 'output_path' in input_data else '.'

            temp_id = self.gateway.submitJobWithInputsAndOutputsPaths(self.proactive_job,
                                                                      input_path,
                                                                      output_path,
                                                                      debug=False)
        else:
            temp_id = self.gateway.submitJob(self.proactive_job, debug=False)

        self.submitted_jobs_names[temp_id] = self.job_name
        self.submitted_jobs_ids[self.job_name] = temp_id
        self.last_submitted_job_id = temp_id

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

    def __traffic_verification__(self, pragma_info):
        if self.semaphore_controls == 1 and pragma_info['trigger'] != 'runs':
            raise PragmaError('Expected a \'runs\' pragma.')
        if self.semaphore_controls == 2 and pragma_info['trigger'] != 'process':
            raise PragmaError('Expected a \'process\' pragma.')
        if self.semaphore_controls == 3 and pragma_info['trigger'] != 'merge':
            raise PragmaError('Expected a \'merge\' pragma.')
        if self.semaphore_controls in [11, 101] and pragma_info['trigger'] != 'condition':
            raise PragmaError('Expected a \'condition\' pragma.')
        if self.semaphore_controls == 12 and pragma_info['trigger'] != 'loop':
            raise PragmaError('Expected a \'loop\' pragma.')
        if self.semaphore_controls == 102 and pragma_info['trigger'] != 'if':
            raise PragmaError('Expected an \'if\' pragma.')
        if self.semaphore_controls == 103 and pragma_info['trigger'] != 'else':
            raise PragmaError('Expected an \'else\' pragma.')
        if self.semaphore_controls == 104 and pragma_info['trigger'] != 'continuation':
            raise PragmaError('Expected a \'continuation\' pragma.')
        if self.semaphore_controls == 0 and pragma_info['trigger'] in ['runs', 'process', 'merge']:
            raise PragmaError('The "replicate" control should start with a \'split\' pragma.')
        if self.semaphore_controls == 0 and pragma_info['trigger'] == 'loop':
            raise PragmaError('The "loop" control should start with a \'start\' pragma.')
        if self.semaphore_controls == 0 and pragma_info['trigger'] in ['if', 'else', 'continuation']:
            raise PragmaError('The "branch" control should start with a \'branch\' pragma,\n')
        if self.semaphore_controls == 0 and pragma_info['trigger'] == 'condition':
            raise PragmaError('The "branch" control should start with a \'branch\' pragma,\n' +
                              'and the "loop" control should start with a \'start\' pragma.')
        return

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

        try:
            self.__traffic_verification__(pragma_info)
        except PragmaError as pe:
            return self.__kernel_print_error_message({'ename': 'Pragma error', 'evalue': pe.strerror})

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
                return self.__kernel_print_error_message({'ename': 'Proactive result error', 'evalue': rer.strerror})
            except JobValidationError as jbe:
                return self.__kernel_print_error_message({'ename': 'Job validation error', 'evalue': jbe.strerror})
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
                proactive_task = self.proactive_tasks[self.__find_task_index_from_name__(pragma_info['name'])]
                proactive_task.setTaskImplementation(pragma_info['code'])
                self.previous_task_history.update(pragma_info)
                self.__kernel_print_ok_message__('Done.\n')
                exitcode = 0
            else:
                return self.__kernel_print_error_message({'ename': 'Pragma error',
                                                          'evalue': 'Blocks should be started by pragmas.'})
        return exitcode

    def do_execute(self, code, silent, store_history=True, user_expressions=True, allow_stdin=True):
        self.silent = silent
        self._allow_stdin = allow_stdin
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
