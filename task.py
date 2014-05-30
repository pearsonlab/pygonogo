"""
Class definition for task object.

TO DO:
* make task metaclass?
* task handles event loop, with list of functions to call each iteration?
"""

import initializers
import controller, display
from psychopy.core import monotonicClock

class Task:
    def __init__(self, taskname, subject):
        self.taskname = taskname
        self.subject = subject
        self.start_time = monotonicClock.getTime()
        self.setup()

    def setup(self):
        self.pars = initializers.setup_pars("parameters.json")
        self.win = initializers.setup_window()
        self.display = display.Display(self.win, self.pars)
        # plexon init here ...
        self.outfile = initializers.setup_data_file(self.taskname, 
            self.subject)
        self.controller = controller.Controller()
        self.data = []

    def teardown(self):
        # plexon close here...
        self.win.close()

    def run(self):
        # start task's monotonic clock, etc. ...
        pass