==================
Detailed tutorial
==================

We recommend users to first try the :ref:`Tool showcase <tool-showcase>` before this detailed tutorial. To demonstrate the toolbox applications and facilitate further understanding of the methods, we provide more detailed examples for the analysis. The datasets can be downloaded with the following commands from within a 6mASCOPE container: ``6mASCOPE get_test_data``.

.. code-block:: none

        Usage: 6mASCOPE <subtasks> [parameters]
            subtasks:
            - deplex: De-multiplex subreads into individal files.
            - ccs: Generate CCS .bam and .fasta files from short insert library sequencing data.
            - ipd: Summarize the IPD and QV information for each molecule by reference-free method.
            - contam: Estimate the contamination in the current sample.
            - quant: Quantify deconvolution of the sample with defined groups.


.. note::

  	Please note 6mASCOPE requires relatively short-insert library (200~400bp) with the PacBio sequencing Sequel II System. This library design will provide 6mASCOPE enough number of DNA molecules with highly accurate CCS references and repeated IPD measurements of individual molecules. Commonly used Sequel II Long-insert library dataset (eg. >1kb) can lead to running errors or inaccurate estimations when analyzed with ``6mASCOPE``. 


De-multiplexing barcoded data
=============================

**Descriptions:**

Multiple samples may be performed in parallel within one sequencing batch by adding different barcodes in PCR primers (`PacBio barcoding guidlines <https://www.pacb.com/wp-content/uploads/Shared-Protocol-PacBio-Barcodes-for-SMRT-Sequencing.pdf>`_). Before analysis, data need to be de-multiplexed into individual files for samples. 

**Inputs:** 

#. Barcode sets used in library preparation (.fasta)
#. Data to be de-multiplexed (.bam)

**Outputs:**

#. Raw data for each sample (.bam) 

.. code-block:: none
		
		Usage: 6mASCOPE deplex -b <barcode.fasta> -i <raw.bam> -o <prefix.bam> [-p <nb_threads>]


Parameters: ``-b`` .fasta file for barcodes set, ``-i`` .bam file for raw subreads, ``-o`` deplexed .bam files for barcoded sample, ``-p`` number of threads to use(default:5). 6mASCOPE has included common barcodes, which could be available in ``~/SLpackage/data/barcode/``.


Generate circular consensus sequencing (CCS) reads
==================================================


**Descriptions:**

6mASCOPE does not need reference for IPD analysis. Instead, 6mASCOPE takes the advantage of the high-accuracy CCS reads from SMRT sequencing and uses them for the following 6mA analysis. The following command will call CCS reads from the raw subreads.

**Input:**

#. Raw subreads.bam file (De-multiplexed)

**Outputs:**

#. CCS reads in .bam format
#. CCS reads in .fasta format

.. code-block:: none

        6mASCOPE ccs -i <raw.bam> -ob <prefix.ccs.bam> -of <prefix.ccs.fasta> [-p <nb_threads>]

Parameters ``-i`` bam file for raw subreads, ``-ob`` bam file for CCS reads, ``-of`` fasta file for CCS reads, ``-p`` number of threads to use (default:5). 


Single-molecule reference-free modification analysis
====================================================

**Description:** 

For each molecule, the Inter-pulse duration (IPD) information on the subreads are calculated with the CCS read as the molecule-specific reference. By collecting the repeated measures of IPD at a single site, the IPD and modification quality value (QV) summarized at single nucleotide resolution for individual molecules.

**Inputs:**

#. bam file for raw subreads
#. fasta file for CCS reads

**Outputs:**

#. Tab-delimited file containing IPD and QV information

Output file description:

.. code-block:: none

	columns: 
		refName				name of molecule
		tpl				genomic position
		strand  			genomic strand, 0 for forward, 1 for reverse     
		base 				genomic base    
		coverage			coverage at this position        
		modelPrediction 	        in silico estimation (based on the sequence context)  
		tMean 				mean IPD collected from subreads    
		ipdRatio 			Ratio of tMean over ModelPrediciton        
		tErr 				Standard error for mapped subreads  
		score 				mapped quality value (QV)

.. code-block:: none

        6mASCOPE ipd -r <raw.bam> -f <ccs.fasta> -o <Ipd.out> [-p <nb_threads>]

Parameters ``-r`` bam file for raw subreads, ``-f`` fasta file for ccs reads, ``-o`` tab-delimited file containing IPD and QV information, ``-p`` number of threads to use (Default 5) .


Contamination estimation
==========================

**Goal**

To get an idea about the overall contamination of a gDNA sample. This step helps users define the composition of a gDNA sample using a metagenomic approach to assign reads to different species.


**Description:** 

For a given CCS dataset generated from short-insert library, 6mASCOPE will examine if there are contaminating species and calculate the proportion of reads mapped to the reference and top 50 contaminated species from reads that do not map to the eukaryotic species of interest.

**Inputs:**

#. CCS reads file capturing all the genetic material in a gDNA sample (.fasta) 
#. Eukaryotic reference of genome of interest (.fasta)

**Outputs:**

Top 50 contaminated species from reads that do not map to the eukaryotic species of interest

.. code-block:: none

        6mASCOPE contam -c <CCS.fasta> -r <reference> -o <output> [-p <nb_threads>]


Parameters ``-c`` fasta file for ccs reads, ``-r`` Reference of genome of interest, ``-o`` top 50 contaminated species from reads that do not map to the eukaryotic species of interest., ``-p`` number of threads to use. 

6mA analysis using quantitative deconvolution
=============================================

**Description:**

For each source determined in ``6mASCOPE contam``, this step will quantify the 6mA/A level and calculate the 6mA contribution (%) of each source to the total 6mA abundance in the gDNA sample.

**Inputs:**

#.	The same CCS reads file as explained above for Contamination Estimation  (.fasta).
#.	IPD and QV information of the CCS reads (can be generated for new data with ``6mASCOPE ipd`` command).
#.	User defined groups besides the genome of interest. Examples as shown below. (Left columns: subgroup name. Right columns: contamination sources, use vertical line if multiple sources included within one subgroup).
#.  The reference of the genome of interest

.. code-block:: none

	Saccharomyces	Saccharomyces
	Acetobacter	Acetobacter|Komagataeibacter
	Lactobacillus	Lactobacillus

**Outputs:**

A table including the following information: the proportion (%) of reads from each source out of the total number of reads; source-specific 6mA/A level with 95% confidence intervals (log10-transformed), and contribution (%) of each source to the total 6mA abundance in the gDNA sample

#. Tab-delimited file containing IPD and QV information

Output file description:

.. code-block:: none

	columns: 
	#Subgroup  			Subgroup name  
	count  				CCS reads mapped to the subgroup
	ReadsProportion  	% of CCS reads to the total
	6mAlevel(ppm)		6mA/A level shown in ppm  
	6mAlevel(log10)  	6mA/A level shown in log10 transformed  
	UpCI  				Upper 95% confidence interval of prediction
	DownCI  			Lower 95% confidence interval of prediction
	subtotal(ppm)		6mA abundance normalized by Reads Proportion  
	contribution(%)		contribution (%) of each source to the total 6mA abundance


.. code-block:: none

        6mASCOPE quant -c <CCS.fasta> -i <ipd file> -r <reference> -s <subgroup.txt> -o <Prefix for output>

Parameters ``-c`` fasta file for ccs reads, ``-i`` tab-delimited file containing IPD and QV information from ipd step, ``-r`` reference for the genome of interest, ``-s``. pre-defined main contamination groups(.txt),  ``-o`` tab-delimited output file. 




