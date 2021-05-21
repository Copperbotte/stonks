
import numpy as np

def criterion(win=2.0, lose=0.5, pwin=1/3, plose=2/3):
    return plose/(1-win) + pwin/(1-lose)
def bankroll_game(win=2.0, lose=0.5, pwin=1/3, plose=2/3, bankroll=1):
    return np.power((win-1)*bankroll + 1, pwin)*np.power((lose-1)*bankroll + 1, plose)


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

def find_profit(time, prices, macd, fee=0.0016):
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

    if len(p_wins) and len(p_lose):
        avg_gain = np.exp(sum(map(np.log, p_wins)) / len(p_wins))#multiplicitive average
        avg_loss = np.exp(sum(map(np.log, p_lose)) / len(p_lose))
        win_pct = len(p_wins) / len(ps_pct)
        lose_pct = 1-win_pct
        #print(avg_gain, avg_loss, win_pct, lose_pct)
        bankroll = criterion(win=avg_gain, lose=avg_loss, pwin=win_pct, plose=lose_pct)
        #print(bankroll)
        #print('\n', cs_pct[-1])
    else:
        bankroll = 0

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
