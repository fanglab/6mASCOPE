#! /usr/bin/env perl
use warnings;

die "ccs.blast.out ccs.fasta in-species out-species\n" if (@ARGV!=4);

open(CCS,$ARGV[0])||die "$!";
while(<CCS>){
        chomp;
        my @i=split /\s+/;
        $hash{$i[0]}=1;
}

close CCS;

open(INS,">".$ARGV[2])||die "$!";
open(OUTS,">".$ARGV[3])||die "$!";

$/="\n>";
open(IPD,$ARGV[1])||die "$!";
while(<IPD>){
        if (/>?(.+?)\n(.+)\n>?/s){
                #print "$name\n";
                ($name,$seq)=($1,$2);
                $seq=~s/\s//g;
                if (defined $hash{$name}){
                        print INS ">$name\n$seq\n";
                }
                else{
                        print OUTS ">$name\n$seq\n";
                }
        }
}
$/="\n";
close IPD;
close INS;
close OUTS;
