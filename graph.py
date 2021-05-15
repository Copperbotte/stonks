import matplotlib.pyplot as plt
import numpy as np
import datetime
import random
#from client import criterion, bankroll_game #circular import

def criterion(win=2.0, lose=0.5, pwin=1/3, plose=2/3):
    return plose/(1-win) + pwin/(1-lose)
def bankroll_game(win=2.0, lose=0.5, pwin=1/3, plose=2/3, bankroll=1):
    return np.power((win-1)*bankroll + 1, pwin)*np.power((lose-1)*bankroll + 1, plose)

from xdg import loadData, processData
from xdg import make_log, make_ema, find_profit, compute_Macd
from xdg import plots
from xdg import computeMacdProfit, randomWalk, nelderMead

data = None

if __name__ == "__main__":
    timefrom = datetime.datetime(2021,1,1).timestamp()
    data = loadData()#timefrom=timefrom)#"XDGUSD_original.csv")
    data = processData(data)
    plots(data)
    #randomwalk(data) #use with a console based terminal for maximum effect, this function never returns.
    
