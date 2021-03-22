import matplotlib.pyplot as plt
import numpy as np

data = None

with open("XDGUSD.csv", 'r') as o:
    text = o.read()
    lines = text.split('\n')[:-1] #exclude empty line at the end
    data = [list(map(float, L.split(','))) for L in lines]

    #split xy coords
    p = np.array(data)
    x,y = p[:,0], p[:,1]

    #plot
    plt.plot(x,y)
    plt.show()
    
    
