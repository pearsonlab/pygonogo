#!/usr/bin/python
#coding:utf-8

###########################################################
### A Python wrapper of Plexon.h
### Written by Huangxin
###########################################################



import logging  # available in Python 2.3
import logging.handlers
############# Logging #############
logger = logging.getLogger('SpikeRecord.Plexon')
logger.setLevel( logging.INFO )
log_formatter = logging.Formatter('%(asctime)s (%(process)d) %(levelname)s: %(message)s')
log_handler_stderr = logging.StreamHandler()
log_handler_stderr.setFormatter(log_formatter)
logger.addHandler(log_handler_stderr)

import os
import ctypes
try:
    from ctypes import Structure, windll
    from ctypes.wintypes import HWND
except ImportError or ValueError:
    logger.warning('Cannot import Plexon dynamic library in your system.')
    raise



###############################################################################
## Plexon Client API Definitions
###############################################################################


PL_SingleWFType = 1
PL_StereotrodeWFType = 2  # reserved
PL_TetrodeWFType = 3      # reserved
PL_ExtEventType = 4
PL_ADDataType = 5
PL_StrobedExtChannel = 257
PL_StartExtChannel = 258
PL_StopExtChannel  = 259
PL_Pause = 260
PL_Resume = 261

MAX_WF_LENGTH = 56
MAX_WF_LENGTH_LONG = 120

# If the server closes the connection, dll sends WM_CONNECTION_CLOSED message to hWndMain
#define WM_CONNECTION_CLOSED    (WM_USER + 401)


##
## PL_Event is used in PL_GetTimestampStructures(...)
## 16 bytes
class PL_Event(Structure):
    _fields_ = [('Type', ctypes.c_byte),                      ## PL_SingleWFType, PL_ExtEventType or PL_ADDataType
                ('NumberOfBlocksInRecord', ctypes.c_byte),    ## reserved
                ('BlockNumberInRecord', ctypes.c_byte),       ## reserved
                ('UpperTS', ctypes.c_ubyte),                  ## Upper 8 bits of the 40-bit timestamp
                ('TimeStamp', ctypes.c_ulong),                ## Lower 32 bits of the 40-bit timestamp
                ('Channel', ctypes.c_short),                  ## Channel that this came from, or Event number
                ('Unit', ctypes.c_short),                     ## Unit classification, or Event strobe value
                ('DataType', ctypes.c_byte),                  ## reserved
                ('NumberOfBlocksPerWaveform', ctypes.c_byte), ## reserved
                ('BlockNumberForWaveform', ctypes.c_byte),    ## reserved
                ('NumberOfDataWords', ctypes.c_byte)]         ## number of shorts (2-byte integers) that follow this header

##
## The same as PL_Event above, but with Waveform added
## 128 bytes
class PL_Wave(Structure):
    _fields_ = [('Type', ctypes.c_byte),                      ## PL_SingleWFType, PL_ExtEventType or PL_ADDataType
                ('NumberOfBlocksInRecord', ctypes.c_byte),    ## reserved
                ('BlockNumberInRecord', ctypes.c_byte),       ## reserved
                ('UpperTS', ctypes.c_ubyte),                  ## Upper 8 bits of the 40-bit timestamp
                ('TimeStamp', ctypes.c_ulong),                ## Lower 32 bits of the 40-bit timestamp
                ('Channel', ctypes.c_short),                  ## Channel that this came from, or Event number
                ('Unit', ctypes.c_short),                     ## Unit classification, or Event strobe value
                ('DataType', ctypes.c_byte),                  ## reserved
                ('NumberOfBlocksPerWaveform', ctypes.c_byte), ## reserved
                ('BlockNumberForWaveform', ctypes.c_byte),    ## reserved
                ('NumberOfDataWords', ctypes.c_byte),         ## number of shorts (2-byte integers) that follow this header
                ('WaveForm', ctypes.c_short * MAX_WF_LENGTH)] ## The actual waveform data

##
## An extended version of PL_Wave for longer waveforms
## 256 bytes
class PL_WaveLong(Structure):
    _fields_ = [('Type', ctypes.c_byte),                     ## PL_SingleWFType, PL_ExtEventType or PL_ADDataType
                ('NumberOfBlocksInRecord', ctypes.c_byte),   ## reserved
                ('BlockNumberInRecord', ctypes.c_byte),      ## reserved
                ('UpperTS', ctypes.c_ubyte),                 ## Upper 8 bits of the 40-bit timestamp
                ('TimeStamp', ctypes.c_ulong),               ## Lower 32 bits of the 40-bit timestamp
                ('Channel', ctypes.c_short),                 ## Channel that this came from, or Event number
                ('Unit', ctypes.c_short),                    ## Unit classification, or Event strobe value
                ('DataType', ctypes.c_byte),                 ## reserved
                ('NumberOfBlocksPerWaveform', ctypes.c_byte),## reserved
                ('BlockNumberForWaveform', ctypes.c_byte),   ## reserved
                ('NumberOfDataWords', ctypes.c_byte),        ## number of shorts (2-byte integers) that follow this header
                ('WaveForm', ctypes.c_short * MAX_WF_LENGTH_LONG)]  ## The actual long waveform data

