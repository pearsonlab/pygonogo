from __future__ import division
import json
from psychopy.visual import Window
from psychopy.core import monotonicClock
from psychopy.hardware import joystick
import numpy as np
import os
from sys import platform


def setup_pars(fname):
    # load parameters from a json file
    with open(fname) as fp:
        pars = json.load(fp)

    return pars


def setup_window():
    win = Window(fullscr=True, allowGUI=False, screen=1, units='height',
                 monitor='testMonitor', colorSpace='rgb255', winType='pyglet')
    return win


def setup_joystick():
    try:
        return joystick.Joystick(0)
    except AttributeError:
        print 'No joystick plugged in.'
        return None


def setup_acquisition(data, plexon, queue):
    if plexon:
        plexon.InitClient()

    def logger(event_name, channel=1):
        if plexon is not None:
            plexon.MarkEvent(channel)
        else:  # photodiode mode
            value = np.binary_repr(channel)
            # zero pad to 8 bits and add stop and start bits
            value = '1' + (8 - len(value)) * '0' + value + '1'
            # add bits to draw queue
            if len(queue) == 0:  # only add to queue if it's empty
                for bit in reversed(value):  # add to queue in reverse since we'll pop it
                    if bit == '1':
                        queue.append(True)
                    if bit == '0':
                        queue.append(False)

        event = {"event": event_name, "time": monotonicClock.getTime()}

        data.append(event)
        return event

    return logger


def setup_geometry(win, pars):
    # define some colors in a dictionary
    geom = ({"go_color": [0, 255, 0], "stop_color": [255, 0, 0],
             "def_color": [125, 125, 125]})

    # determine target sizes by dividing target grid size into screen
    # size in 'height' units (however, only take up a square portion -- total
    # x range is 1, not 1.6 or 4/3)
    border = np.array([0.05, 0.05])  # offset from screen edge
    usable_size = [1.0, 1.0]
    reduced_bounds = usable_size - 2 * border
    grid = pars['grid']
    geom['numtargs'] = np.prod(grid)
    target_max_size = reduced_bounds / grid
    target_scale = 0.5
    target_size = target_scale * np.max(target_max_size) * np.ones(2)
    geom['target_size'] = target_size

    # calculate centers of targets (assuming coords range from 0 to 1)
    xcenters = border[0] + (np.arange(grid[0]) + 0.5) * target_max_size[0]
    ycenters = border[1] + (np.arange(grid[1]) + 0.5) * target_max_size[1]

    # get all pairs of coordinates in grid
    xc, yc = np.meshgrid(xcenters, ycenters)

    # offset so that coord origin is at center
    target_centers = np.array(zip(xc.ravel(), yc.ravel())) - (0.5, 0.5)
    geom['target_centers'] = target_centers

    return geom


def setup_data_file(taskname, subjectname):
    # set up directory structure, if necessary
    root = os.path.splitdrive(os.getcwd())[0]
    if not root:
        root = '/'
    if platform == 'darwin':  # if on OS X (don't want to write to root)
        root = os.path.expanduser('~')
        datadir = os.path.join(root, 'data', taskname, subjectname)
    else:
        datadir = os.path.join(root, 'data', taskname, subjectname)
    if not os.path.exists(datadir):
        print datadir
        os.makedirs(datadir)

    # check previous data files to get next name in sequence for this run
    prev_files = os.listdir(datadir)
    file_pieces = [pf.split('.') for pf in prev_files]
    file_versions = [int(pc[1]) for pc in file_pieces if pc[-1] == 'json']
    if file_versions:
        this_version = max(file_versions) + 1
    else:
        this_version = 1

    # build file name
    fname = '.'.join([subjectname, str(this_version), taskname, 'json'])
    parsname = '.'.join([subjectname, str(this_version), 'pars', 'json'])

    # return absolute path
    return (os.path.join(datadir, fname), os.path.join(datadir, parsname))
