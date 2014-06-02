"""
Class definition for task object.

TO DO:
* make task metaclass?
* task handles event loop, with list of functions to call each iteration?
"""

import initializers
import controller, display
import psychopy.event as event
import json

class Task:
    def __init__(self, taskname, subject):
        self.taskname = taskname
        self.subject = subject
        self.setup()

    def setup(self):
        self.pars = initializers.setup_pars("parameters.json")
        self.display = display.Display(self.pars)
        self.data = []
        self.logger = initializers.setup_plexon(self.data)
        self.outfile = initializers.setup_data_file(self.taskname,
            self.subject)
        self.controller = controller.Controller(self.pars, self.display, 
            self.logger)

    def teardown(self):
        # plexon close here...
        self.display.close()

    def save(self):
        with open(self.outfile, 'w+') as fp:
            json.dump(self.data, fp)

    def run(self):
        while not self.controller.end_task:
            self.controller.run_trial()

            # save data after each trial
            self.save()

            if event.getKeys(keyList=['escape']):
                break

