"""
Contains general purpose classes and functions for defining and running tasks.

In addition there are functions for storing and retrieving both tasks and run
settings.
"""

import os
import time
import subprocess
import yaml
import fnmatch
import glob
import getpass
import warnings
import inspect
import multiprocessing
import sys

from subprocess import Popen, PIPE
from threading  import Thread

import __builtin__

import lsc_tasker
import lsc_tasker.utils

HAS_PYNOTIFY = False
try:
    HAS_PYNOTIFY = True
except ImportError:
    pass

def getFreeOutputDirectory(output_directory_base):
    # find free output directory
    n = 0
    output_dir = os.path.join(output_directory_base, "task_%s/" % (time.strftime("%Y%m%d_%H%M%S")))
    while True:
        if os.path.exists(output_dir):
            output_dir = os.path.join(output_directory_base, "task_%s_%i/" % (time.strftime("%Y%m%d_%H%M%S"), n))
            n += 1
        else:
            break
    return output_dir

class TaskRunfile():
    def __init__(self, name, content, settings_param, description):
        (self.name, self.content, self.settings_param, self.description) = (name, content, settings_param, description)

    def __str__(self):
        return "%s: %s" % (self.name, self.description)

class LogEmitter(object):
    def __init__(self, logfile):
        self.logfile = logfile
    def write(self, text):
        print text
        #self.logfile.write(text)
        #self.logfile.flush()
    def fileno(self):
        return self.logfile.fileno()

# http://stackoverflow.com/questions/4984428/python-subprocess-get-childrens-output-to-file-and-terminal/4985080#4985080
def tee(infile, *files):
    """Print `infile` to `files` in a separate thread."""
    def fanout(infile, *files):
        for line in iter(infile.readline, ''):
            for f in files:
                f.write(line)
        infile.close()
    t = Thread(target=fanout, args=(infile,)+files)
    t.daemon = True
    t.start()
    return t


class TeedCall:
    def __init__(self, cmd_args, **kwargs):
        stdout, stderr = [kwargs.pop(s, None) for s in 'stdout', 'stderr']
        p = Popen(cmd_args,
                  stdout=PIPE if stdout is not None else None,
                  stderr=PIPE if stderr is not None else None,
                  **kwargs)
        threads = []
        self.pid = p.pid
        if stdout is not None:
            threads.append(tee(p.stdout, stdout, sys.stdout))
        if stderr is not None:
            threads.append(tee(p.stderr, stderr, sys.stderr))
        for t in threads:
            t.join()  # wait for IO completion
        p.wait()

    def communicate(self):
        return (None, None)


