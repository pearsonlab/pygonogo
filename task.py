"""
Class definition for task object.

TO DO:
* make task metaclass?
* task handles event loop, with list of functions to call each iteration?
"""

import initializers
import state

class Task:
    def __init__(self, taskname, subject):
        self.taskname = taskname
        self.subject = subject
        self.setup()

    def setup(self):
        self.pars = initializers.setup_pars("parameters.json")
        self.win = initializers.setup_window()
        self.geom = initializers.setup_geometry(self.win, self.pars)
        self.stims = initializers.setup_stims(self.win)
        # plexon init here ...
        self.outfile = initializers.setup_data_file(self.taskname, 
            self.subject)
        self.state = state.State()
        self.data = []

    def teardown(self):
        # plexon close here...
        self.win.close()