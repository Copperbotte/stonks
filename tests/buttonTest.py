import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import numpy as np
import time
import random

#simple button test
def simple_test():

    x = np.linspace(0,5,100)
    y = np.sin(x)
    
    line, = plt.plot(x, y)

    #create a new axis within this range
    axrange = plt.axes([0.7, 0.05, 0.1, 0.075])

    #create a button in that axis
    button = Button(axrange, 'Button')
    
    def update(event):
        print("Button pressed")
    button.on_clicked(update)
    
    plt.show()

#more complex button test, showing adjustable data.
def interactive():
    fig, ax = plt.subplots()
    
    x = np.linspace(0,1,100)
    line1, = ax.plot(x, x**1)
    
    axrange = plt.axes([0.7, 0.05, 0.1, 0.075])
    button = Button(axrange, 'Button')

    #use a class instead of just a func
    class thing:
        power = 1
        def update(self, event):
            self.power = self.power + 1

            #changing plot content
            line1.set_ydata(x**self.power)
            fig.canvas.draw()
            fig.canvas.flush_events()
    storage = thing()
    button.on_clicked(storage.update)
    
    plt.show()

def genstats(stats):
    def mean(stuff):
        return sum(stuff) / len(stuff)
    def stdev(stuff):
        m = mean(stuff)
        var = sum(map(lambda x: (x-m)**2, stuff)) / (len(stuff) - 1)
        return np.sqrt(var)
    def gauss(x, off, sigma):
        return np.exp(-((x-off)/sigma)**2) / (sigma * np.sqrt(np.pi))
    def bellcurve(stuff, name="", v=0):
        m = mean(stuff)
        std = stdev(stuff)
        left = min(stuff) - std
        right = max(stuff) + std

        color = 'C%d'%(v)

        if std == 0:
            plt.axvline(m, label=name, color=color)
            plt.annotate("Mean:%.3f\nStdev:%.3f"%(m, std), xy=(m, gauss(m, m, std)))
            return

        x = np.linspace(left, right, 1000)
        y = gauss(x, m, std)
        randy = [random.random() * gauss(i, m, std) for i in stuff]
        plt.scatter(stuff, randy, color=color)
        plt.plot(x,y, label=name, color=color)
        plt.annotate("Mean:%.3f\nStdev:%.3f"%(m, std), xy=(m, gauss(m, m, std)))
        #plt.show()

    for v,k in enumerate(stats.keys()):
        bellcurve(stats[k], k, v)
    plt.legend()
    plt.show()

def interactive2():
    fig, ax = plt.subplots()

    stats = dict()

    def deltime(t, name=""):
        t2 = time.time()
        dt = t2-t
        #print(name.rjust(16), dt)

        if name not in stats.keys():
            stats[name] = []
        stats[name].append(dt)
        
        return time.time()
    
    class thing:
        line1 = None
        fig = None
        n = 100000
        dx = 1/n
        x = np.linspace(0,1,n)
        y = np.sin(x)
        def update(self, event):
            t = time.time()
            
            nx = self.x[-1] + self.dx
            t = deltime(t, "new x")
            ny = np.sin(nx)
            t = deltime(t, "new y")

            self.x = np.append(self.x, nx)
            t = deltime(t, "append x")
            self.y = np.append(self.y, ny)
            t = deltime(t, "append y")

            self.line1.set_xdata(self.x)
            t = deltime(t, "set x")
            self.line1.set_ydata(self.y)
            t = deltime(t, "set y")

            self.fig.canvas.draw()
            t = deltime(t, "draw")
            self.fig.canvas.flush_events()
            t = deltime(t, "flush events")

            #print('test')

    storage = thing()
    line1, = ax.plot(storage.x, storage.y)
    
    axrange = plt.axes([0.7, 0.00, 0.1, 0.05])
    button = Button(axrange, 'Button')

    storage.line1 = line1
    storage.fig = fig
    button.on_clicked(storage.update)
    plt.show()

    genstats(stats)
    
    #return stats

if __name__ == "__main__":
    #simple_test()
    #interactive()
    interactive2()
