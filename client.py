import matplotlib.pyplot as plt
import numpy as np
import datetime
import random
import asyncio
import websockets
import requests
import json

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
def getData():
    url = "https://api.kraken.com/0/public/Trades?pair=DOGEUSD"
    r = requests.get(url)
    print(r.status_code)
    
    data = json.loads(r.text)
    return data

def toGraphFormat(data):
    data = data['result']['XDGUSD']
    print(len(data))
    
    data = [x[:3] for x in data] #strip off metadata
    data = [[x[2]] + x[0:2] for x in data] #move time to front
    data = [[x[0]] + list(map(float, x[1:])) for x in data] #to floats
    return data

data = None
if __name__ == "__main__":
    data = getData()
    data = toGraphFormat(data)
    data = processData(data)
    plots(data)
    #data = asyncio.get_event_loop().run_until_complete(getDataws())
