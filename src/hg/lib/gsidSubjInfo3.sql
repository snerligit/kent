CREATE TABLE gsidSubjInfo3 (
  subjId varchar(255) NOT NULL default '',
  age varchar(255) NOT NULL default '',
  gender varchar(255) NOT NULL default '',
  race varchar(255) NOT NULL default '',
  weight varchar(255) NOT NULL default '',
  immunStatus varchar(255) NOT NULL default '',
  geography varchar(255) NOT NULL default '',
  injections int(11) NOT NULL default '0',
  riskFactor varchar(255) NOT NULL default '',
  daysInfectF int(11) NOT NULL default '0',
  daysInfectL int(11) NOT NULL default '0',
  newField1 varchar(255) NOT NULL default '',
  newField2 varchar(255) NOT NULL default '',
  comment varchar(255) NOT NULL default '',
  KEY subjId (subjId)
) TYPE=MyISAM;

