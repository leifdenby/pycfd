import threading
import os
import re
import time
import subprocess
import yaml
import fnmatch
import glob
from operator import attrgetter


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
        self.logfile.write(text)
    def fileno(self):
        return self.logfile.fileno()

class TaskRun(object):
    """
    This class contains all the logic required for keeping track of running
    a single task.
    """
    def __init__(self, task, output_directory_base, print_log = False):
        self.task = task
        self.output_directory = self._getFreeOutputDirectory(output_directory_base)
        
        import warnings
        warnings.warn("Need to rethink the way the output_directory is saved in the settings")
        #self.settings.Output.directory = output_directory
        
        self.print_log = print_log

        self._writeRunfiles()
        self._writeSettingsfile()
        self._writeTaskfile()
        self._setupLogfile()

    def __enter__(self):
        self.task_process = self.spawnProcess(logging_target=self.logging_target)
        return self.task_process

    def spawnProcess(self, logging_target):
        args = self.task.getRunArgs()
        return subprocess.Popen(args,stdout=logging_target,stderr=logging_target,stdin=subprocess.PIPE)

    def __exit__(self, typ, val, traceback):
        self.logfile.close()
        # clean up the log file (remove backspace characters) 
        logfile = open(self.log_filename)
        logfile_content_old = logfile.readlines()
        logfile.close()

        logfile = open(self.log_filename,"w")
        for line in logfile_content_old:
            line = line.replace("\010","")
            logfile.write(line)
        logfile.close()
        
    def _setupLogfile(self):
        # setup task logfile
        log_filename = os.path.join(self.output_directory, "run.log")
        self.log_filename = log_filename
        print "b", self.print_log
        self.logfile = open(log_filename, "w")
        if self.print_log:
            self.logging_target = LogEmitter(self.logfile)
        else:
            self.logging_target = self.logfile
        
    def _writeTaskfile(self):
        # write the task definition to a file so that we may run it again if needed
        taskfile_filename = os.path.join(self.output_directory, "taskfile.tsk")
        writeTask(self, taskfile_filename)

    def _writeSettingsfile(self):
        settingsfile_filename = os.path.join(self.output_directory, "settings")
        self.task.settingsfile_filename = settingsfile_filename
        writeSettingsToFile(self.task.settings, settingsfile_filename)

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
    
    def _getFreeOutputDirectory(self, output_directory_base):
        # create output directory
        n = 0
        output_dir = os.path.join(output_directory_base, "task_%s/" % (time.strftime("%Y%m%d_%H%M%S")))
        while True:
            try:
                os.makedirs(output_dir)
                break
            except os.error:
                output_dir = os.path.join(output_directory_base, "task_%s_%i/" % (time.strftime("%Y%m%d_%H%M%S"), n))
                n += 1
        return output_dir

class BaseTask(object):
    def __init__(self,owner,num_processes,executable,settings,description,runfiles = [], generator = None):
        (self.owner, self.num_processes, self.executable, self.settings, self.description, self.runfiles) = (owner, num_processes, executable, settings, description, runfiles)
        self.alreadyRun = False
        self.generator = generator
        self.taskfile = None
        self.initDone = False

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



    def initTaskRun(self, output_directory_base):
        pass

    def getRunArgs(self):
        raise Exception("Any TaskClass should override this method")

    def run(self, output_directory_base):
        with TaskRun(task=self, output_directory_base=output_directory_base, print_log=True) as task_process:
            print task_process.communicate()[1]
        
    #def runAndReturnProcess(self, output_directory_base, logging_target = subprocess.PIPE):
        #"""
        #Call this method without defining the logging_target to run the task
        #interactively.
        #"""
        #if not self.initDone:
            #self.initTaskRun(output_directory_base)

        #args = self._getRunArgs()
        #print " ".join(args)
        #return subprocess.Popen(args,stdout=logging_target,stderr=logging_target,stdin=subprocess.PIPE)
    
    #def run(self, output_directory_base, logging_target = None):
        #"""
        #Call this method without defining the logging_target to run the task
        #interactively.
        #"""
        #if not self.initDone:
            #self.initTaskRun(output_directory_base)

        #args = self._getRunArgs()

        #proc = subprocess.Popen(args,stdout=logging_target,stderr=logging_target,stdin=subprocess.PIPE)
        #print proc.communicate()[1]

        ## TODO: Better interaction with the spawned subprocesses is needed here, but I'll do that
        ##       another day. What I need ideally is to be able to emit certain things to the 
        ##       process and to asynchronously pool the process for output.
        ##       http://stefaanlippens.net/python-asynchronous-subprocess-pipe-reading looks like a good
        ##       starting point, basically the idea is place communication in queues.
        ##       I want to be able to both place output in a log and to write it to screen
        
        ##try:
            ##print " ".join(args)
            ##print self.settings
        ##except KeyboardInterrupt:
            ### clean-up log and exit gracefully
            ##print 'does this catch it?'

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


class UnknownSettingsTypeError(Exception):
    pass

import py_lsc_amr.run_settings
import pysolver.run_settings

def writeSettingsToFile(settings, filename):
    if isinstance(settings, py_lsc_amr.run_settings.LSC_AMR_Settings):
        py_lsc_amr.run_settings.dump(settings, filename)
    elif isinstance(settings, pysolver.run_settings.PySolverSettings):
        filehandle = open(filename,"w")
        yaml.dump(settings, filehandle)
        filehandle.close()
    else:
        raise UnknownSettingsTypeError()

def loadSettingsFromFile(filename):
    """
    This function tries to load the contents of the given filename and interprete
    the contents as settings object.

    Since I now need to support both the format used by LSC-AMR and the YAML format
    of the soundproof solvers I need to determine which I'm dealing with first. With
    respect to the YAML format this is easy because the object type is saved with the
    object content when I used YAML to serialise it. So I try with YAML first, and if
    that fails we assume we're dealing with the LSC-AMR format. If all that fails,
    bail.
    """

    filehandle = open(filename,"r")
    raw_settings = filehandle.read()
    filehandle.close()

    try:
        settings_object = yaml.load(raw_settings)
    except yaml.scanner.ScannerError:
        settings_object = py_lsc_amr.run_settings.load(raw_settings)
    return settings_object

def writeTask(task, filename):
    taskfile = open(filename, "wb")
    yaml.dump(task, taskfile)
    taskfile.close()

def loadTask(task_filename):
    def findTaskFilesAndLoad(path, recursive=False):
        matches = []
        if recursive:
            for root, dirnames, filenames in os.walk(path):
                for filename in fnmatch.filter(filenames, 'taskfile.tsk'):
                    matches.append(os.path.join(root, filename))
        else:
            matches = glob.glob(os.path.join(path,"*/taskfile.tsk"))
        
        taskfiles_list = [(os.stat(i).st_mtime, i) for i in matches]
        taskfiles_list.sort()
        tasks = [loadTask(taskfile[1]) for taskfile in taskfiles_list]
        tasks = [task for task in tasks if task is not None]
        print "%d tasks loaded." % len(tasks)
        return tasks

    taskfile = None
    if task_filename == '*':
        return findTaskFilesAndLoad(os.getcwd(), recursive=True)
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
                return task
            except EOFError:
                print "There was a problem with loading %s, unexpected end of file." % task_filename
                return None
        else:
            return None
