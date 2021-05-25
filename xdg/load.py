import numpy as np
import datetime

#loads a csv file, splits by new lines, removes empty lines.
#outputs a list of strings.
def loadFile(src="XDGUSD.csv"):
    lines = None
    with open(src, 'r') as o:
        text = o.read()
        lines = text.split('\n')
        lines = list(filter(None, lines)) #exclude empty lines
    return lines

#saves a csv file, accepts a list of csv entries.
#   inverse of loadFile.
def saveFile(entries, src="XDGUSD.csv"):
    with open(src, 'w') as o:
        raw = '\n'.join(entries) + '\n'
        o.write(raw)

#splits a loaded csv file from loadFile into a list of lists of floats:
#   [unix time, dollar price, volume]
def parseFile(lines):
    return [list(map(float, L.split(','))) for L in lines]

#merges list of list data into a list of csv strings.
#   inverse of parsefile.
def serializeFile(data):
    return [','.join(map(str, d)) for d in data]

#finds the first datapoint at or later than the given timefrom
#   this can be done faster with a binary search (O(log2(n)) vs O(n))
def clipFile(data, timefrom=1577291768):
    s = 0
    for i in range(len(data)):
        if timefrom <= data[i][0]:
            s = i
            break
    
    return data[s:]

#loads a csv file, outputs a list of lists of floats:
#   [unix time, dollar price, volume]
def loadData(src="XDGUSD.csv", timefrom=1577291768):
    lines = loadFile(src)
    parsed = parseFile(lines)
    return clipFile(parsed, timefrom)

#finds the average price within a timescale, in seconds.
#generates candles?
#accepts list of float data, as written for loadData.
#returns the same format.
def processData(data, timescale=60):
    #process data to a target timescale
    #timescale = 60 # 1 minute
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
