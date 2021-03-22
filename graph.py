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

#find exponential moving average
#ema is a differential value, and has one reduced data point
#ema2 is a lerp from ema1 and the current value
#ema is "constant" between dt values based on the previous value
#mathematically, this makes e^(-St) the lerp value, like fog

def make_ema(t, p, s=3600): #1 hour default ema
    ema = [p[0]]
    for i in range(1, len(p)):
        dt = t[i] - t[i-1]
        #fog?
        S = 2.0 / (s+1)
        e = (ema[-1]-p[i]) * np.exp(-S*dt) + p[i]
        
        ema.append(e)
    return ema

def plots(data, macdFast=3600*24*7, macdSlow=3600*24*7*4, macdLag=3600*24*7):
    #split xy coords
    np_data = np.array(data)
    times, prices = np_data[:,0], np_data[:,1]
    
    #generate ema fast and slow
    fast = make_ema(times, prices, s=macdFast) # 1 week ema
    slow = make_ema(times, prices, s=macdSlow) # 1 month ema

    #generate macd from lag
    cd = np.array(fast) - np.array(slow)
    ma = make_ema(times, cd, s=macdLag)
    macd = cd - ma

    #to log
    l_prices = make_log(prices)
    l_fast = make_log(fast)
    l_slow = make_log(slow)

    #plot
    fig, ax = plt.subplots(2,1, sharex='col')

    #plot raw
    ax[0].plot(times, l_prices)

    #plot ema fast and slow
    ax[0].plot(times, l_fast)
    ax[0].plot(times, l_slow)

    #plot macd
    ax[1].hlines(0, times[0], times[-1], color='black') #x axis
    ax[1].plot(times, cd)
    ax[1].plot(times, ma)
    ax[1].plot(times, macd)
    
    plt.show()
    

if __name__ == "__main__":
    plots(loadData())
    
