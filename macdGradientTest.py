import matplotlib.pyplot as plt
import numpy as np
import random

def invgauss(sig=0.1):
    rpos = sig*np.sqrt(-np.log(1.0-random.random()))
    if random.random() < 0.5:
        rpos *= -1
    return rpos

def genSignal(n=10000, sigma=0.01):
    t = np.arange(n)
    y = [1.0]
    for i0, i1 in zip(t[:-1], t[1:]):
        y1 = np.log(y[-1])
        y2 = y1 + invgauss(sigma)
        y2 = np.exp(y2)
        y.append(y2)
    return t,y

def make_ema(t, p, s=3600): #1 hour default ema
    ema = [p[0]]
    for i in range(1, len(p)):
        dt = t[i] - t[i-1]
        #fog?
        S = 2.0 / (s+1)
        e = (ema[-1]-p[i]) * np.exp(-S*dt) + p[i]
        
        ema.append(e)
    return ema

#ema's parameter gradient is
#dema/ds = (p - ema(t))* dt/ds

def plot_one():
    t,y = genSignal()
    plt.plot(t,y)

    ema = make_ema(t, y, s=3600)
    plt.plot(t, ema)
    plt.show()

def plot_many(seed=400, t_x=6000, t_y=1.2, iters=40, init=360, rate=1000):
    random.seed(seed)
    t,y = genSignal()
    plt.plot(t,y)

    #target_x = 6000
    #target_y = 1.20

    target_x = t_x
    target_y = t_y

    plt.axhline(y=target_y, xmax=10000, color='black')
    plt.axvline(x=target_x, ymin=0, ymax=max(y), color='black')

    s = init

    ema = make_ema(t, y, s=s)
    plt.plot(t, ema)

    #gradient descent loop
    for i in range(iters):
        dE = target_y - ema[target_x]
        error = dE**2

        dErr_dEma = 2*dE
        #dEma / ds
        dEma_dS = (y[target_x] - ema[target_x])*(t[target_x]-t[target_x-1])
        ds = rate * dErr_dEma * dEma_dS
        print(ema[target_x], dE, s,ds)
        s -= ds * 10.0
        ema = make_ema(t, y, s=s)
        plt.plot(t, ema)
    plt.show()
    
if __name__ == "__main__":
    #plot_one()
    plot_many()
