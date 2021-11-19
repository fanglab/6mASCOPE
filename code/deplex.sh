#!/usr/bin/env bash

###
# Wrapper for raw data demultiplex
###

## Describe parameters
nb_jobs_def="Specify how many jobs to run in parallel (affect CPU and memory usage).[5]"
barcode_def="Barcode fasta file."
raw_def="Specify raw bam file to be de-multiplexed."
output_def="Prefix for the output file"

## Default parameters
nb_threads=5

# Read options
while [[ $# -gt 0 ]]; do
  key="$1"

  case $key in
    -b|--barcode)
      if [[ -f $2 ]] ; then
        barcode="$2"
        shift # pass argument
        shift # pass value
      else
        echo "No barcode.fasta file exist" >&2
        echo -e "\t"$barcode_def
        exit 5
      fi
      ;;
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
    -o|--output)
      	output="$2"
        if ! [[ $2 =~ .bam$ ]]; then
          output=$output".bam"
        fi
        shift # pass argument
        shift # pass value
      ;;
    -h|--help) # Print help
      echo "Usage: 6mASCOPE deplex -b <barcode.fasta> -i <raw.bam> -o <prefix.bam> [-p <nb_threads>]" >&2
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
if [ -z "$barcode" ]; then
  flag_mp=1 && echo -e "-b/--barcode is missing. \n\t$barcode_def" >&2
fi
if [ -z "$raw" ]; then
  flag_mp=1 && echo -e "-i/--input is missing. \n\t$raw_def" >&2
fi
if [ -z "$output" ]; then
  flag_mp=1 && echo -e "-o/--output is missing. \n\t$output_def" >&2
fi
# Exit if missing parameters
if [ $flag_mp -eq 1 ]; then
  echo "Usage: 6mASCOPE deplex -b <barcode.fasta> -i <raw.bam> -o <prefix.bam> [-p <nb_threads>]" >&2
  echo -e "\nPlease provide the parameters mentioned above and run again." >&2
  exit 4
fi

lima $raw $barcode $output --same --split-bam-named --peek 50000 --guess 45 --guess-min-count 10 --num-threads $nb_threads


