import re
from .exceptions import *


def get_usage_help():
    return '   #%help([pragma=PRAGMA_NAME])\n'


def get_usage_connect():
    return '   #%connect([host=YOUR_HOST], [port=YOUR_PORT], [login=YOUR_LOGIN], [password=YOUR_PASSWORD])\n' \
           + '   #%connect([url=YOUR_URL], [login=YOUR_LOGIN], [password=YOUR_PASSWORD])\n' \
           + '   #%connect(path=PATH_TO/YOUR_CONFIG_FILE.ini)\n'


def get_usage_configure():
    return '   #%configure(task=block/multiblock)\n'


def get_usage_import():
    return '   #%import([language=SCRIPT_LANGUAGE])\n'


def get_usage_task():
    return '   #%task(name=TASK_NAME, [dep=[TASK_NAME1,TASK_NAME2,...]], [generic_info=[(KEY1,VAL1),' \
           '(KEY2,VALUE2),...]], [variables=[(VAR1,VAL1), (VAR2,VALUE2),...]], [export=[VAR_NAME1,VAR_NAME2,...]], ' \
           '[import=[VAR_NAME1,VAR_NAME2,...]], [path=IMPLEMENTATION_FILE_PATH], [language=SCRIPT_LANGUAGE], ' \
           '[runs=NB_RUNS], [precious_result=true/false])\n'


def get_usage_delete_task():
    return '   #%delete_task(name=TASK_NAME)\n'


def get_usage_pre_script():
    return '   #%pre_script(name=TASK_NAME, language=SCRIPT_LANGUAGE, [path=./PRE_SCRIPT_FILE.py])\n'


def get_usage_post_script():
    return '   #%post_script(name=TASK_NAME, language=SCRIPT_LANGUAGE, [path=./POST_SCRIPT_FILE.py])\n'


def get_usage_selection_script():
    return '   #%selection_script(name=TASK_NAME, [path=./SELECTION_CODE_FILE.py])\n'


def get_usage_job_selection_script():
    return '   #%job_selection_script([language=SCRIPT_LANGUAGE], [path=./SELECTION_CODE_FILE.py], [force=on/off])\n'


def get_usage_fork_env():
    return '   #%fork_env(name=TASK_NAME, [path=./FORK_ENV_FILE.py])\n'


def get_usage_job_fork_env():
    return '   #%job_fork_env([language=SCRIPT_LANGUAGE], [path=./FORK_ENV_FILE.py], [force=on/off])\n'


def get_usage_runtime_env():
    return '   #%runtime_env([type=docker/podman/singularity], [image=docker://...], [nvidia_gpu=true/false], [mount_host_path=PATH], [mount_container_path=PATH], [force=on/off])\n'


def get_usage_split():
    return '   #%split([name=TASK_NAME], [dep=[TASK_NAME1,TASK_NAME2,...]], [generic_info=[(KEY1,VAL1),' \
           '(KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE], [path=./FORK_ENV_FILE.py])\n'


def get_usage_runs():
    return '   #%runs()\n'


def get_usage_process():
    return '   #%process([name=TASK_NAME], [generic_info=[(KEY1,VAL1),(KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE]' \
           ', [path=./FORK_ENV_FILE.py])\n'


def get_usage_merge():
    return '   #%merge([name=TASK_NAME], [generic_info=[(KEY1,VAL1),(KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE]' \
           ', [path=./FORK_ENV_FILE.py])\n'


def get_usage_start():
    return '   #%start([name=TASK_NAME], [dep=[TASK_NAME1,TASK_NAME2,...]], [generic_info=[(KEY1,VAL1),' \
           '(KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE], [path=./FORK_ENV_FILE.py])\n'


def get_usage_condition():
    return '   #%condition()\n'


def get_usage_loop():
    return '   #%loop([name=TASK_NAME], [generic_info=[(KEY1,VAL1),(KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE]' \
           ', [path=./FORK_ENV_FILE.py])\n'


def get_usage_branch():
    return '   #%branch([name=TASK_NAME], [dep=[TASK_NAME1,TASK_NAME2,...]], [generic_info=[(KEY1,VAL1),' \
           '(KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE], [path=./FORK_ENV_FILE.py])\n'


def get_usage_if():
    return '   #%if([name=TASK_NAME], [generic_info=[(KEY1,VAL1),(KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE]' \
           ', [path=./FORK_ENV_FILE.py])\n'


def get_usage_else():
    return '   #%else([name=TASK_NAME], [generic_info=[(KEY1,VAL1),(KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE]' \
           ', [path=./FORK_ENV_FILE.py])\n'


def get_usage_continuation():
    return '   #%continuation([name=TASK_NAME], [generic_info=[(KEY1,VAL1),(KEY2,VALUE2),...]], ' \
           '[language=SCRIPT_LANGUAGE], [path=./FORK_ENV_FILE.py])\n'


def get_usage_job():
    return '   #%job(name=JOB_NAME, [generic_info=[(KEY1,VAL1), (KEY2,VALUE2),...]], ' \
           '[variables=[(VAR1,VAL1), (VAR2,VALUE2),...]])\n'


