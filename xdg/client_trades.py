import matplotlib.pyplot as plt
import numpy as np
import datetime
import random
import asyncio
import websockets
import requests
import json
import hashlib
import hmac
import base64
import time
import urllib
import krakenex

#from graph import processData, plots

#from ..load import loadFile, loadData

#private methods
def callNonce(path="..\\..\\nonce.txt"):
    with open(path) as o:
        Nonce = int(o.read())
    with open(path, 'w') as o:
        o.write(str(Nonce + 1))
    return Nonce

def loadAPIKey(path="../../krakenKey.txt"):
    key = None
    with open(path) as o:
        key = o.read()
    return key

#actual functions
#https://support.kraken.com/hc/en-us/articles/360029054811-What-is-the-authentication-algorithm-for-private-endpoints-
def getActiveTrades(APIKey, otp):
    #private method
    #url = "https://api.kraken.com/0/private/OpenOrders"
    url = "https://api.kraken.com/0/private/OpenOrders"
    urlpath = url[len('https://api.kraken.com'):]
    
    seckey = base64.b64decode(loadAPIKey('..\\..\\krakenKeySecret.txt'))
    
    if True:

        print(base64.b64decode(seckey))
    
        #POST data
        POST = {
            #'nonce':str(callNonce()),
            'nonce':int(time.time()*1000),
            #'otp':otp
        }
        POSTstr = urllib.parse.urlencode(POST)
        #POSTstr = 'nonce='+str(POST['nonce']) + '&otp='+POST['otp']

        #sha256 encode
        sha_content = (str(POST['nonce']) + POSTstr).encode()
        sha256 = hashlib.sha256(sha_content)

        #hmac 512 encode
        hmac_content = urlpath.encode() + sha256.digest()
        
        APIhmac = hmac.new(base64.b64decode(seckey), hmac_content, hashlib.sha512)
        APISign = base64.b64encode(APIhmac.digest()).decode()
        
        Header = {'API-Key':APIkey, 'API-Sign':APISign}
        
        #send POST
        r = requests.Session()
        
        r = requests.post(url, data=POST, headers=Header)
        print(r.status_code)

        r.close()

        data = json.loads(r.text)
        print(data)

    #k = krakenex.API()
    #k.key = APIKey
    #k.secret = seckey
    #data = k.query_private('OpenOrders')
    #k.close()
    
    return data

#uses getActiveTrades to build a complete trade history, 50 at a time.
def getCompleteTradeHistory(n=637):
    returns = []

    k = krakenex.API()
    k.key = loadAPIKey()
    k.secret = loadAPIKey('..\\..\\krakenKeySecret.txt')
    for t in range(0, n, 50):
        data = k.query_private('TradesHistory', {'ofs':t})
        if len(data['error']) != 0:
            print(data['error'])
        else:
            data = data['result']
            trades = data['trades']
            print('collected #', t, 'with', len(trades.keys()), 'trades')

            time.sleep(3)

            returns.append(trades)
    k.close()

    return returns

#processes results of getCompleteTradeHistory to a sorted list of trades, by time.
def processTrades(data):
    #merge dicts
    merge = dict()
    for s in data:
        for k in s.keys():
            merge[k] = s[k]
    
    #to list
    l_d = []
    for k in merge.keys():
        l_d.append([k, merge[k]])
    #sort
    l_d.sort(key=lambda x: x[1]['time'])
    return l_d

#merges trades based on a time window.
def averageWindow(processed, window=30):
    out = []
    cur = None
    elements = 'time pair type price cost vol'.split(' ')
    for p in [x[1] for x in processed]:
        if cur == None:
            cur = dict()
            for e in elements:
                cur[e] = p[e]
            cur['cost'] = float(cur['cost'])
            cur['vol'] = float(cur['vol'])
            continue
        if (p['time'] - cur['time'] < window) and (p['pair'] == cur['pair']) and (p['type'] == cur['type']):
            #find average gains for cur and new
            cur['cost'] += float(p['cost'])
            cur['vol'] += float(p['vol'])
            cur['price'] = cur['cost']/cur['vol']
        else:
            out.append(cur)
            cur = dict()
            for e in elements:
                cur[e] = p[e]
            cur['cost'] = float(cur['cost'])
            cur['vol'] = float(cur['vol'])
    if cur != None:
        out.append(cur)
    return out

def genStats(data):
    buys = data[::2]
    sells = data[1::2]
    wins = 0
    losses = 0
    w_gains = []
    l_gains = []
    for b,s in zip(buys, sells):
        p_b = float(b['price'])
        p_s = float(s['price'])
        ratio = p_s / p_b
        if 1 < ratio: #winner
            wins += 1
            w_gains.append(ratio)
        else:
            losses += 1
            l_gains.append(ratio)
    #print(wins, losses)
    def safe_avg(gains):
        if 0 < len(gains):
            gains = np.average(gains)
        else:
            gains = 0
        return gains
    w_gains = np.exp(safe_avg(list(map(np.log, w_gains))))
    l_gains = np.exp(safe_avg(list(map(np.log, l_gains))))
    #print(w_gains)
    #print(l_gains)
    return wins/(wins+losses), losses/(wins+losses), w_gains, l_gains

def criterion(win=2.0, lose=0.5, pwin=1/3, plose=2/3):
    return plose/(1-win) + pwin/(1-lose)
def bankroll_game(win=2.0, lose=0.5, pwin=1/3, plose=2/3, bankroll=1):
    return np.power((win-1)*bankroll + 1, pwin)*np.power((lose-1)*bankroll + 1, plose)

data = None
APIKey = None

trades = None
t_p = None

if __name__ == "__main__":
    #APIKey = loadAPIKey()
    #updateData()
    
    trades = getCompleteTradeHistory()
    t_p = processTrades(trades)
    a_w = averageWindow(t_p, window=150)
    w, l, w_g, l_g = genStats(a_w[1:83])
    print('win pct:', w, 'lose pct:', l)
    print('win gains:', w_g, 'lose gains:', l_g)
    bankroll = criterion(win=w_g, lose=l_g, pwin=w, plose=l)
    avg_game = bankroll_game(win=w_g, lose=l_g, pwin=w, plose=l)
    bank_game = bankroll_game(win=w_g, lose=l_g, pwin=w, plose=l, bankroll=bankroll)
    print("bankroll:", bankroll, "avg gains:", bank_game, "typical gains:", avg_game)
