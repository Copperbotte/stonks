import numpy as np
import random

from .process import make_log, make_ema, find_profit, compute_Macd

def computeMacdProfit(data, macdFast=3600*24*7, macdSlow=3600*24*7*4, macdLag=3600*24*7):
    times, prices, _,_,_,_, macd = compute_Macd(data, macdFast=macdFast, macdSlow=macdSlow, macdLag=macdLag)
    _,_,c_pct,_,br,s_pct = find_profit(times, prices, macd)
    return s_pct, br
    

def randomWalk(data, macdFast=3600*24*7, macdSlow=3600*24*7*4, macdLag=3600*24*7, sigma=0.1):
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

    attempts = 0

    while True:
        #mutate new parameters
        l_mdf_test = l_mdf + invgauss(sigma)
        l_mds_test = l_mds + invgauss(sigma)
        l_mdl_test = l_mdl + invgauss(sigma)

        #swap fast and slow if slow is less than fast
        if l_mds_test < l_mdf_test:
            temp = l_mdf_test
            l_mdf_test = l_mds_test
            l_mds_test = temp

        #compute test result
        profit_test, br = computeMacdProfit(data, macdFast=np.exp(l_mdf_test), macdSlow=np.exp(l_mds_test), macdLag=np.exp(l_mdl_test))
        attempts += 1
        
        #replace if better
        if profit < profit_test:
            l_mdf = l_mdf_test
            l_mds = l_mds_test
            l_mdl = l_mdl_test
            profit = profit_test
            print("macdFast="+str(np.exp(l_mdf))+',', "macdSlow="+str(np.exp(l_mds))+',', "macdLag="+str(np.exp(l_mdl)), "profit:", profit, "bankroll:", br)
            print("attempts:", attempts)
            attempts = 0
    
def nelderMead(data, macdFast=3600*24*7, macdSlow=3600*24*7*4, macdLag=3600*24*7, shrink=0.5, expand=2.0):
    #nelder-mead optimization, starting with an orthogonal set of vertices, log(param) + 1 per parameter
    #walks are performed in log space
    l_mdf = np.log(macdFast)
    l_mds = np.log(macdSlow)
    l_mdl = np.log(macdLag)

    #build simplex
    verts =     [[0, l_mdf,    l_mds,    l_mdl]]
    verts.append([0, l_mdf+0.1,l_mds,    l_mdl])
    verts.append([0, l_mdf,    l_mds-0.1,l_mdl])
    verts.append([0, l_mdf,    l_mds,    l_mdl+0.1])
    
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