def get_usage_draw_job():
    return '   #%draw_job([name=JOB_NAME], [inline=on/off], [save=on/off])\n'


def get_usage_write_dot():
    return '   #%write_dot(name=FILE_NAME)\n'


def get_usage_import_dot():
    return '   #%import_dot(path=PATH_TO/FILE_NAME.dot)\n'


def get_usage_submit_job():
    return '   #%submit_job([name=JOB_NAME], [nodesource=NODESOURCE_NAME], [host=HOST_NAME], [token=TOKEN_NAME], [input_path=INPUT_FOLDER_PATH], [output_path=OUTPUT_FOLDER_PATH])\n'


def get_usage_get_job_result():
    return '   #%get_job_result([job_id=JOB_ID], [job_name=JOB_NAME])\n'


def get_usage_get_task_result():
    return '   #%get_task_result([job_id=JOB_ID], [job_name=JOB_NAME], task_name=TASK_NAME)\n'


def get_usage_print_job_output():
    return '   #%print_job_output([job_id=JOB_ID], [job_name=JOB_NAME])\n'


def get_usage_print_task_output():
    return '   #%print_task_output([job_id=JOB_ID], [job_name=JOB_NAME], task_name=TASK_NAME)\n'


def get_usage_list_submitted_jobs():
    return '   #%list_submitted_jobs()\n'


def get_usage_export_xml():
    return '   #%export_xml([name=FILE_NAME])\n'


def get_usage_show_resource_manager():
    return '   #%show_resource_manager([host=YOUR_HOST], [height=HEIGHT_VALUE], [width=WIDTH_VALUE])\n'


def get_usage_show_scheduling_portal():
    return '   #%show_scheduling_portal([host=YOUR_HOST], [height=HEIGHT_VALUE], [width=WIDTH_VALUE])\n'


def get_usage_show_workflow_automation():
    return '   #%show_workflow_automation([host=YOUR_HOST], [height=HEIGHT_VALUE], [width=WIDTH_VALUE])\n'


def list_usage_list_nodesources():
    return '   #%list_nodesources()\n'


def list_usage_list_hosts():
    return '   #%list_hosts()\n'


def list_usage_list_tokens():
    return '   #%list_tokens()\n'


def list_usage_list_resources():
    return '   #%list_resources()\n'


