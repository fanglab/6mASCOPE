#!/usr/bin/env bash

###
# Wrapper for raw data demultiplex
###

## Describe parameters
nb_jobs_def="Specify how many jobs to run in parallel (affect CPU and memory usage).[5]"
raw_def="Specify raw bam file."
outbam_def="Output ccs bam file (output.ccs.bam) or prefix (output)"
outfasta_def="Output fasta file (output.ccs.fasta)"

## Default parameters
nb_threads=5

# Read options
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -i|--input)
      if [[ -f $2 ]] ; then
        raw="$2"
        shift # pass argument
        shift # pass value
      else
        echo "No raw bam file exists." >&2
        echo -e "\t"$raw_def
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
    -ob|--outbam)
        output="$2"
        if ! [[ $2 =~ .bam$ ]]; then
        output=$output".bam"
        fi
        shift # pass argument
        shift # pass value
      ;;
    -of|--outfasta)
        fasta="$2"
        shift # pass argument
        shift # pass value
      ;;

    -h|--help) # Print help
      echo "Usage: 6mASCOPE ccs -i <raw.bam> -ob <prefix.ccs.bam> -of <prefix.ccs.fasta> [-p <nb_threads>]" >&2
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
if [ -z "$raw" ]; then
  flag_mp=1 && echo -e "-i/--input is missing. \n\t$raw_def" >&2
fi
if [ -z "$output" ]; then
  flag_mp=1 && echo -e "-ob/--outbam is missing. \n\t$outbam_def" >&2
fi
if [ -z "$fasta" ]; then
  flag_mp=1 && echo -e "-of/--outfasta is missing. \n\t$outfasta_def" >&2
fi
# Exit if missing parameters
if [ $flag_mp -eq 1 ]; then
  echo "Usage: 6mASCOPE ccs -i <raw.bam> -ob <prefix.ccs.bam> -of <prefix.ccs.fasta>" >&2
  echo -e "\nPlease provide the parameters mentioned above and run again." >&2
  exit 4
fi

ccs --minPredictedAccuracy 0.99 --num-threads $nb_threads --logFile $output.log $raw $output
samtools fastq $output|seqtk seq -A - > $fasta.tmp__ 
samtools view $output|cut -f 1,15,16|sed -e 's/np:i://' -e 's/rq:f://' >$output.accuracy
perl ~/code/filter_SEQ2_pass20_ccs.pl $output.accuracy $fasta.tmp__ >$fasta 
rm $output.accuracy $fasta.tmp__ 



