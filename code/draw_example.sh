#!/bin/bash
if [ $# -ne 1 ];then
echo "Usage: [6mASCOPE.output.txt]"
echo "eg. 1"
exit 0
fi

input=$1


python ~/code/draw_example_pie_percent.py $input $input.ReadsProportion.png
python ~/code/draw_example_subgroup_6mA_CI.py $input $input.6mAlevel.png
python ~/code/draw_example_6mA_contribution.py $input $input.6mAcontribution.png

