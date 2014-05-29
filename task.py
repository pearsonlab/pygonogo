"""
Class definition for task object.

TO DO:
* make task metaclass?
* task handles event loop, with list of functions to call each iteration?
"""

import initializers

class Task:
    def __init__(self):
        self.pars = initializers.load_pars("parameters.json")



