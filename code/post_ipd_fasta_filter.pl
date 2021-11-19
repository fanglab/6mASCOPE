#! /usr/bin/env perl
use warnings;

die "IPD.out fasta head-tail-len\n" if (@ARGV!=3);

my($file,$fa,$head)=@ARGV;

$/="\n>";
open(FA,$fa)||die "$!";
while(<FA>){
	if(/>?(.+?)\n(.+)\n>?/s){
		($name,$seq)=($1,$2);
		$seq=~s/\s//g;
		$hash{$name}=length($seq);
	}
}
close FA;
$/="\n";

open(IPD,$file)||die "$!";
while(<IPD>){
	if (/\w/){
	my @i=split /\s+/;
	if (defined $hash{$i[0]}){

		if ($i[1]<$head){
			next;
			#print join("\t",@i)."\t"."head\n";
		}
		elsif($hash{$i[0]}-$i[1]<$head){
			next;
			#print join("\t",@i)."\t"."tail\n";
		}
		else{
			print join("\t",@i)."\n";
		}
	}
	}


}
close IPD;

