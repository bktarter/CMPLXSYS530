from IPython import display
import networkx as nx
import time
import numpy as np
import random
import pandas as pd
import math

# pick = which tracker
pick = 1

def initialize(trackerSheet):
  global g, nextg, prev

  if trackerSheet == 1:
    df = pd.read_excel('California Almond Tracker.xlsx', usecols='A:AA')
  if trackerSheet == 2:
    df = pd.read_excel('California County List.xlsx',usecols="A:AA")
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

  nx.draw(g,pos,node_size=10,node_color='b', edge_color='r')
  
  #list of attributes
  #1) initial fire
  #2) fire probability
  #3) Dairy Yield
  #4) Almond Yield
  #5) Grape Yield
  #6) Pistachio Yield
  #7) Cattle Yield
  #8) Lettuce Yield
  #9) Strawberry Yield
  #10) Tomato Yield
  #11) Walnut Yield

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
  maxCommodityYield['maxlettuceYeild'] = 0
  maxCommodityYield['maxstrawberryYield'] = 0
  maxCommodityYield['maxtomatoYield'] = 0
  maxCommodityYield['maxwalnutYield'] = 0
  
  #Capacity is determined by Node with Max Yield in any Commodity

  fireProb = df['Observed Fire Prob']
  #fireProb = df['Predicted Fire Prob']
  
  if trackerSheet ==1:
     attributes = {i: {'onFire':0 ,
                      'firstFire':False,
                      'almondYield':df['Almond Yield (tons/ac)'][i],
                      } for i in g.nodes()}
     nx.set_node_attributes(g,attributes)

  if trackerSheet == 2:
    attributes = {i: {'onFire':0 ,
                      'firstFire':False,
                      'fireProb':fireProb[i],
                      'dairyYield':df['Dairy Yield'][i],
                      'almondYield':df['Almond Yield'][i],
                      'grapeYield':df['Grape Yield'][i],
                      'pistachioYield':df['Pistachio Yield'][i],
                      'cattleYield':df['Cattle Yield'][i], 
                      'lettuceYield':df['Lettuce Yield'][i],
                      'strawberryYield':df['Strawberry Yield'][i],
                      'tomatoYield':df['Tomato Yield'][i],
                      'walnutYield':df['Walnut Yield'][i]} for i in g.nodes()}
	
  #set maxCommodityYields
  for node in range(len(Nodes)):
       for attributes in g.nodes[node]:
         if attributes != 'pos':
           if attributes != 'onFire':
             if attributes != 'firstFire':
              att = 'max' + attributes
              if g.nodes[node][attributes] > maxCommodityYield[att]:
                maxCommodityYield[att] = g.nodes[node][attributes]

  

def update():
    global g, nextg, stable, failure,totFail
    
    # Update network model
    curprev = 0
    nextg = g.copy()
    nextg.pos = g.pos

    for a in g.nodes:
      if g.nodes[a]['onFire'] == False : #able to catch on fire
        nextg.nodes[a]['OnFire'] = False
        
      for b in g.neighbors(a):
        if g.nodes[b]['onFire'] == True and g.nodes[b]['firstFire'] == True: # if neighbor b is on Fire
          nextg.nodes[a]['onFire']  = 1
      
    g = nextg.copy()
    g.pos = nextg.pos

def observe():
    global g, prev, prev_mf, susc_mf
    cla()
    nx.draw(g, cmap = cm.plasma, vmin = 0, vmax = 2,
            node_color = [g.nodes[i]['state'] for i in g.nodes],
            pos = g.pos)
    x = 'beta:' + str(beta)
    plt.title(x)
    plt.show()

initialize(pick)