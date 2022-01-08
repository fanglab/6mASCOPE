.. _6mASCOPE-index:

6mASCOPE documentation
======================

6mASCOPE is a toolbox to assess 6mA events in eukaryotic species using a quantitative deconvolution approach. By using a novel short-insert library (200~400bp) design with the PacBio sequencing Sequel II System, 6mASCOPE makes an effective use of the large number of circular consensus (CCS) reads to reliably capture deviations in IPD values at single molecule resolution. Taking an innovative metagenomic approach, 6mASCOPE deconvolves the DNA molecules from a gDNA sample into species and genomic regions of interests, and sources of contamination. Using a rationally designed machine learning model, 6mASCOPE enables sensitive and reliable 6mA quantification for each of the deconvolved composition.

Authors' notes
--------------

We are actively developing 6mASCOPE to facilitate usage and broaden features. All feedback is more than welcome. You can reach us on twitter (`@iamfanggang <https://twitter.com/iamfanggang>`_ and `@kong_yimeng <https://twitter.com/kong_yimeng>`_) or directly through the `GitHub issues system <https://github.com/fanglab/6mASCOPE/issues>`_.

Installation
------------

6mASCOPE is distributed as a fully functional image bypassing the need to install any dependencies others than the virtualization software. We recommend using Singularity, which can be installed on Linux systems and is often the preferred solution by HPC administrators  (`Quick Start <https://sylabs.io/guides/3.5/user-guide/quick_start.html>`_). 6mASCOPE was tested extensively with Singularity v3.6.4.

.. code-block:: sh

        module load singularity/3.6.4    # Required only singularity/3.6.4 is a dynamic environment module.
        singularity pull 6mASCOPE.sif library://fanglab/default/6mascope:latest    # Download the image from cloud.sylabs.io; Make sure you have the network connection
        singularity build --sandbox 6mASCOPE 6mASCOPE.sif     # Create a writable container named 6mASCOPE
        singularity run --no-home -w 6mASCOPE    # Start an interactive shell to use 6mASCOPE, type `exit` to leave
        init_6mASCOPE    #Inside the container; Only required once when start using 6mASCOPE
        source run_6mASCOPE    #Inside the container; Required every time when running 6mASCOPE
      

Contents
^^^^^^^^

.. toctree::
   :maxdepth: 2
   
   overview
   tool_showcase
   detailed_tutorial
   commands_overview
   commands_details
   faq




