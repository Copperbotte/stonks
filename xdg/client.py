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

from xdg import processData, plots

from xdg import loadFile, loadData, saveFile, parseFile, clipFile

"""
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
"""

#rest connection
def getData(since=None):
    url = "https://api.kraken.com/0/public/Trades?pair=DOGEUSD"

    if since:
        url += '&since=' + since
    
    r = requests.get(url)
    print(r.status_code)
    
    data = json.loads(r.text)
    return data

#converts rest downloaded data into .csv formatted string:
#   ["unix time, dollar price, volume"]
def toCSVFormat(result):
    data = result['result']['XDGUSD']
    
    #convert data into storage format
    conv = [[int(x[2])] + x[0:2] for x in data] #rearrange
    conv = [list(map(str, x)) for x in conv]    #to string
    conv = [",".join(x) for x in conv]          #to csv
    return conv

#updates unprocessed data with remote data
def updateData(entries):
    if entries == None:
        return
    #valid file found and loaded

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
        
        conv = toCSVFormat(result)

        #merge with previous dataset
        entries += conv[offset:]

        #print new collected entries
        dc = len(conv[offset:])
        collection += dc
        print("updated", dc)

        #repeat until the final time is within 1 minute of the current time
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
    

def toGraphFormat(data):
    print("last", data['result']['last'])
    data = data['result']['XDGUSD']
    print(len(data))
    
    data = [x[:3] for x in data] #strip off metadata
    data = [[x[2]] + x[0:2] for x in data] #move time to front
    data = [[x[0]] + list(map(float, x[1:])) for x in data] #to floats
    return data

data = None
APIKey = None

trades = None
t_p = None

def latest(macdFast=51183.07765162355, macdSlow=68970.07412787144, macdLag=794140.9481321955):
    global data
    data = getData() #download new data
    data = toGraphFormat(data) #convert to loaded format
    data = processData(data) #process as if it were loaded data
    plots(data, macdFast, macdSlow, macdLag)

def fresh(days=48, macdFast=51183.07765162355, macdSlow=68970.07412787144, macdLag=794140.9481321955):
    global data
    entries = loadFile("XDGUSD.csv") #load data from file
    updateData(entries)              #download new data from remote server
    saveFile(entries, "XDGUSD.csv")  #save updated data to a file
    
    timefrom = datetime.datetime.today() - datetime.timedelta(days=days)
    timefrom = timefrom.timestamp()
    
    data = parseFile(entries)               #parse already loaded data
    data = clipFile(data, timefrom=timefrom)#Load, parse, clip are loadData().
    data = processData(data)                #convert to candles
    plots(data, macdFast, macdSlow, macdLag)#plot

if __name__ == "__main__":
    data = getData()
    data = toGraphFormat(data)
    data = processData(data)
    plots(data)
    #data = asyncio.get_event_loop().run_until_complete(getDataws())
