import numpy as np
import datetime

def loadData(src="XDGUSD.csv", timefrom=1577291768):
    data = None
    
    with open(src, 'r') as o:
        text = o.read()
        lines = text.split('\n')[:-1] #exclude empty line at the end
        data = [list(map(float, L.split(','))) for L in lines]

    #find the first datapoint at or later than the given timefrom
    s = 0
    for i in range(len(data)):
        if timefrom <= data[i][0]:
            s = i
            break
    
    return data[s:]

def processData(data, timescale=60):
    #process data to a target timescale
    timescale = 60 # 1 minute
    #timescale = 3600 # 1 hour
    for i in range(len(data)):
        data[i][0] = np.floor(data[i][0]/timescale)*timescale

    #reprocess data to eliminate multiple trades at a single time
    data_avgtime = [data[0]]
    for i in range(1, len(data)):
        if data[i][0] == data_avgtime[-1][0]:
            sumValue = data_avgtime[-1][1] * data_avgtime[-1][2]
            sumValue += data[i][1] * data[i][2] # price * volume = value
            sumVolume = data_avgtime[-1][2] + data[i][2]
            avgPrice = sumValue / sumVolume
            data_avgtime[-1][1] = avgPrice
            data_avgtime[-1][2] = sumVolume
        else:
            data_avgtime.append(data[i])
    data = data_avgtime
    return data
