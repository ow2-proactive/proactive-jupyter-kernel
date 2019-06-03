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

To create a task, write your python implementation into a notebook block code (a default name 
will be given to the created task):

```python
print('Hello world')
```

Or you can provide more information about the task by using the `#%task()` pragma:

```python
#%task(name=TASK_NAME)
print('Hello world')
```

#### 5.2 Adding a fork environment

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
#%fork_env(name=TASK_NAME, path=./FORK_ENV_FILE.py)
```

#### 5.3 Adding a selection script

To add a selection script to a task, use the `#%selection_script()` pragma. A first way to do it,
provide the name of the corresponding task, and the selection code implementation after that:

```python
#%selection_script(name=TASK_NAME)
selected = True
```

A second way is by providing the name of the task, and the path of a .py file containing the selection code:

```python
#%selection_script(name=TASK_NAME, path=./SELECTION_CODE_FILE.py)
```

#### 5.4 Create a job

To create a job, use the `#%job()` pragma:

```python
#%job(name=JOB_NAME)
```

If the job was already been created, the call of this pragma would just rename the job already created by the new provided name.

**Notice that it is not necessary to create and name explicitly the job. If not done by the user, this step is implicitly 
performed when the job is submitted (check section 5.7 for more information).**

#### 5.5 Plot job

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

#### 5.6 Save workflow in dot format

To save the created workflow into a [GraphViz](https://www.graphviz.org/) \_.dot\_ format, use the `#%write_dot()` pragma:

```python
#%write_dot(name=FILE_NAME)
```


#### 5.7 Submit your job to the scheduler

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


#### 5.8 Printing results

To finally get the job result(s), the user has to use the `#%get_result()` pragma by providing the job name:

```python
#%get_result(name=JOB_NAME)
```

or by the job id:

```python
#%get_result(id=JOB_ID)
```

The returned values of your final tasks will be automatically printed in the notebook results.

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

* *submitted_jobs*: gets and prints the ids and names of the submitted jobs

* *plot_resource_manager*: opens the ActiveEon resource manager portal

* *plot_scheduling_portal*: opens the ActiveEon scheduling portal


#### TODO

###### Features improvements
* execute in local a pragma free block
* add options import_as_json/export_as_json
* add draw(on/off), print_result(on/off) options in submit job pragma
* multiple pragmas in a block handling
* apply selection_script and fork_env to a list of names (tasks)
* add auto-complete

###### Documentation
* explain dependencies handling
* add import pragma description
* add import/export description
* add generic_info description
* add pre/post scripts description
* add job_selection_script description
* add job_fork_env description
* add submitted_jobs description
* add some examples pictures
* add plot_resource_manager description
* add plot_scheduling_portal description

