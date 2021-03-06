#!/usr/bin/env python3

import json
import re
from warnings import warn

with open('ncov.json') as f:
    ncov = json.load(f)

chrom = 'NC_045512v2'

# Genes (to which AA mutations are relative):
genePos = {}
geneBed = []
for gene,anno in ncov['meta']['genome_annotations'].items():
    if (gene != 'nuc'):
        genePos[gene] = anno['start'] - 1
        geneBed.append([chrom, anno['start']-1, anno['end'], gene])
def bedStart(bed):
    return bed[1]
geneBed.sort(key=bedStart)
with open('nextstrainGene.bed', 'w') as outG:
    for bed in geneBed:
        outG.write('\t'.join(map(str, bed)) + '\n')
    outG.close()

# Variants and "clades"

snvRe = re.compile('^([ACGT])([0-9]+)([ACGT])$')
snvAaRe = re.compile('^([A-Z*])([0-9]+)([A-Z*])$')

clades = {}
cladeNodes = {}
variantCounts = {}
variantAaChanges = {}
samples = []

cladeColors = { 'A1a': '73,75,225', 'A2': '75,131,233', 'A2a': '92,173,207',
                'A3': '119,199,164', 'A6': '154,212,122', 'A7': '173,189,81',
                'B': '233,205,74', 'B1': '255,176,65', 'B2': '255,122,53',
                'B4': '249,53,41' }

def cladeColorFromName(cladeName):
    color = cladeColors.get(cladeName);
    if (not color):
        color = '0,0,0'
    return color

def subtractStart(coord, start):
    return coord - start

def cladeFromVariants(name, variants, varStr):
    """Extract bed12 info from an object whose keys are SNV variant names"""
    clade = {}
    snvEnds = []
    varNames = []
    for varName in variants:
        m = snvRe.match(varName)
        if (m):
            snvEnds.append(int(m.group(2)))
            varNames.append(varName)
    if snvEnds:
        snvEnds.sort()
        snvStarts = list(map(lambda x: x-1, snvEnds))
        snvSizes = list(map(lambda x: 1, snvEnds))
        clade['thickStart'] = min(snvStarts)
        clade['thickEnd'] = max(snvEnds)
        clade['name'] = name
        clade['color'] = cladeColorFromName(name)
        clade['varSizes'] = snvSizes
        clade['varStarts'] = snvStarts
        clade['varNames'] = varStr
    return clade

def addDatesToClade(clade, numDateAttrs):
    """Add the numeric dates from ncov.json node_attrs.num_date to clade record"""
    clade['dateInferred'] = numDateAttrs['value']
    clade['dateConfMin'] = numDateAttrs['confidence'][0]
    clade['dateConfMax'] = numDateAttrs['confidence'][1]

def addCountryToClade(clade, countryAttrs):
    """Add country data from ncov.json node_attrs.country to clade"""
    clade['countryInferred'] = countryAttrs['value']
    confString = ''
    for country, conf in countryAttrs['confidence'].items():
        if (len(confString)):
            confString += ', '
        confString += "%s: %0.5f" % (country, conf)
    clade['countryConf'] = confString

