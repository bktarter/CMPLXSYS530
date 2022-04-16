from pylab import *
from IPython import display
import networkx as nx
import numpy as np
import random
import pandas as pd
import math
import matplotlib.pyplot as plt

def initialize(fireModel):
  global g, nextg, prices, maxCommodityYield, pos,OutputAllCounties, df, fireMode,labelDict

  
  df = pd.read_excel('CaliforniaAlmondTracker.xlsx', usecols='A:AA')

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
  prices['almondPrice'] = 2.43


  maxCommodityYield = {}
  maxCommodityYield['maxalmondYield'] = 3.06
  
  
  #crop yield should be tons/acre
  #output is by the ton
  
  #Capacity is determined by Node with Max Yield in any Commodity
  if fireModel == 1: fireProb = df['PredictedfireProb']
  if fireModel == 2: fireProb = df['ObservedfireProb']
  

  attributes = {i: {'onFire':0 ,
                   'firstFire':False,
                   'fireProb':fireProb[i],
                   'fireDuration':0 ,
                   'rebornDuration': 0,
                   'Destroyed': False,
                   'BeyondYield': False,
                   'almondOutput':df['almondOutput'][i],
                   'almondAcreage':df['Almond Acreage'][i],
                   'almondOutputMax': 0,
                   'almondYield':df['almondYield'][i],
                   } for i in g.nodes()}
 
  nx.set_node_attributes(g,attributes)
  
def update(itter):
    global g, nextg, pos, OutputAllCounties ,df, fireMode, maxCommodityYield, prices, YieldCap
    # Update network model
    nextg = g.copy()
    #YieldCap = maxCommodityYield['maxalmondYield']
    for a in g.nodes:
       ######################################################### update maxyield ##########################
      if itter % 12 == 0 and itter != 0:
        YieldCap *= 1.0147

       ######################################################## end update maxyield ######################### 
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
            if attributes != 'pos' and attributes != 'onFire' and attributes != 'firstFire' and attributes != 'fireDuration' and attributes != 'rebornDuration' and attributes != 'Destroyed' and attributes != 'BeyondYield':
              #reassign fire probability when farm is reborn
              if attributes == 'fireProb' and fireMode == 1:
                attributes = 'Predicted' + attributes
              if attributes == 'fireProb' and fireMode == 2:
                attributes = 'Observed' + attributes

          nextg.nodes[a]['almondOutput'] = g.nodes[a]['almondOutputMax']
      if g.nodes[a]['almondOutputMax'] < g.nodes[a]['almondOutput']:
        nextg.nodes[a]['almondOutputMax'] = g.nodes[a]['almondOutput']

    ###############################################################   reallocate   ####################################################
    almond_destroyed = 0
    for a in g.nodes:
      if g.nodes[a]['Destroyed'] == True:
        nextg.nodes[a]['Destroyed'] = False

      if nextg.nodes[a]['Destroyed'] == True:
        almond_destroyed = almond_destroyed + g.nodes[a]['almondOutput']
        nextg.nodes[a]['almondOutput'] = 0
      if nextg.nodes[a]['almondAcreage']!=0 and nextg.nodes[a]['almondOutput']/nextg.nodes[a]['almondAcreage'] > YieldCap:
        nextg.nodes[a]['BeyondYield'] = False

    while True:
      top4_index_almond, top4_output_almond, num = Top4()
      if num == 0:
        print('Destroyed output exceeds the total yield cap')
        break
      Reallocate(top4_index_almond, top4_output_almond, almond_destroyed, num)
      almond_destroyed = 0
      flag = 0
      for a in range(num):
        if nextg.nodes[top4_index_almond[a]]['almondOutput']/nextg.nodes[top4_index_almond[a]]['almondAcreage'] > YieldCap:
          almond_destroyed += nextg.nodes[top4_index_almond[a]]['almondOutput'] - nextg.nodes[top4_index_almond[a]]['almondAcreage'] * YieldCap
          nextg.nodes[top4_index_almond[a]]['almondOutput'] = nextg.nodes[top4_index_almond[a]]['almondAcreage'] * YieldCap
          nextg.nodes[top4_index_almond[a]]['BeyondYield'] = True
          flag += 1
      if flag == 0:
        break
    ######################################################### reallocate end #######################################################
    
    ######################################################### price track start ####################################################
    almondPrice = prices['almondPrice']
    totalOutput = 0
    newTotalOutput = 0 
    
    for a in g.nodes():
      if g.nodes[a]['almondOutput'] > 0 and g.nodes[a]['almondOutput'] != 'nan':
        totalOutput += g.nodes[a]['almondOutput']
      
    for a in nextg.nodes():
      if nextg.nodes[a]['almondOutput'] > 0 and nextg.nodes[a]['almondOutput'] != 'nan':
        newTotalOutput += nextg.nodes[a]['almondOutput']

    divisor = totalOutput
    if divisor == 0: # prevents division by zero
      divisor = 1

    slowConverge = 0.4
    change = (newTotalOutput-totalOutput)/divisor
    
    if change > -0.5:
      if change > 2:
        print('spike change, itter:',itter)
        almondPrice /= 2
      else:
        change*= slowConverge
        almondPrice -= almondPrice*change # normal behavior
    if change < -0.25:
      print('change:', change, 'itter:', itter)
      almondPrice*= -10*change #if all crops burn price increases 10x
      print('new almond price:', almondPrice)

    if almondPrice <= 0:
      almondPrice = 0.01

    if itter > 0 and itter % 12 == 0: #not time step 0 & 12 months have passed
      almondPrice *= 1.02 #account for inflation

    priceOverTime.append(almondPrice)
    prices['almondPrice']= almondPrice
    ######################################################### price track end ######################################################


    g = nextg.copy()
    for a in g.nodes:
      OutputAllCounties[a,itter] = g.nodes[a]['almondOutput']

    fireStart(itter)

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

