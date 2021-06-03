![License BSD](https://img.shields.io/badge/License-BSD-blue.svg "License BSD")
![Python 3](https://img.shields.io/badge/Python-3-brightgreen.svg "Python 3")
![blabla](https://img.shields.io/pypi/v/proactive-jupyter-kernel.svg "bla")

# proactive-jupyter-kernel
The ActiveEon Jupyter Kernel adds a kernel backend to Jupyter. This kernel interfaces directly with the ProActive
scheduler and constructs tasks and workflows to execute them on the fly.

With this interface, users can run their code locally and test it using a native python kernel, and by a simple switch to
ProActive kernel, run it on remote public or private infrastructures without having to modify the code. See the example below:

![Image not found](./images/direct_execution_from_jupyter.png "Direct execution from Jupyter with ActiveEon Kernel")

## 1. Installation:

### 1.1 Requirements:

Python 2 or 3

### 1.2 Using PyPi

* open a terminal

* install the ProActive jupyter kernel with the following commands:

```bash
$ pip install proactive proactive-jupyter-kernel --upgrade
$ python -m proactive-jupyter-kernel.install
```

### 1.3 Using source code

* open a terminal

* clone the repository on your local machine:

```bash
$ git clone git@github.com:ow2-proactive/proactive-jupyter-kernel.git
```

* install the ProActive jupyter kernel with the following commands:

```bash
$ pip install proactive-jupyter-kernel/
$ python -m proactive-jupyter-kernel.install
```

## 2. Platform

You can use any jupyter platform.
We recommend to use [jupyter lab](https://jupyterlab.readthedocs.io/en/stable/). To launch it from your terminal after
having installed it:

```bash
$ jupyter lab
```
or in daemon mode:
```bash
$ nohup jupyter lab &>/dev/null &
```

When opened, click on the ProActive icon to open a notebook based on the ProActive kernel.

## 3. Help

As a quick start, we recommend the user to run the `#%help()` pragma using the following script:

```python
#%help()
```

This script gives a brief description of all the different pragmas that the ProActive Kernel provides.

To get a more detailed description of a needed pragma, the user can run the following script:

```python
#%help(pragma=PRAGMA_NAME)
```

## 4. Connection

### 4.1 Using connect()

If you are trying ProActive for the first time, sign up on the [try platform](https://try.activeeon.com/signup.html).
Once you receive your login and password, connect to the trial platform using the `#%connect()` pragma:

```python
#%connect(login=YOUR_LOGIN, password=YOUR_PASSWORD)
```

To connect to another ProActive server host, use the later pragma this way:

```python
#%connect(host=YOUR_HOST, [port=YOUR_PORT], login=YOUR_LOGIN, password=YOUR_PASSWORD)
```

Notice that the `port` parameter is optional. The default connexion port is `8080`.

You can also connect to a distant server by providing its `url` in the following way:

```python
#%connect(url=YOUR_SERVER_URL, login=YOUR_LOGIN, password=YOUR_PASSWORD)
```

By providing the complete `url` of the server, users can eventually connect through the secure HTTPS protocol.

### 4.2 Using a configuration file:

For automatic sign in, create a file named *proactive_config.ini* in your notebook working directory.

Fill your configuration file according to one of the following two formats:

- By providing the server `host` and `port`:

```ini
[proactive_server]
host=YOUR_HOST
port=YOUR_PORT
[user]
login=YOUR_LOGIN
password=YOUR_PASSWORD
```

- By providing the server `url`:

```ini
[proactive_server]
url=YOUR_SERVER_URL
[user]
login=YOUR_LOGIN
password=YOUR_PASSWORD
```

Save your changes and restart the ProActive kernel.

You can also force the current kernel to connect using any _.ini_ config file through the `#%connect()` pragma:

```python
#%connect(path=PATH_TO/YOUR_CONFIG_FILE.ini)
```

(For more information about this format please check
[configParser](https://docs.python.org/3/library/configparser.html))

## 5. Usage

#### 5.1 Creating a Python task

To create a new task, use the pragma `#%task()` followed by the task implementation script written into a notebook
block code.
To use this pragma, a task name has to be provided at least. Example:

```python
#%task(name=myTask)
print('Hello world')
```

General usage:

```python
#%task(name=TASK_NAME, [language=SCRIPT_LANGUAGE], [dep=[TASK_NAME1,TASK_NAME2,...]], [generic_info=[(KEY1,VAL1), (KEY2,VALUE2),...]], [variables=[(VAR1,VAL1), (VAR2,VALUE2),...]], [export=[VAR_NAME1,VAR_NAME2,...]], [import=[VAR_NAME1,VAR_NAME2,...]], [path=IMPLEMENTATION_FILE_PATH])\n'
```

Users can also provide more information about the task using the pragma's options. In the following, we give more
details about the possible options:

##### 5.1.1 Language

The `language` parameter is needed when the task script is not written in native Python. If not provided, Python will be
 selected as the default language.
The supported programming languages are:

* Linux_Bash
* Windows_Cmd
* DockerCompose
* Scalaw
* Groovy
* Javascript
* Jython
* Python
* Ruby
* Perl
* PowerShell
* R

Here is an example that shows a task implementation written in `Linux_Bash`:

```bash
#%task(name=myTask, language=Linux_Bash)
echo 'Hello, World!'
```

##### 5.1.2 Dependencies

One of the most important notions in workflows is the dependencies between tasks. To specify this information, use the
`dep` parameter. Its value should be a list of all tasks on which the new task depends. Example:

```python
#%task(name=myTask,dep=[parentTask1,parentTask2])
print('Hello world')
```

##### 5.1.3 Variables

To specify [task variables](https://doc.activeeon.com/latest/user/ProActiveUserGuide.html#_task_variables), 
you should provide the `variables` parameter. Its value should be a list of tuples `(key,value)` that corresponds to 
the names and adequate values of the corresponding task variables. Example:

```python
#%task(name=myTask, variables=[(var1,value1),(var2,value2)])
print('Hello world')
```

##### 5.1.4 Generic information

To specify the values of some advanced ProActive variables called
[generic_information](https://doc.activeeon.com/latest/user/ProActiveUserGuide.html#_generic_information), you should
provide the `generic_info` parameter. Its value should be a list of tuples `(key,value)` that corresponds to the names
and adequate values of the Generic Information. Example:

```python
#%task(name=myTask, generic_info=[(var1,value1),(var2,value2)])
print('Hello world')
```

##### 5.1.5 Export/import variables

The `export` and `import` parameters ensure variables propagation between the different tasks of a workflow.
If `myTask1` variables `var1` and `var2` are needed in `myTask2`, both pragmas have to specify this information as
follows:

* `myTask1` should include an `export` parameter with a list of these variable names,
* `myTask2` should include an `import` parameter with a list including the same names.

Example:

`myTask1` implementation block would be:
```python
#%task(name=myTask1, export=[var1,var2])
var1 = "Hello"
var2 = "ActiveEon!"
```

and `myTask2` implementation block would be:
```python
#%task(name=myTask2, dep=[myTask1], import[var1,var2])
print(var1 + " from " + var2)
```

##### 5.1.6 Implementation file

It is also possible to use an external implementation file to define the task implementation. To do so, the option `path`
 should be used.

Example:

```python
#%task(name=myTask,path=PATH_TO/IMPLEMENTATION_FILE.py)
```

#### 5.2 Importing libraries

The main difference between the ProActive and 'native language' kernels resides in the way the memory is accessed
during blocks execution. In a common native language kernel, the whole script code (all the notebook blocks) is
locally executed in the same shared memory space; whereas the ProActive kernel will execute each created task in an
independent process. In order to facilitate the transition from native language to ProActive kernels, we included the
pragma `#%import()`. This pragma gives the user the ability to add libraries that are common to all created tasks, and
thus relative distributed processes, that are implemented in the same native script language.

The import pragma is used as follows:

`#%import([language=SCRIPT_LANGUAGE])`.

Example:

```python
#%import(language=Python)
import os
import pandas
```

NOTE: If the language is not specified, Python is considered as default language.

#### 5.3 Adding a fork environment

To configure a fork environment for a task, use the `#%fork_env()` pragma. To do so, you have to provide the name of the
corresponding task and the fork environment implementation.

Example:

```python
#%fork_env(name=TASK_NAME)
containerName = 'activeeon/dlm3'
dockerRunCommand =  'docker run '
dockerParameters = '--rm '
paHomeHost = variables.get("PA_SCHEDULER_HOME")
paHomeContainer = variables.get("PA_SCHEDULER_HOME")
proActiveHomeVolume = '-v '+paHomeHost +':'+paHomeContainer+' '
workspaceHost = localspace
workspaceContainer = localspace
workspaceVolume = '-v '+localspace +':'+localspace+' '
containerWorkingDirectory = '-w '+workspaceContainer+' '
preJavaHomeCmd = dockerRunCommand + dockerParameters + proActiveHomeVolume + workspaceVolume + containerWorkingDirectory + containerName
```

Or, you can provide the task name and the path of a _.py_ file containing the fork environment code:

```python
#%fork_env(name=TASK_NAME, path=PATH_TO/FORK_ENV_FILE.py)
```

#### 5.4 Adding a selection script

To add a selection script to a task, use the `#%selection_script()` pragma. To do so, you have to provide the name of
the corresponding task and the selection code implementation.

Example:

```python
#%selection_script(name=TASK_NAME)
selected = True
```

Or, you can provide the task name and the path of a _.py_ file containing the selection code:

```python
#%selection_script(name=TASK_NAME, path=PATH_TO/SELECTION_CODE_FILE.py)
```

#### 5.5 Adding job fork environment and/or selection script

If the selection scripts and/or the fork environments are the same for all job tasks, we can add them just once using
the `job_selection_script` and/or the `job_fork_env` pragmas.

Usage:

For a job selection script, please use:

```python
#%job_selection_script([language=SCRIPT_LANGUAGE], [path=./SELECTION_CODE_FILE.py], [force=on/off])
```

For a job fork environment, use:

```python
#%job_fork_env([language=SCRIPT_LANGUAGE], [path=./FORK_ENV_FILE.py], [force=on/off])
```

The `force` parameter defines whether the pragma has to overwrite the task selection scripts or the fork environment
already set.

#### 5.6 Adding pre and/or post scripts

Sometimes, specific scripts has to be executed before and/or after a particular task. To do that, the solution provides
 `pre_script` and `post_script` pragmas.

To add a pre-script to a task, please use:

```python
#%pre_script(name=TASK_NAME, language=SCRIPT_LANGUAGE, [path=./PRE_SCRIPT_FILE.py])
```

To add a post-script to a task, use:

```python
#%post_script(name=TASK_NAME, language=SCRIPT_LANGUAGE, [path=./POST_SCRIPT_FILE.py])
```

#### 5.7 Branch control

The [branch](https://doc.activeeon.com/latest/user/ProActiveUserGuide.html#_branch) control provides the ability to 
choose between two alternative task flows, with the possibility to merge back to a common one.

To add a branch control to the current workflow, four specific tasks and one control condition should be added in 
accordance with the following order:

1. a `branch` task,
2. the related branching `condition` script,
3. an `if` task that should be executed if the result of the `condition` task if `true`,
4. an `else` task that should be executed if the result of the `condition` task if `false`,
5. a `continuation` task that should be executed after the `if` or the `else` tasks.

To add a `branch` task, you can rely on the following macro:

```python
#%branch([name=TASK_NAME], [dep=[TASK_NAME1,TASK_NAME2,...]], [generic_info=[(KEY1,VAL1), (KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE], [path=./FORK_ENV_FILE.py])
```

For the branching `condition` script, use:

```python
#%condition()
```

For an `if` task, please use:

```python
#%if([name=TASK_NAME], [generic_info=[(KEY1,VAL1),(KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE], [path=./FORK_ENV_FILE.py])
```

For an `else` task, use:

```python
#%else([name=TASK_NAME], [generic_info=[(KEY1,VAL1),(KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE], [path=./FORK_ENV_FILE.py])
```

And finally, for the `continuation` task:

```python
#%continuation([name=TASK_NAME], [generic_info=[(KEY1,VAL1),(KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE], [path=./FORK_ENV_FILE.py])
```


#### 5.8 Loop control

The [loop](https://doc.activeeon.com/latest/user/ProActiveUserGuide.html#_loop) control provides the ability to repeat 
a set of tasks.

To add a loop control to the current workflow, two specific tasks and one control condition should be added 
in the following order:

1. a `start` task,
2. the related looping `condition` script,
3. a `loop` task.

For a `start` task, use:

```python
#%start([name=TASK_NAME], [dep=[TASK_NAME1,TASK_NAME2,...]], [generic_info=[(KEY1,VAL1), (KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE], [path=./FORK_ENV_FILE.py])
```

For the looping `condition` script, use:

```python
#%condition()
```

For a `loop` task, please use:

```python
#%loop([name=TASK_NAME], [generic_info=[(KEY1,VAL1),(KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE], [path=./FORK_ENV_FILE.py])
```

#### 5.9 Replicate control

The [replication](https://doc.activeeon.com/latest/user/ProActiveUserGuide.html#_replicate) allows the execution of 
multiple tasks in parallel when only one task is defined, and the number of tasks to run could change.

Through the ProActive Jupyter Kernel, users can add replicate controls in two main ways, a generic and a straight 
forward way.

##### 5.9.1 Generic usage

To add a replicate control to the current workflow in the generic method, three specific tasks and one control runs 
script should be added according to the following order:

1. a `split` task,
2. the related replication `runs` script,
3. a `process` task,
4. a `merge` task.

For a `split` task, use:

```python
#%split([name=TASK_NAME], [dep=[TASK_NAME1,TASK_NAME2,...]], [generic_info=[(KEY1,VAL1), (KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE], [path=./FORK_ENV_FILE.py])
```

For the replication `runs` script, use:

```python
#%runs()
```

For a `process` task, please use:

```python
#%process([name=TASK_NAME], [generic_info=[(KEY1,VAL1),(KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE], [path=./FORK_ENV_FILE.py])
```

And finally, for a `merge` task, use:

```python
#%merge([name=TASK_NAME], [generic_info=[(KEY1,VAL1),(KEY2,VALUE2),...]], [language=SCRIPT_LANGUAGE], [path=./FORK_ENV_FILE.py])
```

##### 5.9.2 Straight forward usage

The straight forward method to add a replication is most of all useful when the parallelism that should be 
implemented is a task parallelism (the generic usage is more adapted to data parallelism).

To add a replication to a task, just add the runs control script by providing the `runs` option of the `task` pragma.
Example:

```python
#%task(name=T2,dep=[T1],runs=3)
print("This output should be displayed 3 times ...")
```

NOTE: To construct a valid workflow, straight forward replicated tasks must have one and only one parent task and one 
child task at most. More information about replicate validation criteria are available 
[here](https://doc.activeeon.com/latest/user/ProActiveUserGuide.html#_replicate).

#### 5.10 Delete a task

To delete a task from the workflow, the user should run the pragma `#%delete_task()` in the following way:

```python
#%delete_task(name=TASK_NAME)
```

#### 5.11 Create a job

To create a job, specify job variables and/or job generic information, use the `#%job()` pragma:

```python
#%job(name=JOB_NAME, [generic_info=[(KEY1,VAL1), (KEY2,VALUE2),...]], [variables=[(VAR1,VAL1), (VAR2,VALUE2),...]])
```

NOTE: It is not necessary to create and assign a name explicitly to the job. If not done by the user, this step is
implicitly performed when the job is submitted (check section [Submit your job to the scheduler](#510-submit-your-job-to-the-scheduler) for more
information).

#### 5.12 Visualize job

To visualize the created workflow, use the `#%draw_job()` pragma to plot the workflow graph that represents the job
into a separate window:

```python
#%draw_job()
```

Two optional parameters can be used to configure the way the kernel plots the workflow graph.

**inline plotting:**

If this parameter is set to `off`, plotting the workflow graph is done through a [Matplotlib](https://matplotlib.org/) 
external window. The default value is `on`.

```python
#%draw_job(inline=off)
```

**save the workflow graph locally:**

To be sure that the workflow is saved into a _.png_ file, this option needs to be set to `on`. The default value is
`off`.

```python
#%draw_job(save=on)
```

Note that the job's name can take one of the following possible values:

1. The parameter `name` 's value, if provided
2. The job's name, if created
3. The notebook's name, if the kernel can retrieve it
4. `Unnamed_job`, otherwise

General usage:

```python
#%draw_job([name=JOB_NAME], [inline=off], [save=on])
```

#### 5.13 Export the workflow in dot format

To export the created workflow into a [GraphViz](https://www.graphviz.org/) _.dot_ format, use the `#%write_dot()` pragma:

```python
#%write_dot(name=FILE_NAME)
```

#### 5.14 Import a workflow from a dot file

To create a workflow according to a [GraphViz](https://www.graphviz.org/) _.dot_ file, use the pragma `#%import_dot()`:

```python
#%import_dot(path=PATH_TO/FILE_NAME.dot)
```

By default, the workflow will contain _Python_ tasks with empty implementation scripts. If you want to modify or add 
any information to a specific task, please use, as explained in [Creating a Task](#51-creating-a-python-task), the `#%task()` 
pragma.

#### 5.15 Submit your job to the scheduler

To submit the job to the ProActive Scheduler, the user has to use the `#%submit_job()` pragma:

```python
#%submit_job()
```

If the job is not created, or is not up-to-date, the `#%submit_job()` creates a new job named as the old one.
To provide a new name, use the same pragma and provide a name as parameter:

```python
#%submit_job([name=JOB_NAME])
```

If the job's name is not set, the ProActive kernel uses the current notebook name, if possible, or gives a random one.

#### 5.16 List all submitted jobs

To get all submitted job IDs and names, use `list_submitted_jobs` pragma this way:

```python
#%list_submitted_jobs()
```

#### 5.17 Export the workflow in XML format

To export the created workflow in _.xml_ format, use the `#%export_xml()` pragma:

```python
#%export_xml([name=FILENAME])
```

Notice that the _.xml_ file will be saved under one of the following names:

1. The parameter `name` 's value, if provided
2. The job's name, if created
3. The notebook's name, if the kernel can retrieve it
4. `Unnamed_job`, otherwise

#### 5.18 Get results

After the execution of a ProActive workflow, two outputs can be obtained,
* results: values that have been saved in the 
[task result variable](https://doc.activeeon.com/latest/user/ProActiveUserGuide.html#_task_result),
* console outputs: classic outputs that have been displayed/printed 

To get task results, please use the `#%get_task_result()` pragma by providing the task name, and either the job ID or
the job name:

```python
#%get_task_result([job_id=JOB_ID], [job_name=JOB_NAME], task_name=TASK_NAME)
```

The result(s) of all the tasks of a job can be obtained with the `#%get_job_result()` pragma, by providing the job name
or the job ID:

```python
#%get_job_result([job_id=JOB_ID], [job_name=JOB_NAME])
```

To get and display console outputs of a task, you can use the `#%print_task_output()` pragma in the following
way:

```python
#%print_task_output([job_id=JOB_ID], [job_name=JOB_NAME], task_name=TASK_NAME)
```

Finally, the  `#%print_job_output()` pragma allows to print all job outputs, by providing the job name or the job ID:

```python
#%print_job_output([job_id=JOB_ID], [job_name=JOB_NAME])
```

NOTE: If neither `job_name` nor the `job_id` are provided, the last submitted job is selected by default. 

### 6. Display and use ActiveEon Portals directly in Jupyter

Finally, to have the hand on more parameters and features, the user should use ActiveEon Studio portals.
The main ones are the _Resource Manager_, the _Scheduling Portal_ and the _Workflow Automation_.

The example below shows how the user can directly monitor his submitted job's execution in the scheduling portal:

![Image not found](./images/direct_submit_and_see_from_jupyter.png "Directly in Jupyter: Submit, See your Job executing, Get Results")

To show the resource manager portal related to the host you are connected to, just run:

```python
#%show_resource_manager([host=YOUR_HOST], [height=HEIGHT_VALUE], [width=WIDTH_VALUE])
```

For the related scheduling portal:

```python
#%show_scheduling_portal([host=YOUR_HOST], [height=HEIGHT_VALUE], [width=WIDTH_VALUE])
```

And, for the related workflow automation:

```python
#%show_workflow_automation([host=YOUR_HOST], [height=HEIGHT_VALUE], [width=WIDTH_VALUE])
```

NOTE: The parameters `height` and `width` allow the user to adjust the size of the window inside the notebook.

#### Current status

Features:

* *help*: prints all different pragmas/features of the kernel

* *connect*: connects to an ActiveEon server (OPTION: connection using a configuration file)

* *import*: import specified libraries to all tasks of a same script language

* *task*: creates a task

* *pre_script*: sets the pre-script of a task

* *post_script*: sets the post-script of a task

* *selection_script*: sets the selection script of a task

* *job_selection_script*: sets the default selection script of a job

* *fork_env*: sets the fork environment script

* *job_fork_env*: sets the default fork environment of a job

* *split*: creates/modifies a splitting task of a replicate control

* *runs*: creates/modifies the configuration script of a replicate control

* *process*: creates/modifies the script of a replicated processing task

* *merge*: creates/modifies a merging task of a replicate control

* *start*: creates/modifies a start task of a loop control

* *loop*: creates/modifies a loop task of a loop control

* *condition*: creates/modifies the condition script of a branch/loop control

* *branch*: creates/modifies a branch task of a branching control

* *if*: creates/modifies an if task of a branching control

* *else*: creates/modifies an else task of a branching control

* *continuation*: creates/modifies a continuation task of a branching control

* *delete_task*: deletes a task from the workflow

* *job*: creates/renames the job

* *draw_job*: plot the workflow

* *write_dot*: writes the workflow in .dot format

* *import_dot*: imports the workflow from a .dot file

* *submit_job*: submits the job to the scheduler

* *get_result*: gets and prints the job results

* *get_job_result*: gets and prints the job results

* *get_task_result*: gets and prints the results of a given task

* *print_job_output*: gets and prints the job outputs

* *print_task_output*: gets and prints the outputs of a given task

* *list_submitted_jobs*: gets and prints the ids and names of the submitted jobs

* *export_xml*: exports the workflow in .xml format

* *show_resource_manager*: opens the ActiveEon resource manager portal

* *show_scheduling_portal*: opens the ActiveEon scheduling portal

* *show_workflow_automation*: opens the ActiveEon workflow automation portal


#### TODO

###### Features improvements
* execute in local a pragma free block
* add options import_as_json/export_as_json
* add draw(on/off), print_result(on/off) options in submit job pragma
* multiple pragmas in a block handling
* apply selection_script and fork_env to a list of names (tasks)
* add auto-complete

###### Documentation
* add some examples pictures
* add configure pragma section (block, multiblock)

