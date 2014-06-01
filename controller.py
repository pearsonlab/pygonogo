import numpy as np
from psychopy.core import CountdownTimer, Clock, StaticPeriod
import psychopy.event as event

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
        self.input_received = False
        self.no_response = False
        self.response_timer = None
        self.rt = None
        self.data = {} 

        numtargs = np.prod(self.pars['grid'])
        self.which_target = np.random.randint(0, numtargs) 
        self.onset_interval = np.random.uniform(self.pars['min_onset'], 
            self.pars['max_onset'])
        self.is_nogo = np.random.rand() < self.pars['frac_nogo']
        if self.is_nogo:
            self.trial_type = 'no'
        else:
            self.trial_type = 'go'

        self.onset_countdown = CountdownTimer(self.onset_interval) 
        # mark event: trial onset

    def run_trial(self):
        self.open_trial()

        while not self.trial_over:
            self.wait_for_input()

            if self.input_received:
                self.handle_input()
                self.display_outcome()
            else:
                self.handle_no_input()

            self.clean_up()

        self.close_trial()

        return self.data

    def wait_for_input(self):
        pressed = []
        while True:
            self.present_target()
            pressed = event.getKeys(keyList=['left', 'right', 'escape'])
            if 'escape' in pressed:
                self.end_task = True
                break
            elif pressed:
                self.input_received = True
                break
            elif self.target_is_on and (self.response_timer.getTime() > 
                self.pars['max_rt']):
                self.no_response = True
                break

    def present_target(self):
        if not self.target_is_on and self.onset_countdown.getTime() < 0:    
            # rotate target into view
            self.display.onset(self.which_target, self.trial_type)
            self.target_is_on = True
            self.response_timer = Clock()
            # mark event: target onset

        self.display.draw()

    def handle_input(self):
        if self.target_is_on:
            self.result = 'hit'
            self.trial_over = True
            self.rt = self.response_timer.getTime()

            self.correct = not self.is_nogo
            if self.correct:
                self.pts_this_trial = self.calculate_points(self.pars, 
                    self.rt) 
                self.outcome_sound = self.display.cashsnd
            else: 
                self.pts_this_trial = -self.pars['pts_per_correct']
                self.outcome_sound = self.display.buzzsnd

            self.outcome_delay = self.pars['disp_resp']

        else:
            self.result = 'premature'
            self.pts_this_trial = -self.pars['pts_per_correct']
            self.outcome_sound = self.display.firesnd
            self.outcome_delay = 0.3

    def handle_no_input(self):
        self.result = 'no response'
        self.correct = self.is_nogo
        self.trial_over = True

    def display_outcome(self):
        # update text onscreen
        self.display.set_target_text(self.which_target, 
            str(self.pts_this_trial))
        self.score += self.pts_this_trial
        self.display.set_score(self.score)

        # refresh screen
        self.outcome_sound.play()
        # mark event: outcome

        # during static period, code between start and complete will run
        iti = StaticPeriod()
        iti.start(self.outcome_delay)
        self.display.draw()
        iti.complete()

        # remove text overlay on target 
        self.display.set_target_text(self.which_target, '')

    def clean_up(self):
        if self.target_is_on:
            self.display.offset(self.which_target)
            self.display.draw()

    def close_trial(self):
        # print to screen
        # save data to file
        pass

    def calculate_points(self, pars, rt):
        return int(np.floor(pars['pts_per_correct'] * np.exp(
            -(rt - pars['pts_offset']) / pars['pts_decay'])))