class TaskRun(object):
    """
    This class contains all the logic required for keeping track of running
    a single task.
    """
    def __init__(self, task, output_directory_base, fork_process=False, override_output_directory=None, num_repeats=0):
        self.task = task

        if override_output_directory is not None:
            self.output_directory = override_output_directory
        else:
            self.output_directory = BaseTask.getFreeOutputDirectory(output_directory_base=output_directory_base)
            os.makedirs(self.output_directory)
            task.save(self.output_directory)

        self.print_log = not fork_process

        self.fork_process = fork_process
        self.num_repeats = num_repeats
        self.current_run = -1

    def __enter__(self):
        child_pid = None
        if self.fork_process:
            forked_pid = os.fork()
            if forked_pid == 0:
                child_pid = os.getpid()

        self._setupLogfile()

        if not self.fork_process or child_pid is not None:
            self.task_process = self.spawnProcess(logging_target=self.logging_target)

        try:
            self.pid = self.task_process.pid
        except AttributeError:
            self.pid = None

        if self.fork_process:
            if self.pid is not None:
                print "Forked process and running in pid %d" % self.pid
                print "Output in %s" % self.output_directory
            else:
                class FakeProcess:
                    def communicate(self):
                        return (None, None)
                self.task_process = FakeProcess()

        return self

    def spawnProcess(self, logging_target):
        self.current_run += 1

        executable = self.task.get_executable(outputdir=self.output_directory)

        os.chdir(self.output_directory)
        args = executable
        if self.print_log:
            return TeedCall(args, stdout=self.logfile, stderr=self.logfile)
        else:
            return subprocess.Popen(args,bufsize=-1, stdout=logging_target,stderr=logging_target,stdin=subprocess.PIPE)

    def kill(self):
        self.__exit__(None, None, None)

    def __exit__(self, typ, val, traceback):
        if self.task_process is not None:
            try:
                self.task_process.kill()
            except (OSError, AttributeError):
                pass

        if self.pid is not None:
            if self.current_run < self.num_repeats:
                self.task_process = self.spawnProcess(logging_target=self.logging_target)
                self.task_process.communicate()

                return self.__exit__(typ, val, traceback)

            self.logfile.close()
            # clean up the log file (remove backspace characters)
            logfile = open(self.log_filename)
            logfile_content_old = logfile.readlines()
            logfile.close()

            logfile = open(self.log_filename,"w+")
            for line in logfile_content_old:
                line = line.replace("\010","")
                logfile.write(line)
            logfile.close()

            try:
                import pynotify
                pynotify.init("Basic")
                n = pynotify.Notification("%s has finished running" % str(self.task), self.output_directory)
                n.show()
            except ImportError:
                pass


    def _setupLogfile(self):
        # setup task logfile
        log_filename = os.path.join(self.output_directory, "run.log")
        self.log_filename = log_filename
        self.logfile = open(log_filename, "w")
        self.logging_target = LogEmitter(self.logfile)

    def communicate(self):
        return self.task_process.communicate()[1]


class ForkedTaskRun(TaskRun):
    pass

class RunfileBasedTaskRun(TaskRun):

    def spawnProcess(self, logging_target):
        saved_generator_filename = self.task.getGeneratorSaveFilename(self.output_directory)

        args = ['/usr/bin/python', saved_generator_filename]
        print " ".join(args)
        return subprocess.Popen(args,stdout=logging_target,stderr=logging_target,stdin=subprocess.PIPE)

    def _writeRunfiles(self):
        # write the run files (these get written to the "runfiles" folder), and set the correct filename in the settings
        if len(self.task.runfiles) > 0:
            runfiles_dir = os.path.join(self.output_directory,"runfiles")
            try:
                os.makedirs(runfiles_dir)
            except os.error:
                pass

            for runfile in self.task.runfiles:
                full_filename = os.path.join(runfiles_dir,"%s.dat" % runfile.name)
                fh = open(full_filename, "w")
                fh.write(runfile.content)
                fh.close()
                #utils.set_task_parm_from_string(self.settings, "%s" % runfile.settings_param, full_filename)
                import warnings
                # TODO: If I start using runfiles again I should try and find out why the line below was needed
                warnings.warn("Storing of runfiles in settings is currently not working correctly")

