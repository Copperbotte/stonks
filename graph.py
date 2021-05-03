import matplotlib.pyplot as plt
import numpy as np
import datetime
import random
#from client import criterion, bankroll_game #circular import

def criterion(win=2.0, lose=0.5, pwin=1/3, plose=2/3):
    return plose/(1-win) + pwin/(1-lose)
def bankroll_game(win=2.0, lose=0.5, pwin=1/3, plose=2/3, bankroll=1):
    return np.power((win-1)*bankroll + 1, pwin)*np.power((lose-1)*bankroll + 1, plose)

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

    #find first state
    first = None
    #first = 'buy'
    #if macd[0] < 0:
    #    first = 'sell'

    #macd will never perform a buy without a next corresponding sell, as these are intercepts.
    #if the intercept touches the x axis threshold, it'll immidiately buy and sell.
    #if the sequence starts below the x axis, the next action is a buy, so a sell should occur first.
    #weather this is a buy or a sell depends on the value of first
    #sequence = [ [0, int(time[0])] ]
    sequence = []

    for i in range(1, len(time)): #skip the first datapoint, used for a derivative
        before = 0 < macd[i-1]
        after = 0 < macd[i]
        if before != after:
            sequence.append([i, int(time[i])])

            #find first state
            if len(sequence) == 1:
                if 0 < macd[i] - macd[i-1]:
                    first = "buy"
                else:
                    first = "sell"

    #append final sale
    sequence += [ [-1, int(time[-1])] ]
    
    #find gains per each step in the sequence
    ps_pct = [] #profit percent, with shorts
    p_pct = [] #profit percent, without shorts
    cs_pct = [1.0] #cumulative profit percent, with shorts
    c_pct = [1.0] #cumulative profit percent, without shorts 

    #always use sell/buy, but raise it to the -1st power for each subsequent item
    #this is the same as a boolean 1/pct
    short = False
    if first == 'sell':
        short = True
        
    for b, s in zip(sequence[:-1], sequence[1:]):
        buyprice = prices[b[0]]
        sellprice = prices[s[0]]
        pct = sellprice / buyprice
        if short:
            pct = buyprice / sellprice
        pct *= 1 - fee
        
        ps_pct.append(pct)
        cs_pct.append(cs_pct[-1] * pct)
        if not short:
            p_pct.append(pct)
            c_pct.append(c_pct[-1] * pct)

        #print("b", b, "s", s, "spct", pct, "short", short)
            
        short = not short
    
    #find data for kelly criterion
    p_wins = list(filter(lambda x: 1 < x, ps_pct))
    p_lose = list(filter(lambda x: x <= 1, ps_pct))
    avg_gain = np.exp(sum(map(np.log, p_wins)) / len(p_wins))#multiplicitive average
    avg_loss = np.exp(sum(map(np.log, p_lose)) / len(p_lose))
    win_pct = len(p_wins) / len(ps_pct)
    lose_pct = 1-win_pct
    #print(avg_gain, avg_loss, win_pct, lose_pct)
    bankroll = criterion(win=avg_gain, lose=avg_loss, pwin=win_pct, plose=lose_pct)
    #print(bankroll)
    #print('\n', cs_pct[-1])

    #split buys and sells to gel with other algos
    if first == 'buy':
        buys = sequence[::2]
        sells = sequence[1::2]
    else:
        buys = sequence[1::2]
        sells = sequence[::2]
    
    return buys,sells, c_pct,p_pct, bankroll,cs_pct[-1]

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

def plots(data, #macdFast=3600*24*7, macdSlow=3600*24*7*4, macdLag=3600*24*7):
    macdFast=660571, macdSlow=1572479, macdLag=329809):
    #compute macd
    times, prices, fast, slow, cd, ma, macd = compute_Macd(data, macdFast, macdSlow, macdLag)

    #find profit using macd intercept strategy
    buys, sells, c_pct, p_pct, bankroll, s_pct = find_profit(times, prices, macd)
    print("bankroll:", bankroll)
    print("earnings: {p:.5f}%".format(p=c_pct[-1]*100))
    print("earnings with shorts: {p:.5f}%".format(p=s_pct*100))
    
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

    #these prints below should be debugs, can't pass locals in efficiently
    #def debug(expression):
    #    print(expression, eval(expression))

    #annotate sells with percentages gained
    #offset is 1 if there's an initial short
    offset = 0
    if sells[0][0] < buys[0][0]:
        offset = 1

    #print("debugging")
    #print("offset", offset)
    #print("len(sells)", len(sells))
    #print("len(p_pct)", len(sells))
    
    for s, pct in zip(sells[offset:], p_pct[offset:]):
        st = s[0]
        
        p = 100.0*(pct - 1.0)
        if pct < 1:
            p = 100.0*(1.0 - (1.0 / pct))
        
        stext = "{p:.2f}%".format(p=p)
        ax[0].annotate(text=stext, xy=(times[st], l_prices[st])).set_rotation(45)

    #title the final profit or loss
    plt.title(label="profit: " + "{pct:.2f}%".format(pct=c_pct[-1]*100.0))
    
    plt.show()