def get_help(trigger):
    if trigger == 'connect':
        help_msg = 'Pragma #%connect(): connects to an ActiveEon server\n'
        help_msg += 'Usages:\n' + get_usage_connect()
    elif trigger == 'import':
        help_msg = '#%import(): imports specified libraries to all tasks of a same script language\n'
        help_msg += 'Usages:\n' + get_usage_import()
    elif trigger == 'configure':
        help_msg = '#%configure(): configures the ProActive kernel\'s behavior\n'
        help_msg += 'Usages:\n' + get_usage_configure()
    elif trigger == 'task':
        help_msg = '#%task(): creates/modifies a task\n'
        help_msg += 'Usages:\n' + get_usage_task()
    elif trigger == 'delete_task':
        help_msg = '#%delete_task(): remove a task from the workflow\n'
        help_msg += 'Usages:\n' + get_usage_delete_task()
    elif trigger == 'pre_script':
        help_msg = '#%pre_script(): sets the pre-script of a task\n'
        help_msg += 'Usages:\n' + get_usage_pre_script()
    elif trigger == 'post_script':
        help_msg = '#%post_script(): sets the post-script of a task\n'
        help_msg += 'Usages:\n' + get_usage_post_script()
    elif trigger == 'selection_script':
        help_msg = '#%selection_script(): sets the selection script of a task\n'
        help_msg += 'Usages:\n' + get_usage_selection_script()
    elif trigger == 'job_selection_script':
        help_msg = '#%job_selection_script(): sets the selection script of a job\n'
        help_msg += 'Usages:\n' + get_usage_job_selection_script()
    elif trigger == 'fork_env':
        help_msg = '#%fork_env(): sets the fork environment script\n'
        help_msg += 'Usages:\n' + get_usage_fork_env()
    elif trigger == 'job_fork_env':
        help_msg = '#%job_fork_env(): sets the fork environment of a job\n'
        help_msg += 'Usages:\n' + get_usage_job_fork_env()
    elif trigger == 'runtime_env':
        help_msg = '#%runtime_env(): sets the runtime environment of a job\n'
        help_msg += 'Usages:\n' + get_usage_runtime_env()
    elif trigger == 'split':
        help_msg = '#%split(): creates/modifies a splitting task of a replicate control\n'
        help_msg += 'Usages:\n' + get_usage_split()
    elif trigger == 'runs':
        help_msg = '#%runs(): creates/modifies the configuration script of a replicate control\n'
        help_msg += 'Usages:\n' + get_usage_runs()
    elif trigger == 'process':
        help_msg = '#%process(): creates/modifies the script of a replicated processing task \n'
        help_msg += 'Usages:\n' + get_usage_process()
    elif trigger == 'merge':
        help_msg = '#%merge(): creates/modifies a merging task of a replicate control\n'
        help_msg += 'Usages:\n' + get_usage_merge()
    elif trigger == 'start':
        help_msg = '#%start(): creates/modifies a start task of a loop control\n'
        help_msg += 'Usages:\n' + get_usage_start()
    elif trigger == 'loop':
        help_msg = '#%loop(): creates/modifies a loop task of a loop control\n'
        help_msg += 'Usages:\n' + get_usage_loop()
    elif trigger == 'condition':
        help_msg = '#%condition(): creates/modifies the condition script of a branch/loop control\n'
        help_msg += 'Usages:\n' + get_usage_condition()
    elif trigger == 'branch':
        help_msg = '#%branch(): creates/modifies a branch task of a branching control\n'
        help_msg += 'Usages:\n' + get_usage_branch()
    elif trigger == 'if':
        help_msg = '#%if(): creates/modifies an if task of a branching control\n'
        help_msg += 'Usages:\n' + get_usage_if()
    elif trigger == 'else':
        help_msg = '#%else(): creates/modifies an else task of a branching control\n'
        help_msg += 'Usages:\n' + get_usage_else()
    elif trigger == 'continuation':
        help_msg = '#%continuation(): creates/modifies a continuation task of a branching control\n'
        help_msg += 'Usages:\n' + get_usage_continuation()
    elif trigger == 'job':
        help_msg = '#%job(): creates/renames the job\n'
        help_msg += 'Usages:\n' + get_usage_job()
    elif trigger == 'draw_job':
        help_msg = '#%draw_job(): plot the workflow\n'
        help_msg += 'Usages:\n' + get_usage_draw_job()
    elif trigger == 'write_dot':
        help_msg = '#%write_dot(): writes the workflow in .dot format\n'
        help_msg += 'Usages:\n' + get_usage_write_dot()
    elif trigger == 'import_dot':
        help_msg = '#%import_dot(): imports the workflow from a .dot file\n'
        help_msg += 'Usages:\n' + get_usage_import_dot()
    elif trigger == 'submit_job':
        help_msg = '#%submit_job(): submits the job to the scheduler\n'
        help_msg += 'Usages:\n' + get_usage_submit_job()
    elif trigger == 'get_job_result':
        help_msg = '#%get_job_result(): gets and prints the job results\n'
        help_msg += 'Usages:\n' + get_usage_get_job_result()
    elif trigger == 'get_task_result':
        help_msg = '#%get_task_result(): gets and prints the results of a given task\n'
        help_msg += 'Usages:\n' + get_usage_get_task_result()
    elif trigger == 'print_job_output':
        help_msg = '#%print_job_output(): gets and prints the job outputs\n'
        help_msg += 'Usages:\n' + get_usage_print_job_output()
    elif trigger == 'print_task_output':
        help_msg = '#%print_task_output(): gets and prints the outputs of a given task\n'
        help_msg += 'Usages:\n' + get_usage_print_task_output()
    elif trigger == 'list_submitted_jobs':
        help_msg = '#%list_submitted_jobs(): gets and prints the ids and names of the submitted jobs\n'
        help_msg += 'Usages:\n' + get_usage_list_submitted_jobs()
    elif trigger == 'export_xml':
        help_msg = '#%export_xml(): exports the job in xml format\n'
        help_msg += 'Usages:\n' + get_usage_export_xml()
    elif trigger == 'show_resource_manager':
        help_msg = '#%show_resource_manager(): opens the ActiveEon resource manager portal\n'
        help_msg += 'Usages:\n' + get_usage_show_resource_manager()
    elif trigger == 'show_scheduling_portal':
        help_msg = '#%show_scheduling_portal(): opens the ActiveEon scheduling portal\n'
        help_msg += 'Usages:\n' + get_usage_show_scheduling_portal()
    elif trigger == 'show_workflow_automation':
        help_msg = '#%show_workflow_automation(): opens the ActiveEon workflow automation portal\n'
        help_msg += 'Usages:\n' + get_usage_show_workflow_automation()
    elif trigger == 'list_nodesources':
        help_msg = '#%list_nodesources(): lists and prints any available node source\n'
        help_msg += 'Usages:\n' + list_usage_list_nodesources()
    elif trigger == 'list_hosts':
        help_msg = '#%list_hosts(): lists and prints any available host\n'
        help_msg += 'Usages:\n' + list_usage_list_hosts()
    elif trigger == 'list_tokens':
        help_msg = '#%list_tokens(): lists and prints any available token\n'
        help_msg += 'Usages:\n' + list_usage_list_tokens()
    elif trigger == 'list_resources':
        help_msg = '#%list_resources(): lists and prints any available node source, host and token\n'
        help_msg += 'Usages:\n' + list_usage_list_resources() 
    else:
        raise ParameterError('Pragma \'' + trigger + '\' not known.')

    return help_msg


