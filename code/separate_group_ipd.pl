#! /usr/bin/env perl

use warnings;

die "ipd ccs.sg.txt GOI.prefix\n" if (@ARGV!=3);

my ($ccs,$sg,$pre)=@ARGV;

open(SG,$sg)||die "$!";
while(<SG>){
	if (/^\w/){
		my @i=split /\s+/;
		$ccssg{$i[0]}=$i[1];
	}
}

close SG;

open(IPD,$ccs)||die "$!";
open (GOI,">".$ccs.".Genome_of_interest")||die "$!";
while(<IPD>){
	$line=$_;
	my @i=split /\s+/,$line;
	if (defined $ccssg{$i[0]} && $ccssg{$i[0]} eq $pre){
		print GOI "$line";
	}
	else{
		$allsgccs{$ccssg{$i[0]}}.=$line;
	}
}
close IPD;
close GOI;

foreach $subgroup(keys %allsgccs){
	open (OUT,">".$ccs.".$subgroup")||die "$!";
	print OUT $allsgccs{$subgroup};
	close OUT;
}
