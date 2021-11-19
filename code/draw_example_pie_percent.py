#! /usr/bin/env python
#draw Scatter plot for IPD score 
import sys
import numpy as np

if len(sys.argv) != 3:
	print "Usage: data pie.png"
	sys.exit(0)

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
fig = plt.figure(figsize=(4,3))



f=open(sys.argv[1],"r")



labels=list()
sizes=list()
for x in f:
	if '#' in x:
		continue
	x=x.strip()
	info=x.split()
	labels.append(info[0])
	sizes.append(int(info[1]))

#print labels
#print sizes


#fig, (ax0, ax1) = plt.subplots(ncols=2, constrained_layout=True)
#fig, ax1 = plt.subplots()
ax0 = fig.add_subplot(121)


colors = ['#50B547','#9E7400']

goi=sizes[0]
contaminant=sizes[1:]
totalcontam=sum(contaminant)
totalccs=sum(sizes)

pie0=ax0.pie([goi,totalcontam], colors=colors,explode=(0,0), 
	 autopct='%1.2f%%',shadow=False, startangle=0,wedgeprops=dict(width=1, edgecolor='w'),textprops={'fontsize': 6})
ax0.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

#handles, lb = ax0.axes.get_legend_handles_labels()
ax0.legend(pie0[0], [labels[0],"contaminants"], prop={'size':6},
          bbox_to_anchor=(0.5,0.10),loc=10)


ax1 = fig.add_subplot(122)
#colors = ['gold', 'yellowgreen', 'lightcoral', 'lightskyblue']
colors = ['#4C98D8','#FFC200','#306D2B','#145B93']
explode = (0, 0, 0,0)  # explode 1st slice

def func(pct,dex):
	
	newpct = float(pct*dex)
	#print pct, newpct
	return '{:.2f}%'.format(newpct)


pie1=ax1.pie(contaminant, colors=colors,explode=explode, shadow=False, startangle=0,wedgeprops=dict(width=1, edgecolor='w'),counterclock=False,autopct=lambda pct: func(pct, totalcontam*1.0/totalccs),textprops={'fontsize': 6})
ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

#handles, lb = ax1.axes.get_legend_handles_labels()
ax1.legend(pie1[0], labels[1:], prop={'size':6},
          bbox_to_anchor=(0.5,0.10),loc=10)
# Set aspect ratio to be equal so that pie is drawn as a circle.



# Plot
#plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=False, startangle=90,counterclock=False)


fig.savefig(sys.argv[2],format='png',dpi=300)