libname = "PlexClient.dll"
dirname = os.path.dirname(__file__)
try:
    _lib = windll.LoadLibrary(os.path.join(dirname, libname))
except:
    _lib = None
    logger.warning("Could not find PlexClient.dll in your system.")
else:
    PL_InitClient = _lib.PL_InitClient
    PL_InitClient.argtypes = [ctypes.c_int, HWND]
    PL_InitClient.restype = ctypes.c_int
    PL_InitClientEx2 = _lib.PL_InitClientEx2
    PL_InitClientEx2.argtypes = [ctypes.c_int, HWND]
    PL_InitClientEx2.restype = ctypes.c_int
    PL_InitClientEx3 = _lib.PL_InitClientEx3
    PL_InitClientEx3.argtypes = [ctypes.c_int, HWND, HWND]
    PL_InitClientEx3.restype = ctypes.c_int
    PL_CloseClient = _lib.PL_CloseClient
    PL_CloseClient.argtypes = []
    PL_CloseClient.restype = None
    PL_IsLongWaveMode = _lib.PL_IsLongWaveMode
    PL_IsLongWaveMode.argtypes = []
    PL_IsLongWaveMode.restype = ctypes.c_int
    PL_GetTimeStampArrays = _lib.PL_GetTimeStampArrays
    PL_GetTimeStampArrays.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_short), ctypes.POINTER(ctypes.c_short), ctypes.POINTER(ctypes.c_short), ctypes.POINTER(ctypes.c_int)]
    PL_GetTimeStampArrays.restype = None
    PL_GetTimeStampStructures = _lib.PL_GetTimeStampStructures
    PL_GetTimeStampStructures.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(PL_Event)]
    PL_GetTimeStampStructures.restype = None
    PL_SendUserEvent = _lib.PL_SendUserEvent
    PL_SendUserEvent.argtypes = [ctypes.c_int]
    PL_SendUserEvent.restype = None
    PL_GetOUTInfo = _lib.PL_GetOUTInfo
    PL_GetOUTInfo.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    PL_GetOUTInfo.restype = None
    PL_GetSlowInfo = _lib.PL_GetSlowInfo
    PL_GetSlowInfo.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    PL_GetSlowInfo.restype = None
    PL_GetSlowInfo64 = _lib.PL_GetSlowInfo64
    PL_GetSlowInfo64.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    PL_GetSlowInfo64.restype = None
    PL_GetNumNIDAQCards = _lib.PL_GetNumNIDAQCards
    PL_GetNumNIDAQCards.argtypes = [ctypes.POINTER(ctypes.c_int)]
    PL_GetNumNIDAQCards.restype = None
    PL_GetSlowInfo256 = _lib.PL_GetSlowInfo256
    PL_GetSlowInfo256.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    PL_GetSlowInfo256.restype = None
    PL_GetNIDAQCardSlow4 = _lib.PL_GetNIDAQCardSlow4
    PL_GetNIDAQCardSlow4.argtypes = [ctypes.POINTER(ctypes.c_int)]
    PL_GetNIDAQCardSlow4.restype = None
    PL_GetTIMClockFreq = _lib.PL_GetTIMClockFreq
    PL_GetTIMClockFreq.argtypes = []
    PL_GetTIMClockFreq.restype = ctypes.c_int
    PL_GetNIDAQBandwidth = _lib.PL_GetNIDAQBandwidth
    PL_GetNIDAQBandwidth.argtypes = []
    PL_GetNIDAQBandwidth.restype = ctypes.c_int
    PL_GetActiveChannel = _lib.PL_GetActiveChannel
    PL_GetActiveChannel.argtypes = []
    PL_GetActiveChannel.restype = ctypes.c_int
    PL_IsElClientRunning = _lib.PL_IsElClientRunning
    PL_IsElClientRunning.argtypes = []
    PL_IsElClientRunning.restype = ctypes.c_int
    PL_IsSortClientRunning = _lib.PL_IsSortClientRunning
    PL_IsSortClientRunning.argtypes = []
    PL_IsSortClientRunning.restype = ctypes.c_int
    PL_IsNIDAQEnabled = _lib.PL_IsNIDAQEnabled
    PL_IsNIDAQEnabled.argtypes = []
    PL_IsNIDAQEnabled.restype = ctypes.c_int
    PL_IsDSPProgramLoaded = _lib.PL_IsDSPProgramLoaded
    PL_IsDSPProgramLoaded.argtypes = []
    PL_IsDSPProgramLoaded.restype = ctypes.c_int
    PL_GetTimeStampTick = _lib.PL_GetTimeStampTick
    PL_GetTimeStampTick.argtypes = []
    PL_GetTimeStampTick.restype = ctypes.c_int
    PL_GetGlobalPars = _lib.PL_GetGlobalPars
    PL_GetGlobalPars.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    PL_GetGlobalPars.restype = None
    PL_GetGlobalParsEx = _lib.PL_GetGlobalParsEx
    PL_GetGlobalParsEx.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    PL_GetGlobalParsEx.restype = None
    PL_GetChannelInfo = _lib.PL_GetChannelInfo
    PL_GetChannelInfo.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    PL_GetChannelInfo.restype = None
    PL_GetSIG = _lib.PL_GetSIG
    PL_GetSIG.argtypes = [ctypes.POINTER(ctypes.c_int)]
    PL_GetSIG.restype = None
    PL_GetFilter = _lib.PL_GetFilter
    PL_GetFilter.argtypes = [ctypes.POINTER(ctypes.c_int)]
    PL_GetFilter.restype = None
    PL_GetGain = _lib.PL_GetGain
    PL_GetGain.argtypes = [ctypes.POINTER(ctypes.c_int)]
    PL_GetGain.restype = None
    PL_GetMethod = _lib.PL_GetMethod
    PL_GetMethod.argtypes = [ctypes.POINTER(ctypes.c_int)]
    PL_GetMethod.restype = None
    PL_GetThreshold = _lib.PL_GetThreshold
    PL_GetThreshold.argtypes = [ctypes.POINTER(ctypes.c_int)]
    PL_GetThreshold.restype = None
    PL_GetNumUnits = _lib.PL_GetNumUnits
    PL_GetNumUnits.argtypes = [ctypes.POINTER(ctypes.c_int)]
    PL_GetNumUnits.restype = None
    PL_GetTemplate = _lib.PL_GetTemplate
    PL_GetTemplate.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
    PL_GetTemplate.restype = None
    PL_GetNPointsSort = _lib.PL_GetNPointsSort
    PL_GetNPointsSort.argtypes = [ctypes.POINTER(ctypes.c_int)]
    PL_GetNPointsSort.restype = None
    PL_SWHStatus = _lib.PL_SWHStatus
    PL_SWHStatus.argtypes = []
    PL_SWHStatus.restype = ctypes.c_int
    PL_GetPollingInterval = _lib.PL_GetPollingInterval
    PL_GetPollingInterval.argtypes = []
    PL_GetPollingInterval.restype = ctypes.c_int
    PL_GetNIDAQNumChannels = _lib.PL_GetNIDAQNumChannels
    PL_GetNIDAQNumChannels.argtypes = []
    PL_GetNIDAQNumChannels.restype = ctypes.c_int
    PL_EnableExtLevelStartStop = _lib.PL_EnableExtLevelStartStop
    PL_EnableExtLevelStartStop.argtypes = [ctypes.c_int]
    PL_EnableExtLevelStartStop.restype = None
    PL_IsNidaqServer = _lib.PL_IsNidaqServer
    PL_IsNidaqServer.argtypes = []
    PL_IsNidaqServer.restype = ctypes.c_int
    PL_GetName = _lib.PL_GetName
    PL_GetName.argtypes = [ctypes.c_int, ctypes.c_char_p]
    PL_GetName.restype = None
    PL_GetEventName = _lib.PL_GetEventName
    PL_GetEventName.argtypes = [ctypes.c_int, ctypes.c_char_p]
    PL_GetEventName.restype = None
    PL_SetSlowChanName = _lib.PL_SetSlowChanName
    PL_SetSlowChanName.argtypes = [ctypes.c_int, ctypes.c_char_p]
    PL_SetSlowChanName.restype = None
    PL_GetSlowChanName = _lib.PL_GetSlowChanName
    PL_GetSlowChanName.argtypes = [ctypes.c_int, ctypes.c_char_p]
    PL_GetSlowChanName.restype = None
    PL_GetValidPCA = _lib.PL_GetValidPCA
    PL_GetValidPCA.argtypes = [ctypes.POINTER(ctypes.c_int)]
    PL_GetValidPCA.restype = None
    PL_GetTemplateFit = _lib.PL_GetTemplateFit
    PL_GetTemplateFit.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
    PL_GetTemplateFit.restype = None
    PL_GetBoxes = _lib.PL_GetBoxes
    PL_GetBoxes.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
    PL_GetBoxes.restype = None
    PL_GetPC = _lib.PL_GetPC
    PL_GetPC.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_float)]
    PL_GetPC.restype = None
    PL_GetMinMax = _lib.PL_GetMinMax
    PL_GetMinMax.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_float)]
    PL_GetMinMax.restype = None
    PL_GetGlobalWFRate = _lib.PL_GetGlobalWFRate
    PL_GetGlobalWFRate.argtypes = [ctypes.POINTER(ctypes.c_int)]
    PL_GetGlobalWFRate.restype = None
    PL_GetWFRate = _lib.PL_GetWFRate
    PL_GetWFRate.argtypes = [ctypes.POINTER(ctypes.c_int)]
    PL_GetWFRate.restype = None
