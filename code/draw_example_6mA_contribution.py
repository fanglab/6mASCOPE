#! /usr/bin/env python
import sys
import matplotlib as mpl
mpl.use('Agg')
mpl.rcParams['axes.spines.right'] = False
mpl.rcParams['axes.spines.top'] = False
mpl.rcParams['axes.spines.left'] = False
mpl.rcParams['axes.spines.bottom'] = True
import numpy as np
import matplotlib.pyplot as plt

if len(sys.argv) != 3:
	print "Usage: [predict] [stack.bar.plot.png]" 
	sys.exit(0)


f=open(sys.argv[1],"r")

pred=list()
newlabel=[]

for x in f:
	x=x.strip()
	info=x.split()
	if '#' in info[0]:
		continue
	newlabel.append(info[0])
	pred.append(float(info[8]))
	
fig = plt.figure(figsize=(3,2))

#Get values from the group and categories
#quarter = np.array(newlabel)
#jeans = np.array(pred)
    
#add colors
colors=["#50B547", "#4C98D8", "#FFC200","#306D2B", "#145B93"]
# The position of the bars on the x-axis
#r = range(len(quarter))
barWidth = 1
#plot bars

for x in range(len(newlabel)):
	plt.barh(x, pred[x], left=sum(pred[:x]), color=colors[x], edgecolor='white', height=barWidth, label=newlabel[x])
plt.legend(frameon=False,prop={'size': 6},loc=4)
#plt.yticks(range(len(newlabel)), newlabel, fontweight='bold')
plt.yticks([],[])

plt.xlabel("6mA contribution", fontsize=6)
plt.xticks(fontsize=6)
plt.subplots_adjust(bottom=0.2)
fig.savefig(sys.argv[2],format='png',dpi=300)





