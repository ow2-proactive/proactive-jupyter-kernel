# proactive-jupyter-kernel
The ActiveEon Jupyter Kernel adds a kernel backend for Jupyter to interface directly with the ProActive scheduler and 
construct tasks and workflows and execute them on the fly.

## 1. Requirements:

Python 2 or 3

## 2. Installation:

### 2.1 Using PyPi

* open a terminal

* install the proactive jupyter kernel

```bash
$ pip install proactive proactive-jupyter-kernel --upgrade
$ python -m proactive-jupyter-kernel.install
```

### 2.2 Using source code

* open a terminal

* clone the repository on your local machine:

```bash
$ git clone git@github.com:ow2-proactive/proactive-jupyter-kernel.git
```

* install the proactive jupyter kernel:

```bash
$ pip install proactive-jupyter-kernel/
$ python -m proactive-jupyter-kernel.install
```

## 3. Platform

You can use any jupyter platform.
We recommend the use of jupyter lab. To launch it from your terminal after having installed it:

```bash
$ jupyter lab
```
or in daemon mode:
```bash
$ nohup jupyter lab &>/dev/null &
```

When opened, click on the Proactive icon to open a notebook based on the proactive kernel.

## 4. Connect:

### 4.1 Using connect()

If you are trying proactive for the first time, please sign up on [try platform](https://try.activeeon.com/signup.html).
Once you receive your login and password, connect using the `#%connect()` pragma:

```python
#%connect(login=YOUR_LOGIN, password=YOUR_PASSWORD)
```

To connect to another host, use the later pragma this way:

```python
#%connect(host=YOUR_HOST, port=YOUR_PORT, login=YOUR_LOGIN, password=YOUR_PASSWORD)
```

### 4.2 Using config file:

For automatic sign in, create a file named *proactive_config.ini* in your notebook location. 

Fill your configuration file according to the format:

```ini
[proactive_server]
host=YOUR_HOST
port=YOUR_PORT
[user]
login=YOUR_LOGIN
password=YOUR_PASSWORD
```

Save your file changes and restart the proactive kernel.

You can also force the current Kernel to connect using any .ini config file through the `#%connect()` pragma:

```python
#%connect(path=PATH_TO/YOUR_CONFIG_FILE.ini)
```

(for more information about this format please check 
[configParser](https://docs.python.org/3/library/configparser.html))

## 5. Usage

#### 5.1 Creating a Python task

To create a task, use the pragma `#%task()` followed by the task implementation script wrote into a notebook block code.
To use this pragma, at least, a task name has to be provided. Example:

```python
#%task(name=myTask)
print('Hello world')
```

General usage:

```python
#%task(name=TASK_NAME, [language=SCRIPT_LANGUAGE], [dep=[TASK_NAME1,TASK_NAME2,...]], [generic_info=[(KEY1,VAL1), (KEY2,VALUE2),...]], [export=[VAR_NAME1,VAR_NAME2,...]], [import=[VAR_NAME1,VAR_NAME2,...]], [path=IMPLEMENTATION_FILE_PATH])\n'
```

As seen in the general usage, users can also provide more information about the task by using the `#%task()` pragma's 
options:

##### 5.1.1 Language

`language` parameter is needed when the task script is not written in native Python, the default language.
The handled programming languages are:

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

Example of usage for a task written in `Linux_Bash`:

```bash
#%task(name=myTask, language=Linux_Bash)
echo 'Hello, World!'
```

##### 5.1.2 Dependencies

One of the most important notions in workflows is the dependencies between tasks. To specify this information, use the 
`dep` parameter. The value should be a list of all the tasks on which the new task depends. Example:

```python
#%task(name=myTask,dep=[parentTask1,parentTask2])
print('Hello world')
```

##### 5.1.3 Generic information

To specify the advanced ProActive scheduler variables values (check XXX for more details), the parameter 
`generic_info` is provided. The value should be a tuples `(key,value)` list of all the names and values of the 
ProActive parameters. Example:

```python
#%task(name=myTask, generic_info=[(var1,value1),(var2,value2)])
print('Hello world')
```

##### 5.1.4 Export/import variables

The `export` and `import` parameters make possible variables propagation between the different tasks of a workflow. 
If `myTask1` variables `var1` and `var2` are needed in `myTask2`, the `myTask1` pragma should include and `export` with 
a list of these variable names and `myTask2` pragma an `import` with a list including these names too. Example:

`myTask1` implementation bloc would be:
```python
#%task(name=myTask1, export=[var1,var2])
var1 = "Hello"
var2 = "ActiveEon!"
```

and `myTask2` implementation bloc would be:
```python
#%task(name=myTask2, dep=[myTask1], import[var1,var2])
print(var1 + " from " + var2)
```

##### 5.1.5 Implementation file

It is possible to use an external implementation file as task implementation. To do so, the option `path` should be used.
Example:

```python
#%task(name=myTask,path=PATH_TO/IMPLEMENTATION_FILE.py)
```

#### 5.2 Imports libraries

Since each created ProActive task will be executed as an independent process, to facilitate the transition from native 
language kernels to the ProActive one, a pragma that allows the user to add just once the libraries that are common to 
all created tasks that are implemented in a same script language. This pragma is used in this manner 
`#%import([language=SCRIPT_LANGUAGE])`. If the language is not specified, Python is considered by default. Example:

```python
#%import(language=Python)
import os
import pandas
```

#### 5.3 Adding a fork environment

To configure a fork environment for a task, use the `#%fork_env()` pragma. A first way to do this
is by providing the name of the corresponding task, and the fork environment implementation after that:

```text
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

A second way is by providing the name of the task, and the path of a \_.py\_ file containing the fork environment code:

```python
#%fork_env(name=TASK_NAME, path=PATH_TO/FORK_ENV_FILE.py)
```

#### 5.4 Adding a selection script

To add a selection script to a task, use the `#%selection_script()` pragma. A first way to do it,
provide the name of the corresponding task, and the selection code implementation after that:

```python
#%selection_script(name=TASK_NAME)
selected = True
```

A second way is by providing the name of the task, and the path of a .py file containing the selection code:

```python
#%selection_script(name=TASK_NAME, path=PATH_TO/SELECTION_CODE_FILE.py)
```

#### 5.5 Adding job fork environment and/or selection script

If the selection scripts and/or the fork environments are the same for all job tasks, we can add them just once using 
the `job_selection_script` and/or the `job_fork_env` pragmas. Usage:

For a job selection script use:

```python
#%job_selection_script([language=SCRIPT_LANGUAGE], [path=./SELECTION_CODE_FILE.py], [force=on/off])
```

For a job fork environment use:

```python
#%job_fork_env([language=SCRIPT_LANGUAGE], [path=./FORK_ENV_FILE.py], [force=on/off])
```

The `force` parameter says if the pragma has to overwrite the task selection scripts or fork environment already set or not.

#### 5.6 Adding pre and/or post scripts

Sometimes, specified scripts has to be executed before and/or after a particular task. To add those scripts both 
`pre_script` and `post_script` exist.

To add a pre-script to a task, use:

```python
#%pre_script(name=TASK_NAME, language=SCRIPT_LANGUAGE, [path=./PRE_SCRIPT_FILE.py])
```

To add a post-script to a task, use:

```python
#%post_script(name=TASK_NAME, language=SCRIPT_LANGUAGE, [path=./POST_SCRIPT_FILE.py])
```

#### 5.7 Create a job

To create a job, use the `#%job()` pragma:

```python
#%job(name=JOB_NAME)
```

If the job was already been created, the call of this pragma would just rename the job already created by the new provided name.

**Notice that it is not necessary to create and name explicitly the job. If not done by the user, this step is implicitly 
performed when the job is submitted (check section 5.7 for more information).**

#### 5.8 Plot job

To verify the created workflow, use the `#%draw_job()` pragma to plot it into a separate window:

```python
#%draw_job()
```

Two optional parameters can be used to configure the way the kernel plot the workflow.

**inline plotting:**

If this parameter is set to 'off', the workflow plotting is made through the [Matplotlib](https://matplotlib.org/) 
external window. The default value is 'on'.

```python
#%draw_job(inline=off)
```

**saving into hard disk:**

To be sure the workflow is saved into a \_.png\_ file, this option needs to be set to *on*. The default value is *off*.

```python
#%draw_job(save=on)
```

Note that the job will be named (in the order of existence) by the name provided using the 'name' parameter, by the name of the job 
if it is created, by the name of the notebook if reachable or at worst by "Unnamed_job".

```python
#%draw_job([name=JOB_NAME], [inline=off], [save=on])
```

#### 5.9 Save workflow in dot format

To save the created workflow into a [GraphViz](https://www.graphviz.org/) \_.dot\_ format, use the `#%write_dot()` pragma:

```python
#%write_dot(name=FILE_NAME)
```


#### 5.10 Submit your job to the scheduler

To submit the job to the proactive scheduler, the user has to use the `#%submit_job()` pragma:

```python
#%submit_job()
```

If the job is not created, or is not up-to-date, the `#%submit_job()` starts by creating a new job named as the old one.
To provide a new name, use the same pragma and provide a name as parameter:

```python
#%submit_job(name=JOB_NAME)
```

If the kernel, during its execution, never received a job name, he uses the current notebook name, if possible, or gives a random one.

#### 5.11 List all submitted jobs

To get all the submitted job ids and names, please use `list_submitted_jobs` pragma this way:

```python
#%list_submitted_jobs()
```

#### 5.12 Printing results

To get the job result(s), the user has to use the `#%get_result()` pragma by providing the job name:

```python
#%get_result(name=JOB_NAME)
```

or by the job id:

```python
#%get_result(id=JOB_ID)
```

The returned values of your final tasks will be automatically printed.

#### 5.13 Showing ActiveEon portals

Finally, to have the hand on more parameters and features, the user should use ActiveEon portals. 
The two main ones are the _Resource Manager_ and the _Scheduling Portal_.

To show the resource manager portal related to the host you are connected to, just tape:

```python
#%show_resource_manager([height=HEIGHT_VALUE, width=WIDTH_VALUE])
```

And for the related scheduling portal:

```python
#%show_scheduling_portal([height=HEIGHT_VALUE, width=WIDTH_VALUE])
```

Notice that the parameters `height` and `width` allow the user to adjust the size of the window inside the notebook.

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

* *job*: creates/renames the job

* *draw_job*: plot the workflow

* *write_dot*: writes the workflow in .dot format

* *submit_job*: submits the job to the scheduler

* *get_result*: gets and prints the job results

* *list_submitted_jobs*: gets and prints the ids and names of the submitted jobs

* *show_resource_manager*: opens the ActiveEon resource manager portal

* *show_scheduling_portal*: opens the ActiveEon scheduling portal


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

