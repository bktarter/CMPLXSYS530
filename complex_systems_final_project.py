from pylab import *
from IPython import display
import networkx as nx
import time
import numpy as np
import random
import pandas as pd
import math
import matplotlib.pyplot as plt

# pick = which tracker
pick = 2

# global parameters
firePeriod = 2
rebornPeriod = 60

def initialize(trackerSheet):
  global g, nextg, prices, maxCommodityYield, pos, test, df

  if trackerSheet == 1:
    df = pd.read_excel('CaliforniaAlmondTracker.xlsx', usecols='A:AA')
  if trackerSheet == 2:
    df = pd.read_excel('CaliforniaCountyList.xlsx',usecols="A:AA")
  
  g = nx.Graph()

  Nodes = list(range(len(df['Latitude']))) # number of counties (58)
  pos = {}
  R = 6371 # for conversion from lon/lat to cartercian
  for i in range(len(Nodes)):
    pos[Nodes[i]] = (df['Longitude'][i],df['Latitude'][i])
    g.add_node(Nodes[i],pos=pos[i])
  
  for node in Nodes:
    borderList = []
    strToNum = ''
    i = 0
    for char in df['borders'][node]:
      i+=1
      if char != ',':
        strToNum += char
      if(char == ',' or i == len(df['borders'][node])):
        borderList.append(int(strToNum))
        strToNum = ''
    #print('Node:',node ,'borderList:',borderList)
    for county in borderList:
      e = (node,county-1) #when counted counties are listed 1-58 vs Node list 0-57
      g.add_edge(*e)

  #All data gathered is from 2020
  #https://www.cdfa.ca.gov/Statistics/PDFs/2020_Ag_Stats_Review.pdf
  # $/lb
  prices = {}
  prices['dairyPrice'] = 0.1578
  prices['almondPrice'] = 2.43
  prices['grapePrice'] = 0.423
  prices['pistachiosPrice'] = 2.62
  prices['cattlePrice'] = 1899.75 #price per head (slaughtered)
  prices['lettucePrice'] = 0.329
  prices['strawberryPrice'] = 1.08
  prices['tomatoPrice'] = 0.051
  prices['walnutPrice'] = 0.985

  maxCommodityYield = {}
  maxCommodityYield['maxdairyYield'] = 0
  maxCommodityYield['maxalmondYield'] = 0
  maxCommodityYield['maxgrapeYield'] = 0
  maxCommodityYield['maxpistachioYield'] = 0
  maxCommodityYield['maxcattleYield'] = 0
  maxCommodityYield['maxlettuceYield'] = 0
  maxCommodityYield['maxstrawberryYield'] = 0
  maxCommodityYield['maxtomatoYield'] = 0
  maxCommodityYield['maxwalnutYield'] = 0
  
  #crop yield should be tons/acre
  
  #Capacity is determined by Node with Max Yield in any Commodity

  #fireProb = df['Observed Fire Prob']
  fireProb = df['Predicted Fire Prob']
  fireprob = np.array(fireProb) / np.sum(np.array(fireProb))
  
  if trackerSheet ==1:
     attributes = {i: {'onFire':0 ,
                      'firstFire':False,
                      'fireProb':fireProb[i],
                      'almondYield':df['Almond Yield (tons/ac)'][i],
                      } for i in g.nodes()}

  if trackerSheet == 2:
    attributes = {i: {'onFire':0 ,
                      'firstFire':False,
                      'fireProb':fireProb[i],
                      'fireDuration':0 ,
                      'rebornDuration': 0,
                      #'dairyYield':df['Dairy Yield'][i], # removed from sheet
                      'almondYield':df['Almond Yield'][i], 
                      'grapeYield':df['Grape Yield'][i],
                      'pistachioYield':df['Pistachio Yield'][i],
                      'cattleYield':df['Cattle Yield'][i], 
                      'lettuceYield':df['Lettuce Yield'][i],
                      'strawberryYield':df['Strawberry Yield'][i],
                      'tomatoYield':df['Tomato Yield'][i],
                      'walnutYield':df['Walnut Yield'][i]} for i in g.nodes()}
    
  nx.set_node_attributes(g,attributes)
	
  #set maxCommodityYields
  for node in range(len(Nodes)):
       for attributes in g.nodes[node]:
         if attributes != 'pos' and attributes != 'onFire' and attributes != 'firstFire' and attributes != 'fireProb' and attributes != 'rebornDuration' and attributes != 'fireDuration':
              att = 'max' + attributes
              if g.nodes[node][attributes] > maxCommodityYield[att]:
                maxCommodityYield[att] = g.nodes[node][attributes]
  
  #where to start first fire
  initialFire_index = 10
  g.nodes[initialFire_index]['onFire'] = 1
  g.nodes[initialFire_index]['firstFire'] = True
  g.nodes[initialFire_index]['fireDuration'] = firePeriod
  g.nodes[initialFire_index]['rebornDuration'] = firePeriod + rebornPeriod
  for attributes in g.nodes[initialFire_index]:
    if attributes != 'pos' and attributes != 'onFire' and attributes != 'firstFire' and attributes != 'fireDuration' and attributes != 'rebornDuration':
      g.nodes[initialFire_index][attributes] = 0
  
def update():
    global g, nextg, pos, test,df
    
    # Update network model
    curprev = 0
    nextg = g.copy()
    #nextg.pos = g.pos

    for a in g.nodes:
      if g.nodes[a]['firstFire'] == True and g.nodes[a]['fireDuration'] == 1: #able to catch on fire
        nextg.nodes[a]['firstFire'] == False
        for b in g.neighbors(a):
          nextg.nodes[b]['onFire']  = 1
          nextg.nodes[b]['fireDuration']  = firePeriod
          nextg.nodes[b]['rebornDuration']  = rebornPeriod + firePeriod

      if g.nodes[a]['onFire'] == 1 and g.nodes[a]['fireDuration'] >= 1:
        nextg.nodes[a]['fireDuration']  = g.nodes[a]['fireDuration'] - 1

      if g.nodes[a]['onFire'] == 1 and g.nodes[a]['fireDuration'] == 0:
        nextg.nodes[a]['onFire'] = 0

      if g.nodes[a]['rebornDuration'] > 0:
        nextg.nodes[a]['rebornDuration'] = g.nodes[a]['rebornDuration'] - 1
        if g.nodes[a]['rebornDuration'] == 1:
          #nextg.nodes[a]['cattleYield'] = df['Cattle Yield'][a]
          for attributes in g.nodes[a]:
            if attributes != 'onFire' and attributes != 'firstFire' and attributes != 'fireDuration' and attributes != 'rebornDuration':
              nextg.nodes[a][attributes] = df[attributes][a]
      
    g = nextg.copy()
    test.append(g.nodes[12]['cattleYield'])
    #g.pos = nextg.pos

def observe():
    global g, nextg, prices, maxCommodityYield
    cla()
    nx.draw(g, cmap = cm.plasma, vmin = 0, vmax = 2,
            node_color = [(g.nodes[i]['onFire']+g.nodes[i]['rebornDuration'])/62 for i in g.nodes],
            pos = pos)
    x = 'beta:' + str(beta)
    plt.title(x)
    plt.show()

# initialize(pick)
# update()
# observe()

test = [] 

initialize(pick)
observe()
plt.show()
for i in range(10):
  update()
  observe()
  plt.show() #show every step
  # if i%10==0: plt.show() #show the plot every 10 steps

plt.plot(test)
plt.show()