def get_usage(trigger):
    if trigger == 'help':
        return get_usage_help()
    elif trigger == 'connect':
        return get_usage_connect()
    elif trigger == 'import':
        return get_usage_import()
    elif trigger == 'configure':
        return get_usage_configure()
    elif trigger == 'task':
        return get_usage_task()
    elif trigger == 'delete_task':
        return get_usage_delete_task()
    elif trigger == 'pre_script':
        return get_usage_pre_script()
    elif trigger == 'post_script':
        return get_usage_post_script()
    elif trigger == 'selection_script':
        return get_usage_selection_script()
    elif trigger == 'job_selection_script':
        return get_usage_job_selection_script()
    elif trigger == 'fork_env':
        return get_usage_fork_env()
    elif trigger == 'job_fork_env':
        return get_usage_job_fork_env()
    elif trigger == 'runtime_env':
        return get_usage_runtime_env()
    elif trigger == 'split':
        return get_usage_split()
    elif trigger == 'runs':
        return get_usage_runs()
    elif trigger == 'process':
        return get_usage_process()
    elif trigger == 'merge':
        return get_usage_merge()
    elif trigger == 'start':
        return get_usage_start()
    elif trigger == 'loop':
        return get_usage_loop()
    elif trigger == 'condition':
        return get_usage_condition()
    elif trigger == 'branch':
        return get_usage_branch()
    elif trigger == 'if':
        return get_usage_if()
    elif trigger == 'else':
        return get_usage_else()
    elif trigger == 'continuation':
        return get_usage_continuation()
    elif trigger == 'job':
        return get_usage_job()
    elif trigger == 'draw_job':
        return get_usage_draw_job()
    elif trigger == 'write_dot':
        return get_usage_write_dot()
    elif trigger == 'import_dot':
        return get_usage_import_dot()
    elif trigger == 'submit_job':
        return get_usage_submit_job()
    elif trigger == 'get_job_result':
        return get_usage_get_job_result()
    elif trigger == 'get_task_result':
        return get_usage_get_task_result()
    elif trigger == 'print_job_output':
        return get_usage_print_job_output()
    elif trigger == 'print_task_output':
        return get_usage_print_task_output()
    elif trigger == 'list_submitted_jobs':
        return get_usage_list_submitted_jobs()
    elif trigger == 'export_xml':
        return get_usage_export_xml()
    elif trigger == 'show_resource_manager':
        return get_usage_show_resource_manager()
    elif trigger == 'show_scheduling_portal':
        return get_usage_show_scheduling_portal()
    elif trigger == 'show_workflow_automation':
        return get_usage_show_workflow_automation()
    elif trigger == 'list_nodesources':
        return list_usage_list_nodesources()
    elif trigger == 'list_hosts':
        return list_usage_list_hosts()
    elif trigger == 'list_tokens':
        return list_usage_list_tokens()
    elif trigger == 'list_resources':
        return list_usage_list_resources()
    return None


def extract_list(msg):
    draft = re.split(']', msg, 1)[0].strip('[')
    return re.split(',', draft)


def extract_tuples_list(msg):
    draft = re.split('\)]', msg, 1)[0].strip('[(')
    draft = re.split(',', draft.replace(')', "").replace('(', ""))
    t_list = []
    for index in range(0, len(draft), 2):
        t_list.append((draft[index], draft[index + 1]))
    return t_list


def extract_params(params, data):
    params = params.replace(" ", "")
    while '=' in params:
        draft = re.split(r'=', params, 1)
        left = draft[0]
        if draft[1].startswith('[('):
            right = extract_tuples_list(draft[1])
            if ')],' in params:
                params = re.split('\)],', params, 1)[1]
            else:
                params = re.split('\)]', params, 1)[1]
        elif draft[1].startswith('['):
            right = extract_list(draft[1])
            if '],' in params:
                params = re.split('],', params, 1)[1]
            else:
                params = re.split(']', params, 1)[1]
        elif ',' in params:
            temp = re.split(r',', draft[1], 1)
            right = temp[0]
            params = temp[1]
        else:
            right = draft[1]
            params = ""

        data[left] = right


def is_valid_help(data):
    pattern_pragma_name = r"^[a-z_]+$"
    if 'pragma' in data and not re.match(pattern_pragma_name, data['pragma']):
        raise ParameterError('Invalid pragma parameter')
    return


def is_valid_connect(data):
    pattern_name = r"^[a-zA-Z_]\w*$"
    pattern_password = r"^[^ ]+$"
    pattern_path_cars = r"^[a-zA-Z0-9_\/\\:\.-]+$"
    pattern_port = r"^\d+$"
    if 'path' in data and re.match(pattern_path_cars, data['path']):
        return
    if 'login' in data and not re.match(pattern_name, data['login']):
        raise ParameterError('Invalid login parameter')
    if 'password' in data and not re.match(pattern_password, data['password']):
        raise ParameterError('Invalid password parameter')
    if 'url' in data and not re.match(pattern_path_cars, data['url']):
        raise ParameterError('Invalid url parameter')
    if 'host' in data and not re.match(pattern_path_cars, data['host']):
        raise ParameterError('Invalid host parameter')
    if 'port' in data and not re.match(pattern_port, data['port']):
        raise ParameterError('Invalid port parameter')
    return


