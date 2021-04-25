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

from graph import processData, plots

#websocket connection
async def getDataws():
    url = "https://api.kraken.com/0/public/Trades?pair=DOGEUSD"
    
    data = None
    async with websockets.connect(url) as web:
            data = await web.recv()
            print(data)
            
            await web.send('wss://api.kraken.com/pair=DOGEUSD')
            data = await web.recv()
            print(type(data))
            print(len(data))
            print(data[:512])
    return data

#rest connection
def getData(since=None):
    url = "https://api.kraken.com/0/public/Trades?pair=DOGEUSD"

    if since:
        url += '&since=' + since
    
    r = requests.get(url)
    print(r.status_code)
    
    data = json.loads(r.text)
    return data

#updates current .csv file to match remote data
def updateData(path="XDGUSD.csv"):
    R = None
    #read file
    with open(path, 'r') as o:
        R = o.read()
    if R == None:
        return
    #valid file found
    entries = R.split('\n')
    entries = list(filter(None, entries))

    collection = 0

    #loop until data is fully updated
    while True:
        #find first entry with latest time
        final = entries[-1].split(',')
        offset = 0
        for i in range(1000):
            test = entries[-1 - i].split(',')
            if int(test[0]) != int(final[0]):
                #print("broke at", i)
                offset = i
                break
            final = test
        
        #get next batch of data
        result = getData(since=final[0])
        if result['error']:
            print("error:", result['error'])

        data = result['result']['XDGUSD']
        

        #convert data into storage format
        conv = [[int(x[2])] + x[0:2] for x in data] #rearrange
        conv = [list(map(str, x)) for x in conv]    #to string
        conv = [",".join(x) for x in conv]          #to csv

        #merge with previous dataset
        entries += conv[offset:]
        dc = len(conv[offset:])
        collection += dc
        print("updated", dc)

        #repeat until the final time is within 5 minutes of the current time
        latest = float(result['result']['last']) / 1e9
        dt = time.time() - latest

        #display current time behind
        ddate = datetime.timedelta(seconds=dt)
        days = ddate.days
        hours, mins = divmod(ddate.seconds, 3600)
        mins, secs = divmod(mins, 60)
        
        print("time behind: %s days, %s hours, %s minutes, %s seconds" % (days, hours, mins, secs))
        if dt < 60:
            break

        #prevent a timeout
        time.sleep(3)

    print("updated a total of", collection, "entries")
    with open(path, "w") as o:
        for e in entries:
            o.write(e + '\n')

def toGraphFormat(data):
    print("last", data['result']['last'])
    data = data['result']['XDGUSD']
    print(len(data))
    
    data = [x[:3] for x in data] #strip off metadata
    data = [[x[2]] + x[0:2] for x in data] #move time to front
    data = [[x[0]] + list(map(float, x[1:])) for x in data] #to floats
    return data


#private methods
def callNonce(path="nonce.txt"):
    with open(path) as o:
        Nonce = int(o.read())
    with open(path, 'w') as o:
        o.write(str(Nonce + 1))
    return Nonce

def loadAPIKey(path="krakenKey.txt"):
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
    
    seckey = base64.b64decode(loadAPIKey('krakenKeySecret.txt'))
    
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
    k.secret = loadAPIKey('krakenKeySecret.txt')
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
def processData(data):
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
    APIKey = loadAPIKey()
    trades = getCompleteTradeHistory()
    t_p = processData(trades)
    a_w = averageWindow(t_p, window=150)
    w, l, w_g, l_g = genStats(a_w[1:83])
    print('win pct:', w, 'lose pct:', l)
    print('win gains:', w_g, 'lose gains:', l_g)
    bankroll = criterion(win=w_g, lose=l_g, pwin=w, plose=l)
    avg_game = bankroll_game(win=w_g, lose=l_g, pwin=w, plose=l)
    bank_game = bankroll_game(win=w_g, lose=l_g, pwin=w, plose=l, bankroll=bankroll)
    print("bankroll:", bankroll, "avg gains:", bank_game, "typical gains:", avg_game)
    
    #trades = getActiveTrades(APIKey, '474123')
    #print(trades)
    #data = getData()
    #data = toGraphFormat(data)
    #data = processData(data)
    #plots(data)
    #data = asyncio.get_event_loop().run_until_complete(getDataws())
