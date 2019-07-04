import re
from .exceptions import *


def get_usage_help():
    return '   #%help([pragma=PRAGMA_NAME])\n'


def get_usage_connect():
    return '   #%connect([host=YOUR_HOST], [port=YOUR_PORT], login=YOUR_LOGIN, password=YOUR_PASSWORD)\n' \
           + '   #%connect(path=PATH_TO/YOUR_CONFIG_FILE.ini)\n'


def get_usage_import():
    return '   #%import([language=SCRIPT_LANGUAGE])\n'


def get_usage_task():
    return '   #%task(name=TASK_NAME, [dep=[TASK_NAME1,TASK_NAME2,...]], [generic_info=[(KEY1,VAL1),' \
           '(KEY2,VALUE2),...]], [export=[VAR_NAME1,VAR_NAME2,...]], [import=[VAR_NAME1,VAR_NAME2,...]], ' \
           '[path=IMPLEMENTATION_FILE_PATH], [language=SCRIPT_LANGUAGE])\n'


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


def get_usage_job():
    return '   #%job(name=JOB_NAME)\n'


def get_usage_draw_job():
    return '   #%draw_job([name=JOB_NAME], [inline=on/off], [save=on/off])\n'


def get_usage_write_job():
    return '   #%write_dot(name=FILE_NAME)\n'


def get_usage_submit_job():
    return '   #%submit_job([name=JOB_NAME])\n'


def get_usage_get_result():
    return '   #%get_result(id=JOB_ID)\n'


def get_usage_list_submitted_jobs():
    return '   #%list_submitted_jobs()\n'


def get_usage_show_resource_manager():
    return '   #%show_resource_manager([height=HEIGHT_VALUE, width=WIDTH_VALUE])\n'


def get_usage_show_scheduling_portal():
    return '   #%show_scheduling_portal([height=HEIGHT_VALUE, width=WIDTH_VALUE])\n'


def get_usage_show_workflow_automation():
    return '   #%show_workflow_automation([height=HEIGHT_VALUE, width=WIDTH_VALUE])\n'


def get_help(trigger):
    if trigger == 'connect':
        help_msg = 'Pragma #%connect(): connects to an ActiveEon server\n'
        help_msg += 'Usages:\n' + get_usage_connect()
    elif trigger == 'import':
        help_msg = '#%import(): imports specified libraries to all tasks of a same script language\n'
        help_msg += 'Usages:\n' + get_usage_import()
    elif trigger == 'task':
        help_msg = '#%task(): creates/modifies a task\n'
        help_msg += 'Usages:\n' + get_usage_task()
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
    elif trigger == 'job':
        help_msg = '#%job(): creates/renames the job\n'
        help_msg += 'Usages:\n' + get_usage_job()
    elif trigger == 'draw_job':
        help_msg = '#%draw_job(): plot the workflow\n'
        help_msg += 'Usages:\n' + get_usage_draw_job()
    elif trigger == 'write_dot':
        help_msg = '#%write_dot(): writes the workflow in .dot format\n'
        help_msg += 'Usages:\n' + get_usage_write_job()
    elif trigger == 'submit_job':
        help_msg = '#%submit_job(): submits the job to the scheduler\n'
        help_msg += 'Usages:\n' + get_usage_submit_job()
    elif trigger == 'get_result':
        help_msg = '#%get_result(): gets and prints the job results\n'
        help_msg += 'Usages:\n' + get_usage_get_result()
    elif trigger == 'list_submitted_jobs':
        help_msg = '#%list_submitted_jobs(): gets and prints the ids and names of the submitted jobs\n'
        help_msg += 'Usages:\n' + get_usage_list_submitted_jobs()
    elif trigger == 'show_resource_manager':
        help_msg = '#%show_resource_manager(): opens the ActiveEon resource manager portal\n'
        help_msg += 'Usages:\n' + get_usage_show_resource_manager()
    elif trigger == 'show_scheduling_portal':
        help_msg = '#%show_scheduling_portal(): opens the ActiveEon scheduling portal\n'
        help_msg += 'Usages:\n' + get_usage_show_scheduling_portal()
    elif trigger == 'show_workflow_automation':
        help_msg = '#%show_workflow_automation(): opens the ActiveEon workflow automation portal\n'
        help_msg += 'Usages:\n' + get_usage_show_workflow_automation()
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
    elif trigger == 'task':
        return get_usage_task()
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
    elif trigger == 'job':
        return get_usage_job()
    elif trigger == 'draw_job':
        return get_usage_draw_job()
    elif trigger == 'write_dot':
        return get_usage_write_job()
    elif trigger == 'submit_job':
        return get_usage_submit_job()
    elif trigger == 'get_result':
        return get_usage_get_result()
    elif trigger == 'list_submitted_jobs':
        return get_usage_list_submitted_jobs()
    elif trigger == 'show_resource_manager':
        return get_usage_show_resource_manager()
    elif trigger == 'show_scheduling_portal':
        return get_usage_show_scheduling_portal()
    elif trigger == 'show_workflow_automation':
        return get_usage_show_workflow_automation()
    return None


def extract_list(msg):
    draft = re.split(']', msg, 1)[0].strip('[')
    return re.split(',', draft)


def extract_tuples_list(msg):
    draft = re.split('\)]', msg, 1)[0].strip('[(')
    draft = re.split(',', draft.replace(')', "").replace('(', ""))
    t_list = []
    for index in range(0, len(draft), 2):
        t_list.append((draft[index],draft[index + 1]))
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
    if 'login' not in data or not re.match(pattern_name, data['login']) or \
            'password' not in data or not re.match(pattern_password, data['password']):
        raise ParameterError('Invalid login/password parameters')
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


