import numpy as np
from psychopy.core import CountdownTimer, Clock, StaticPeriod
import psychopy.event as event

class Controller:
    def __init__(self, pars, display, logger, joystick):
        self.pars = pars
        self.display = display
        self.trialnum = 0
        self.score = 0
        self.end_task = False
        self.mark_event = logger
        self.joy = joystick

    def open_trial(self):
        self.trialnum += 1
        self.result = ''
        self.pts_this_trial = 0
        self.trial_over = False
        self.target_is_on = False
        self.input_received = False
        self.no_response = False
        self.response_timer = None
        self.rt = float('NaN') 
        self.data = [] 

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
        self.mark_event('trial_start', channel=1)

    def run_trial(self):
        self.open_trial()

        while not self.trial_over:
            self.wait_for_input()

            if self.input_received:
                self.handle_input()
                self.display_outcome()
            else:
                self.handle_no_input()

            self.refresh()

        self.close_trial()

        return self.data

    def wait_for_input(self):
        pressed = []
        while True:
            self.present_target()
            pressed = event.getKeys(keyList=['left', 'right', 'escape'])
            joypull = joy.getButton(0) 
            if 'escape' in pressed:
                self.end_task = True
                break
            elif pressed or joypull:
                self.input_received = True
                self.mark_event('responded', channel=3)
                break
            elif self.target_is_on and (self.response_timer.getTime() > 
                self.pars['max_rt']):
                self.no_response = True
                self.mark_event('no_response', channel=4)
                break

    def present_target(self):
        if not self.target_is_on and self.onset_countdown.getTime() < 0:    
            # rotate target into view
            self.display.onset(self.which_target, self.trial_type)
            self.target_is_on = True
            self.response_timer = Clock()
            self.mark_event('target on', channel=2)

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

        # remember to reset input
        self.input_received = False

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
        self.mark_event('outcome', channel=5)

        # during static period, code between start and complete will run
        iti = StaticPeriod()
        iti.start(self.outcome_delay)
        self.display.draw()
        iti.complete()

        # remove text overlay on target 
        self.display.set_target_text(self.which_target, '')

    def refresh(self):
        if self.target_is_on:
            self.display.offset(self.which_target)
            self.display.draw()

    def close_trial(self):
        # print to screen
        self.mark_event('trial_over', channel=8)
        print 'Trial {0:d}: Type {1}  Result: {2}  RT: {3:0.3g}  Correct: {4:d}  Points: {5:d}'.format(self.trialnum, self.trial_type, self.result, self.rt, self.correct, self.pts_this_trial)

    def calculate_points(self, pars, rt):
        return int(np.floor(pars['pts_per_correct'] * np.exp(
            -(rt - pars['pts_offset']) / pars['pts_decay'])))
