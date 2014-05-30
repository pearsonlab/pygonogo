import json
from psychopy.visual import Window

def setup_pars(fname):
    # load parameters from a json file
    with open(fname) as fp:
        pars = json.load(fp)

    return pars

def setup_window():
    win = Window(fullscr=True, allowGUI=False, screen=0, units='height', 
        monitor='testMonitor')
    return win

def setup_joystick():
    pass

def setup_plexon():
    pass

def setup_geometry():
    pass