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
# fireMode = 1) Predicted 2)Observed
pick = 2
fireMode = 2

# global parameters
firePeriod = 2
rebornPeriod = 17 # how many months to reborn

def initialize(trackerSheet,fireModel):
  global g, nextg, prices, maxCommodityYield, pos, test, df, fireMode,labelDict

  if trackerSheet == 1:
    df = pd.read_excel('CaliforniaAlmondTracker.xlsx', usecols='A:AA')
  if trackerSheet == 2:
    df = pd.read_excel('CaliforniaCountyList.xlsx',usecols="A:AA")
  
  g = nx.Graph()

  Nodes = list(range(len(df['Latitude']))) # number of counties (58)
  pos = {}
  labelDict = {}
  R = 6371 # for conversion from lon/lat to cartercian
  for i in range(len(Nodes)):
    pos[Nodes[i]] = (df['Longitude'][i],df['Latitude'][i])
    labelDict[Nodes[i]] = (df['County'][i])
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
  if fireModel == 1: fireProb = df['ObservedfireProb']
  if fireModel == 2: fireProb = df['PredictedfireProb']
  fireprob = np.array(fireProb) / np.sum(np.array(fireProb))
  
  if trackerSheet ==1:
     attributes = {i: {'onFire':0 ,
                      'firstFire':False,
                      'fireProb':fireProb[i],
                      'fireDuration':0 ,
                      'rebornDuration': 0,
                      'almondYield':df['almondYield'][i],
                      } for i in g.nodes()}

  if trackerSheet == 2:
    attributes = {i: {'onFire':0 ,
                      'firstFire':False,
                      'fireProb':fireProb[i],
                      'fireDuration':0 ,
                      'rebornDuration': 0,
                      'Destroyed': False,
                      #'dairyYield':df['Dairy Yield'][i], # removed from sheet
                      'almondYield':df['almondYield'][i], 
                      'grapeYield':df['grapeYield'][i],
                      'pistachioYield':df['pistachioYield'][i],
                      'cattleYield':df['cattleYield'][i], 
                      'lettuceYield':df['lettuceYield'][i],
                      'strawberryYield':df['strawberryYield'][i],
                      'tomatoYield':df['tomatoYield'][i],
                      'walnutYield':df['walnutYield'][i]} for i in g.nodes()}
    
  nx.set_node_attributes(g,attributes)
	
  #set maxCommodityYields
  for node in range(len(Nodes)):
       for attributes in g.nodes[node]:
         if attributes != 'pos' and attributes != 'onFire' and attributes != 'firstFire' and attributes != 'fireProb' and attributes != 'rebornDuration' and attributes != 'fireDuration' and attributes != 'Destroyed':
              att = 'max' + attributes
              if g.nodes[node][attributes] > maxCommodityYield[att]:
                maxCommodityYield[att] = g.nodes[node][attributes]
  
  #where to start first fire
  initialFire_index = 10
  g.nodes[initialFire_index]['onFire'] = 1
  g.nodes[initialFire_index]['Destroyed'] = True
  g.nodes[initialFire_index]['firstFire'] = True
  g.nodes[initialFire_index]['fireDuration'] = firePeriod
  g.nodes[initialFire_index]['rebornDuration'] = firePeriod + rebornPeriod
  for attributes in g.nodes[initialFire_index]:
    if attributes != 'pos' and attributes != 'onFire' and attributes != 'firstFire' and attributes != ' fireProb' and attributes != 'fireDuration' and attributes != 'rebornDuration' and attributes != 'Destroyed':
      g.nodes[initialFire_index][attributes] = 0
  
