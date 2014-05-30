from __future__ import division
import json
from psychopy.visual import Window, ImageStim
from psychopy.sound import Sound
import numpy as np
import os

def setup_pars(fname):
    # load parameters from a json file
    with open(fname) as fp:
        pars = json.load(fp)

    return pars

def setup_window():
    win = Window(fullscr=True, allowGUI=True, screen=0, units='height', 
        monitor='testMonitor', colorSpace='rgb255')
    return win

def setup_joystick():
    pass

def setup_plexon():
    pass

def setup_geometry(win, pars):
    # define some colors in a dictionary
    geom = ({"go_color": [0, 255, 0], "stop_color": [255, 0, 0], 
        "def_color": [125, 125, 125]})

    # determine target sizes by dividing target grid size into screen
    # size in 'height' units (however, only take up a square portion -- total
    # x range is 1, not 1.6 or 4/3)
    border = np.array([0.05, 0.05])  #offset from screen edge
    usable_size = [1.0, 1.0]
    reduced_bounds = usable_size - 2 * border
    grid = pars['grid']
    numtargs = np.prod(grid)
    target_max_size = reduced_bounds / grid 
    target_scale = 0.5
    target_size = target_scale * np.max(target_max_size) * np.ones(2)
    geom['target_sizes'] = np.tile(target_size, (numtargs, 1))

    # calculate centers of targets (assuming coords range from 0 to 1)
    xcenters = border[0] + (np.arange(grid[0]) + 0.5) * target_max_size[0] 
    ycenters = border[1] + (np.arange(grid[1]) + 0.5) * target_max_size[1]

    # get all pairs of coordinates in grid
    xc, yc = np.meshgrid(xcenters, ycenters)

    # offset so that coord origin is at center 
    target_centers = np.array(zip(xc.ravel(), yc.ravel())) - (0.5, 0.5)
    geom['target_centers'] = target_centers

    return geom

def setup_stims(win):
    # get relevant audio and visual resources loaded
    stims = {}
    stims['cashsnd'] = Sound('cash.wav')
    stims['firesnd'] = Sound('bbhit.wav')
    stims['buzzsnd'] = Sound('buzz.wav')

    stims['noimg'] = ImageStim(win, image='rfrog2.jpg')
    stims['goimg'] = ImageStim(win, image='gfrog2.jpg')
    stims['defimg'] = ImageStim(win, image='lilypad.jpg')
    stims['bkimg'] = ImageStim(win, image='pond.jpg')

    return stims

def setup_data_file(taskname, subjectname):
    # set up directory structure, if necessary
    root = os.path.splitdrive(os.getcwd())[0]
    if not root:
        root = '/'
    datadir = os.path.join(root, 'data', taskname, subjectname)
    if not os.path.exists(datadir):
        os.mkdir(datadir)

    # check previous data files to get next name in sequence for this run
    prev_files = os.listdir(datadir)
    file_pieces = [pf.split('.') for pf in prev_files]
    file_versions = [int(pc[1]) for pc in file_pieces if pc[-1] == 'mat']
    this_version = max(file_versions) + 1

    # build file name
    fname = '.'.join([subjectname, str(this_version), taskname, 'mat'])

    # return absolute path
    return os.path.join(datadir, fname)
