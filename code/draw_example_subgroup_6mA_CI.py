#! /usr/bin/env python
import sys
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from numpy import median


if len(sys.argv) != 3:
	print "Usage: [predict] [line.plot.png]" 
	sys.exit(0)

f=open(sys.argv[1],"r")

pred=list()
uppred=list()
lowpred=list()
realppm=list()
newlabel=[]
for x in f:
	x=x.strip()
	info=x.split()
	if '#' in info[0]:
		continue
	newlabel.append(info[0])

	pred.append(float(info[4]))
	uppred.append(float(info[5]))
	lowpred.append(float(info[6]))
	realppm.append(round(10**float(info[4])*1000000,1))
	


f.close()

df=pd.DataFrame({'Bin':newlabel,'ppm':pred,'level':'Predict'})
updf=pd.DataFrame({'Bin':newlabel,'ppm':uppred,'level':'Upper'})
lwdf=pd.DataFrame({'Bin':newlabel,'ppm':lowpred,'level':'Lower'})

mydata=pd.concat([df,updf,lwdf])



with sns.axes_style("ticks"):
        ax = sns.pointplot(x="Bin", y="ppm", data=mydata,capsize=0.1,errwidth=0.5,markers=["o"], linestyles=["-",'--'],legend_out=False, palette=sns.color_palette(["#50B547", "#4C98D8", "#FFC200","#306D2B", "#145B93"]),scale=0.3, join=False,estimator=median) #linestyles="--",
fig=ax.get_figure()

#print mydata
for line in range(0,len(pred)):

	#print line+0.2, pred[line],realppm[line]
	ax.text(line+0.1, pred[line],str(realppm[line])+"ppm", horizontalalignment='left',verticalalignment='center', size=6, color='black')

fig.set_size_inches(5, 2)
ax.tick_params(labelsize=6,width=0.5)#,fontweight='bold')
ax.set_xticklabels(newlabel,rotation=40,ha="right")

ax.set_yticks(range(-6,0,1))
ax.set_yticklabels(['-6.0','-5.0','-4.0','-3.0','-2.0','-1.0','0'])
#ax.set_yticklabels([])
#ax.set_xticklabels(newlabel)
for axis in ['bottom','left']:
	ax.spines[axis].set_linewidth(0.5)
ax.xaxis.set_tick_params(width=0.5)
ax.yaxis.set_tick_params(width=0.5)

#ax.set_ytickfontsize(fontsize=30)
ax.set_xlabel("")
ax.set_ylabel("")
box=ax.get_position()
#ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height *0.85])
#ax.legend(bbox_to_anchor=(0.5, -0.15), loc='upper center', fancybox=True,borderaxespad=0.,ncol=2)
#ax.legend()
ax.set_position([box.x0+box.width*0.05, box.y0+box.height*0.3, box.width, box.height*0.8 ])
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.tick_params(direction='out')
h,l = ax.get_legend_handles_labels()
#ax.legend(h,newlabel,ncol=1,facecolor="white",frameon=False,fontsize=25,bbox_to_anchor=(-0.05, 1.05), loc='upper left',handletextpad=0)


#ax._legend.remove()

fig.savefig(sys.argv[2],format='png',dpi=300)





