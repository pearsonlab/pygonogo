"""
Class definition for task object.

TO DO:
* make task metaclass?
* task handles event loop, with list of functions to call each iteration?
"""

import initializers

class Task:
    def __init__(self, taskname, subject):
        self.taskname = taskname
        self.subject = subject
        self.setup()

    def setup(self):
        self.pars = initializers.setup_pars("parameters.json")
        self.win = initializers.setup_window()
        self.geom = initializers.setup_geometry(self.win, self.pars)
        self.outfile = initializers.setup_data_file(self.taskname, 
            self.subject)


    def teardown(self):
        pass
