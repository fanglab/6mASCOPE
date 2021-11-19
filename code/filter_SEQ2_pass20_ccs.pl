#! /usr/bin/perl 
use warnings;

die "pass.accuracy ccs.fasta\n" if (@ARGV!=2);

open (ACC,$ARGV[0])||die "$!";
while(<ACC>){
	my @i=split /\s+/;
	if ($i[1]>=20){
		$hash{$i[0]}=1;
	}
}
close ACC;


$/="\n>";
open (IPD,$ARGV[1])||die "$!";
while(<IPD>){
	#my @i=split /\s+/;
	if (/>?(.+?)\n(.+)\n>?/s){
		($name,$seq)=($1,$2);
		$seq=~s/\s//g;
		if (defined $hash{$name}){
			print ">$name\n$seq\n";
		}
	}
		
}
close IPD;
$/="\n";
