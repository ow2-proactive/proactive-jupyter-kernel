# proactive-jupyter-kernel
ProActiveKernel for Jupyter

## 1. Requirements:

* Python 2 or 3

## 2. Installation:

### 2.1 Using Pypi

1) open a terminal

2) install the proactive jupyter kernel

    ```Bash
    $ pip install proactive-kernel --upgrade
    ```

### 2.2 Using source code

1) open a terminal

2) clone the repository on your local machine:

    ```bash
    $ git clone git@github.com:ow2-proactive/proactive-jupyter-kernel.git
    ```
3) install the proactive jupyter kernel:

    ```Bash
    $ pip install proactive-jupyter-kernel/
    $ python -m proactive-jupyter-kernel.install
    ```
    
## 3. Platform

You can use any jupyter platform.
We recommend the use of jupyter lab. To launch it from your terminal after having installed it:

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

If you want to connect to another host, use the later pragma this way:

```python
#%connect(host=YOUR_HOST, port=YOUR_PORT, login=YOUR_LOGIN, password=YOUR_PASSWORD)
```

### 4.2 Using config file:

For automatic sign in, create a file named 'proactive_config.ini' in your notebook's location.

Fill your configuration file according to the format:

```Bash
[proactive_server]
host = YOUR_HOST
port = YOUR_PORT

[user]
login = YOUR_LOGIN
password = YOUR_PASSWORD
```

Save your file changes and restart the proactive kernel.

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

A second way is by providing the name of the task, and the path of a .py file containing the fork environment code:

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

Notice that it is not necessary to create and name explicitly the job. If not done by the user, this step is implicitly 
performed when the job is submitted (check next section). In the later case, the job will be named same as your notebook.

#### 5.5 Submit your job to the scheduler

To finally submit your job to the proactive scheduler, use the `#%submit_job()` pragma:

```python
#%submitJob()
```

The returned values of your final tasks will be automatically printed in the notebook results.

Current status
----------

Features:

* connect, task, selection_script, fork_env, job, submit_job
* connection using a configuration file
* get and print results implicitly in submit_job

TODO:

1. add task dependency
2. less spaces sensitivity in pragma's parsing
3. get_results pragma
4. check how to use NetworkX for plotting graphs
5. check how to highlight Python syntax