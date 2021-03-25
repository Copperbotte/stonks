import matplotlib.pyplot as plt
import numpy as np
import datetime
import random

def loadData(src="XDGUSD.csv", timescale=60):
    data = None
    
    with open(src, 'r') as o:
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

def find_profit(time, prices, macd, fee=0.016):
    #find buys and sells using macd intercept method
    buys = []
    sells = []
    bought = True
    for i in range(1, len(time)):
        before = 0 < macd[i-1]
        after = 0 < macd[i]
        if before != after:
            if after:
                bought = True
                buys.append([i, int(time[i])])
            else:
                bought = False
                sells.append([i, int(time[i])])

    #find total net gain using this method
    states = [0,0] #dogecoin has an anomalous price at the start of its history, skips first trade
    
    #find first buy
    while sells[states[1]][1] < buys[states[0]][1]:
        if states[1] + 1 == len(sells):
            break
        states[1] += 1

    c_pct = [1.0] #cumulative pct
    p_pct = [] #profit pct

    #print("buys", buys)
    #print("sells", sells)
    #print("lens", len(buys), len(sells), len(time), len(prices))

    #sell at current price
    if bought: #sell at current price
        sells.append([len(time)-1, int(time[-1])])

    #find sell / buy pairs
    while states[0] != len(buys) and states[1] != len(sells):
        buyprice = prices[buys[states[0]][0]]
        sellprice = prices[sells[states[1]][0]]
        diff = sellprice / buyprice
        diff *= (1.0 - fee)

        p_pct.append(diff)
        c_pct.append(c_pct[-1] * diff)
        
        states[0] += 1
        states[1] += 1

    return buys,sells, c_pct,p_pct

def compute_Macd(data, macdFast=3600*24*7, macdSlow=3600*24*7*4, macdLag=3600*24*7):
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

    return times, prices, fast, slow, cd, ma, macd

def plots(data, macdFast=3600*24*7, macdSlow=3600*24*7*4, macdLag=3600*24*7):
    #compute macd
    times, prices, fast, slow, cd, ma, macd = compute_Macd(data, macdFast, macdSlow, macdLag)

    #find profit using macd intercept strategy
    buys, sells, c_pct, p_pct = find_profit(times, prices, macd)
    
    #to log
    l_prices = make_log(prices)
    l_fast = make_log(fast)
    l_slow = make_log(slow)

    #plot
    fig, ax = plt.subplots(2,1, sharex='col')

    #time formatting
    def major_formatter(x, pos):
        return datetime.datetime.utcfromtimestamp(x).strftime('%Y/%m/%d\n%H:%M:%S')
    for a in ax:
        a.xaxis.set_major_formatter(major_formatter)

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

    #plot buys and sells
    for i in range(len(ax)):
        for b in buys:
            ax[i].axvline(x=b[1], color='green')
        for s in sells:
            ax[i].axvline(x=s[1], color='red')

    #annotate sells with percentages gained
    for s in range(0, len(sells)): #skip first sale
        st = sells[s][0]

        p = 100.0*(p_pct[s-1] - 1.0)
        if p_pct[s-1] < 1:
            p = 100.0*(-1.0 / p_pct[s-1] + 1.0)
        
        stext = "{p:.2f}%".format(p=p)
        ax[0].annotate(text=stext, xy=(times[st], l_prices[st])).set_rotation(45)

    #title the final profit or loss
    plt.title(label="profit: " + "{pct:.2f}%".format(pct=c_pct[-1]*100.0))
    
    plt.show()

def computeMacdProfit(data, macdFast=3600*24*7, macdSlow=3600*24*7*4, macdLag=3600*24*7):
    times, prices, _,_,_,_, macd = compute_Macd(data, macdFast=macdFast, macdSlow=macdSlow, macdLag=macdLag)
    _,_,c_pct,_ = find_profit(times, prices, macd)
    return c_pct[-1]
    

def rndwlk(data, macdFast=3600*24*7, macdSlow=3600*24*7*4, macdLag=3600*24*7, sigma=0.1):
    def invgauss(sig=sigma):
        rpos = sig*np.sqrt(-np.log(1.0-random.random()))
        if random.random() < 0.5:
            rpos *= -1
        return rpos

    #random walks are performed in log space
    l_mdf = np.log(macdFast)
    l_mds = np.log(macdSlow)
    l_mdl = np.log(macdLag)

    #compute initial value
    profit = computeMacdProfit(data, macdFast=macdFast, macdSlow=macdSlow, macdLag=macdLag)

    print("macdFast="+str(np.exp(l_mdf))+',', "macdSlow="+str(np.exp(l_mds))+',', "macdLag="+str(np.exp(l_mdl)), "profit:", profit)

    while True:
        #mutate new parameters
        l_mdf_test = l_mdf + invgauss(sigma)
        l_mds_test = l_mds + invgauss(sigma)
        l_mdl_test = l_mdl + invgauss(sigma)

        #swap fast and slow if slow is greater than fast
        if l_mdf_test < l_mds_test:
            temp = l_mdf_test
            l_mdf_test = l_mds_test
            l_mds_test = temp

        #compute test result
        profit_test = computeMacdProfit(data, macdFast=np.exp(l_mdf_test), macdSlow=np.exp(l_mds_test), macdLag=np.exp(l_mdl_test))

        #replace if better
        if profit < profit_test:
            l_mdf = l_mdf_test
            l_mds = l_mds_test
            l_mdl = l_mdl_test
            profit = profit_test
            print("macdFast="+str(np.exp(l_mdf))+',', "macdSlow="+str(np.exp(l_mds))+',', "macdLag="+str(np.exp(l_mdl)), "profit:", profit)
    
