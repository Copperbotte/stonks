import numpy as np
import matplotlib.pyplot as plt
import datetime

#from .process import find_profit, compute_Macd
from .process import make_log, make_ema, find_profit, compute_Macd

def criterion(win=2.0, lose=0.5, pwin=1/3, plose=2/3):
    return plose/(1-win) + pwin/(1-lose)
def bankroll_game(win=2.0, lose=0.5, pwin=1/3, plose=2/3, bankroll=1):
    return np.power((win-1)*bankroll + 1, pwin)*np.power((lose-1)*bankroll + 1, plose)

#def plots(data, tradefunc):
#    #find profit using tradefunc intercept strategy
    

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
    #ax[0].plot(times, l_prices)
    ax[0].plot(times, prices)

    #plot ema fast and slow
    #ax[0].plot(times, l_fast)
    #ax[0].plot(times, l_slow)
    ax[0].plot(times, fast)
    ax[0].plot(times, slow)

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

    print("debugging")
    print("offset", offset)
    print("len(sells)", len(sells))
    print("len(p_pct)", len(sells))
    
    for s, pct in zip(sells[offset:], p_pct[offset:]):
        st = s[0]
        
        p = 100.0*(pct - 1.0)
        if pct < 1:
            p = 100.0*(1.0 - (1.0 / pct))
        
        stext = "{p:.2f}%".format(p=p)
        ax[0].annotate(text=stext, xy=(times[st], prices[st])).set_rotation(45)

    #title the final profit or loss
    plt.title(label="profit: " + "{pct:.2f}%".format(pct=c_pct[-1]*100.0))
    
    plt.show()
