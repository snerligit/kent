# clusterInputAwgDnase.sql was originally generated by the autoSql program, which also 
# generated clusterInputAwgDnase.c and clusterInputAwgDnase.h.  This creates the database representation of
# an object which can be loaded and saved from RAM in a fairly 
# automatic way.

#Information on ENCODE analysis (AWG) data used as input for DNase clustering
CREATE TABLE clusterInputAwgDnase (
    tableName varchar(255) not null,	# Name of table used as an input
    cellType varchar(255) not null,	# Name of cell type
    treatment varchar(255) not null,	# Drug or other treatment given to cells while alive
    lab varchar(255) not null,	# Lab this was done in
              #Indices
    PRIMARY KEY(tableName)
);
