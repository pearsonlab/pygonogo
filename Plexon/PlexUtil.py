#!/usr/bin/python
#coding:utf-8

###########################################################
### Utilities for Plexon data collection
### Written by Huangxin
###########################################################

import numpy as np
import logging
logger = logging.getLogger('SpikeRecord.Plexon')
from SpikeRecord import Plexon

def reconstruct_word_in_python(WORD_BITS,bits_num,unstrobed_bits,words_buffer,timestamps_buffer):
    bits_indices = np.array([0]*WORD_BITS)
    oldest_timestamps = np.array([unstrobed_bits[bit][0] for bit in xrange(WORD_BITS)])
    # synonyms
    bits_num = bits_num
    unstrobed_bits = unstrobed_bits
    words_buffer = words_buffer
    timestamps_buffer = timestamps_buffer
    
    where = np.where
    left_shift = np.left_shift
    timestamps_min = oldest_timestamps.min
    
    words_count = 0
    indices_sum = 0
    while indices_sum < bits_num:
        timestamp = timestamps_min()
        word_bits = where(oldest_timestamps==timestamp)[0]
        # construct word from bits
        word = left_shift(1,word_bits).sum()
        # increment the indices of previous word bits
        bits_indices[word_bits] += 1
        # increment indices sum so that the loop will run until all bits are processed
        indices_sum += word_bits.size
        # update oldest timestamp of previous word bits
        oldest_timestamps[word_bits] = unstrobed_bits[word_bits,bits_indices[word_bits]]
        # fill word and timestamp in buffers
        words_buffer[words_count] = word
        timestamps_buffer[words_count] = timestamp
        words_count += 1
    return words_count

try:
    import _unstrobed_word
    reconstruct_word = _unstrobed_word.reconstruct_word_32
except ImportError or ValueError:
    reconstruct_word = reconstruct_word_in_python
    logger.info("Cannot import C version of reconstruct_word. Building a C version is highly recommended. We will use Python version this time.")

