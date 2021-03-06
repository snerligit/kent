# affyPairs.sql was originally generated by the autoSql program, which also 
# generated affyPairs.c and affyPairs.h.  This creates the database representation of
# an object which can be loaded and saved from RAM in a fairly 
# automatic way.

#Representation of the 'pairs' file format from the Affymetrix transcriptome data
CREATE TABLE affyPairs (
    x int unsigned not null,	# X, the x-coordinate of the perfect-complement oligo on the chip.
    y int unsigned not null,	# Y, the y-coordinate of the perfect-complement oligo on the chip.
    probeSet varchar(255) not null,	# set, the probe set.
    method varchar(255) not null,	# Method (not informative)
    tBase int unsigned not null,	# tBase, the target base (base in target at central position of 25-mer probe).
    pos int unsigned not null,	# Pos, the position in the probeset of the central base of the probe.
    pm float not null,	# PM, the perfect-complement probe intensity.
    pms float not null,	# PM.s, the standard deviation of the pixels in the perfect-complement feature.
    pmp float not null,	# PM.p, the number of pixel used in the perfect-complement feature.
    mm float not null,	# MM, the mismatch-complement probe intensity.
    mms float not null,	# MM.s, the standard deviation of the pixels in the mismatch-complement feature.
    mmp float not null,	# MM.p, the number of pixel used in the mismatch-complement feature. 
              #Indices
    PRIMARY KEY(x)
);