def is_valid_import(data):
    pattern_language = r"^[a-zA-Z_]+$"
    if 'language' in data and not re.match(pattern_language, data['language']):
        raise ParameterError('Invalid script language')
    return


def is_valid_configure(data):
    pattern_block_multiblock = r"^block$|^multiblock$"
    if 'task' not in data or not re.match(pattern_block_multiblock, data['task']):
        raise ParameterError('Invalid task parameter')
    return


def is_valid_names_tuples_list(gen_info):
    pattern_name = r"^[a-zA-Z_]\w*$"
    for pair in gen_info:
        if not re.match(pattern_name, pair[0]) or not re.match(pattern_name, pair[1]):
            raise ParameterError('Invalid generic information parameter')
    return


def is_valid_names_list(deps):
    pattern_name = r"^[a-zA-Z_](\w|\-)*$"
    for name in deps:
        if not re.match(pattern_name, name):
            raise ParameterError('Invalid dependencies parameter')
    return


def is_valid_task(data):
    pattern_name = r"^[a-zA-Z_](\w|\-)*$"
    pattern_language = r"^[a-zA-Z_]+$"
    pattern_path_cars = r"^[a-zA-Z0-9_\/\\:\.-]+$"
    pattern_expression = r"^(\d+|[a-zA-Z_]\w*)([+*\/-](\d+|[a-zA-Z_]\w*))*$"
    pattern_boolean = r"^([Tt][Rr][Uu][Ee]|[Ff][Aa][Ll][Ss][Ee])$"
    if 'name' not in data or not re.match(pattern_name, data['name']):
        raise ParameterError('Invalid name parameter')
    if 'language' in data and not re.match(pattern_language, data['language']):
        raise ParameterError('Invalid script language parameter')
    if 'dep' in data:
        is_valid_names_list(data['dep'])
    if 'generic_info' in data:
        is_valid_names_tuples_list(data['generic_info'])
    if 'variables' in data:
        is_valid_names_tuples_list(data['variables'])
    if 'export' in data:
        is_valid_names_list(data['export'])
    if 'import' in data:
        is_valid_names_list(data['import'])
    if 'precious_result' in data and not re.match(pattern_boolean, data['precious_result']):
        raise ParameterError('Invalid precious result parameter')
    if 'path' in data and not re.match(pattern_path_cars, data['path']):
        raise ParameterError('Invalid path parameter')
    if 'runs' in data and not re.match(pattern_expression, data['runs']):
        raise ParameterError('Invalid runs parameter')
    return


def is_valid_delete_task(data):
    pattern_name = r"^[a-zA-Z_]\w*$"
    if 'name' not in data or not re.match(pattern_name, data['name']):
        raise ParameterError('Invalid name parameter')
    return


def is_valid_pre_script(data):
    pattern_name = r"^[a-zA-Z_]\w*$"
    pattern_language = r"^[a-zA-Z_]+$"
    pattern_path_cars = r"^[a-zA-Z0-9_\/\\:\.-]+$"
    if 'name' not in data or not re.match(pattern_name, data['name']):
        raise ParameterError('Invalid name parameter ')
    if 'language' not in data or not re.match(pattern_language, data['language']):
        raise ParameterError('Invalid script language')
    if 'path' in data and not re.match(pattern_path_cars, data['path']):
        raise ParameterError('Invalid path parameter')
    return


def is_valid_post_script(data):
    return is_valid_pre_script(data)


def is_valid_selection_script(data):
    pattern_name = r"^[a-zA-Z_]\w*$"
    pattern_path_cars = r"^[a-zA-Z0-9_\/\\:\.-]+$"
    if 'name' not in data or not re.match(pattern_name, data['name']):
        raise ParameterError('Invalid name parameter')
    if 'path' in data and not re.match(pattern_path_cars, data['path']):
        raise ParameterError('Invalid path parameter')
    return


def is_valid_job_selection_script(data):
    pattern_language = r"^[a-zA-Z_]+$"
    pattern_path_cars = r"^[a-zA-Z0-9_\/\\:\.-]+$"
    pattern_on_off = r"^on$|^off$"
    if 'language' in data and not re.match(pattern_language, data['language']):
        raise ParameterError('Invalid script language parameter')
    if 'path' in data and not re.match(pattern_path_cars, data['path']):
        raise ParameterError('Invalid path parameter')
    if 'force' in data and not re.match(pattern_on_off, data['force']):
        raise ParameterError('Invalid forcing parameter')
    return


def is_valid_fork_env(data):
    return is_valid_selection_script(data)


def is_valid_job_fork_env(data):
    return is_valid_job_selection_script(data)


