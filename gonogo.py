"""
Code to run go/no-go task. Ported from Matlab.
"""

import task

if __name__ == '__main__':
    mytask = task.Task()
    mytask.run()
    mytask.teardown()
