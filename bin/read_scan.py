#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-

"""Extract data from CamCASP energy-scan files and construct Orient map files.
"""

import argparse
import os
import os.path
import re
import sys

parser=argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
description = """Extract data from one or more CamCASP energy-scan files and construct
Orient map files.
""", epilog="""
One or more directories may be specified. Input and output file names are
relative to each directory, and it's assumed that the same file-names
and other details apply within each directory, if there is more than one.
In the CamCASP output file, columns are numbered from 0. Column 0 is usually
the index. Columns 1, 2 and 3 are the position coordinates and are always
printed. Columns 4-7 give the orientation, and are printed if the --orient
flag is specified. Data columns start at 8, and their energy units are given
in the file. The values for the selected columns are output in the unit
specified.

Columns may be specified by number or by name, e.g. "E(1)elst". The quotes are
needed if the name includes parentheses.

E.g.
~/molecules/bin/read_scan.py scan* --file OUT/V-scan.dat --to V-scan_vdW2.0.grid \\
   --grid vdW2.0.grid --cols "E(1)elst" --unit eV 
""")

parser.add_argument("file", help="Path to CamCASP energy-scan output file")
parser.add_argument("--dirs", help="Directories containing files (default .)",
                    nargs="+", default=["."])
parser.add_argument("--unit", help="Energy unit for output grid", default="au",
                    choices=["cm-1", "eV", "meV", "hartree", "au", "kJ/mol"])
parser.add_argument("--cols", help="Columns to extract", nargs="+")
parser.add_argument("--sum", help="Output sum of specified columns",
                    action="store_true")
parser.add_argument("--index", help="Include index numbers",action="store_true")
parser.add_argument("--orient", help="Include orientation coordinates",
                    action="store_true")
parser.add_argument("-o", "--to", required=True, help="File for output")
parser.add_argument("--grid", help="Grid file containing triangle list")
parser.add_argument("--gridname", 
                    help="Name of grid associated with the points file")
parser.add_argument("--mapname", help="Name of this map")
args = parser.parse_args()

col_name = {
"INDEX": 1,
"E(1)elst": 8,
"E(2)ind": 9,
"E(2)disp": 10,
"E(1)exch": 11,
"E(2)exind": 12,
"E(2)exdisp": 13,
"TotOverlap": 14,
"Eelst-MP": 15,
"Eind-MP": 16,
"Edisp-MP": 17,
"Delta": 18,
}

factor = {"cm-1": 1.0, "eV": 8065.54, "meV": 8.06554, "hartree": 219475.0, "kJ/mol": 83.5935}

col = []
for c in range(len(args.cols)):
  if args.cols[c] in col_name:
    col.append(int(col_name[args.cols[c]]))
  else:
    col.append(int(args.cols[c]))

for dir in args.dirs:
  if not os.path.exists(os.path.join(dir,args.file)):
    print("Can't find file {}".format(os.path.join(dir,args.file)))
    continue
  else:
    print(os.path.join(dir,args.file))
  outfile = os.path.join(dir,args.to)
  OUT = open(outfile,"w")
  head=["","","","","","",""]
  if args.mapname:
    OUT.write("NAME {}\n".format(args.mapname))
  if args.gridname:
    OUT.write("GRID {}\n".format(args.gridname))
  with open(os.path.join(dir,args.file)) as IN: 
    while True:
      line = IN.readline()
      m=re.match(r'([-A-Z]+)',line)
      if m:
        word = m.group(1)
        if word == "TITLE":
          OUT.write(re.sub(word, "!", line))
        elif word == "ENERGY-UNITS":
          OUT.write("ENERGY-UNITS "+args.unit+"\n")
        elif word == "LENGTH-UNITS":
          OUT.write(line)
        elif word == "POINTS":
          OUT.write(line)
          p = int(re.sub(r'POINTS *', '', line.rstrip()))
          OUT.write("TRIANGLES {:6d}\n".format(2*p-4))
        elif word == "LABELS":
          line = re.sub(r'LABELS +', '', line)
          head = line.split()
          for c in range(len(head)):
            col_name[head[c]] = c
          if args.index:
            OUT.write("INDEXED\n! Index")
          else:
            OUT.write("!")
          OUT.write(" {:^12s} {:^12s} {:^12s} ".format(head[1],head[2],head[3]))
          if args.orient:
            #  Angle-axis coordinates
            OUT.write("{:^9s} {:^8s} {:^8s} {:^8s} ".format(head[4],head[5],head[6],head[7]))
          for c in col:
            OUT.write("{:^14s} ".format(head[c]))
          OUT.write("\nBEGIN DATA\n")
          break
        else:
          OUT.write("! "+line)
    while True:
      line = IN.readline()
      v = line.split()
      if v[0] == "END":
          break
      else:
        if args.index:
          #  Index
          buffer = "{:6d} ".format(int(v[0]))
        else:
          buffer = ""
        #  Position
        buffer += "{:12.7f} {:12.7f} {:12.7f} ".format(float(v[1]),float(v[2]),float(v[3]))
        if args.orient:
          #  Orientational coordinates
          buffer += "{:9.3f} {:8.5f} {:8.5f} {:8.5f} ".format(float(v[4]),float(v[5]),float(v[6]),float(v[7]))
        #  Print specified column values, or their sum if --sum was specified.
        if args.sum:
          sum = 0.0
          for c in col:
            sum += float(v[c])/factor[args.unit]
          buffer += " {:14.6e}".format(sum)
        else:
          for c in col:
            buffer += " {:14.6e}".format(float(v[c])/factor[args.unit])
        OUT.write(buffer+"\n")

  #  Optionally add triangle list from specified gridfile at end
  #  Not required with Orient 4.9
  if args.grid:
    with open(os.path.join(dir,args.grid)) as G:
      add = False
      while True:
        line = G.readline()
        if line == "": break
        if re.match(r' +1 +2 +3', line):
          add = True
        if add:
          OUT.write(line)

  OUT.close()
  print("Scan grid written to {}".format(outfile))