def fireStart(month):
  global g, df, fireMode
  if 5< month % 12 < 9:
    for a in g.nodes:
      fireRoll = random.random()
      
      if g.nodes[a]['rebornDuration'] == 0 and g.nodes[a]['fireProb'] > fireRoll:
        g.nodes[a]['onFire'] = 1
        g.nodes[a]['firstFire'] = True
        g.nodes[a]['fireDuration'] = firePeriod
        g.nodes[a]['rebornDuration'] = firePeriod + rebornPeriod
        g.nodes[a]['destroyed'] = True
        for attributes in g.nodes[a]:
          if attributes != 'pos' and attributes != 'fireProb' and attributes != 'onFire' and attributes != 'firstFire' and attributes != 'fireDuration' and attributes != 'rebornDuration':
            g.nodes[a][attributes] = 0
  
def Top4():
  global g, nextg

  almondValue = np.array([])
  almondIndex = np.array([])
  for a in g.nodes:
    if nextg.nodes[a]['Destroyed'] == False and g.nodes[a]['almondAcreage'] != 0 and nextg.nodes[a]['BeyondYield'] == False:
      if g.nodes[a]['almondOutput']/g.nodes[a]['almondAcreage'] <= YieldCap:
        almondValue = np.append(almondValue, nextg.nodes[a]['almondOutput'])
        almondIndex = np.append(almondIndex, a)
  if np.shape(almondValue)[0] >= 4:
    top4_index_almond = almondIndex[np.argpartition(almondValue, -4)[-4:]].astype(int)
    top4_output_almond = almondValue[np.argpartition(almondValue, -4)[-4:]]
    return top4_index_almond, top4_output_almond,4
  else:
    top4_index_almond = almondIndex
    top4_output_almond = almondValue
    return top4_index_almond, top4_output_almond,np.shape(almondValue)[0]

def Reallocate(top4_index_almond, top4_output_almond, almond_destroyed, num):
  global g, nextg

  for a in range(num):
    nextg.nodes[top4_index_almond[a]]['almondOutput'] += almond_destroyed * top4_output_almond[a]/  (np.sum(top4_output_almond))

# fireMode = 1) Predicted 2)Observed
fireMode = 2

# global parameters
firePeriod = 2
rebornPeriod = 60 # how many months to reborn
priceOverTime = [2.43]
YieldCap = 3.06
Time = 240
OutputAllCounties = np.zeros((58,Time))
initialize(fireMode)

for i in range(Time):
  update(i)

plt.subplot(2, 1, 1)
for i in range(58):
  plt.plot(OutputAllCounties[i,:])

plt.subplot(2, 1, 2)
plt.plot(list(range(Time+1)),priceOverTime)
plt.show()

print('final price:',prices['almondPrice'])