# 6mASCOPE

## Description
6mASCOPE is a toolbox to assess 6mA events in eukaryotic species using a quantitative deconvolution approach. By using a novel short-insert library (200~400bp) design with the PacBio sequencing Sequel II System, 6mASCOPE makes an effective use of the large number of circular consensus (CCS) reads to reliably capture deviations in IPD values at single molecule resolution. Taking an innovative metagenomic approach, 6mASCOPE deconvolves the DNA molecules from a gDNA sample into species and genomic regions of interests, and sources of contamination. Using a rationally designed machine learning model, 6mASCOPE enables sensitive and reliable 6mA quantification for each of the deconvolved composition.


## Authors' notes
We are actively developing 6mASCOPE to facilitate usage and broaden features. All feedback is more than welcome. You can reach us on twitter ([@iamfanggang](https://twitter.com/iamfanggang) and [@kong_yimeng](https://twitter.com/kong_yimeng)) or directly through the [GitHub issues system](https://github.com/fanglab/6mASCOPE/issues).


## Installation
6mASCOPE is distributed as a fully functional image bypassing the need to install any dependencies others than the virtualization software. We recommend using Singularity, which can be installed on Linux systems and is often the preferred solution by HPC administrators ([Quick Start](https://sylabs.io/guides/3.5/user-guide/quick_start.html)). ```6mASCOPE``` was tested extensively with Singularity v3.6.4. 

```sh
module load singularity/3.6.4    # Required only singularity/3.6.4 is a dynamic environment module. 
singularity pull 6mASCOPE.sif library://fanglabcode/default/6mascope:latest    # Download the image from cloud.sylabs.io; Make sure you have the network connection
singularity build --sandbox 6mASCOPE 6mASCOPE.sif     # Create a writable container named 6mASCOPE
singularity run --no-home -w 6mASCOPE    # Start an interactive shell to use 6mASCOPE, type `exit` to leave
init_6mASCOPE    #Inside the container; Only required once when start using 6mASCOPE
source run_6mASCOPE    #Inside the container; Required every time when running 6mASCOPE
```

The image retrieved from [Sylab Cloud](https://cloud.sylabs.io/home) with ```singularity pull``` (e.g. 6mASCOPE.sif) is already built and can be reused at will. Containers built with those instructions are writable meaning that results from 6mASCOPE analysis can be retrieved when the container is not running. Outputs for the following commands can be found at ``./path/to/6mASCOPE/home/6mASCOPE/``. To re-run the same container:

```sh
singularity run --no-home -w 6mASCOPE    # Re-run container 6mASCOPE, type `exit` to leave
source run_6mASCOPE    #Inside the container; Required every time when running 6mASCOPE
```

## Tool showcase

To showcase the toolbox applications, we provide examples for the analysis of the Drosophila ~45min embryo dataset presented in our manuscript (Fig 5). The dataset can be downloaded with the following commands from within a 6mASCOPE container: ```6mASCOPE get_test_data```


### Contamination estimation

#### Goal

To get an idea about the overall contamination of a gDNA sample. This step helps users define the composition of a gDNA sample using a metagenomic approach to assign reads to different species.

#### Description:

For a given CCS dataset generated from short-insert library, 6mASCOPE will examine if there are contaminating species and calculate the proportion of reads mapped to the reference and top 50 contaminated species from reads that do not map to the eukaryotic species of interest.

#### Inputs: 

1. CCS reads file capturing all the genetic material in a gDNA sample (.fasta, pre-computed in the following example)
2. Eukaryotic reference of genome of interest (.fasta)

#### Outputs:

For a given CCS dataset generated from short-insert library, ```6mASCOPE``` will examine if there are contaminating species and calculate the proportion of reads mapped to the reference and top 50 contaminated species from reads that do not map to the eukaryotic species of interest.


##### Example of the Output: 
```
Remove 8491 possible inter-species chimeric reads for further analysis
#total_CCS	mapped_to_goi	contaminants
666159	640345 (96.1249%)	25814 (3.87505%)

Top 50 mapped species outside goi reference
#Count	Species
  10836 Saccharomyces cerevisiae
   2413 Acetobacter tropicalis
   1524 Acetobacter pasteurianus
   1479 Lactobacillus plantarum
    882 Acetobacter sp.
 ...
```
(Full species list can be viewed in ```test.contam.estimate.txt```)

##### Example commands: 

```
6mASCOPE contam -c test.ccs.fasta -r test.ref.fasta -o test.contam.estimate.txt
```
In this example, ```test.ccs.fasta``` includes CCS reads (674,650) from the Drosophila ~45min embryo reads dataset described in our manuscript and pre-filtered with command ```6mASCOPE ccs```. Using 5 cores, runtime is ~12m51s. The output shows ~3.9% CCS reads come from contaminated sources other than Drosophila melanogaster, the genome of interest (goi). Please be noted, blastn is embedded within this step, which will need at least 32-64G RAM.  

### 6mA analysis using quantitative deconvolution

#### Goal:
For each source determined in ```6mASCOPE contam```, this step will quantify the 6mA/A level and calculate the 6mA contribution (%) of each source to the total 6mA abundance in the gDNA sample.

#### Inputs: 
1. The same CCS reads file as explained above for Contamination Estimation (.fasta).
2. IPD and QV information of the CCS reads (pre-computed in the following example, ; this can be generated for new data with ```6mASCOPE ipd``` command, as explained in detailed tutorial).
3. User defined groups besides the genome of interest. Examples as shown below. (Left columns: subgroup name. Right columns: contamination sources, use vertical line if multiple sources included within one subgroup).

```
Saccharomyces   Saccharomyces
Acetobacter     Acetobacter|Komagataeibacter
Lactobacillus   Lactobacillus
```

#### Outputs:
A table including the following information: the proportion (%) of reads from each source out of the total number of reads; source-specific 6mA/A level with 95% confidence intervals (log10-transformed), and contribution (%) of each source to the total 6mA abundance in the gDNA sample (as presented in the manuscript Figure 5A, B, C)

#### Example commands:
```
6mASCOPE quant -c test.ccs.fasta -i test.IPD.out.A -o test -r test.ref.fasta -s subgroup.txt
```
In this example, the file ```test.IPD.out.A``` includes the pre-calculated IPD and QV information on the CCS molecules (can be generated with ```6mASCOPE ipd```). Only Adenines were included here to to reduce computational time and ease evaluation. ```subgroup.txt``` includes the pre-defined main contamination groups, inferred from the top mapped species and blast output from ```6mASCOPE contam```. Using 5 cores, runtime is ~13m17s.

#### Example output:

```
     #Subgroup   count  ReadsProportion  6mAlevel(ppm)  6mAlevel(log10)  UpCI  DownCI  subtotal(ppm)  contribution(%)
           goi  640345           0.9612         2.0417            -5.69  -5.0    -6.0         1.9625           1.4431
 Saccharomyces   11011           0.0165        45.7088            -4.34  -3.9    -6.0         0.7542           0.5546
   Acetobacter    5757           0.0086      5495.4087            -2.26  -2.0    -2.5        47.2605          34.7522
 Lactobacillus    1517           0.0023       977.2372            -3.01  -2.7    -3.3         2.2476           1.6528
        others    7529           0.0113      7413.1024            -2.13  -1.9    -2.4        83.7681          61.5974
```


<p align="center">
  <img src="/docs/figures/test.6mASCOPE.ReadsProportion.png" alt="The proportion of CCS reads from each group 6mA" width="400"/>
</p>
1. The % of total CCS reads mapped to different subgroups. Left: The % of CCS reads mapped to D. melanogaster (genome of interest) and contamintant subgroups. Right: The % of CCS reads mapped to different contaminant sources.

<p align="center">
  <img src="/docs/figures/test.6mASCOPE.6mAlevel.png" alt="Group-specific 6mA/A level prediction with confidence intervals 6mA" width="500"/>
</p>
2. 6mA quantification and 95% confidence intervals (log10-transformed) on CCS reads mapped to different subgroups. Please be noted, it is important to combine the estimated 6mA/A level with its confidence interval for reliable data interpretation. In this example, the 6mA/A level of Saccharomyces (45.7ppm) does not mean abundant 6mA events in this subgroup because it has a wide range of confidence interval (1-125ppm; -6.0 to -3.9 with log10 transformed). In the paper, an additional Sequel II run for this single species (higher yield) actually shows extremely low 6mA level (2ppm, confidence interval: 1-10ppm).


<p align="center">
  <img src="/docs/figures/test.6mASCOPE.6mAcontribution.png" alt="Group-specific 6mA/A level prediction with confidence intervals 6mA" width="300"/>
</p>
3. Contribution (%) of each source to total 6mA abundance in the gDNA sample. CCS reads mapped to the D. melanogaster genome only explains 1.4% of the total 6mA events in the gDNA sample (green).

These figures can be drawn with ```sh ~/code/draw_example.sh test.6mASCOPE.txt```.


## Documentation
For a comprehensive description of 6mASCOPE including installation guide, data preprocessing and a detailed tutorial, including how to apply 6mASCOPE to your own datasets, please refer to the [complete documentation](https://6mascope.readthedocs.io/en/latest/overview.html) . 


<<<<<<< HEAD
## Citation
Yimeng Kong, Lei Cao, Gintaras Deikus, Yu Fan, Edward A. Mead, Weiyi Lai, Yizhou Zhang, Raymund Yong, Robert Sebra, Hailin Wang, Xue-Song Zhang & Gang Fang. Critical assessment of DNA adenine methylation in eukaryotes using quantitative deconvolution. *Science* (2022). doi:[10.1126/science.abe7489](http://doi.org/10.1126/science.abe7489). 

=======
>>>>>>> bf3705e1c5ff4e0aed09d3de073163e9e7514401