def is_valid_names_tuples_list(gen_info):
    pattern_name = r"^[a-zA-Z_]\w*$"
    for pair in gen_info:
        if not re.match(pattern_name, pair[0]) or not re.match(pattern_name, pair[1]):
            raise ParameterError('Invalid generic information parameter')
    return


def is_valid_names_list(deps):
    pattern_name = r"^[a-zA-Z_]\w*$"
    for name in deps:
        if not re.match(pattern_name, name):
            raise ParameterError('Invalid dependencies parameter')
    return


def is_valid_task(data):
    pattern_name = r"^[a-zA-Z_]\w*$"
    pattern_language = r"^[a-zA-Z_]+$"
    pattern_path_cars = r"^[a-zA-Z0-9_\/\\:\.-]+$"
    if 'name' not in data or not re.match(pattern_name, data['name']):
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


def is_valid_job(data):
    pattern_name = r"^[a-zA-Z_]\w*$"
    if 'name' not in data or not re.match(pattern_name, data['name']):
        raise ParameterError('Invalid name parameter')
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


def is_valid_submit_job(data):
    return is_valid_write_dot(data)


def is_valid_get_result(data):
    pattern_name = r"^[a-zA-Z_]\w*$"
    pattern_id = r"^\d+$"
    if 'name' in data and re.match(pattern_name, data['name']):
        return
    if 'id' in data and re.match(pattern_id, data['id']):
        return
    raise ParameterError('Invalid parameters')


def is_valid_list_submitted_jobs(data):
    pass


def is_valid_show_resource_manager(data):
    pattern_dimension = r"^\d+$"
    pattern_path_cars = r"^[a-zA-Z0-9_\/\\:\.-]+$"
    if ('width' in data and 'height' not in data) or ('width' not in data and 'height' in data):
        raise ParsingError('Missing one of height/width parameters')
    if 'width' in data and 'height' in data and \
            not (re.match(pattern_dimension, data['width']) and re.match(pattern_dimension, data['height'])):
        raise ParameterError('Invalid height/width parameters')
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
    elif data['trigger'] == 'task':
        return is_valid_task(data)
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
    elif data['trigger'] == 'job':
        return is_valid_job(data)
    elif data['trigger'] == 'draw_job':
        return is_valid_draw_job(data)
    elif data['trigger'] == 'write_dot':
        return is_valid_write_dot(data)
    elif data['trigger'] == 'submit_job':
        return is_valid_submit_job(data)
    elif data['trigger'] == 'get_result':
        return is_valid_get_result(data)
    elif data['trigger'] == 'list_submitted_jobs':
        return is_valid_list_submitted_jobs(data)
    elif data['trigger'] == 'show_resource_manager':
        return is_valid_show_resource_manager(data)
    elif data['trigger'] == 'show_scheduling_portal':
        return is_valid_show_scheduling_portal(data)
    elif data['trigger'] == 'show_workflow_automation':
        return is_valid_show_workflow_automation(data)
    return None


class Pragma:
    pattern = r"\w+"

    def __init__(self):
        self.trigger = 'task'

    def is_valid_for_parsing(self, params):
        pattern_list = r"\[ *[a-zA-Z_]\w* *( *, *[a-zA-Z_]\w*)* *\]"
        pattern_list_tuples = r"\[ *\( *\w+ *, *\w+ *\)( *, *\( *\w+ *, *\w+ *\))* *\]"
        pattern_path_cars = r"[a-zA-Z0-9_\/\\:\.-]*"
        pattern_l = r"[a-zA-Z_]\w*"
        pattern_r = r"([a-zA-Z_]\w*|" + pattern_list_tuples + r"|" + pattern_list + r"|" + pattern_path_cars + r")"
        pattern_connect = r"^( *host *= *" + pattern_path_cars + r" *, *)?(port *= *\d+ *, *)?" \
                          r"(login *= *[a-zA-Z_][a-zA-Z0-9_]* *, *password *= *[^ ]*)$"
        pattern_connect_with_path = r"^( *path *= *" + pattern_path_cars + r" *)$"
        pattern_generic = r"^( *" + pattern_l + r" *= *" + pattern_r + r")( *, *" + pattern_l + r" *= *" + \
                          pattern_r + r" *)*$"

        pragmas_generic = ['draw_job',
                           'task',
                           'import',
                           'job',
                           'selection_script',
                           'job_selection_script',
                           'fork_env',
                           'job_fork_env',
                           'pre_script',
                           'post_script',
                           'write_dot',
                           'submit_job',
                           'help',
                           'list_submitted_jobs',
                           'show_resource_manager',
                           'show_scheduling_portal',
                           'show_workflow_automation'
                           ]
        pragmas_empty = ['submit_job',
                         'import',
                         'job_selection_script',
                         'job_fork_env',
                         'draw_job',
                         'help',
                         'list_submitted_jobs',
                         'show_resource_manager',
                         'show_scheduling_portal',
                         'show_workflow_automation'
                         ]

        invalid_generic = not re.match(pattern_generic, params) and self.trigger in pragmas_generic
        invalid_connect = not (re.match(pattern_connect, params) or
                               re.match(pattern_connect_with_path, params)) and self.trigger == 'connect'
        valid_empty = params == "" and self.trigger in pragmas_empty

        if valid_empty:
            return

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