def computeMacdProfit(data, macdFast=3600*24*7, macdSlow=3600*24*7*4, macdLag=3600*24*7):
    times, prices, _,_,_,_, macd = compute_Macd(data, macdFast=macdFast, macdSlow=macdSlow, macdLag=macdLag)
    _,_,c_pct,_,br,s_pct = find_profit(times, prices, macd)
    return s_pct, br
    

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
    profit, br = computeMacdProfit(data, macdFast=macdFast, macdSlow=macdSlow, macdLag=macdLag)

    print("macdFast="+str(np.exp(l_mdf))+',', "macdSlow="+str(np.exp(l_mds))+',', "macdLag="+str(np.exp(l_mdl)), "profit:", profit, "bankroll:", br)

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
        profit_test, br = computeMacdProfit(data, macdFast=np.exp(l_mdf_test), macdSlow=np.exp(l_mds_test), macdLag=np.exp(l_mdl_test))

        #replace if better
        if profit < profit_test:
            l_mdf = l_mdf_test
            l_mds = l_mds_test
            l_mdl = l_mdl_test
            profit = profit_test
            print("macdFast="+str(np.exp(l_mdf))+',', "macdSlow="+str(np.exp(l_mds))+',', "macdLag="+str(np.exp(l_mdl)), "profit:", profit, "bankroll:", br)
    
def nelderMead(data, macdFast=3600*24*7, macdSlow=3600*24*7*4, macdLag=3600*24*7, shrink=0.5, expand=2.0):
    #nelder-mead optimization, starting with an orthogonal set of vertices, log(param) + 1 per parameter
    #walks are performed in log space
    l_mdf = np.log(macdFast)
    l_mds = np.log(macdSlow)
    l_mdl = np.log(macdLag)

    #build simplex
    verts =     [[0, l_mdf,    l_mds,    l_mdl]]
    verts.append([0, l_mdf+0.5,l_mds,    l_mdl])
    verts.append([0, l_mdf,    l_mds-0.5,l_mdl])
    verts.append([0, l_mdf,    l_mds,    l_mdl+0.5])
    
    #find profits in simplex
    for v in range(len(verts)):
        verts[v][0], br = computeMacdProfit(data, macdFast=np.exp(verts[v][1]), macdSlow=np.exp(verts[v][2]), macdLag=np.exp(verts[v][3]))
        print("macdFast="+str(np.exp(verts[v][1]))+',', "macdSlow="+str(np.exp(verts[v][2]))+',', "macdLag="+str(np.exp(verts[v][3])), "profit:", verts[v][0], "bankroll:", br)

    bestProfit = 0.0
    
    #nelder-mead algorithm:
    #find worst performing vertex
    #reflect it through the centroid of all the other vertices
    #sort the new vertex with the other two
    #if its between the other two, no further transforms are needed
    #if its the worst performer, shrink the vertex through the centroid
    #if its the best performer, expand the vertex through the centroid
    br = 0
    while True:
        #find worst performing vertex
        verts.sort(key=lambda x: x[0])
        bP = verts[-1][0]
        if bestProfit < bP:
            bestProfit = bP
            print("macdFast="+str(np.exp(verts[v][1]))+',', "macdSlow="+str(np.exp(verts[v][2]))+',', "macdLag="+str(np.exp(verts[v][3])), "profit:", verts[v][0], "bankroll:", br)
            
        #find simplex of all other vertices
        simp = np.array([0.0,0.0,0.0,0.0])
        for i in range(1, len(verts)):
            simp += np.array(verts[i]) / (len(verts) - 1)

        #adjust vertex
        delta = simp - np.array(verts[0])
        verts[0] = (simp + delta).tolist()
        verts[0][0], br = computeMacdProfit(data, macdFast=np.exp(verts[0][1]), macdSlow=np.exp(verts[0][2]), macdLag=np.exp(verts[0][3]))

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
            print("macdFast="+str(np.exp(verts[v][1]))+',', "macdSlow="+str(np.exp(verts[v][2]))+',', "macdLag="+str(np.exp(verts[v][3])), "profit:", verts[v][0])
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
        print("macdFast="+str(np.exp(verts[v][1]))+',', "macdSlow="+str(np.exp(verts[v][2]))+',', "macdLag="+str(np.exp(verts[v][3])), "profit:", verts[v][0])

data = None

if __name__ == "__main__":
    timefrom = datetime.datetime(2021,1,1).timestamp()
    data = loadData(timefrom=timefrom)#"XDGUSD_original.csv")
    data = processData(data)
    plots(data)
    #rndwlk(data) #use with a console based terminal for maximum effect, this function never returns.
    