def nelderMead(data, macdFast=3600*24*7, macdSlow=3600*24*7*4, macdLag=3600*24*7, shrink=0.5, expand=2.0):
    #nelder-mead optimization, starting with an orthogonal set of vertices, log(param) + 1 per parameter
    #walks are performed in log space
    l_mdf = np.log(macdFast)
    l_mds = np.log(macdSlow)
    l_mdl = np.log(macdLag)

    #build simplex
    verts =     [[0, l_mdf,   l_mds,   l_mdl]]
    verts.append([0, l_mdf+2, l_mds,   l_mdl])
    verts.append([0, l_mdf,   l_mds-2, l_mdl])
    verts.append([0, l_mdf,   l_mds,   l_mdl+2])
    
    #find profits in simplex
    for v in range(len(verts)):
        verts[v][0] = computeMacdProfit(data, macdFast=np.exp(verts[v][1]), macdSlow=np.exp(verts[v][2]), macdLag=np.exp(verts[v][3]))
        print("macdFast="+str(np.exp(verts[v][1]))+',', "macdSlow="+str(np.exp(verts[v][2]))+',', "macdLag="+str(np.exp(verts[v][3])), "profit:", verts[v][0])

    bestProfit = 0.0
    
    #nelder-mead algorithm:
    #find worst performing vertex
    #reflect it through the centroid of all the other vertices
    #sort the new vertex with the other two
    #if its between the other two, no further transforms are needed
    #if its the worst performer, shrink the vertex through the centroid
    #if its the best performer, expand the vertex through the centroid
    while True:
        #find worst performing vertex
        verts.sort(key=lambda x: x[0])
        bP = verts[-1][0]
        if bestProfit < bP:
            bestProfit = bP
            print("macdFast="+str(np.exp(verts[v][1]))+',', "macdSlow="+str(np.exp(verts[v][2]))+',', "macdLag="+str(np.exp(verts[v][3])), "profit:", verts[v][0])
            
        #find simplex of all other vertices
        simp = np.array([0.0,0.0,0.0,0.0])
        for i in range(1, len(verts)):
            simp += np.array(verts[i]) / (len(verts) - 1)

        #adjust vertex
        delta = simp - np.array(verts[0])
        verts[0] = (simp + delta).tolist()
        verts[0][0] = computeMacdProfit(data, macdFast=np.exp(verts[0][1]), macdSlow=np.exp(verts[0][2]), macdLag=np.exp(verts[0][3]))

        #swap fast and slow if slow is greater than fast
        if verts[0][2] < verts[0][1]:
            temp = verts[0][1]
            verts[0][1] = verts[0][2]
            verts[0][2] = temp

        #compare to extremes
        ext = [[verts[0][0], 'N'], [verts[1][0], 'S'], [verts[-1][0], 'L']]
        ext.sort(key=lambda x: x[0])

        #if N is in the middle: use new simplex
        if ext[1][1] == 'N':
            #print("macdFast="+str(np.exp(verts[v][1]))+',', "macdSlow="+str(np.exp(verts[v][2]))+',', "macdLag="+str(np.exp(verts[v][3])), "profit:", verts[v][0])
            continue

        #if N is the smallest, shrink new vertex
        offset = 1.0
        if ext[0][1] == 'N':
            offset = -shrink 
        else: #grow to new vertex
            offset = expand

        verts[0] = (simp + offset*delta).tolist()
        #swap fast and slow if slow is greater than fast
        if verts[0][2] < verts[0][1]:
            temp = verts[0][1]
            verts[0][1] = verts[0][2]
            verts[0][2] = temp
        #print("macdFast="+str(np.exp(verts[v][1]))+',', "macdSlow="+str(np.exp(verts[v][2]))+',', "macdLag="+str(np.exp(verts[v][3])), "profit:", verts[v][0])

data = None

if __name__ == "__main__":
    data = loadData()
    plots(data)
    #rndwlk(data) #use with a console based terminal for maximum effect, this function never returns.
    