def is_valid_split(data):
    pattern_name = r"^[a-zA-Z_]\w*$"
    pattern_language = r"^[a-zA-Z_]+$"
    pattern_path_cars = r"^[a-zA-Z0-9_\/\\:\.-]+$"
    if 'name' in data and data['name'] != '' and not re.match(pattern_name, data['name']):
        raise ParameterError('Invalid name parameter')
    if 'language' in data and not re.match(pattern_language, data['language']):
        raise ParameterError('Invalid script language parameter')
    if 'dep' in data:
        is_valid_names_list(data['dep'])
    if 'generic_info' in data:
        is_valid_names_tuples_list(data['generic_info'])
    if 'export' in data:
        is_valid_names_list(data['export'])
    if 'import' in data:
        is_valid_names_list(data['import'])
    if 'path' in data and not re.match(pattern_path_cars, data['path']):
        raise ParameterError('Invalid path parameter')
    return


def is_valid_runs(data):
    return


def is_valid_process(data):
    pattern_name = r"^[a-zA-Z_]\w*$"
    pattern_language = r"^[a-zA-Z_]+$"
    pattern_path_cars = r"^[a-zA-Z0-9_\/\\:\.-]+$"
    if 'name' in data and data['name'] != '' and not re.match(pattern_name, data['name']):
        raise ParameterError('Invalid name parameter')
    if 'language' in data and not re.match(pattern_language, data['language']):
        raise ParameterError('Invalid script language parameter')
    if 'generic_info' in data:
        is_valid_names_tuples_list(data['generic_info'])
    if 'export' in data:
        is_valid_names_list(data['export'])
    if 'import' in data:
        is_valid_names_list(data['import'])
    if 'path' in data and not re.match(pattern_path_cars, data['path']):
        raise ParameterError('Invalid path parameter')
    return


def is_valid_merge(data):
    return is_valid_process(data)


def is_valid_start(data):
    return is_valid_split(data)


def is_valid_loop(data):
    return is_valid_process(data)


def is_valid_condition(data):
    return


def is_valid_branch(data):
    return is_valid_split(data)


def is_valid_if(data):
    return is_valid_process(data)


def is_valid_else(data):
    return is_valid_process(data)


def is_valid_continuation(data):
    return is_valid_process(data)


def is_valid_job(data):
    pattern_name = r"^[a-zA-Z_]\w*$"
    if 'name' not in data or not re.match(pattern_name, data['name']):
        raise ParameterError('Invalid name parameter')
    if 'generic_info' in data:
        is_valid_names_tuples_list(data['generic_info'])
    if 'variables' in data:
        is_valid_names_tuples_list(data['variables'])
    return


def is_valid_draw_job(data):
    pattern_name = r"^[a-zA-Z_]\w*$"
    pattern_on_off = r"^on$|^off$"
    if 'name' in data and data['name'] != '' and not re.match(pattern_name, data['name']):
        raise ParameterError('Invalid name parameter')
    if 'inline' in data and not re.match(pattern_on_off, data['inline']):
        raise ParameterError('Invalid inline parameter')
    if 'save' in data and not re.match(pattern_on_off, data['save']):
        raise ParameterError('Invalid save parameter')
    return


def is_valid_write_dot(data):
    pattern_name = r"^[a-zA-Z_]\w*$"
    if 'name' in data and data['name'] != '' and not re.match(pattern_name, data['name']):
        raise ParameterError('Invalid name parameter')
    return


def is_valid_import_dot(data):
    pattern_path_cars = r"^[a-zA-Z0-9_\/\\:\.-]+$"
    if 'path' not in data or not re.match(pattern_path_cars, data['path']):
        raise ParameterError('Invalid path parameter')
    return


def is_valid_submit_job(data):
    # `pattern_name` represents the pattern of a valid variable name,
    # A valid variable name starts with a letter or underscore, followed by letters, digits, or/and underscores.
    pattern_name = r"^[a-zA-Z_]\w*$"
    pattern_path_cars = r"^[a-zA-Z0-9_\/\\:\.-]+$"
    if 'name' in data and data['name'] != '' and not re.match(pattern_name, data['name']):
        raise ParameterError('Invalid name parameter')
    if 'input_path' in data and not re.match(pattern_path_cars, data['input_path']):
        raise ParameterError('Invalid input path parameter')
    if 'output_path' in data and not re.match(pattern_path_cars, data['output_path']):
        raise ParameterError('Invalid output path parameter')
    if 'nodesource' in data and not re.match(pattern_path_cars, data['nodesource']):
        raise ParameterError('Invalid nodesource parameter')
    if 'host' in data and not re.match(pattern_path_cars, data['host']):
        raise ParameterError('Invalid host parameter')
    if 'token' in data and not re.match(pattern_path_cars, data['token']):
        raise ParameterError('Invalid token parameter')
    return


def is_valid_get_job_result(data):
    pattern_name = r"^[a-zA-Z_]\w*$"
    pattern_id = r"^\d+$"
    if 'job_name' in data and not re.match(pattern_name, data['job_name']):
        raise ParameterError('Invalid job_name parameter')
    if 'job_id' in data and not re.match(pattern_id, data['job_id']):
        raise ParameterError('Invalid job_id parameter')
    return


