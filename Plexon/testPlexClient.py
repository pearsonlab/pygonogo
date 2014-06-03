#!/usr/bin/pyhton
import time
#from guppy import hpy; h = hpy()
from PlexClient import PlexClient
from PlexUtil import PlexUtil

if __name__ == "__main__":
    with PlexClient() as pc:
        pu = PlexUtil()
        while True:
            #print "reading from server"
            data = pc.GetTimeStampArrays()
            # get spike trains altogether 
            spike_trains = pu.GetSpikeTrains(data)
            for channel,channel_trains in spike_trains.iteritems():
                print '\nfound spike trains of channel:%c' % channel
                print '  ' + ', '.join(str(spike) for unit_train in channel_trains.itervalues() for spike in unit_train)
            # get spike trian of specific channel and unit
            spike_info = pu.GetSpikesInfo(data)
            for channel,units in spike_info:
                print 'found spikes in channel:%d unit:%s' % (channel, ', '.join(unit for unit in units))
                for unit in units:
                    spikes = pu.GetSpikeTrain(data, channel=channel, unit=unit)
                    for timestamp in spikes:
                        print "spike:DSP%d%c t=%f" % (channel, unit, timestamp)
            
            start_events = pu.GetExtEvents(data, event='start')
            for timestamp in start_events:
                print "PlexControl started at t=%f" % timestamp
                
            stop_events = pu.GetExtEvents(data, event='stop')
            for timestamp in stop_events:
                print "PlexControl stopped at t=%f" % timestamp
            
            bit_2_events = pu.GetExtEvents(data, event='unstrobed_bit', bit=2)
            bit_3_events = pu.GetExtEvents(data, event='unstrobed_bit', bit=3)
            for timestamp in bit_2_events:
                print "found event:unstrobed bit 2 t=%f" % timestamp
            for timestamp in bit_3_events:
                print "found event:unstrobed bit 3 t=%f" % timestamp
            
            unstrobed_word = pu.GetExtEvents(data, event='unstrobed_word')
            for value,timestamp in zip(unstrobed_word['value'],unstrobed_word['timestamp']) :
                print "found event:unstrobed word:%d t=%f" % (value,timestamp)
            
            time.sleep(1.0)

            #print h.heap()

