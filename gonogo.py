"""
Code to run go/no-go task. Ported from Matlab.
"""

import task 
import psychopy.event as event

if __name__ == '__main__':
    taskname = 'gonogo'
    subject = 'test'
    mytask = task.Task(taskname, subject)

    mytask.stims['bkimg'].draw()
    for stim in mytask.stims['targets']:
        stim.draw()
    mytask.stims['scoretxt'].draw()
    mytask.win.flip()
    event.waitKeys()