def is_valid_get_task_result(data):
    pattern_name = r"^[a-zA-Z_]\w*$"
    pattern_id = r"^\d+$"
    if 'job_name' in data and not re.match(pattern_name, data['job_name']):
        raise ParameterError('Invalid job_name parameter')
    if 'job_id' in data and not re.match(pattern_id, data['job_id']):
        raise ParameterError('Invalid job_id parameter')
    if 'task_name' not in data or not re.match(pattern_name, data['task_name']):
        raise ParameterError('Invalid task_name parameter')
    return


def is_valid_print_job_output(data):
    return is_valid_get_job_result(data)


def is_valid_print_task_output(data):
    return is_valid_get_task_result(data)


def is_valid_list_submitted_jobs(data):
    pass


def is_valid_list_nodesources(data):
    pass


def is_valid_list_hosts(data):
    pass


def is_valid_list_tokens(data):
    pass


def is_valid_list_resources(data):
    pass


def is_valid_export_xml(data):
    return is_valid_write_dot(data)


def is_valid_show_resource_manager(data):
    pattern_dimension = r"^\d+$"
    pattern_path_cars = r"^[a-zA-Z0-9_\/\\:\.-]+$"
    if 'width' in data and not re.match(pattern_dimension, data['width']):
        raise ParameterError('Invalid width parameter')
    if 'height' in data and not re.match(pattern_dimension, data['height']):
        raise ParameterError('Invalid height parameter')
    if 'host' in data and not re.match(pattern_path_cars, data['host']):
        raise ParameterError('Invalid host parameter')
    return


def is_valid_show_scheduling_portal(data):
    return is_valid_show_resource_manager(data)


def is_valid_show_workflow_automation(data):
    return is_valid_show_resource_manager(data)


def is_valid(data):
    if data['trigger'] == 'help':
        return is_valid_help(data)
    elif data['trigger'] == 'connect':
        return is_valid_connect(data)
    elif data['trigger'] == 'import':
        return is_valid_import(data)
    elif data['trigger'] == 'configure':
        return is_valid_configure(data)
    elif data['trigger'] == 'task':
        return is_valid_task(data)
    elif data['trigger'] == 'delete_task':
        return is_valid_delete_task(data)
    elif data['trigger'] == 'pre_script':
        return is_valid_pre_script(data)
    elif data['trigger'] == 'post_script':
        return is_valid_post_script(data)
    elif data['trigger'] == 'selection_script':
        return is_valid_selection_script(data)
    elif data['trigger'] == 'job_selection_script':
        return is_valid_job_selection_script(data)
    elif data['trigger'] == 'fork_env':
        return is_valid_fork_env(data)
    elif data['trigger'] == 'job_fork_env':
        return is_valid_job_fork_env(data)
    elif data['trigger'] == 'split':
        return is_valid_split(data)
    elif data['trigger'] == 'runs':
        return is_valid_runs(data)
    elif data['trigger'] == 'process':
        return is_valid_process(data)
    elif data['trigger'] == 'merge':
        return is_valid_merge(data)
    elif data['trigger'] == 'start':
        return is_valid_start(data)
    elif data['trigger'] == 'loop':
        return is_valid_loop(data)
    elif data['trigger'] == 'condition':
        return is_valid_condition(data)
    elif data['trigger'] == 'branch':
        return is_valid_branch(data)
    elif data['trigger'] == 'if':
        return is_valid_if(data)
    elif data['trigger'] == 'else':
        return is_valid_else(data)
    elif data['trigger'] == 'continuation':
        return is_valid_continuation(data)
    elif data['trigger'] == 'job':
        return is_valid_job(data)
    elif data['trigger'] == 'draw_job':
        return is_valid_draw_job(data)
    elif data['trigger'] == 'write_dot':
        return is_valid_write_dot(data)
    elif data['trigger'] == 'import_dot':
        return is_valid_import_dot(data)
    elif data['trigger'] == 'submit_job':
        return is_valid_submit_job(data)
    elif data['trigger'] == 'get_job_result':
        return is_valid_get_job_result(data)
    elif data['trigger'] == 'get_task_result':
        return is_valid_get_task_result(data)
    elif data['trigger'] == 'print_job_output':
        return is_valid_print_job_output(data)
    elif data['trigger'] == 'print_task_output':
        return is_valid_print_task_output(data)
    elif data['trigger'] == 'list_submitted_jobs':
        return is_valid_list_submitted_jobs(data)
    elif data['trigger'] == 'list_nodesources':
        return is_valid_list_nodesources(data)
    elif data['trigger'] == 'list_hosts':
        return is_valid_list_hosts(data)
    elif data['trigger'] == 'list_tokens':
        return is_valid_list_tokens(data)
    elif data['trigger'] == 'list_resources':
        return is_valid_list_resources(data)
    elif data['trigger'] == 'export_xml':
        return is_valid_export_xml(data)
    elif data['trigger'] == 'show_resource_manager':
        return is_valid_show_resource_manager(data)
    elif data['trigger'] == 'show_scheduling_portal':
        return is_valid_show_scheduling_portal(data)
    elif data['trigger'] == 'show_workflow_automation':
        return is_valid_show_workflow_automation(data)
    return None