def numDateToYmd(numDate):
    """Convert numeric date (decimal year) to integer year, month, day"""
    year = int(numDate)
    isLeapYear = 1 if (year % 4 == 0) else 0
    # Get rid of the year
    numDate -= year
    # Convert to Julian day
    daysInYear = 366 if isLeapYear else 365
    jDay = int(numDate * daysInYear) + 1
    if (jDay > 334 + isLeapYear):
        month, day = 11, (jDay - 334 - isLeapYear)
    elif (jDay > 304 + isLeapYear):
        month, day = 10, (jDay - 304 - isLeapYear)
    elif (jDay > 273 + isLeapYear):
        month, day = 9, (jDay - 273 - isLeapYear)
    elif (jDay > 243 + isLeapYear):
        month, day = 8, (jDay - 243 - isLeapYear)
    elif (jDay > 212 + isLeapYear):
        month, day = 7, (jDay - 212 - isLeapYear)
    elif (jDay > 181 + isLeapYear):
        month, day = 6, (jDay - 181 - isLeapYear)
    elif (jDay > 151 + isLeapYear):
        month, day = 5, (jDay - 151 - isLeapYear)
    elif (jDay > 120 + isLeapYear):
        month, day = 4, (jDay - 120 - isLeapYear)
    elif (jDay > 90 + isLeapYear):
        month, day = 3, (jDay - 90 - isLeapYear)
    elif (jDay > 59 + isLeapYear):
        month, day = 2, (jDay - 59 - isLeapYear)
    elif (jDay > 31):
        month, day = 1, (jDay - 31)
    else:
        month, day = 0, jDay
    return year, month, day

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

def numDateToMonthDay(numDate):
    """Transform decimal year timestamp to string with only month and day"""
    year, month, day = numDateToYmd(numDate)
    return months[month] + str(day)

def numDateToYmdStr(numDate):
    """Convert decimal year to YY-MM-DD string"""
    year, month, day = numDateToYmd(numDate)
    return "%02d-%02d-%02d" % (year, month+1, day)

def rUnpackNextstrainTree(branch, parentVariants, parentVarStr):
    """Recursively descend ncov.tree and build data structures for genome browser tracks"""
    # Gather variants specific to this node/branch (if any)
    localVariants = []
    if (branch.get('branch_attrs') and branch['branch_attrs'].get('mutations') and
        branch['branch_attrs']['mutations'].get('nuc')):
        # Nucleotide variants specific to this branch
        for varName in branch['branch_attrs']['mutations']['nuc']:
            if (snvRe.match(varName)):
                localVariants.append(varName)
                if (not variantCounts.get(varName)):
                    variantCounts[varName] = 0;
        # Amino acid variants: figure out which nucleotide variant goes with each
        for geneName in branch['branch_attrs']['mutations'].keys():
            if (geneName != 'nuc'):
                for change in branch['branch_attrs']['mutations'][geneName]:
                    # Get nucleotide coords & figure out which nuc var this aa change corresponds to
                    aaM = snvAaRe.match(change)
                    if (aaM):
                        aaRef, aaPos, aaAlt = aaM.groups()
                        varStartMin = (int(aaPos) - 1) * 3
                        if (genePos.get(geneName)):
                            cdsStart = genePos.get(geneName)
                            varStartMin += cdsStart
                            varStartMax = varStartMin + 2
                            for varName in localVariants:
                                ref, pos, alt = snvRe.match(varName).groups()
                                pos = int(pos) - 1
                                if (pos >= varStartMin and pos <= varStartMax):
                                    variantAaChanges[varName] = geneName + ':' + change
                        else:
                            warn("Can't find start for gene " + geneName)
                    else:
                        warn("Can't match amino acid change" + change)
    # Inherit parent variants
    branchVariants = parentVariants.copy()
    # Add variants specific to this branch (if any)
    for varName in localVariants:
        branchVariants[varName] = 1
    # Make an ordered variant string as David requested: semicolons between nodes,
    # comma-separated within a node:
    branchVarStr = ''
    for varName in localVariants:
        if (len(branchVarStr)):
            branchVarStr += ', '
        branchVarStr += varName
        aaVar = variantAaChanges.get(varName)
        if (aaVar):
            branchVarStr += ' (' + aaVar + ')'
    if (len(parentVarStr) and len(branchVarStr)):
        branchVarStr = parentVarStr + '; ' + branchVarStr
    nodeAttrs = branch['node_attrs']
    if (nodeAttrs.get('clade_membership')):
        cladeName = nodeAttrs['clade_membership']['value']
        if (cladeName != 'unassigned' and not cladeName in clades):
            clades[cladeName] = cladeFromVariants(cladeName, branchVariants, branchVarStr)
            addDatesToClade(clades[cladeName], nodeAttrs['num_date'])
            if (nodeAttrs.get('country')):
                addCountryToClade(clades[cladeName], nodeAttrs['country'])
            elif (nodeAttrs.get('division')):
                addCountryToClade(clades[cladeName], nodeAttrs['division'])
            else:
                warn('No country or division for new clade ' + cladeName)
            cladeNodes[cladeName] = branch
    kids = branch.get('children')
    if (kids):
        for child in kids:
            rUnpackNextstrainTree(child, branchVariants, branchVarStr);
    else:
        for varName in branchVariants:
            variantCounts[varName] += 1
        samples.append({ 'id': nodeAttrs['gisaid_epi_isl']['value'],
                         'name': branch['name'],
                         'clade': nodeAttrs['clade_membership']['value'],
                         'date': numDateToMonthDay(nodeAttrs['num_date']['value']),
                         'variants': branchVariants })

