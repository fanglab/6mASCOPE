if [ $# -ne 2 ] ; then
    echo "USAGE: $0 [IPD.out] [prefix]"
    exit 1;
fi

x=$1
myprefix=$2

#module load python/2.7.16
awk '$4=="A"&&$8<=7' "$x" >"$x".A.7
python ~/code/get_num_slope.py "$x".A.7 >"$x".A.7.overslope.txt
python ~/code/model_predict_n_CI.py /home/6mASCOPE/database/model/RF.pickle /home/6mASCOPE/database/model/RF.CI.txt "$x".A.7.overslope.txt $myprefix

rm "$x".A.7 "$x".A.7.overslope.txt #myprefix