class Pragma:
    pattern = r"\w+"

    pragmas_generic = ['draw_job',
                       'configure',
                       'task',
                       'delete_task',
                       'import',
                       'split',
                       'runs',
                       'process',
                       'merge',
                       'start',
                       'loop',
                       'condition',
                       'branch',
                       'if',
                       'else',
                       'continuation',
                       'job',
                       'selection_script',
                       'job_selection_script',
                       'fork_env',
                       'job_fork_env',
                       'pre_script',
                       'post_script',
                       'write_dot',
                       'import_dot',
                       'submit_job',
                       'help',
                       'get_job_result',
                       'get_task_result',
                       'list_nodesources',
                       'list_hosts',
                       'list_tokens',
                       'list_resources',
                       'print_job_output',
                       'print_task_output',
                       'list_submitted_jobs',
                       'export_xml',
                       'show_resource_manager',
                       'show_scheduling_portal',
                       'show_workflow_automation'
                       ]

    pragmas_empty = ['connect',
                     'submit_job',
                     'import',
                     'split',
                     'runs',
                     'process',
                     'merge',
                     'start',
                     'loop',
                     'condition',
                     'branch',
                     'if',
                     'else',
                     'continuation',
                     'job_selection_script',
                     'job_fork_env',
                     'draw_job',
                     'help',
                     'get_job_result',
                     'print_job_output',
                     'list_submitted_jobs',
                     'list_nodesources',
                     'list_hosts',
                     'list_tokens',
                     'list_resources',
                     'export_xml',
                     'show_resource_manager',
                     'show_scheduling_portal',
                     'show_workflow_automation'
                     ]

    pragmas_connected_mode = ['draw_job',
                              'task',
                              'delete_task',
                              'import',
                              'job',
                              'split',
                              'runs',
                              'process',
                              'merge',
                              'start',
                              'loop',
                              'condition',
                              'branch',
                              'if',
                              'else',
                              'continuation',
                              'selection_script',
                              'job_selection_script',
                              'fork_env',
                              'job_fork_env',
                              'pre_script',
                              'post_script',
                              'write_dot',
                              'import_dot',
                              'submit_job',
                              'get_job_result',
                              'get_task_result',
                              'list_nodesources',
                              'list_hosts',
                              'list_tokens',
                              'list_resources',
                              'print_job_output',
                              'print_task_output',
                              'list_submitted_jobs',
                              'export_xml',
                              'show_resource_manager',
                              'show_scheduling_portal',
                              'show_workflow_automation'
                              ]

    pragmas_not_connected_mode = ['connect',
                                  'help',
                                  'configure'
                                  ]

    def __init__(self):
        self.trigger = 'task'

    def is_valid_for_parsing(self, params):
        pattern_list = r"\[ *[a-zA-Z_](\w|\-)* *( *, *[a-zA-Z_](\w|\-)*)* *\]"
        pattern_list_tuples = r"\[ *\( *\w+ *, *\w+ *\)( *, *\( *\w+ *, *\w+ *\))* *\]"
        pattern_path_cars = r"[a-zA-Z0-9_\/\\:\.-]*"
        pattern_l = r"[a-zA-Z_](\w|\-)*"
        pattern_r = r"([a-zA-Z_](\w|\-)*|" + pattern_list_tuples + r"|" + pattern_list + r"|" + pattern_path_cars + r")"
        pattern_connect = r"^( *host *= *" + pattern_path_cars + r" *, *)?(port *= *\d+ *, *)?" \
                          r"(login *= *[a-zA-Z_][a-zA-Z0-9_]* *, *password *= *[^ ]*)$"
        pattern_connect_with_url = r"^( *url *= *" + pattern_path_cars + r" *)" \
                                   r"(login *= *[a-zA-Z_][a-zA-Z0-9_]* *, *password *= *[^ ]*)$"
        pattern_connect_with_path = r"^( *path *= *" + pattern_path_cars + r" *)$"
        pattern_generic = r"^( *" + pattern_l + r" *= *" + pattern_r + r")( *, *" + pattern_l + r" *= *" + \
                          pattern_r + r" *)*$"

        valid_empty = params == "" and self.trigger in Pragma.pragmas_empty

        if valid_empty:
            return

        invalid_generic = not re.match(pattern_generic, params) and self.trigger in Pragma.pragmas_generic
        invalid_connect = not (re.match(pattern_connect, params) or re.match(pattern_connect_with_url, params) or
                               pattern_connect_with_path) and self.trigger == 'connect'

        if invalid_connect or invalid_generic:
            raise ParsingError('Invalid parameters.')

    def parse(self, pragma_string):
        pragma_string = pragma_string.strip(" #%)")
        sep_lines = pragma_string.split('(', 1)
        self.trigger = sep_lines[0].strip(" ")
        data = dict(trigger=self.trigger, name='')
        if len(sep_lines) == 2:
            self.is_valid_for_parsing(sep_lines[1])
            extract_params(sep_lines[1], data)
            is_valid(data)
        return data
