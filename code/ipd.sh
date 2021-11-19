#!/usr/bin/env bash

###
# Wrapper for single-molecule IPD summarization
###

## Describe parameters
nb_jobs_def="Specify how many jobs to run in parallel (affect CPU and memory usage).[5]"
raw_def="Specify raw bam file."
fasta_def="Specify ccs.fasta file."
output_def="Output file (output.bam) or prefix (output)"

## Default parameters
nb_threads=5

#ccs --minPredictedAccuracy 0.99 --num-threads $cpu --logFile $i.ccs.log $i $i.ccs.bam


# Read options
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -r|--raw)
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
    -f|--fasta)
      if [[ -f $2 ]] ; then
        fasta="$2"
        shift # pass argument
        shift # pass value
      else
        echo "No ccs.fasta exists." >&2
        echo -e "\t"$fasta_def
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
        if ! [[ $2 =~ .bam$ ]]; then
        output=$output".bam"
        fi
      	output="$2"
        shift # pass argument
        shift # pass value
      ;;
    -h|--help) # Print help
      echo "Usage: 6mASCOPE ipd -r <raw.bam> -f <ccs.fasta> -o <Ipd.out> [-p <nb_threads>]" >&2
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
  flag_mp=1 && echo -e "-r/--raw is missing. \n\t$raw_def" >&2
fi
if [ -z "$fasta" ]; then
  flag_mp=1 && echo -e "-f/--fasta is missing. \n\t$fasta_def" >&2
fi
if [ -z "$output" ]; then
  flag_mp=1 && echo -e "-o/--output is missing. \n\t$output_def" >&2
fi
# Exit if missing parameters
if [ $flag_mp -eq 1 ]; then
  echo "Usage: 6mASCOPE ipd -r <raw.bam> -f <ccs.fasta> -o <Ipd.out> [-p <nb_threads>]" >&2
  echo -e "\nPlease provide the parameters mentioned above and run again." >&2
  exit 4
fi


if [[ -d $output.tmp__ ]]; then
	rm -r $output.tmp__
fi
if [[ -d $output.tmp___shell ]]; then
	rm -r $output.tmp___shell
fi

samtools view -H $raw >$raw.head.tmp__
perl /home/6mASCOPE/code/split_SM.pl $fasta $raw $raw.head.tmp__ $output.tmp__ 500
cat $output.tmp___shell/$output.tmp__.run.sh|parallel -j $nb_threads
sh $output.tmp___shell/$output.tmp__.combine.sh
mv $output.tmp__/$output.tmp__.ipd.out $output
rm -r $output.tmp__ $output.tmp___shell $raw.head.tmp__


