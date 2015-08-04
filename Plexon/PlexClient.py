#!/usr/bin/python
# coding:utf-8

###########################################################
# A Python wrapper of PlexClient
# Written by Huangxin
###########################################################

from __future__ import division
import ctypes
import numpy as np
import Plexon
import logging
logger = logging.getLogger('SpikeRecord.Plexon')

MAX_MAP_EVENTS_PER_READ = 8000


class PlexClient(object):

    """
    A Python wrapper for Plexon PlexClient.dll
    All memory that will be manipulated in Plexon library is allocated in the PlexClient object by ndarray and ctypes array. What's important is that the length of these arrays is constant after the API calls. The length of the real array that the server transferred is in the first value of the return Tuple. We have to deal with the C library so forget the dirty code. 
    """

    def __init__(self):
        self.library = Plexon._lib
        self.MAX_MAP_EVENTS_PER_READ = MAX_MAP_EVENTS_PER_READ
        self.MAPSampleRate = None
        self.EventTypeArray = np.empty(
            self.MAX_MAP_EVENTS_PER_READ, dtype=np.uint16)
        self.EventChannelArray = np.empty(
            self.MAX_MAP_EVENTS_PER_READ, dtype=np.uint16)
        self.EventUnitArray = np.empty(
            self.MAX_MAP_EVENTS_PER_READ, dtype=np.uint16)
        self.EventTimestampArray = np.empty(
            self.MAX_MAP_EVENTS_PER_READ, dtype=np.uint32)
        self.ServerEventBuffer = (
            Plexon.PL_Event * self.MAX_MAP_EVENTS_PER_READ)()

    def __enter__(self):
        self.InitClient()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.CloseClient()

    def __getattr__(self, name):
        try:
            return getattr(self.library, name)
        except AttributeError:
            raise

    def InitClient(self):
        """
        InitClient() 

        Initializes PlexClient.dll for a client. Opens MMF's and registers the client with the server. Remeber to close the client by yourself. Or try the 'with' statement to initialize the PlexClient class.
        """
        if not self.library:
            logger.warning('Failed to load Plexon client library.')
            return
        if not Plexon.PL_InitClientEx3(0, None, None):
            raise RuntimeError("Failed to initiate Plexon client.")
        TimeStampTick = self.GetTimeStampTick()
        if not TimeStampTick in (25, 40, 50):
            raise RuntimeError("Failed to get timestamp tick.")
        self.MAPSampleRate = 1000 / TimeStampTick * 1000

    def CloseClient(self):
        """
        CloseClient() 

        Cleans up PlexClient.dll (deletes CClient object) and
        Sends ClientDisconnected command to the server.
        The server decrements the counter for the number of connected clients.
        """
        if not self.library:
            return
        Plexon.PL_CloseClient()

    def IsSortClientRunning(self):
        """
        IsSortClientRunning() -> bool

        Return whether the SortClient is running. 
        """
        return Plexon.PL_IsSortClientRunning()

    def GetTimeStampTick(self):
        """
        GetTimeStampTick() -> integer

        Return timestamp resolution in microseconds.
        """
        return Plexon.PL_GetTimeStampTick()

    def IsLongWaveMode(self):
        """
        IsLongWaveMode() -> bool

        Return whether the server is using long wave mode.
        """
        return Plexon.PL_IsLongWaveMode()

    def MarkEvent(self, channel):
        return Plexon.PL_SendUserEvent(channel)

    def GetTimeStampArrays(self, num=MAX_MAP_EVENTS_PER_READ):
        """
        GetTimeStampArrays(num) -> {'type', 'channel', 'unit', 'timestamp'}

        Return dictionary of recent timestamps.
        Parameters
        ----------
        num: number
            Interger of maximun number of timestamp structures

        Returns
        -------
        'type', 'channel', 'unit', 'timestamp': dict keys
            Values are four 1-D arrays of the timestamp structure fields. The array length is the actual transferred TimeStamps.
            'timestamp' is converted to seconds.
        """
        num = ctypes.c_int(num)
        data = {}
        if self.library:
            Plexon.PL_GetTimeStampArrays(ctypes.byref(num),
                                         self.EventTypeArray.ctypes.data_as(
                                             ctypes.POINTER(ctypes.c_short)),
                                         self.EventChannelArray.ctypes.data_as(
                                             ctypes.POINTER(ctypes.c_short)),
                                         self.EventUnitArray.ctypes.data_as(
                                             ctypes.POINTER(ctypes.c_short)),
                                         self.EventTimestampArray.ctypes.data_as(ctypes.POINTER(ctypes.c_int)))
            data['type'] = self.EventTypeArray[:num.value]
            data['channel'] = self.EventChannelArray[:num.value]
            data['unit'] = self.EventUnitArray[:num.value]
            # make man readable timestamp
            data['timestamp'] = self.EventTimestampArray[
                :num.value] / self.MAPSampleRate
        else:
            data['type'] = np.empty(0, dtype=np.uint16)
            data['channel'] = np.empty(0, dtype=np.uint16)
            data['unit'] = np.empty(0, dtype=np.uint16)
            data['timestamp'] = np.empty(0)
        return data

    def GetTimeStampStructures(self, num=MAX_MAP_EVENTS_PER_READ):
        """
        GetTimeStampStructures(num) -> (num, array)

        Get recent timestamp number and structures.
        Parameters
        -------
        num: number
            Interger of maximun number of timestamp structures

        Returns
        -------
        num: number 
            Number of actual number of timestamp structures transferred
        array: ctype array
            Array of PL_Event structures filled with new data
        """
        num = ctypes.c_int(num)
        Plexon.PL_GetTimeStampStructures(
            ctypes.byref(num), ctypes.byref(self.ServerEventBuffer[0]))
        return (num.value, self.ServerEventBuffer)