rUnpackNextstrainTree(ncov['tree'], {}, '')

sampleCount = len(samples)
sampleNames = [ '|'.join([sample['id'], sample['name'], sample['date']]) for sample in samples ]

# Parse variant names like 'G11083T' into pos and alleles; bundle in VCF column order
parsedVars = []
for varName in variantCounts.keys():
    m = snvRe.match(varName)
    if (m):
        ref, pos, alt = m.groups()
        parsedVars.append([int(pos), varName, ref, alt])
    else:
        warn("Can't match " + varName)
# Sort by position
def parsedVarPos(pv):
    return pv[0]
parsedVars.sort(key=parsedVarPos)

def boolToStr01(bool):
    """Convert boolean to string 1 or 0."""
    if (bool):
        return '1'
    else:
        return '0'

def writeVcfHeaderExceptSamples(outF):
    """Write VCF header lines -- except for sample names (this ends with a \t not a \n)."""
    outF.write('##fileformat=VCFv4.3\n')
    outF.write('##source=nextstrain.org\n')
    outF.write('\t'.join(['#CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'INFO', 'FORMAT']) +
               '\t');

# VCF
with open('nextstrainSamples.vcf', 'w') as outC:
    writeVcfHeaderExceptSamples(outC)
    outC.write('\t'.join(sampleNames) + '\n')
    for pv in parsedVars:
        varName = pv[1]
        info = 'AC=' + str(variantCounts[varName]) + ';AN=' + str(sampleCount)
        aaChange = variantAaChanges.get(varName)
        if (aaChange):
            info += ';AACHANGE=' + aaChange
        genotypes = []
        for sample in samples:
            gt = boolToStr01(sample['variants'].get(varName))
            genotypes.append(gt + ':' + sample['clade'])
        outC.write('\t'.join([ chrom,
                               '\t'.join(map(str, pv)),
                               '\t'.join(['.', 'PASS', info, 'GT:CLADE']),
                               '\t'.join(genotypes) ]) + '\n')
    outC.close()

# Assign samples to clades; a sample can appear in multiple clades if they are nested.
cladeSamples = {}
cladeSampleCounts = {}
cladeSampleNames = {}

def sampleIdsFromNode(node, ids):
    """Fill in a dict of IDs of all samples found under node."""
    kids = node.get('children')
    if (kids):
        for kid in kids:
            sampleIdsFromNode(kid, ids)
    else:
        sampleId = node['node_attrs']['gisaid_epi_isl']['value']
        ids[sampleId] = 1

for cladeName, node in cladeNodes.items():
    sampleIds = {}
    sampleIdsFromNode(node, sampleIds)
    cladeSampleList = [ sample for sample in samples if sample['id'] in sampleIds ]
    cladeSamples[cladeName] = cladeSampleList
    cladeSampleCounts[cladeName] = len(cladeSampleList)
    cladeSampleNames[cladeName] = [ '|'.join([ sample['id'], sample['name'], sample['date'] ])
                                    for sample in cladeSampleList ]

# Per-clade VCF subset
for cladeName, cladeSampleList in cladeSamples.items():
    with open('nextstrainSamples' + cladeName + '.vcf', 'w') as outV:
        writeVcfHeaderExceptSamples(outV)
        outV.write('\t'.join(cladeSampleNames[cladeName]) + '\n')
        for pv in parsedVars:
            varName = pv[1]
            genotypes = []
            ac=0
            for sample in cladeSampleList:
                gt = boolToStr01(sample['variants'].get(varName))
                genotypes.append(gt)
                if (sample['variants'].get(varName)):
                    ac += 1
            if (ac > 0):
                info = 'AC=' + str(ac) + ';AN=' + str(cladeSampleCounts[cladeName])
                aaChange = variantAaChanges.get(varName)
                if (aaChange):
                    info += ';AACHANGE=' + aaChange
                outV.write('\t'.join([ chrom,
                                       '\t'.join(map(str, pv)),
                                       '\t'.join(['.', 'PASS', info, 'GT']),
                                       '\t'.join(genotypes) ]) + '\n')
        outV.close()

# BED+ file for clades
with open('nextstrainClade.bed', 'w') as outC:
    for name, clade in clades.items():
        if (clade.get('thickStart')):
            outC.write('\t'.join(map(str,
                                     [ chrom, 0, 29903, name, 0, '.',
                                       clade['thickStart'], clade['thickEnd'], clade['color'],
                                       len(clade['varSizes']) + 2,
                                       '1,' + ','.join(map(str, clade['varSizes'])) + ',1,',
                                       '0,' + ','.join(map(str, clade['varStarts'])) + ',29902,',
                                       clade['varNames'],
                                       numDateToYmdStr(clade['dateInferred']),
                                       numDateToYmdStr(clade['dateConfMin']),
                                       numDateToYmdStr(clade['dateConfMax']),
                                       clade['countryInferred'],
                                       clade['countryConf'],
                                       cladeSampleCounts[name],
                                       ', '.join(cladeSampleNames[name]) ])) + '\n')
    outC.close()

# Newick-formatted tree of samples for VCF display
def cladeRgbFromName(cladeName):
    """Look up the r,g,b string color for clade; convert to int RGB."""
    rgbCommaStr = cladeColorFromName(cladeName)
    r, g, b = [ int(x) for x in rgbCommaStr.split(',') ]
    rgb = (r << 16) | (g << 8) | b
    return rgb

def rNextstrainToNewick(node, parentColor=None):
    """Recursively descend ncov.tree and build Newick tree string of samples to file"""
    kids = node.get('children')
    if (kids):
        nodeAttrs = node['node_attrs']
        if (nodeAttrs.get('clade_membership')):
            cladeName = nodeAttrs['clade_membership']['value']
            color = str(cladeRgbFromName(cladeName))
        elif (parentColor):
            color = parentColor
        else:
            color = '0'
        descendants = ','.join([ rNextstrainToNewick(child, color) for child in kids ])
        treeString = '(' + descendants + ')' + ':' + color
    else:
        nodeAttrs = node['node_attrs']
        gId = nodeAttrs['gisaid_epi_isl']['value']
        name = node['name']
        date = numDateToMonthDay(nodeAttrs['num_date']['value'])
        cladeName = nodeAttrs['clade_membership']['value']
        color = str(cladeRgbFromName(cladeName))
        treeString = '|'.join([ gId, name, date ]) + ':' + color
    return treeString

with open('nextstrain.nh', 'w') as outF:
    outF.write(rNextstrainToNewick(ncov['tree']) + ';\n')
    outF.close

for cladeName, node in cladeNodes.items():
    filename = 'nextstrain' + cladeName + '.nh'
    with open(filename, 'w') as outF:
        outF.write(rNextstrainToNewick(node) + ';\n')
        outF.close
