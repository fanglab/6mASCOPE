.. _faq:

===
FAQ
===

* Q1: what eukaryotic species can ``6mASCOPE`` handle?
	Basically all eukaryotic species with reference genome could be analyzed by ``6mASCOPE``. 

* Q2: Is there any limitation in the type of bacterial contamination?
	No, we can detect contamination in all known bacteria.

* Q3: What SMRT-seq libraries are recommended for ``6mASCOPE``?
	6mASCOPE is requires relatively short-insert library (200~400bp) with the PacBio sequencing Sequel II System. This library design will provide ``6mASCOPE`` enough number of DNA molecules with highly accurate CCS references and repeated IPD measurements of individual molecules at single site. Commonly used Sequel II Long-insert library dataset (e.g. >1kb) can lead to running errors or inaccurate estimations when analyzed with ``6mASCOPE``. 

* Q4: What PacBio instrument are supported by ``6mASCOPE``?
	Currently, ``6mASCOPE`` supports data from SEQ2 platform， which provides longer reads and better throughput, and are more widely used. In the future, we will also support SEQ1 and RS II in case some users want to analyze data generated before SEQ2.

* Q5: how long does pre-processing need?
	Before ``6mASCOPE``, a standard pre-processing (``deplex``, ``CCS``, ``ipd``) of a 3-plex SEQ2 dataset (~300G) will take 7-10 days with 20 CPUs. For each sub-task, ``deplex`` will take 4-6 hrs; ``CCS``, 1-2 days; ``ipd``, 4-8 days. After the pre-processing, ``contam`` will take ~0.5 hrs and ``quant`` will take ~0.5 hrs. High performance computing (HPC) with more CPUs will shorten the computing time, especially for ``ipd`` subtask. Running time may be varied depending on the contaminations and machine performance. 

* Q6: Is ``6mASCOPE`` available for other systems than Singularity in Linux?
	Sylabs also offers solutions to install Singularity on Windows and Mac. Singularity is recommend  when using ``6mASCOPE`` for running analysis. We will also provide a solution to use Docker as image management software in the future. 

* Q7: Why don’t container times match the host machine?
	6mASCOPE image uses a default timezone. You can change it by exporting TZ variable as follow: 1. Use tzselect to find your time zone. 2. Enter ``export TZ='America/New_York'`` and add it to the ``/home/6mASCOPE/.bashrc`` file.

* Q8: How much yield is needed for one sample?
	The number of molecules is a reflection of the sequencing yield. With more molecules available, the confidence interval will become narrower for the same 6mA/A level. Please refer to figures 3C and S5B for the confidence interval distribution for different number of molecules at various 6mA/A predictions. However, when number of molecules is <8000, the quantification process may result in running error because of not enough features captured from the dataset. 

* Q9: How to provide the subgroup file in ``6mASCOPE`` quant if I only want to study the species of genome_of_interest (goi)?
        You must provide a subgroup file for ``6mASCOPE quant``. However, if you only want to separate the reads into two groups: goi and others, you could leave the subgroup file empty. Try ``touch subgroup.txt`` before you do ``6mASCOPE quant``.

* Q10: Can I use ``6mASCOPE`` to analyze data outside the container?
        Yes. You could analyze your own data outside the container. Please use the full path to the directory on your system. Everything stays the same except for /home, which is defined when container is built.  
