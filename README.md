# Overview

This code re-implements a simple go/no-go task previously coded in Matlab. It uses the excellent [PsychoPy](http://www.psychopy.org/). To run, simply load `gonogo.py` in the PsychoPy Coder and click Run. Some things to note:

* Data files are saved in JSON format, as a list of event objects containing the event name and time. This is intended to aid readability by both humans and computers, since JSON is likely to outlast Python's pickle format and PsychoPy's experiment format.

* Tested on the Mac Standalone version of PsychoPy using OSX 10.6 (Snow Leopard) and (coming soon) Ubuntu 12.04 LTS. Your mileage may vary.

# Organization:
Code is organized in a really basic Controller-View setup, since Python and PsychoPy aren't really set up for asynchronous designs like publish-subscribe, which would be the easiest to do here. Specifically: 

1. `gonogo.py` instantiates and runs the `Task` class (located in `task.py`)
2. The Task class performs a lot of setup using functions from `initializers.py`, including loading parameters (from `parameters.json`), calculating screen geometry, setting up the Plexon or NI-DAQ, and figuring out where to save the data file and what to call it. 
    * The task parameters are used to instantiate a `Display` (`display.py`), which handles all drawing onscreen and exposes a high-level API.
    * `setup_plexon` returns a function that encapsulates all the details of signaling events via TTL pulse or Plexon event buffer and saving events to the task's data structure. It can then simply be called as a black box by the Controller, supplying an event name and channel.
    * The task also instantiates a `Controller` (`controller.py`), which is passed references to the Display, the logger, and the task parameters. The Controller handles all task logic and calls the logging function to mark task events.
3. `gonogo.py` calls the Task's `run` method, which calls the Controller's `run_trial` method in a loop, saving the data repeatedly.

# To-Do:
* Save task parameters for each run.
* Incorporate joystick support.
* Incorporate support for Plexon using the wrapper in [RealTimeElectrophy](https://github.com/chrox/RealTimeElectrophy)