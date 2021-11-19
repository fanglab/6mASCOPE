.. _commands-details:

==================
Commands Details
==================

Commands overview
==================

6mASCOPE <subtask> [options], <subtask> include:

* `deplex`_: De-multiplex subreads into individual files.
* `ccs`_: Generate CCS .bam and .fasta files from short insert library sequencing data.
* `ipd`_: Summarize the IPD and QV information for each molecule by reference-free method.
* `contam`_: Estimate the contamination in the current sample.
* `quant`_: Quantify deconvolution of the sample with defined groups.
* `version`_: Plot version.
* `help`_: Print help.

.. _deplex:

deplex
======

De-multiplex subreads into individual files.


**Usage:**

.. code-block:: none

	6mASCOPE deplex -b <barcode.fasta> -i <raw.bam> -o <prefix.bam> [-p <nb_threads>]
		-b .fasta file for barcodes set.
		-i .bam file for raw subreads.
		-o deplexed .bam files for barcoded sample.
		-p number of threads to use.

Output:
De-plexed bam files for each sample.


.. _ccs:

ccs
====

generate circular consensus sequencing (CCS) reads.

**Usage:**

.. code-block:: none

	 6mASCOPE ccs -i <raw.bam> -ob <prefix.ccs.bam> -of <prefix.ccs.fasta> [-p <nb_threads>]
		-r bam file for raw subreads.
		-ob bam file for CCS reads.
                -of fasta file for CCS reads.
		-p number of threads to use. 

**Outputs:**

#. .bam for circular consensus reads. 
#. .fasta files for circular consensus reads. 

.. _ipd:

ipd
====

Summarize the IPD and QV information.

**Usage:**

.. code-block:: none

	6mASCOPE ipd -r <raw.bam> -f <ccs.fasta> -o <Ipd.out> [-p <nb_threads>]
		-r bam file for raw subreads.
		-f fasta file for ccs reads.
		-o tab-delimited file containing IPD and QV information.
		-p number of threads to use. 

**Outputs:**

#. tab-delimited file containing IPD and QV information.

Output file description:

.. code-block:: none

	refName				name of molecule
	tpl				genomic position
	strand				genomic strand, 0 for forward, 1 for reverse     
	base				genomic base    
	coverage			coverage at this position        
	modelPrediction 	        in silico estimation (based on the sequence context)  
	tMean 				mean IPD collected from subreads    
	ipdRatio 			Ratio of tMean over ModelPrediciton        
	tErr 				Standard error for mapped subreads  
	score 				mapped quality value (QV)

.. _contam:

contam
======
Estimate the contamination in the current sample

**Usage:**

.. code-block:: none

	6mASCOPE contam -c <CCS.fasta> -r <reference> -o <output> [-p <nb_threads>]
		-c fasta file for ccs reads.
		-r Reference of genome of interest.
		-o top 50 contaminated species from reads that do not map to the eukaryotic species of interest.
		-p number of threads to use. 

**Outputs:**

#. Folder containing reads mapped to reference.
#. Folder containing unmapped reads and their matches to NCBI-NT database.
#. Summary of the ccs reads, including mapping percentage and the top 50 most contaminated species from reads that do not map to the eukaryotic species of interest.


.. _quant:

quant
=====
Quantify deconvolution of the sample with defined groups.

**Usage:**

.. code-block:: none

	6mASCOPE quant -c <CCS.fasta> -i <ipd file> -o <Prefix for output> -r <reference> -s <subgroup.txt>
		-c fasta file for ccs reads.
		-i tab-delimited file containing IPD and QV information from ipd step.
		-s pre-defined main contamination groups(.txt).
		-o tab-delimited file.  

**Outputs:**

#. Tab-delimited file containing the 6mA level prediction and contribution of sub-groups.

Output file description:

.. code-block:: none

	Subgroup 			subgroups
	count 				count of ccs reads within each subgroups
	ReadsProportion 	        percentage of ccs reads  
	6mAlevel(ppm) 		        6mA level prediction (ppm)  
	6mAlevel(log10) 	        6mA level prediction (log10-transformed)     
	UpCI 				95% uppper confidence interval of 6mA level prediction (log10-transformed)  
	DownCI 				95% lower confidence interval of 6mA level prediction (log10-transformed)  
	subtotal(ppm) 		        6mA level contribution (ppm)   
	contribution(%) 	        6mA level contribution (percentage) 


.. _version:

version
=======
Print version.

**Usage:**

.. code-block:: none

	6mASCOPE version

.. _help:

help
=====

Print help.

**Usage:**

.. code-block:: none

	6mASCOPE help


