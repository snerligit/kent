# dnaProbe.sql was originally generated by the autoSql program, which also 
# generated dnaProbe.c and dnaProbe.h.  This creates the database representation of
# an object which can be loaded and saved from RAM in a fairly 
# automatic way.

#data about a dna probe used for microarrays
CREATE TABLE dnaProbe (
    name varchar(255) not null,	# name of the dna probe
    dna varchar(255) not null,	# sequence of probe, {a,t,g,c}
    size int not null,	# size of sequence
    chrom varchar(255) not null,	# chromosome that sequence is from
    start int not null,	# start position in chromosome
    end int not null,	# end position in chromosome
    strand char(3) not null,	# strand that probe is on
    tpDist int not null,	# distance of from three prime end
    tm float not null,	# extimated binding tm
    pGC float not null,	# percentage of bases that are g's and c's
    affyHeur int not null,	# 1 if oligo passes affyMetrix heuristic, 0 otherwise
    secStruct float not null,	# gibbs free energy of secondary structure, higher is better
    blatScore int not null,	# blat score of the second greatest region of homology
    comparison float not null,	# weighted average of other scores used for comparison
              #Indices
    index(name)
);
