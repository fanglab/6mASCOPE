#! /usr/bin/env perl
use warnings;

die "fasta minimap2 output\n" if (@ARGV!=3);

my($fa,$mm2,$out)=@ARGV;

sub check_flag(){
	$left=0;
	$right=0;
	my ($flag,$map)=@_;
	if (($flag & 4) ==0 ){                      
        if (($flag & 16) == 0 ) { ## forwad strand
        	if ($map=~m/^(\d+)[SH]/){
				$clip=$1;
				#print $clip."----1\n";
				if ($clip >=50) {
					$left=1;					
				}
			}
			if ($map=~m/(\d+)[SH]$/){
				$clip=$1;
				#print $clip."----2\n";
				if ($clip >=50) {
					$right=-1;					
				}
			}
        }
        else{
        	if ($map=~m/^(\d+)[SH]/){
        		$clip=$1;
        		#print $clip."----3\n";
				if ($clip >=50) {
					$right=-1;					
				}
			}
			if ($map=~m/(\d+)[SH]$/){
				$clip=$1;
				#print $clip."----4\n";
				if ($clip >=50) {
					$left=1;					
				}
			}
        }
    	$score=$left+$right;
    	
	}
	else{
		$score=0;
	}
	return $score;
}


open (MM,$mm2)||die "$!";
while (<MM>){
	if (/^\w/){
		my @i=split /\s+/;
		#print $i[0]."\n";
		$tag= & check_flag ($i[1],$i[5]);
		$hash{$i[0]}+=$tag;

	}
}
close MM;

open (OUT,">".$out)||die "$!";
$/="\n>";
open(FA,$fa)||die "$!";
while(<FA>){
	if (m/>?(.+?)\n(.+)\n>?/s){
		($name,$seq)=($1,$2);
		#print $name;
		if ($hash{$name} ==0 ){
			print OUT ">$name\n$seq\n";
		}
	}
}

$/="\n";
close FA;
close OUT;




