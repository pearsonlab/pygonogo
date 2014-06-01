from psychopy.sound import Sound
from psychopy.visual import ImageStim, TextStim
from psychopy.core import Clock
import initializers
from math import cos, pi

class Display:
    def __init__(self, pars):
        self.win = initializers.setup_window()
        self.pars = pars
        self.geom = initializers.setup_geometry(self.win, self.pars)
        self.rotation_clocks = [None] * self.geom['numtargs']
        self.type = ['default'] * self.geom['numtargs']

        self.setup_sounds()
        self.setup_images()
        self.setup_text()

    def setup_sounds(self):
        self.cashsnd = Sound('resources/cash.wav')
        self.firesnd = Sound('resources/bbhit.wav')
        self.buzzsnd = Sound('resources/buzz.wav')

    def setup_images(self):
        self.notargs = []
        self.gotargs = []
        self.deftargs = []
        self.bkimg = ImageStim(self.win, image='resources/pond.jpg', 
            units='norm', size=(2.0, 2.0))

        for targ in range(self.geom['numtargs']):
            self.notargs.append(ImageStim(self.win, 
                image='resources/rfrog2.jpg', 
                size=self.geom['target_size'],
                pos=self.geom['target_centers'][targ]))
            self.gotargs.append(ImageStim(self.win, 
                image='resources/gfrog2.jpg', 
                size=self.geom['target_size'],
                pos=self.geom['target_centers'][targ]))
            self.deftargs.append(ImageStim(self.win, 
                image='resources/lilypad.jpg', 
                size=self.geom['target_size'], 
                pos=self.geom['target_centers'][targ]))

        # set initial target stims to be the defaults
        self.targets = []
        for targ in self.deftargs:
            self.targets.append(targ)

    def setup_text(self):
        self.scoretxt = TextStim(self.win, text="Total Points:", 
        font='Helvetica', alignHoriz='left', alignVert='top', units='norm', 
        pos=(-1, 1), height=0.2, color=[178, 34, 34], colorSpace='rgb255')

        self.targtxt = []
        for targ in range(self.geom['numtargs']):
            self.targtxt.append(TextStim(self.win, 
                pos=self.geom['target_centers'][targ], 
                color='White', units='height', height=0.05, text=''))
 
    def set_target_image(self, index, value='default'):
        if value == 'go':
            self.targets[index] = self.gotargs[index]
        elif value == 'no':
            self.targets[index] = self.notargs[index] 
        elif value == 'default':
            self.targets[index] = self.deftargs[index]

    def set_target_text(self, index, value):
        self.targtxt[index].setText(value)

    def set_score(self, pts):
        self.scoretxt.setText('Total Points: ' + str(pts))

    def onset(self, index, value):
        self.rotation_clocks[index] = Clock()
        self.type[index] = value

    def offset(self, index):
        self.rotation_clocks[index] = Clock()
        self.type[index] = 'default'

    def update(self):
        # for each target with clock running (i.e., rotating) ...
        for idx, clk in enumerate(self.rotation_clocks):
            if clk:
                rot_time = clk.getTime()
                rot_dur = self.pars['rot_dur']

                if rot_time > rot_dur:
                    rotfrac = -1  # fully revealed
                    self.rotation_clocks[idx] = None  # get rid of clock
                else:
                    rotfrac = cos(pi * rot_time / self.pars['rot_dur'])

                # adjust target size to give illusion of rotation    
                base_size = self.geom['target_size']
                self.targets[idx].size = (abs(rotfrac) * base_size[0], 
                    base_size[1])

                # set correct image on target based on rotation angle
                if rotfrac < 0:
                    self.set_target_image(idx, self.type[idx])

    def draw(self):
        self.update()
        self.bkimg.draw()
        self.scoretxt.draw()
        for stim in self.targets:
            stim.draw()
        for stim in self.targtxt:
            stim.draw()
        self.win.flip()

    def close(self):
        self.win.close()

