.. _faq:

===
FAQ
===

* Q1: What eukaryotic species can ``6mASCOPE`` analyze?
	Basically any eukaryotic species with a reference genome can be analyzed by ``6mASCOPE``. For a eukaryotic species without a reference genome yet, its de novo assembled genome need to be used with cautions because it may contain contigs from bacteria.

* Q2: Is there any limitation in the type of bacterial contamination?
	``6mASCOPE`` detects bacterial contamination by mapping CCS reads to ``NCBI-NT`` database, which includes all bacteria known to date. We may add in more resources from other databases (`PLSDB <https://ccb-microbe.cs.uni-saarland.de/plsdb/>`_, etc) for wider detection of contaminations in the future.  

* Q3: What type of SMRT-seq libraries is recommended for ``6mASCOPE``?
	``6mASCOPE`` uses relatively short-insert library (200~400bp) with the PacBio sequencing Sequel II System. This library design provides ``6mASCOPE`` with a large number of accurate CCS reads, each with an extensive number of repeated IPD measurements of individual DNA molecules. Commonly used Sequel II long-insert library dataset (e.g. >1kb) are not recommended for reliable quantitative 6mA deconvolution by 6mASCOPE and may lead to running errors or unreliable estimations.

* Q4: What PacBio instruments are supported by ``6mASCOPE``?
	Currently, ``6mASCOPE`` supports data from the widely used the PacBio Sequel II platform, which provides longer raw reads and higher throughput. Sequel I is compatible but not recommended. The lower number of DNA molecules by Sequel I will result in wider confidence interval or encounter running errors due to insufficient features for reliable quantification. In the future, we may also support for the older RS II platform in case some users want to use these platforms, although we highly recommend all users to use the Sequel II platform for the reasons mentioned above (also see ``Q3``).

* Q5: How long does the pre-processing step take? 
	Before running the core analysis of ``6mASCOPE``, a standard pre-processing (``deplex``, ``CCS``, ``ipd``) of a 3-plex (3-sample multiplexing) SequelII dataset (~300G) takes 7-10 days with 20 CPUs: ``deplex``  4-6 hrs; ``CCS`` 1-2 days; ``ipd`` 4-8 days. After the pre-processing, contam will take ~0.5 hrs and quant will take ~0.5 hrs. (Please note: running time may have some variations depending on the extent of bacterial contaminations and computing resources). High performance computing (HPC) with more CPUs significantly shorten the computing time, especially for ipd subtask. So, we highly recommend users to perform the analysis using HPC resources. 

* Q6: Is ``6mASCOPE`` available for other systems than Singularity in Linux?
	Sylabs also offers solutions to install Singularity on Windows and Mac. Singularity is recommended when using ``6mASCOPE`` for running analysis. 

* Q7: Why don’t container times match the host machine?
	``6mASCOPE`` image uses a default timezone. You can change it by exporting TZ variable as follow: 1. Use tzselect to find your time zone. 2. Enter ``export TZ='America/New_York'`` and add it to the ``/home/6mASCOPE/.bashrc`` file.


* Q8: How many reads are needed per sample for ``6mASCOPE`` analysis?
	With more molecules available, the confidence interval of 6mA estimation will become narrower (better). Please refer to Figures 2F and S5B for how the confidence interval changes over different number of CCS reads across different 6mA/A levels. However, when number of molecules is <8000, the 6mA quantification analysis may encounter running errors due to insufficient features for reliable quantification.

* Q9: How to provide the subgroup file in ``6mASCOPE quant``  if I only want to study the species of genome of interest (goi)?
    You must provide a subgroup file for ``6mASCOPE quant``. However, if you only want to separate the reads into two groups: goi and others, you could leave the subgroup file empty. Try ``touch subgroup.txt`` before you do ``6mASCOPE quant``.

* Q10: Can I use ``6mASCOPE`` to analyze data outside the container?
	Yes. You can analyze your own data outside the container. Please use the full path to the directory on your system. Everything stays the same except for ``/home``, which is defined when container is built.

* Q11: How to interpret the 6mA levels estimated by ``6mASCOPE``?
	For reliable data interpretation, it is important to combine the 6mA/A levels estimated by ``6mASCOPE`` with their confidence intervals which depend on sequencing depth and 6mA/A levels. Please refer to Figures 2F and S5B. So we do not recommend users to solely rely on the 6mA/A levels estimated by ``6mASCOPE`` when comparing different samples. Finally, ``6mASCOPE`` does not precisely differentiate 6mA/A levels below 10 ppm because the confidence interval includes 1 ppm, which is the lowest 6mA/A level in our training dataset (Fig. 2F)

* Q12: How can I examine 6mA level associated with a specific motif, genomic region?
	``6mASCOPE`` provides reference-free single-molecule single-nucleotide 6mA analysis results (the file after ``6mASCOPE ipd``). Therefore, IPD information of specific motif can be parsed by screening of the CCS read sequences. Similarly, you can also get the IPD information of specific genomic regions by mapping the CCS reads to the genome. 6mA level of the specific motif / genomic region can be estimated with the code ``~/code/predict_6mA_level.sh``. 

* Q13: Does ``6mASCOPE`` support detection of individual 6mA sites?
	The focus of ``6mASCOPE`` is more about quantitatively deconvolving the global 6mA/A level into different species and genomic regions of interests, rather than mapping specific 6mA events in a particular genome. We prioritized this focus because the most controversial 6mA findings to date were those reporting high 6mA/A levels in multicellular eukaryotes. 
	Depending on the 6mA/A level in a eukaryote genome, single site 6mA mapping faces different levels of challenge. For genomes with high 6mA/A levels, such as the two protozoa we characterized in the paper, single site 6mA mapping can be performed by ``6mASCOPE`` as shown in Figures 3D and 3E. However, for genomes with much lower 6mA/A levels, the precise mapping of specific 6mA events would require deeper SMRT sequencing and additional methods development, and can be pursued in future work.

* Q14: Does ``6mASCOPE`` also support 4mC quantification?
	Currently, ``6mASCOPE`` does not support 4mC quantification. However, N4-methylcytosine (4mC), another form of DNA methylation prevalent in bacteria, was also detected in CCS reads from Acetobacter in the fly embryo data (fig. S11). This observation shows that 4mC analysis for eukaryotic organisms also should be cautiously examined for possible bacterial contamination. 






