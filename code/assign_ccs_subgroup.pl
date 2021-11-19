#! /usr/bin/env perl

use warnings;

die "reads reads.ref.minimap2.mapped reads.non.pre.nt.blastn.tab GOI.prefix subgroup reads.subgroup.txt reads.proportion.txt" if (@ARGV!=7);

my ($reads,$refmap,$ntmap,$pre,$subgroup,$readsgrouplist,$readsprop)=@ARGV;

open (REF,$refmap)||die "$!";

while(<REF>){
	my @i=split /\s+/;
	$group{$i[0]}=$pre;
}
close REF;

my @gorder=();
open (GROUP,$subgroup)||die "$!";
while(<GROUP>){
        my @i=split /\s+/;
        $allgroup{$i[1]}=$i[0];
        push (@gorder,$i[0]);

}
close GROUP;

open(BLAST,$ntmap)||die "$!";
while(<BLAST>){
        $line=$_;
        my $reads=(split /\s+/,$line)[0];
        foreach $g(keys %allgroup){
                if ($line=~m/$g/){
                        $group{$reads}=$allgroup{$g};
                }
        }
}
close BLAST;

open(RDGP,">$readsgrouplist")||die "$!";
open(RD,$reads)||die "$!";

my %count;
my $total=0;
while(<RD>){
	if (/>(.+)/){
		$oneread=$1;
		$total++;
		print RDGP "$oneread\t";
		if (defined $group{$oneread}){
			$count{$group{$oneread}}++;
			print RDGP "$group{$oneread}\n";
		}
		else{
			print RDGP "others\n";
			$count{"others"}++;
		}
	}
}
close RD;
close RDGP;


open(RDPR,">$readsprop")||die "$!";
printf RDPR "#Subgroup\tcount\tProportion\n";
$k=$pre;
printf RDPR "%s\t%d\t%.4f\n",$k,$count{$k},$count{$k}/$total;
delete $count{$k};

$k="others";
$others=sprintf "%s\t%d\t%.4f\n", $k,$count{$k},$count{$k}/$total;
delete $count{$k};

foreach $k (@gorder){
	printf RDPR "%s\t%d\t%.4f\n",$k,$count{$k},$count{$k}/$total;
}
print RDPR "$others";
close RDPR;










