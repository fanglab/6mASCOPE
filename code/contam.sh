#!/bin/bash
#module load minimap2 samtools blast


###
# Wrapper for computing contamination estimation
###
# 1. Map CCS reads to the reference of genome of interest
# 2. Unmapped reads would be hereafter mapped to nt database

## Describe parameters
nb_jobs_def="Specify how many jobs to run in parallel (affect CPU and memory usage)."
ccs_def="Specify the .fasta file for the Circular consensus Reads (CCS)."
ref_def="Specify the reference for the genome of interest."
output_def="output file"

## Default parameters
nb_threads=5

# Read options
while [[ $# -gt 0 ]]; do
  key="$1"

  case $key in
    -c|--ccs)
      if [[ -f $2 ]] ; then
        ccs="$2"
        shift # pass argument
        shift # pass value
      else
        echo "No ccs.fasta file exist" >&2
        echo -e "\t"$ccs_def
        exit 5
      fi
      ;;
    -r|--ref)
      if [[ -f $2 ]] ; then
        ref="$2"
        shift # pass argument
        shift # pass value
      else
        echo "No reference file exists." >&2
        echo -e "\t"$ref_def
        exit 5
      fi
      ;;
    -p|--nb_threads)
      if [[ $2 =~ ^[\-0-9]+$ ]] && (( $2 > 0)); then
        nb_threads="$2"
        shift # pass argument
        shift # pass value
      else
        echo "-p/--nb_threads positive integer required." >&2
        echo -e "\t"$nb_threads_def
        exit 5
      fi
      ;;
    -o|--output)
      	output="$2"
        shift # pass argument
        shift # pass value
      ;;
    -h|--help) # Print help
      echo "Usage: 6mASCOPE contam -c <CCS.fasta> -r <reference> -o <output> [-p <nb_threads>]" >&2
      echo -e "\tAdditional information can be found in our GitHub repository." >&2
      exit 3
      ;;
    *) # unknown option
      echo "Option $1 isn't recognized." >&2
      exit 3
      ;;
  esac
done

## Check that all parameters are set
flag_mp=0 # Flag for missing parameters
 
# Parallelization parameters
if [ -z "$ccs" ]; then
  flag_mp=1 && echo -e "-c/--ccs is missing. \n\t$ccs_def" >&2
fi
if [ -z "$ref" ]; then
  flag_mp=1 && echo -e "-r/--ref is missing. \n\t$ref_def" >&2
fi
if [ -z "$output" ]; then
  flag_mp=1 && echo -e "-o/--output is missing. \n\t$output_def" >&2
fi
# Exit if missing parameters
if [ $flag_mp -eq 1 ]; then
  echo "Usage: 6mASCOPE contam -c <CCS.fasta> -r <reference> -o <output> [-p <nb_threads>]" >&2
  echo -e "\nPlease provide the parameters mentioned above and run again." >&2
  exit 4
fi

refbase="${ref##*/}"
ccsbase="${ccs##*/}"

if [[ -d $ccsbase.$refbase.mapped ]]; then
        rm -r $ccsbase.$refbase.mapped
fi
if [[ -d $ccsbase.$refbase.unmapped ]]; then
        rm -r $ccsbase.$refbase.unmapped
fi

mkdir $ccsbase.$refbase.mapped $ccsbase.$refbase.unmapped
echo -n "["`date`"] "
echo "Map to the genome of interest..."
minimap2 -x sr -N 20 -a -o $ccsbase.$refbase.mapped/$ccs.goi.minimap2.out $ref $ccs 2>/dev/null
samtools view -F 4 $ccsbase.$refbase.mapped/$ccs.goi.minimap2.out >$ccsbase.$refbase.mapped/$ccs.goi.ref.minimap2.mapped
echo -n "["`date`"] "
echo "Separate unmapped molecules..." 

perl ~/code/remove_chimeric_reads.pl $ccs $ccsbase.$refbase.mapped/$ccs.goi.minimap2.out $ccsbase.$refbase.mapped/$ccs.remove.chimeric

rm $ccsbase.$refbase.mapped/$ccs.goi.minimap2.out
perl ~/code/sep_species_ccs_fasta.pl $ccsbase.$refbase.mapped/$ccs.goi.ref.minimap2.mapped $ccsbase.$refbase.mapped/$ccs.remove.chimeric $ccsbase.$refbase.mapped/$ccs.goi $ccsbase.$refbase.unmapped/$ccs.non.goi
allspecies=`grep ">" -c $ccs`
after_chimeric_filter=`grep ">" -c $ccsbase.$refbase.mapped/$ccs.remove.chimeric`
chimeric_reads=`expr $allspecies - $after_chimeric_filter`
inspecies=`grep ">" -c $ccsbase.$refbase.mapped/$ccs.goi`
outspecies=`grep ">" -c $ccsbase.$refbase.unmapped/$ccs.non.goi`
echo -e "Remove $chimeric_reads possible inter-species chimeric reads for further analysis"  >$output
echo -e "#total_CCS\tmapped_to_goi\tcontaminants"  >>$output
inspecies_percent=$(awk -v i=$inspecies -v t=$after_chimeric_filter 'BEGIN { print i/t*100 }')
outspecies_percent=$(awk -v o=$outspecies -v t=$after_chimeric_filter 'BEGIN { print o/t*100 }')
echo -e "$after_chimeric_filter\t$inspecies ($inspecies_percent%)\t$outspecies ($outspecies_percent%)" >>$output
echo -n "["`date`"] "
echo "Search unmapped molecules in NT database..."
blastn -query $ccsbase.$refbase.unmapped/$ccs.non.goi -db /home/6mASCOPE/database/nt-pre-build/nt -out $ccsbase.$refbase.unmapped/$ccs.non.goi.nt.blastn -outfmt 5 -evalue 1e-5 -num_threads 5 -max_target_seqs 1 2>/dev/null
python ~/code/blastxml2tab.py -c ext $ccsbase.$refbase.unmapped/$ccs.non.goi.nt.blastn >$ccsbase.$refbase.unmapped/$ccs.non.goi.nt.blastn.txt
rm $ccsbase.$refbase.unmapped/$ccs.non.goi.nt.blastn
echo >>$output
echo "Top 50 mapped species outside goi reference" >>$output
echo -e "#Count\tSpecies" >>$output
cut -f 1,25 $ccsbase.$refbase.unmapped/$ccs.non.goi.nt.blastn.txt|sort -u|cut -f 2|cut -d " " -f 1,2|sort|uniq -c|sort -nr|head -50 >>$output

echo -n "["`date`"] "
echo "Done."
#cat $output



