mkdir test
cd test
wget "https://6mascope-test-data.s3.us-east-2.amazonaws.com/test.ccs.fasta.gz"
wget "https://6mascope-test-data.s3.us-east-2.amazonaws.com/test.IPD.out.A.gz"
wget "https://6mascope-test-data.s3.us-east-2.amazonaws.com/subgroup.txt"
wget "https://6mascope-test-data.s3.us-east-2.amazonaws.com/test.ref.fasta.gz"
gunzip test.ccs.fasta.gz 
gunzip test.IPD.out.A.gz
gunzip test.ref.fasta.gz

