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

import xdg
import xdg.client

data = None
APIKey = None

trades = None
t_p = None

def latest(macdFast=51183.07765162355, macdSlow=68970.07412787144, macdLag=794140.9481321955):
    global data
    data = xdg.client.getData() #download new data
    data = xdg.client.toGraphFormat(data) #convert to loaded format
    data = xdg.processData(data) #process as if it were loaded data
    xdg.plots(data, macdFast, macdSlow, macdLag)

def fresh(days=48, macdFast=51183.07765162355, macdSlow=68970.07412787144, macdLag=794140.9481321955):
    global data
    entries = xdg.load.loadFile("XDGUSD.csv") #load data from file
    xdg.client.updateData(entries)              #download new data from remote server
    xdg.load.saveFile(entries, "XDGUSD.csv")  #save updated data to a file
    
    #timefrom = datetime.datetime.today() - datetime.timedelta(days=days)
    timefrom = datetime.datetime(2021, 4, 8)
    timefrom = timefrom.timestamp()
    
    data = xdg.load.parseFile(entries)               #parse already loaded data
    data = xdg.load.clipFile(data, timefrom=timefrom)#Load, parse, clip are loadData().
    data = xdg.load.processData(data)                #convert to candles
    xdg.plots(data, macdFast, macdSlow, macdLag)     #plot

if __name__ == "__main__":
    data = xdg.client.getData()
    data = xdg.client.toGraphFormat(data)
    data = xdg.load.processData(data)
    xdg.plots(data)
    #data = asyncio.get_event_loop().run_until_complete(getDataws())
