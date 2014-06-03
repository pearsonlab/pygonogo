#!/usr/bin/python
#coding:utf-8

###########################################################
### A Python wrapper for reading Plexon plx/ddt files
### Written by Huangxin
###########################################################

from __future__ import division
import time
import numpy as np
import logging
import mmap
logger = logging.getLogger('SpikeRecord.Plexon')
import ctypes
from ctypes import Structure
from datetime import datetime

#######################################/
# Plexon .plx File Structure Definitions
#######################################/

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

LATEST_PLX_FILE_VERSION = 105

# file header (is followed by the channel descriptors)
class  PL_FileHeader(Structure):
    _fields_ = [('MagicNumber', ctypes.c_uint),            # = 0x58454c50;
                ('Version', ctypes.c_int),                 # Version of the data format; determines which data items are valid
                ('Comment', ctypes.c_char * 128),          # User-supplied comment 
                ('ADFrequency', ctypes.c_int),             # Timestamp frequency in hertz
                ('NumDSPChannels', ctypes.c_int),          # Number of DSP channel headers in the file
                ('NumEventChannels', ctypes.c_int),        # Number of Event channel headers in the file
                ('NumSlowChannels', ctypes.c_int),         # Number of A/D channel headers in the file
                ('NumPointsWave', ctypes.c_int),           # Number of data points in waveform
                ('NumPointsPreThr', ctypes.c_int),         # Number of data points before crossing the threshold

                ('Year', ctypes.c_int),                    # Time/date when the data was acquired
                ('Month', ctypes.c_int), 
                ('Day', ctypes.c_int), 
                ('Hour', ctypes.c_int),
                ('Minute', ctypes.c_int),
                ('Second', ctypes.c_int),

                ('FastRead', ctypes.c_int),                # reserved
                ('WaveformFreq', ctypes.c_int),            # waveform sampling rate; ADFrequency above is timestamp freq 
                ('LastTimestamp', ctypes.c_double),        # duration of the experimental session, in ticks
    
                # The following 6 items are only valid if Version >= 103
                ('Trodalness', ctypes.c_byte),             # 1 for single, 2 for stereotrode, 4 for tetrode
                ('DataTrodalness', ctypes.c_byte),         # trodalness of the data representation
                ('BitsPerSpikeSample', ctypes.c_byte),     # ADC resolution for spike waveforms in bits (usually 12)
                ('BitsPerSlowSample', ctypes.c_byte),      # ADC resolution for slow-channel data in bits (usually 12)
                ('SpikeMaxMagnitudeMV', ctypes.c_ushort),  # the zero-to-peak voltage in mV for spike waveform adc values (usually 3000)
                ('SlowMaxMagnitudeMV', ctypes.c_ushort),   # the zero-to-peak voltage in mV for slow-channel waveform adc values (usually 5000)
                
                # Only valid if Version >= 105
                ('SpikePreAmpGain', ctypes.c_ushort),      # usually either 1000 or 500
            
                ('Padding', ctypes.c_byte * 46),           # so that this part of the header is 256 bytes
                
                
                # Counters for the number of timestamps and waveforms in each channel and unit.
                # Note that these only record the counts for the first 4 units in each channel.
                # channel numbers are 1-based - array entry at [0] is unused
                ('TSCounts', ctypes.c_int * 130 * 5),      # number of timestamps[channel][unit]
                ('WFCounts', ctypes.c_int * 130 * 5),      # number of waveforms[channel][unit]
            
                # Starting at index 300, this array also records the number of samples for the 
                # continuous channels.  Note that since EVCounts has only 512 entries, continuous 
                # channels above channel 211 do not have sample counts.
                ('EVCounts', ctypes.c_int * 512)]          # number of timestamps[event_number]

