#! /usr/bin/env python
import numpy as np 
import sys
#c0-----c5-------c10-------c25---------c50--------c75---------c90----------c95----------c100

def over_slope(dslope,dcov,left,right,slopecut):
	#(left,right)=np.percentile(dcov, [minpercentile,maxpercentile])
	indx=np.where ((dcov>=left)&(dcov<=right))
	indots=dslope[indx]
	total=np.size(indots)
	overslope=np.sum (indots>=slopecut)
	overslope=overslope
	pct=round(float(overslope+1)/total*100,6)
	return pct

if len(sys.argv) != 2:
	print "IPD.out"
	sys.exit(0)

IPDfile=sys.argv[1]
#cutslope=float(cutslope)

qv=list()
cov=list()
n=0
last=""

with open(IPDfile) as f:
	for line in f:
		line.strip()
		info=line.split()
		cov.append(float(info[4]))
		qv.append(float(info[9]))
		#if info[0] != last:
		n=n+1
		#last=info[0]

dqv=np.asarray(qv, dtype =  float)
dcov=np.asarray(cov, dtype =  float)

dslope=dqv/cov

slopevalue=list()

for cutslope in np.arange(1.0,2.1,0.1):
	#print ("%.1f" % cutslope),
	#print "\t",
	part=[]
	for x in range(1,12):
		left=x*20
		right=left+20
		part.append(over_slope(dslope,dcov,left,right,cutslope))
		part=[str(x) for x in part]
	slopevalue.extend(part)
	#print  "\t".join(part),
	#print "\t"
n=n/100
print str(n)+"\t"+"\t".join(slopevalue)