class PlexUtil(object):
    """
    Utilities for data collection
    """
    def __init__(self):
        self.last_word = None
        self.last_timestamp = None
        
    def GetSpikesInfo(self,data):
        """
        GetSpikesInfo(data) -> info

        Return spike units collected in this period of time.
        Parameters
        ----------
        data: dict 
            {'type', 'channel', 'unit', 'timestamp'} dictionary from the return value of PlexClient.GetTimeStampArray().

        Returns
        info: list of units for every spikes occurring channels
            [(channel, units)]
        """
        sorted_spikes = (data['type'] == Plexon.PL_SingleWFType) & (data['unit'] > 0)
        info = []
        for channel in np.unique(data['channel'][sorted_spikes]):
            channel_units = map(chr, np.unique(data['unit'][sorted_spikes & (data['channel'] == channel)]) + (ord('a')-1))
            info.append((channel, channel_units))
        return info
        
    def GetSpikeTrains(self,data):
        spike_trains = {}
        sorted_spikes = (data['type'] == Plexon.PL_SingleWFType) & (data['unit'] > 0)
        for channel in np.unique(data['channel'][sorted_spikes]):
            spike_trains[channel] = {}
            for unit in map(chr,np.unique(data['unit'][sorted_spikes & (data['channel'] == channel)]) + (ord('a')-1)):
                spike_trains[channel][unit] = self.GetSpikeTrain(data, channel=channel, unit=unit)
        return spike_trains
            
    def GetSpikeTrain(self, data, channel, unit):
        """
        GetSpikeTrain(data) -> spike_train

        Return sorted spikes of the specific unit in one channel.
        Parameters
        ----------
        data: dict 
            {'type', 'channel', 'unit', 'timestamp'} dictionary from the return value of PlexClient.GetTimeStampArray().
        channel: int 
            currently 1-128
        unit: str 
            a-z

        Returns
        -------
        spiketrain: array 
            timestamp array of the specific unit
        """
        unit_spikes = (data['type'] == Plexon.PL_SingleWFType) & \
                      (data['channel'] == channel) & \
                      (data['unit'] == ord(unit)-ord('a')+1)

        return np.copy(data['timestamp'][unit_spikes])
    
    def GetEventsNum(self, data):
        return len(data['timestamp'])
    
    #@profile
    def GetExtEvents(self, data, event, bit=None, online=True):
        """
        GetExtEvents(data) -> extevents

        Return external events.
        Parameters
        ----------
        data: dict
            {'type', 'channel', 'unit', 'timestamp'} dictionary from the return value of PlexClient.GetTimeStampArray().
        event: string
            event types: 'first_strobe_word','second_strobe_word','start','stop','pause','resume','unstrobed_bit'
        bit: int
            currently 1-32, used only in unstrobed_bit event 
        Returns
        -------
        extevents: timestamp array of 'first_strobe', 'second_strobe', 'start', 'stop', 'pause', 'resume' events. for strobe_word events 
        the array is contained in a dictionary which take the key 'value' as the strobed word and the key 'timestamp' as event stamp.
        """
        ext_event_type = (data['type'] == Plexon.PL_ExtEventType)
        #extevents = data['type'][ext_event_type]
        channel = data['channel'][ext_event_type]
        unit = data['unit'][ext_event_type]
        timestamp = data['timestamp'][ext_event_type]
        # for strobed word event
        if event in ('first_strobe_word','second_strobe_word'):
            strobed_events = (channel == Plexon.PL_StrobedExtChannel)
            strobed_unit = unit[strobed_events]
            strobed_timestamp = timestamp[strobed_events]
            first_strobe  = (strobed_unit & 0x8000) == 0
            second_strobe = (strobed_unit & 0x8000) != 0
            if event == 'first_strobe_word':
                return {'value':strobed_unit[first_strobe] & 0x7FFF , 'timestamp':strobed_timestamp[first_strobe]}
            else:
                return {'value':strobed_unit[second_strobe]         , 'timestamp':strobed_timestamp[second_strobe]}
        # for start event 
        if event == 'start':
            return timestamp[channel == Plexon.PL_StartExtChannel]
        # for stop event
        if event == 'stop':
            return timestamp[channel == Plexon.PL_StopExtChannel]
        # for pause event
        if event == 'pause':
            return timestamp[channel == Plexon.PL_Pause]
        # for resume event 
        if event == 'resume':
            return timestamp[channel == Plexon.PL_Resume]
        # for unstrobed events
        if event == 'unstrobed_bit':
            return timestamp[channel == bit + 1 ]
        # reconstruct unstrobed word from unstrobed bits
        if event == 'unstrobed_word':
            infinity = float('inf')
            WORD_BITS = 32
            # add an additional infinity in array end so that index of unstrobed_bits will not get out of range
            unstrobed_bits_list = [timestamp[channel == bit+1] for bit in xrange(WORD_BITS)]
            bits_length = [len(unstrobed_bits_list[bit]) for bit in xrange(WORD_BITS)] # actural bits length
            max_length = max(bits_length)
            bits_num = sum(bits_length)
            # make 2d array of timestamp 
            unstrobed_bits = np.array([np.append(unstrobed_bits_list[bit], [infinity]*(max_length-bits_length[bit]+1)) \
                                       for bit in xrange(WORD_BITS)],dtype=np.float32)
            # create numpy buffer to hold words and timestamps
            words_buffer = np.empty(bits_num,dtype=np.int32)
            timestamps_buffer = np.empty(bits_num,dtype=np.float32)
            
            words_count = reconstruct_word(WORD_BITS,bits_num,unstrobed_bits,words_buffer,timestamps_buffer)
            
            words = words_buffer[:words_count]
            timestamps = timestamps_buffer[:words_count]
            if len(timestamps) and self.last_timestamp == timestamps[0]:
                words[0] += self.last_word
            elif self.last_word is not None:
                words = np.append(self.last_word, words)
                timestamps = np.append(self.last_timestamp, timestamps)
                if len(timestamps)==1: 
                    self.last_word = None
                    self.last_timestamp = None
                    return {'value': np.array(words), 'timestamp': np.array(timestamps)}
            if online:      # in offline mode all timestamps are read at once
                if len(timestamps):
                    self.last_word = words[-1]
                    self.last_timestamp = timestamps[-1]
                return {'value': np.array(words[:-1]), 'timestamp': np.array(timestamps[:-1])}
            else:
                return {'value': np.array(words), 'timestamp': np.array(timestamps)}
