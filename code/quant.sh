#!/bin/bash
#module load minimap2 samtools blast python/2.7.16

###
# Wrapper for computing quantify deconvolution
###
# 1. Separate the molecules based on the subgroup provided by the user
# 2. 6mA level estimation for each group
# 3. check 6mA contribution of each group

## Describe parameters
ccs_def="Specify the ccs.fasta file."
ipd_def="Specify the tab-delim file containing IPD and QV information."
sg_def="Specify a .txt containing the subgroup for quantify deconvolution."
ref_def="Specify the reference for the genome of interest."
output_def="output file"


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
    -i|--ipd)
      if [[ -f $2 ]] ; then
        ipd="$2"
        shift # pass argument
        shift # pass value
      else
        echo "No IPD information file exists." >&2
        echo -e "\t"ipd_def
        exit 5
      fi
      ;;
    -r|--ref)
        ref="$2"
        shift # pass argument
        shift # pass value
      ;;
    -s|--sub)
        sg="$2"
        shift # pass argument
        shift # pass value
      ;;
    -o|--output)
      	output="$2"
        shift # pass argument
        shift # pass value
      ;;
    -h|--help) # Print help
      echo "Usage: 6mASCOPE quant -c <CCS.fasta> -i <ipd file> -o <Prefix for output> -r <reference.fasta> -s <subgroup.txt>" >&2
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
if [ -z "$ipd" ]; then
  flag_mp=1 && echo -e "-i/--ipd is missing. \n\t$ipd_def" >&2
fi
if [ -z "$sg" ]; then
  flag_mp=1 && echo -e "-s/--sub is missing. \n\t$sg_def" >&2
fi
if [ -z "ref" ]; then
  flag_mp=1 && echo -e "-r/--ref is missing. \n\tref_def" >&2
fi
if [ -z "$output" ]; then
  flag_mp=1 && echo -e "-o/--output is missing. \n\t$output_def" >&2
fi



# Exit if missing parameters
if [ $flag_mp -eq 1 ]; then
  echo "Usage: 6mASCOPE quant -c <CCS.fasta> -i <ipd file> -o <Prefix for output> -r <reference> -s <subgroup.txt>]" >&2
  echo -e "\nPlease provide the parameters mentioned above and run again." >&2
  exit 4
fi




#echo "...........................assign ccs molecules to different subgroup..........................."


## assign ccs molecules to different subgroup -> write to files
## separate the IPD information files into different groups based on the former file

refbase="${ref##*/}"
ccsbase="${ccs##*/}"



if [[ ! -d $ccsbase.$refbase.mapped || ! -d $ccsbase.$refbase.unmapped ]]; then
	echo -e "\n Did not find the mapping profiles for $ccs" >&2
	echo -e "\n Please generate it using 6mASCOPE contam -c <CCS.fasta> -r <reference> -o output" >&2
  exit 4
fi

echo -n "["`date`"] "
echo "Seperate IPD information to subgroups (goi/contaminant sources)..."
perl ~/code/assign_ccs_subgroup.pl $ccsbase.$refbase.mapped/$ccs.remove.chimeric $ccsbase.$refbase.mapped/$ccs.goi.ref.minimap2.mapped $ccsbase.$refbase.unmapped/$ccs.non.goi.nt.blastn.txt goi $sg $output.sg.txt $output.prop.txt
perl ~/code/get_fasta_ipd.pl $ccsbase.$refbase.mapped/$ccs.remove.chimeric $ipd $ipd.remove.chimeric
perl ~/code/separate_group_ipd.pl $ipd.remove.chimeric $output.sg.txt goi 
#cat $output.prop.txt >&2
rm $output.sg.txt 

echo -n "["`date`"] "
echo "Predict 6mA levels and contribution..."

sh ~/code/predict_6mA_level.sh $ipd.remove.chimeric.Genome_of_interest goi >$output.6mA.level.txt
rm $ipd.remove.chimeric.Genome_of_interest

for x in `cut -f 1 $sg |tr '\n' ' '`;
do
sh ~/code/predict_6mA_level.sh $ipd.remove.chimeric."$x" "$x" >>$output.6mA.level.txt
rm $ipd.remove.chimeric."$x"
done
sh ~/code/predict_6mA_level.sh $ipd.remove.chimeric."others" "others"  >>$output.6mA.level.txt
rm $ipd.remove.chimeric."others"


python ~/code/6mA_contribution.py $output.prop.txt $output.6mA.level.txt $output.6mASCOPE.txt
rm $output.prop.txt $output.6mA.level.txt
#cat $output.6mASCOPE.txt
rm $ipd.remove.chimeric

echo -n "["`date`"] "
echo "Done."











