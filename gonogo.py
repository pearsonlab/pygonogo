"""
Code to run go/no-go task. Ported from Matlab.
"""

import task 

if __name__ == '__main__':
    taskname = 'gonogo'
    subject = 'test'
    mytask = task.Task(taskname, subject)

    mytask.stims['noimg'].draw()
    mytask.win.flip()