def update():
    global g, nextg, pos, test,df, fireMode
    print(g.nodes[10])
    # Update network model
    nextg = g.copy()
    #nextg.pos = g.pos

    for a in g.nodes:

      if g.nodes[a]['firstFire'] == True and g.nodes[a]['fireDuration'] == 1: #able to catch on fire
        nextg.nodes[a]['firstFire'] = False
        for b in g.neighbors(a):
          nextg.nodes[b]['onFire']  = 1
          nextg.nodes[b]['fireDuration']  = firePeriod
          nextg.nodes[b]['rebornDuration']  = rebornPeriod + firePeriod
          nextg.nodes[b]['Destroyed'] = True

      if g.nodes[a]['onFire'] == 1 and g.nodes[a]['fireDuration'] >= 1:
        nextg.nodes[a]['fireDuration']  = g.nodes[a]['fireDuration'] - 1

      if g.nodes[a]['onFire'] == 1 and g.nodes[a]['fireDuration'] == 0:
        nextg.nodes[a]['onFire'] = 0

      if g.nodes[a]['rebornDuration'] > 0:
        nextg.nodes[a]['rebornDuration'] = g.nodes[a]['rebornDuration'] - 1
        if g.nodes[a]['rebornDuration'] == 1:
          for attributes in g.nodes[a]:
            if attributes != 'pos' and attributes != 'onFire' and attributes != 'firstFire' and attributes != 'fireDuration' and attributes != 'rebornDuration' and attributes != 'Destroyed':
              #reassign fire probability when farm is reborn
              if attributes == 'fireProb' and fireMode == 1:
                attributes = 'Predicted' + attributes
              if attributes == 'fireProb' and fireMode == 2:
                attributes = 'Observed' + attributes

              nextg.nodes[a][attributes] = df[attributes][a]

    ###############################################################   reallocate   ####################################################
    cattleYield_destroyed = 0
    almondYield_destroyed = 0
    almondValue = np.array([])
    almondIndex = np.array([])
    cattleValue = np.array([])
    cattleIndex = np.array([])


    for a in g.nodes:
      if nextg.nodes[a]['Destroyed'] == False:
        almondValue = np.append(almondValue, nextg.nodes[a]['almondYield'])
        almondIndex = np.append(almondIndex, a)
        cattleValue = np.append(cattleValue, nextg.nodes[a]['cattleYield'])
        cattleIndex = np.append(cattleIndex, a)

    top4_index_almond = almondIndex[np.argpartition(almondValue, -4)[-4:]].astype(int)
    top4_index_cattle = cattleIndex[np.argpartition(cattleValue, -4)[-4:]].astype(int)
    top4_yield_almond = almondValue[np.argpartition(almondValue, -4)[-4:]]
    top4_yield_cattle = cattleValue[np.argpartition(cattleValue, -4)[-4:]]

    for a in g.nodes:
      if g.nodes[a]['Destroyed'] == True:
        nextg.nodes[a]['Destroyed'] = False

      if nextg.nodes[a]['Destroyed'] == True:
        cattleYield_destroyed = cattleYield_destroyed + g.nodes[a]['cattleYield']
        almondYield_destroyed = almondYield_destroyed + g.nodes[a]['almondYield']
        nextg.nodes[a]['cattleYield'] = 0
        nextg.nodes[a]['almondYield'] = 0

    for a in range(4):
      nextg.nodes[top4_index_almond[a]]['almondYield'] += almondYield_destroyed * top4_yield_almond[a]/  (np.sum(top4_yield_almond))
      nextg.nodes[top4_index_cattle[a]]['cattleYield'] += cattleYield_destroyed * top4_yield_cattle[a]/  (np.sum(top4_yield_cattle))
    ######################################################### reallocate end #######################################################
   
    g = nextg.copy()
    #test.append(g.nodes[53]['cattleYield'])
    test.append(almondYield_destroyed)

def observe(time):
    global g, nextg, prices, maxCommodityYield, firePeriod, rebornPeriod, pos,labelDict

    colorGrad = firePeriod + rebornPeriod
    cla()
    nx.draw(g, cmap = cm.plasma, vmin = 0, vmax = 2,
            node_color = [(g.nodes[i]['onFire']+g.nodes[i]['rebornDuration'])/colorGrad for i in g.nodes],
            pos = pos, labels = labelDict, with_labels = True)
    x = 'timestep:' + str(time)
    plt.title(x)
    plt.show()

test = [] 

initialize(pick,fireMode)
for i in range(100):
  update()
  #plt.show() #show every step
  if i%10==0: 
    observe(i) #show the plot every 10 steps

print(test)