#! /usr/bin/env python
import numpy as np
import sys

import pandas as pd

if len(sys.argv) !=4 :
	print "[prop.txt] [6mA.level.txt] [6mA.contribution]"
	sys.exit(0)



f=open(sys.argv[1],"r")

label1=list()
prop=list()
count=list()

for x in f:
	if x[0].isalnum():
		x=x.strip()
		info=x.split()
		label1.append(info[0])
		count.append(int(info[1]))
		prop.append(float(info[2]))
	
	#real.append(float(info[4]))
f.close()


f=open(sys.argv[2],"r")
label2=list()
level=list()
loglevel=list()
uplevel=list()
downlevel=list()
for x in f:
	if x[0].isalnum():
		x=x.strip()
		info=x.split()
		label2.append(info[0])
		level.append(10**float(info[1])*1000000)
		loglevel.append(float(info[1]))
		uplevel.append(float(info[2]))
		downlevel.append(float(info[3]))

	
	#real.append(float(info[4]))
f.close()

if label2 == label1:
	mydata=pd.DataFrame({'Subgroup':label2,'proportion':prop,'level':level,'loglevel':loglevel,'uplevel':uplevel,'downlevel':downlevel,'count':count})
	f.close()


	mydata.eval('subtotal = proportion*level', inplace = True)
	total=mydata['subtotal'].sum()
	mydata["contribution"]=mydata['subtotal']/total*100
	#mydata['level'] = mydata['level'].apply(int)


	mydata = mydata[['Subgroup', 'count','proportion', 'level','loglevel','uplevel','downlevel', 'subtotal', 'contribution']]

	
	mydata.columns =['#Subgroup','count','ReadsProportion','6mAlevel(ppm)','6mAlevel(log10)','UpCI','DownCI','subtotal(ppm)','contribution(%)'] 

	mydata=mydata.round(4)
	#print mydata
	tfile = open(sys.argv[3], 'w')
	tfile.write(mydata.to_string(index=False))
	tfile.write("\n")
	tfile.close()




