"""
Class definition for task object.
"""

import sys
from psychopy.gui import DlgFromDict
import initializers
import controller
import display
import psychopy.event as event
from psychopy import visual
import json
from Plexon import PlexClient


class Task:

    def __init__(self):
        task_info = self.get_subject()
        self.taskname = task_info['Task Name']
        self.subject = task_info['Subject']
        self.mode = task_info['Mode']
        self.setup()

    def get_subject(self):
        info = {"Task Name": 'gonogo', "Subject": 'test', 'Mode': ('Photodiode', 'Plexon')}
        infoDlg = DlgFromDict(dictionary=info,
                              title='Enter a subject number or name')
        if infoDlg.OK:
            print info
        else:
            sys.exit()

        return info

    def setup(self):
        self.pars = initializers.setup_pars("parameters.json")
        self.data = []
        if self.mode == 'Plexon':
            self.plexon = PlexClient.PlexClient()
        else:
            self.plexon = None
        self.flicker_queue = []
        self.logger = initializers.setup_acquisition(self.data, self.plexon, self.flicker_queue)
        self.display = display.Display(self.pars, self.flicker_queue)
        self.outfile, self.parsfile = initializers.setup_data_file(
            self.taskname, self.subject)
        self.joystick = initializers.setup_joystick()
        self.controller = controller.Controller(self.pars, self.display,
                                                self.logger, self.joystick)

        # save task parameters
        with open(self.parsfile, 'w+') as fp:
            json.dump(self.pars, fp)

    def teardown(self):
        if self.plexon is not None:
            self.plexon.CloseClient()
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