class BaseTask(object):
    def __init__(self, generator, description, output_directory = None, output_directory_base = None, task_name = None, runfiles = [], owner = None, auto_run = False, exit_on_complete = False):
        if owner is None:
            owner = getpass.getuser()

        (self.owner, self.description, self.runfiles) = (owner, description, runfiles)
        self.alreadyRun = False
        self.generator = generator
        self.taskfile = None
        self.initDone = False
        self.task_name = task_name
        self.allow_output_overwrite = False
        self.output_directory = output_directory
        self.output_directory_base = output_directory_base
        self.exit_on_complete = exit_on_complete

        if auto_run:
            if self._hasTargetHostDefined():
                self.generator += "interactive_settings = None"
                self.enqueue(self._targetHost())
            else:
                self.run(self.output_directory)

    def _hasTargetHostDefined(self):
        if hasattr(self, 'runTargetHost') or hasattr(__builtin__, 'runTargetHost'):
            return True
        else:
            return False

    def _targetHost(self):
        if hasattr(self, 'runTargetHost'):
            return self.runTargetHost
        else:
            return __builtin__.runTargetHost

    @staticmethod
    def getFreeOutputDirectory(output_directory_base):
        # find free output directory
        n = 0
        output_dir = os.path.join(output_directory_base, "task_%s/" % (time.strftime("%Y%m%d_%H%M%S")))
        while True:
            if os.path.exists(output_dir):
                output_dir = os.path.join(output_directory_base, "task_%s_%i/" % (time.strftime("%Y%m%d_%H%M%S"), n))
                n += 1
            else:
                break
        return output_dir

    def getGeneratorSaveFilename(self, output_directory):
        return os.path.join(output_directory, 'runscript.py')

    def save(self, output_directory):
        """
        Create a python script that will let me rerun this task without any
        need for additional setup. This also serves as the main task
        executable.
        """
        f = open(self.getGeneratorSaveFilename(output_directory), 'w')
        f.write(self.generator)
        f.close()

    def enqueue(self, host = None):
        """
        try and enqueue this task on the taskerServer requested.
        """
        lsc_tasker.utils.sendTask(self, host)

    def run(self, output_directory = None):
        if output_directory is None:
            if self.output_directory_base is not None:
                output_directory_base = self.output_directory_base
                if self.task_name is not None:
                    output_directory = os.path.join(output_directory_base, self.task_name)
                else:
                    output_directory = self.getFreeOutputDirectory(output_directory_base=output_directory_base)
                os.makedirs(output_directory)
            else:
                output_directory = None

        self.output_directory = output_directory
        if output_directory is not None:
            self.save(output_directory)
            print "Output being written to %s" % str(output_directory)

        self._run(self.output_directory)
        if self.exit_on_complete:
            sys.exit(0)

    def __str__(self):
        string = ""
        string += str(self.settings)
        string += "runfiles:\n" + "".join(["\t%s.dat: %s\n" % (runfile.name, runfile.description) for runfile in self.runfiles])
        string += "\nOwner: %s\nNum processes: %s\nexecutable: %s\ndescription: %s\n" % (self.owner, self.num_processes, self.executable, self.description)
        return string

    def taskIsComplete(self):
        return self.getRunDuration() is not None

    def getRunDuration(self):
        try:
            logfile = open(os.path.join(self.settings.Output.directory,"run.log"),"r")
            runDuration = None
            for line in logfile.readlines():
                if "Total time" in line:
                    runDuration = float(line.split()[3][:-1])
                    break
            if not runDuration:
                print "Task is still running (or was killed before completion)"
            return runDuration
        except IOError:
            print "Task hasn't been started yet"
            return None

    def getLog(self):
        try:
            logfile = open(os.path.join(self.settings.Output.directory,"run.log"),"r")
            log_content = logfile.readlines()
            logfile.close()
            return log_content
        except IOError:
            print "Task hasn't been started yet"
            return None

    #def initTaskRun(self, output_directory_base):
        #pass

class CompoundTask(BaseTask):
    def __init__(self, sub_tasks, generator, description, output_directory_base,
                 task_name = None, runfiles = [], owner = None, auto_run = False,
                 exit_on_complete = False):

        self.sub_tasks = sub_tasks

    def _run(self, output_directory):
        for t in self.sub_tasks:
            t.run()

class ParameterStudyHelper:
    """
    This class is intended for use when a parameter study is to be run. A full copy
    of the generator script (the script in which an instance of this class is created)
    will be included within the task definition, so that the task can be easily rerun.
    """

    def __init__(self, generator_filename, base_settings, executable, num_processes, description, task_type):
        self.generator_filename = generator_filename
        self.base_settings = base_settings
        self.executable = executable
        self.num_processes = num_processes
        self.description = description

    def sendTask(self, settings, runfiles = []):
        pass

