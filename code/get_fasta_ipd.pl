#! /usr/bin/env perl
use warnings;

die "ccs.fasta IPD.all output \n" if (@ARGV!=3);

#$/="\n>";
open(CCS,$ARGV[0])||die "$!";
while(<CCS>){
	if (/>(.+)/){
		$hash{$1}=1;
	}
}

close CCS;
#$/="\n";

open(INS,">".$ARGV[2])||die "$!";


open(IPD,$ARGV[1])||die "$!";
while(<IPD>){
	my $line=$_;
	my @i=split /\s+/;
	if (defined $hash{$i[0]}){
		print INS $line;
	}
}
close IPD;
close INS;
