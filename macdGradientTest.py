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

def plot_profit_grad(seed=400, i_t_b=4000, i_t_s=6000, iters=40, rate=1000000):
    random.seed(seed)
    #t,y = genSignal()
    t = np.arange(10000)
    y = 1000.0*(-np.sin(t*(np.pi/5000)) + 2)
    plt.plot(t,y)

    #generate profit derivative
    dy = [0.0] + [a-b for a,b in zip(y[1:], y[:-1])]

    #profit initial state
    t_b = i_t_b
    t_s = i_t_s

    profit = y[t_s]/y[t_b]
    print(t_b, t_s, profit)

    dataset = [[t_b, t_s, profit]]

    #gradient descent loop
    for i in range(iters):
        #gradient descent profit func
        d_s = -profit*(dy[t_s]/y[t_s])
        d_b =  profit*(dy[t_b]/y[t_b])
        
        t_s -= int(rate*d_s)
        t_b -= int(rate*d_b)
        if len(y) <= t_s:
            t_s = len(y) - 1
        if t_b < 0:
            t_b = 0
        
        profit = y[t_s]/y[t_b]
        #print(t_b, t_s, profit)
        dataset.append([t_b, t_s, profit])

    #plot results
    buys = np.array(dataset)[:,0]
    sells = np.array(dataset)[:,1]

    p_b = np.array(list(map(lambda x: y[int(x)], buys)))
    p_s = np.array(list(map(lambda x: y[int(x)], sells)))
    
    plt.plot(buys, p_b, marker='o', color='red')
    plt.plot(sells, p_s, marker='o', color='blue')
    #plt.quiver(buys[:-1], p_b[:-1], buys[1:]-buys[:-1], p_b[1:]-p_b[:-1], scale_units='xy', angles='xy', scale=1)
    #plt.quiver(sells[:-1], p_s[:-1], sells[1:]-sells[:-1], p_s[1:]-p_s[:-1], scale_units='xy', angles='xy', scale=1)
    plt.quiver(buys[0], p_b[0], buys[-1]-buys[0], p_b[-1]-p_b[0], scale_units='xy', angles='xy', scale=1, width=0.01)
    plt.quiver(sells[0], p_s[0], sells[-1]-sells[0], p_s[-1]-p_s[0], scale_units='xy', angles='xy', scale=1, width=0.01)
    

    plt.show()
    
if __name__ == "__main__":
    #plot_one()
    #plot_many()
    plot_profit_grad()