class SettingsGenerationHelper(object):
    def __init__(self, generator, task_description, settings, output_dir):
        self.settings = settings
        self.task_description = task_description
        self.generator = generator
        self.output_dir = output_dir

    def run(self):
        """
        generate task and set output directory relative to the path of the generator
        """
        pycfd_basedir = self._getBasedir()
        basedir_output = self.output_dir
        task = self._makeTask()
        return task.run(output_directory_base=basedir_output)

    def _makeTask(self):
        owner = getpass.getuser()
        description = self.task_description

        import sys
        solver_module = sys.modules[self.settings.__module__]
        task_class = getattr(solver_module,'Task')
        task = task_class(owner=owner, num_processes=self.num_processes, executable=self.executable,
                          settings=self.settings, description=description, generator=self.generator)
        return task

    def _getExecutable(self):
        raise Exception("This method should be overriden.")

    def _getBasedir(self):
        import common
        pycfd_basedir = common.basedir
        return pycfd_basedir

    def enqueue(self, host = None):
        """
        try and enqueue this task on the taskerServer requested.
        """
        task = self._makeTask()
        lsc_tasker.utils.sendTask(task, host)

class UnknownSettingsTypeError(Exception):
    pass

#def loadSettingsFromFile(filename):
    #"""
    #This function tries to load the contents of the given filename and interprete
    #the contents as settings object.

    #Since I now need to support both the format used by LSC-AMR and the YAML format
    #of the soundproof solvers I need to determine which I'm dealing with first. With
    #respect to the YAML format this is easy because the object type is saved with the
    #object content when I used YAML to serialise it. So I try with YAML first, and if
    #that fails we assume we're dealing with the LSC-AMR format. If all that fails,
    #bail.
    #"""

    #filehandle = open(filename,"r")
    #raw_settings = filehandle.read()
    #filehandle.close()

    #try:
        #settings_object = yaml.load(raw_settings)
        #return settings_object
    #except yaml.scanner.ScannerError:
        #import py_lsc_amr
        #return py_lsc_amr.Settings.load(filename)

def writeTask(task, filename):
    taskfile = open(filename, "wb")
    yaml.dump(task, taskfile)
    taskfile.close()


def loadTask(task_filename):
    taskfile = None
    if '*' in task_filename:
        return findTaskFilesAndLoad(task_filename)
    else:
        try:
            taskfile = open(task_filename,"r")
        except IOError:
            print "Error: Couldn't find the task specified, either pass in the full filename with path or write the task date and time.\ne.g. loadTask('20110516_091754')"

        if taskfile:
            try:
                task = yaml.load(taskfile.read())
                # Override the output-dir so that files associated with tasks may be accessed properly if the task has been moved
                task.taskfile = taskfile.name
                task.parent_directory = os.path.dirname(os.path.abspath(task_filename))
                return task
            except EOFError:
                print "There was a problem with loading %s, unexpected end of file." % task_filename
                return None
            #except yaml.constructor.ConstructorError:
                #print "The stored task object could not be recreated (%s)" % task_filename
        else:
            return None


def get_workpool():
    return multiprocessing.Pool(processes=multiprocessing.cpu_count())

def findTaskFilesAndLoad(path, recursive=False):
    matches = []
    if recursive:
        for root, dirnames, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, 'taskfile.tsk'):
                matches.append(os.path.join(root, filename))
    else:
        matches = glob.glob(os.path.join(path,"taskfile.tsk"))

    taskfiles_list = [(os.stat(i).st_mtime, i) for i in matches]
    taskfiles_list.sort()
    taskfiles_list = [taskfile[1] for taskfile in taskfiles_list]
    print "Loading %d tasks..." % len(taskfiles_list)
    workpool = get_workpool()
    tasks = workpool.map(loadTask, taskfiles_list)
    tasks = [task for task in tasks if task is not None]
    print "%d tasks loaded." % len(tasks)
    return tasks
