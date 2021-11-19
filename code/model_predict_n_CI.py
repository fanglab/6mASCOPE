#! /usr/bin/env python 
import numpy as np
from sklearn import linear_model
import sys
import pickle
from math import log


def get_num_range(trainmols,molnum):
	mols=trainmols[:]
	mols.sort()
	#print mols
	#print molnum
	upnum=mols[-1]
	lownum=mols[0]
	if molnum in mols:
		upnum=molnum
		lownum=molnum
	else:
		mols.append(molnum)
		mols.sort()
		#print mols
		idx=mols.index(molnum)
		if idx == 0:
			upnum=lownum
		elif idx==len(mols)-1:
			lownum=upnum
		else:
			upnum=mols[idx+1]
			lownum=mols[idx-1]
	return lownum

def get_lv_range(trainlvs,mollv):
	lvs=trainlvs[:]
	lvs.sort()
	#print lvs
	#print mollv
	uplv=lvs[-1]
	lowlv=lvs[0]
	if mollv in lvs:
		uplv=mollv
		lowlv=mollv
	else:
		lvs.append(mollv)
		lvs.sort()
		idx=lvs.index(mollv)
		if idx == 0:
			uplv=lowlv
		elif idx==len(lvs)-1:
			lowlv=uplv
		else:
			uplv=lvs[idx+1]
			lowlv=lvs[idx-1]
	return uplv if abs(uplv-mollv) < abs(mollv-lowlv) else lowlv
	#return (uplv,lowlv)


if len(sys.argv) !=5 :
	print "[model] [CI] [features] [prefix]"
	sys.exit(0)


mdl=sys.argv[1]
with open(mdl, 'rb') as m:
	model = pickle.load(m)

upCI=dict()
lowCI=dict()
allmols=dict()
alllvs=dict()


cif=open(sys.argv[2],'r')

for line in cif:
	info=line.split()
	mol=int(info[0])
	lv=float(info[1])
	allmols[mol]=1
	alllvs[lv]=1
	molwpre=str(mol)+str(lv)
	upCI[molwpre]=float(info[2])
	lowCI[molwpre]=float(info[3])
	#iii[molwpre]=line

cif.close()

myprefix=sys.argv[4]

f=open(sys.argv[3],"r")

#print "#mol\tpredict_level\tNearest_mol\tNearest_lv\tupCI\tlowCI"
for line in f:
	if line[0].isalnum():
		info=line.split()
		molnum=int(info[0]) # molecule number
		finalnum=str(get_num_range(allmols.keys(),molnum))
		cov=[log(float(x),10) for x in info[1:]]
		#cov=np.append(cov,tmp,axis=0)
		cov=np.array(cov).reshape(1,-1)
		modelpredlv = round(model.predict(cov).flatten()[0],2) #predict value
		finallv=str(get_lv_range(alllvs.keys(),modelpredlv))
		print ("%s\t%.2f\t%.2f\t%.2f" % (myprefix,modelpredlv,upCI[finalnum+finallv],lowCI[finalnum+finallv]))

f.close()	










