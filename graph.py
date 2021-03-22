import matplotlib.pyplot as plt
import numpy as np

data = None

def loadData(src="XDGUSD.csv", timescale=60):
    data = None
    
    with open("XDGUSD.csv", 'r') as o:
        text = o.read()
        lines = text.split('\n')[:-1] #exclude empty line at the end
        data = [list(map(float, L.split(','))) for L in lines]

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

def make_log(data):
    return list(map(np.log, data))

def plots(data):
    np_data = np.array(data)
    
    #process to log
    np_data[:,1] = make_log(np_data[:,1])
    
    #split xy coords
    x,y = np_data[:,0], np_data[:,1]

    #plot
    plt.plot(x,y)
    plt.show()
    

if __name__ == "__main__":
    plots(loadData())
    