class PL_ChanHeader(Structure):
    _fields_ = [('Name', ctypes.c_char * 32),       # Name given to the DSP channel
                ('SIGName', ctypes.c_char * 32),    # Name given to the corresponding SIG channel
                ('Channel', ctypes.c_int),          # DSP channel number, 1-based
                ('WFRate', ctypes.c_int),           # When MAP is doing waveform rate limiting, this is limit w/f per sec divided by 10
                ('SIG', ctypes.c_int),              # SIG channel associated with this DSP channel 1 - based
                ('Ref', ctypes.c_int),              # SIG channel used as a Reference signal, 1- based
                ('Gain', ctypes.c_int),             # actual gain divided by SpikePreAmpGain. For pre version 105, actual gain divided by 1000. 
                ('Filter', ctypes.c_int),           # 0 or 1
                ('Threshold', ctypes.c_int),        # Threshold for spike detection in a/d values
                ('Method', ctypes.c_int),           # Method used for sorting units, 1 - boxes, 2 - templates
                ('NUnits', ctypes.c_int),           # number of sorted units
                ('Template', ctypes.c_short * 5 * 64),  # Templates used for template sorting, in a/d values
                ('Fit', ctypes.c_int * 5),          # Template fit 
                ('SortWidth', ctypes.c_int),        # how many points to use in template sorting (template only)
                ('Boxes', ctypes.c_short * 5 * 2 * 4),  # the boxes used in boxes sorting
                ('SortBeg', ctypes.c_int),          # beginning of the sorting window to use in template sorting (width defined by SortWidth)
                ('Comment', ctypes.c_char * 128),
                ('Padding', ctypes.c_int * 11)]

class PL_EventHeader(Structure): 
    _fields_ = [('Name', ctypes.c_char * 32),       # name given to this event
                ('Channel', ctypes.c_int),          # event number, 1-based
                ('Comment', ctypes.c_char * 128),
                ('Padding', ctypes.c_int * 33)]

class PL_SlowChannelHeader(Structure):
    _fields_ = [('Name', ctypes.c_char * 32),       # name given to this channel
                ('Channel', ctypes.c_int),          # channel number, 0-based
                ('ADFreq', ctypes.c_int),           # digitization frequency
                ('Gain', ctypes.c_int),             # gain at the adc card
                ('Enabled', ctypes.c_int),          # whether this channel is enabled for taking data, 0 or 1
                ('PreAmpGain', ctypes.c_int),       # gain at the preamp
            
                # As of Version 104, this indicates the spike channel (PL_ChanHeader.Channel) of
                # a spike channel corresponding to this continuous data channel. 
                # <=0 means no associated spike channel.
                ('SpikeChannel', ctypes.c_int),
            
                ('Comment', ctypes.c_char * 128),
                ('Padding', ctypes.c_int * 28)]

# The header for the data record used in the datafile (*.plx)
# This is followed by NumberOfWaveforms*NumberOfWordsInWaveform
# short integers that represent the waveform(s)

class PL_DataBlockHeader(Structure):
    _fields_ = [('Type', ctypes.c_short),                           # Data type; 1=spike, 4=Event, 5=continuous
                ('UpperByteOf5ByteTimestamp', ctypes.c_ushort),     # Upper 8 bits of the 40 bit timestamp
                ('TimeStamp', ctypes.c_uint),                       # Lower 32 bits of the 40 bit timestamp
                ('Channel', ctypes.c_short),                        # Channel number
                ('Unit', ctypes.c_short),                           # Sorted unit number; 0=unsorted
                ('NumberOfWaveforms', ctypes.c_short),              # Number of waveforms in the data to folow, usually 0 or 1
                ('NumberOfWordsInWaveform', ctypes.c_short)]        # Number of samples per waveform in the data to follow
                # 16 bytes

TESTED_PLX_VERSIONS = (105,106)

