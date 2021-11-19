#! /usr/bin/env perl
use strict;
use warnings;

my $usage="perl $0 [CCS fasta file] [subread bam file] [subreads bam header] [output_dir] [cut_num]\n";
die $usage if (@ARGV!=5);

my($faf,$sbam,$hea,$op,$num)=@ARGV;

my $core=1;
my $file=0;
my $pwd=`pwd`;
chomp $pwd;
mkdir $op;mkdir "$op/$core";mkdir "$op"."_shell";
open(SH, ">$op"."_shell/$op.$core.sh") or die "";
print SH "for subread in ";
my %hold;
open IN1,$faf or die "open infile1 error:$!\n";
$/='>';<IN1>;$/="\n";
while (<IN1>){
		chomp;
		my $name=$_;
		$/='>';
        if ($file == $num){
                print SH <<END_OF_STRING;

do
cat $pwd/$hea $pwd/$op/$core/\$subread/\$subread.sam |samtools view -S -b >$pwd/$op/$core/\$subread/\$subread.bam
samtools faidx $pwd/$op/$core/\$subread/\$subread.fa
pbalign --quiet $pwd/$op/$core/\$subread/\$subread.bam $pwd/$op/$core/\$subread/\$subread.fa $pwd/$op/$core/\$subread/\$subread.pbalign.bam
ipdSummary $pwd/$op/$core/\$subread/\$subread.pbalign.bam --reference $pwd/$op/$core/\$subread/\$subread.fa --quiet --identify m6A,m4C --methylFraction --bigwig $pwd/$op/$core/\$subread/\$subread.bigwig --gff $pwd/$op/$core/\$subread/\$subread.gff --csv $pwd/$op/$core/\$subread/\$subread.csv
awk -F "," '{print \$1"\\t"\$2"\\t"\$3"\\t"\$4"\\t"\$10"\\t"\$8"\\t"\$6"\\t"\$9"\\t"\$7"\\t"\$5}' $pwd/$op/$core/\$subread/\$subread.csv|sed -e 's/\"//g'  > $pwd/$op/$core/\$subread/\$subread.ipd.out
perl ~/code/post_ipd_fasta_filter.pl $pwd/$op/$core/\$subread/\$subread.ipd.out $pwd/$op/$core/\$subread/\$subread.fa 10 >$pwd/$op/$core/\$subread/\$subread.ipd.out.middle
cat $pwd/$op/$core/\$subread/\$subread.ipd.out.middle >>$pwd/$op/$core/$op.$core.ipd.out
done
END_OF_STRING
close SH;
                $file=1;
                $core++;
                mkdir "$op/$core";
                open(SH, ">$op"."_shell/$op.$core.sh") or die "";
                print SH "for subread in ";
        }
        else{
                $file++;
        }
		my $subread=$1 if ($name =~ /^\S+\/(\S+)\/ccs/);
			$hold{$subread}=$core;
		my $seq=<IN1>;
		chomp $seq;
		$/="\n";
		mkdir  "$op/$core/$subread";
        open(OUT, ">$op/$core/$subread/$subread.fa") or die "";
			print OUT ">$name\n$seq";
		close OUT;
		print SH "$subread ";
		#last if ($core >=200);
}
close IN1;

print SH <<END_OF_STRING;

do
cat $pwd/$hea $pwd/$op/$core/\$subread/\$subread.sam |samtools view -S -b >$pwd/$op/$core/\$subread/\$subread.bam
samtools faidx $pwd/$op/$core/\$subread/\$subread.fa
pbalign --quiet $pwd/$op/$core/\$subread/\$subread.bam $pwd/$op/$core/\$subread/\$subread.fa $pwd/$op/$core/\$subread/\$subread.pbalign.bam
ipdSummary $pwd/$op/$core/\$subread/\$subread.pbalign.bam --reference $pwd/$op/$core/\$subread/\$subread.fa --quiet --identify m6A,m4C --methylFraction --bigwig $pwd/$op/$core/\$subread/\$subread.bigwig --gff $pwd/$op/$core/\$subread/\$subread.gff --csv $pwd/$op/$core/\$subread/\$subread.csv
awk -F "," '{print \$1"\\t"\$2"\\t"\$3"\\t"\$4"\\t"\$10"\\t"\$8"\\t"\$6"\\t"\$9"\\t"\$7"\\t"\$5}' $pwd/$op/$core/\$subread/\$subread.csv|sed -e 's/\"//g'  > $pwd/$op/$core/\$subread/\$subread.ipd.out
perl  ~/code/post_ipd_fasta_filter.pl $pwd/$op/$core/\$subread/\$subread.ipd.out $pwd/$op/$core/\$subread/\$subread.fa 10 >$pwd/$op/$core/\$subread/\$subread.ipd.out.middle
cat $pwd/$op/$core/\$subread/\$subread.ipd.out.middle >>$pwd/$op/$core/$op.$core.ipd.out
done
END_OF_STRING
close SH;

open(RU, ">$op"."_shell/$op.run.sh") or die "";
for(my $i=1;$i<=$core;$i++){
	print RU "sh $pwd/$op"."_shell/$op.$i.sh\n";
}
close RU;

open(CO, ">$op"."_shell/$op.combine.sh") or die "";
print CO <<END_OF_STRING;
for x in {1..$core}
do
cat $pwd/$op/"\$x"/$op."\$x".ipd.out 
done >$pwd/$op/$op.ipd.out
END_OF_STRING
close CO;
		

open IN2, "samtools view $sbam|" or die "open infile2 error:$!\n";
while (<IN2>){
	my @t = split(/\t/,$_);
	my $name=$1 if ($t[0] =~ /^\S+\/(\S+)\/\S+/);
	if (exists $hold{$name}){
		my $value=$hold{$name};
		open(OUT2, ">>$pwd/$op/$value/$name/$name.sam") or die "";
              		print OUT2 $_;
		close OUT2;
	}
}
close IN2;


