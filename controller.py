import numpy as np
from psychopy.core import CountdownTimer

class Controller:
    def __init__(self, pars, display):
        self.pars = pars
        self.display = display
        self.trialnum = 0
        self.score = 0
        self.end_task = False

    def open_trial(self):
        self.result = ''
        self.pts_this_trial = 0
        self.trial_over = False
        self.target_is_on = False
        numtargs = np.prod(self.pars['grid'])
        self.which_target = np.random.randint(0, numtargs) 
        self.onset_interval = np.random.uniform(self.pars['min_onset'], 
            self.pars['max_onset'])
        self.is_nogo = np.random.rand() < self.pars['frac_nogo']
        if self.is_nogo:
            self.trial_type = 'no'
        else:
            self.trial_type = 'go'

        self.onset_timer = CountdownTimer(self.onset_interval) 
        # mark event: trial onset
        print "open trial"

    def update(self):
        if not self.target_is_on and self.onset_timer.getTime() < 0: 
            self.display.onset(self.which_target, self.trial_type)
            self.target_is_on = True
            self.response_timer = CountdownTimer(self.pars['max_rt'])
            # mark event: target onset
            print "target onset"
        elif self.target_is_on and self.response_timer.getTime() < 0: 
            self.display.offset(self.which_target)
            self.target_is_on = False
            self.trial_over = True
            # mark event: trial over
            print "target offset"

        self.display.draw()

    def run_trial(self):
        self.open_trial()

        while not self.trial_over:
            self.update() 
            # get input
            # handle input

        self.close_trial()

    def close_trial(self):
        # print to screen
        # save data to file
        print "close trial"