class PlexFile(object):
    """
    Reading Plexon plx file
    """
    def __init__(self,filename):   
        self.file = open(filename, 'rb')
        if not self.file:
            logger.error("Could not open file " + filename)
        self.file_header = self._get_header(PL_FileHeader)
        if self.file_header.Version not in TESTED_PLX_VERSIONS:
            raise RuntimeError("PLX file version other than %s is not supported. "
                               "The version of this file is %d." \
                               %(','.join([str(v) for v in TESTED_PLX_VERSIONS]),self.file_header.Version))
        
        self.chan_headers = None
        self.event_headers = None
        self.slow_headers = None
        
        self.single_wf_counts = sum([self.file_header.WFCounts[i][j] for i in xrange(5) for j in xrange(130)])
        self.ext_event_counts = sum([self.file_header.EVCounts[i] for i in xrange(300)])
        self.ad_data_counts = sum([self.file_header.EVCounts[i] for i in xrange(300,512)])

        
        self.data_header_offset = ctypes.sizeof(PL_FileHeader)
        self.data_offset = self.data_header_offset + \
                           self.file_header.NumDSPChannels * ctypes.sizeof(PL_ChanHeader) + \
                           self.file_header.NumEventChannels * ctypes.sizeof(PL_EventHeader) + \
                           self.file_header.NumSlowChannels * ctypes.sizeof(PL_SlowChannelHeader)
    def __del__(self):
        if self.file:
            self.file.close()
            
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        pass
            
    def _get_header(self,Header):
        header = Header()
        self.file.readinto(header)
        return header
    
    def get_datetime(self):
        year = self.file_header.Year
        month = self.file_header.Month
        day = self.file_header.Day
        hour = self.file_header.Hour
        minute = self.file_header.Minute
        second = self.file_header.Second
        return datetime(year,month,day,hour,minute,second)
    
    def read_data_header(self):
        self.file.seek(self.data_header_offset)
        self.chan_headers = [self._get_header(PL_ChanHeader) for _i in range(self.file_header.NumDSPChannels)]
        self.event_headers = [self._get_header(PL_EventHeader) for _i in range(self.file_header.NumEventChannels)]
        self.slow_headers = [self._get_header(PL_SlowChannelHeader) for _i in range(self.file_header.NumSlowChannels)]
    
    def read_timestamps(self, callback):
        evtcounts = self.single_wf_counts + self.ext_event_counts
        
        event_type = np.zeros(evtcounts,dtype=np.uint16)
        event_channel = np.zeros(evtcounts,dtype=np.uint16)
        event_unit = np.zeros(evtcounts,dtype=np.uint16)
        event_timestamp = np.zeros(evtcounts,dtype=np.float32)
        index = 0
        
        ad_frequency = self.file_header.ADFrequency
        
        fileno = self.file.fileno()
        mfile = mmap.mmap(fileno,0,access=mmap.ACCESS_READ)
        #mfile = mmap.mmap(fileno,0,access=mmap.ACCESS_WRITE|mmap.ACCESS_READ,prot=mmap.PROT_READ|mmap.PROT_WRITE)

        # timing file processing
        start_time = time.time()
        previous_speed = 20.0
        current_speed = previous_speed
        end_offset = len(mfile)
        file_size = end_offset/10**6
        nbs = 0
        
        current_pos = self.data_offset
        data_offset = self.data_offset
        db_size = ctypes.sizeof(PL_DataBlockHeader)
        try:
            while(True):
                # pylint: disable=E1101
                db = PL_DataBlockHeader.from_buffer_copy(mfile,current_pos)
                nbs += 1
                if db.Type == PL_SingleWFType or db.Type == PL_ExtEventType:
                    event_type[index] = db.Type
                    event_channel[index] = db.Channel
                    event_unit[index] = db.Unit
                    event_timestamp[index] = db.TimeStamp/ad_frequency
                    index += 1
                waveform_size = db.NumberOfWaveforms * db.NumberOfWordsInWaveform *2
                current_pos += db_size + waveform_size      # skip waveform block
                
                if callback and nbs % 30000 == 0:        # callback to indicate progress every 30000 blocks
                    elapsed_time = time.time() - start_time
                    avg_speed = (current_pos - data_offset)/10**6/(elapsed_time)
                    current_speed = previous_speed * 0.5 + avg_speed * 0.5
                    previous_speed = current_speed
                    estimated_time_left = (end_offset - current_pos)/10**6/current_speed
                    done_size = current_pos/10**6
                    done_percentage = current_pos / end_offset
                    callback(done_percentage,done_size,file_size,elapsed_time,estimated_time_left)
        except ValueError:
            if callback:
                elapsed_time = time.time() - start_time
                callback(1.0,file_size,file_size,elapsed_time,0.0)
            return {'type':event_type, 'channel':event_channel, 'unit':event_unit, 'timestamp':event_timestamp}
    
    def GetTimeStampArrays(self,callback=None):
        """
        GetTimeStampArrays(callback) -> {'type', 'channel', 'unit', 'timestamp'}
        
        Parameters
        ----------
        callback(percentage,done_size,file_size,elapsed_time,left_time)
            Callback method reports file reading progress.
        
        Return dictionary of all timestamps.
        
        Returns
        -------
        'type', 'channel', 'unit', 'timestamp': dict keys
            Values are four 1-D arrays of the timestamp structure fields. The array length is the actual transferred TimeStamps.
            'timestamp' is converted to seconds.
        """
        data = self.read_timestamps(callback)
        return data

    def GetNullTimeStamp(self):
        data = {}
        data['type'] = np.empty(0,dtype=np.uint16)
        data['channel'] = np.empty(0,dtype=np.uint16)
        data['unit'] = np.empty(0,dtype=np.uint16)
        data['timestamp'] = np.empty(0)
        return data
    
    def read_ad_data(self, callback=None):
        self.read_data_header()
        gains = [self.slow_headers[channel].Gain for channel in xrange(self.file_header.NumSlowChannels)]
        adfreqs = [self.slow_headers[channel].ADFreq for channel in xrange(self.file_header.NumSlowChannels)]
        
        ad_data_counts = self.ad_data_counts
        wf_buffer = (ctypes.c_short * 256)()
        ad_channel = np.zeros(ad_data_counts,dtype=np.uint16)
        ad_value = np.zeros(ad_data_counts,dtype=np.float32)
        ad_timestamp = np.zeros(ad_data_counts,dtype=np.float32)
        index = 0
        
        ad_frequency = self.file_header.ADFrequency
        
        fileno = self.file.fileno()
        mfile = mmap.mmap(fileno,0,access=mmap.ACCESS_READ)

        # timing file processing
        start_time = time.time()
        previous_speed = 20.0
        current_speed = previous_speed
        end_offset = len(mfile)
        file_size = end_offset/10**6
        nbs = 0
        
        current_pos = self.data_offset
        data_offset = self.data_offset
        db_size = ctypes.sizeof(PL_DataBlockHeader)
        try:
            while(True):
                # pylint: disable=E1101
                db = PL_DataBlockHeader.from_buffer_copy(mfile,current_pos)
                waveform_size = db.NumberOfWaveforms * db.NumberOfWordsInWaveform * 2
                current_pos += db_size
                if db.Type == PL_ADDataType:
                    channel = db.Channel
                    ctypes.memmove(wf_buffer, mfile[current_pos:current_pos+waveform_size], waveform_size)
                    for i in xrange(db.NumberOfWordsInWaveform):
                        ad_channel[index] = channel
                        ad_value[index] = (wf_buffer[i]*5./2048.)/gains[channel]
                        ad_timestamp[index] = (db.TimeStamp + i*ad_frequency/adfreqs[channel])/ad_frequency
                        index += 1
                current_pos += waveform_size
                
                nbs += 1
                if callback and nbs % 30000 == 0:        # callback to indicate progress every 30000 blocks
                    elapsed_time = time.time() - start_time
                    avg_speed = (current_pos - data_offset)/10**6/(elapsed_time)
                    current_speed = previous_speed * 0.5 + avg_speed * 0.5
                    previous_speed = current_speed
                    estimated_time_left = (end_offset - current_pos)/10**6/current_speed
                    done_size = current_pos/10**6
                    done_percentage = current_pos / end_offset
                    callback(done_percentage,done_size,file_size,elapsed_time,estimated_time_left)
        except ValueError:
            if callback:
                elapsed_time = time.time() - start_time
                callback(1.0,file_size,file_size,elapsed_time,0.0)
            return {'channel':ad_channel, 'value':ad_value, 'timestamp':ad_timestamp}
        
    def GetADDataArrays(self,callback=None):
        """
        GetADDataArrays(callback) -> {'channel', 'value', 'timestamp'}
        
        Parameters
        ----------
        callback(percentage,done_size,file_size,elapsed_time,left_time)
            Callback method reports file reading progress.
        
        Return dictionary of all channels,values and timestamps.
        
        Returns
        -------
        'channel', 'value', 'timestamp': dict keys
            Values are four 1-D arrays of the ad data fields.
            'timestamp' is converted to seconds.
        """
        data = self.read_ad_data(callback)
        return data
    