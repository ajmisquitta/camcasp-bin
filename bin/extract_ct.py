#!/usr/bin/env python3
# -*- coding: latin-1 -*-

"""Extract charge-transfer energy from CamCASP summary files.
"""

import os
import re
import sys
import string
import argparse
from camcasp import die

parser=argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
description="""Extract charge-transfer energy from CamCASP summary files.
""",epilog="""
For the StoneM09 procedure the directories are <path>_mc and <path>_dc
for the two SAPT-DFT calculations. For the Misquitta13, <path>_dc is
used if present, or <path> otherwise.
The data are taken from <path>*/OUT/<job>.summary, if present, or
<path>*/OUT/<job>-data-summary.data. Energy values in cm^{-1} are
converted to kJ/mol.
The job file prefix (CamCASP job name) must be given. If it is in the form
(\w+)[.-_]+(\w+) and the molecule names are not given explicitly, the names
are taken as the first and second group in the regular expression.
Otherwise, the molecule names are taken as "A" and "B".

The --summary or -s flag optionally specifies a file to which the ct energies
are sent, in a form suitable for input to a plotting program. If the optional
--split flag is used, it should provide a re.match pattern for the job name,
and a list of matched groups that are to be output as data columns.
e.g. extract_ct.py --job H2O-HOH H2O-HOH_*_{mc,dc} --sm09 \\
--split 'H2O-HOH_(.....)_(...)_dc' 1 2 -s ct.data
where the actual directory names are of the form, e.g., H2O-HOH_1.957_135_dc
Note that the pattern will be substituted by the shell.
""")
parser.add_argument("--job", help="CamCASP job file prefix", required=True)
parser.add_argument("--paths", nargs="+",
                    help="paths to job directories (omitting any trailing _mc/dc)")
parser.add_argument("--names", help="Molecule names", nargs=2)
# parser.add_argument("--method", "-m", help="CT method (M13 (default) or SM09)",
#                    default="M13")
parser.add_argument("--summary", "-s", 
                    help="File for summary of ct values (optional)")
parser.add_argument("--details", help="Show details of ct contributions",
                    default=False, action="store_true")
parser.add_argument("--all", help="Also show other terms",
                    default=False, action="store_true")
parser.add_argument("--verbose", "-v", help="Verbose output",
                    action="store_true")
parser.add_argument("--sm09", help="Include StoneM09 method",
                    action="store_true")
parser.add_argument("--show_xct", "--xct", help="Also print non-exch-ct and exch-ct",
                    action="store_true")
parser.add_argument("--split", nargs="*",
                    help="Split directory name to provide variable data")
parser.add_argument("--S2", help="Use S2 approximation for E(1)exch and E(2)exind",
                    action="store_true")
parser.add_argument("--unit", "--units", help="Unit for output (default kJ/mol)",
                    choices=["cm-1","kJ/mol","au","hartree","eV","meV","K","kelvin","kcal/mol"],
                    default="kJ/mol")

args = parser.parse_args()

if args.paths:
    paths = args.paths
else:
    paths = [args.job]

print("Paths : ",paths)


units = {
"kj/mol": 2625.5,
"cm-1":   219475.0,
"au":          1.0,
"hartree":     1.0,
"ev":      27.2113,
"mev":     27211.3,
"k":       315773.0,
"kelvin":  315773.0,
"kcal/mol":627.510,
}
out_unit_conv = units[string.lower(args.unit)]
# print(out_unit )

job = args.job
if args.names:
  molA = args.names[0]
  molB = args.names[1]
else:
  m = re.match(r'(\w+)[-_.]+(\w+)$', args.job)
  if m:
    print("WARNING: Using molecule names extracted from JOB name. May not be correct!")
    print("If you have not used the convention JOB = molA_molB this will not work.   ")
    molA = m.group(1)
    molB = m.group(2)
  else:
    molA = "A"
    molB = "B"

done = {}
ct = {}
padlen = 0
for name in paths:
  #  Strip off any trailing slashes
  name = name.rstrip("/")
  #  Strip off trailing _mc or _dc if present
  name = re.sub(r'_[md]c$', '', name, flags=re.I)
  if name in done.keys():
    continue
  padlen = max(padlen,len(name))
  label = name
  stderr = sys.stderr
  
  energy = {}
  path = {}
  path["mc"] = os.path.join(name + "_mc", "OUT", job + ".summary")
  if not os.path.exists(path["mc"]):
    path1 = path["mc"]
    path["mc"] = os.path.join(name + "_mc", "OUT", job + "-data-summary.data")
    if not os.path.exists(path["mc"]):
      if args.verbose:
        stderr.write("Can't find " + path1 + " or " + path["mc"] + "\n")
      path["mc"]=None
  path["dc"] = os.path.join(name + "_dc", "OUT", job + ".summary")
  if not os.path.exists(path["dc"]):
    path1 = path["dc"]
    path["dc"] = os.path.join(name + "_dc", "OUT", job + "-data-summary.data")
    if not os.path.exists(path["dc"]):
      if args.verbose:
        stderr.write("Can't find {} or {}.\n".format(path1,path["dc"]))
      path["dc"] = None

  if args.sm09 and path["mc"] and path["dc"]:
    #  Evaluate energies according to StoneM09
    print("\nCharge-transfer energy according to Stone & Misquitta 2009")
    for t in ("mc","dc"):
      with open(path[t]) as IN:
        print("Using", path[t])
        for line in IN:
          m = re.match(r'E\^\{2\}\_\{(\S+)\}\(([AB])\) +(-?\d+\.\d+(E[ +-]\d+)?) +(\S+) +.*NoReg', line, flags=re.I)
          if m:
            # print(line)
            cmpnt = m.group(1)
            mol = m.group(2)
            value = float(m.group(3))
            inunit = m.group(5)
            in_unit_conv = units[string.lower(inunit)]
            value = value*out_unit_conv/in_unit_conv
            # print(cmpnt, mol, value, inunit, un_init_conv)
            #if unit == "CM-1":
            #  value = value/83.5935
            if cmpnt == "ind":
              key = "ind" + mol + t
            else:
              key = "indx" + mol + t
            energy[key] = value
            # print(key, value)
  
    energy["indABmc"] = energy["indAmc"]+energy["indBmc"]
    energy["indxABmc"] = energy["indxAmc"]+energy["indxBmc"]
    energy["indABdc"] = energy["indAdc"]+energy["indBdc"]
    energy["indxABdc"] = energy["indxAdc"]+energy["indxBdc"]
    print("kJ/mol         {:^14s} {:^14s}      total".format(molA,molB))
    if args.details:
      print("ind      mc  {: 14.7f} {: 14.7f} {: 14.7f}".format(energy["indAmc"],
                   energy["indBmc"], energy["indABmc"]))
      print("exch-ind mc  {: 14.7f} {: 14.7f} {: 14.7f}".format(energy["indxAmc"],
                   energy["indxBmc"], energy["indxABmc"]))
      print("ind      dc  {: 14.7f} {: 14.7f} {: 14.7f}".format(energy["indAdc"],
                   energy["indBdc"], energy["indABdc"]))
      print("exch-ind dc  {: 14.7f} {: 14.7f} {: 14.7f}".format(energy["indxAdc"],
                   energy["indxBdc"], energy["indxABdc"]))
      print("ind total    {: 14.7f} {: 14.7f} {: 14.7f}".format(
        energy["indAdc"]+energy["indxAdc"],
        energy["indBdc"]+energy["indxBdc"],
        energy["indABdc"]+energy["indxABdc"]))
      print("ct           {: 14.7f} {: 14.7f} {: 14.7f}".format(
        energy["indAdc"]-energy["indAmc"], energy["indBdc"]-energy["indBmc"],
        energy["indABdc"]-energy["indABmc"]))
    xctA = energy["indxAdc"]-energy["indxAmc"]
    xctB = energy["indxBdc"]-energy["indxBmc"]
    xctT = energy["indxABdc"]-energy["indxABmc"]
    if args.details:
      print("exch-ct      {: 14.7f} {: 14.7f} {: 14.7f}".format(xctA,xctB,xctT))
    ctA = energy["indAdc"]+energy["indxAdc"]-energy["indAmc"]-energy["indxAmc"]
    ctB = energy["indBdc"]+energy["indxBdc"]-energy["indBmc"]-energy["indxBmc"]
    ctT = energy["indABdc"]+energy["indxABdc"]-energy["indABmc"]-energy["indxABmc"]
    done[name] = "{: 14.7f} {: 14.7f} {: 14.7f}".format(ctA,ctB,ctT)
    ct[name] = "{: 14.7f} {: 14.7f} {: 14.7f}".format(ctT-xctT,xctT,ctT)
    print("ct + exch-ct {}".format(done[name]))
  elif args.sm09:
    done[name] = "      ---            ---            ---     "
    if args.verbose:
      stderr.write("Can't evaluate StoneM09 charge transfer energy\n")
    ct[name] = done[name]
  else:
    done[name] = ""
    ct[name] = ""

  if not path["dc"]:
    #  Try the path without either suffix
    path["dc"] = os.path.join(name, "OUT", job + ".summary")
    if not os.path.exists(path["dc"]):
      path["dc"] = os.path.join(name, "OUT", job + "-data-summary.data")
  if os.path.exists(path["dc"]):
    print("\nCharge-transfer energy according to Misquitta 2013")
    with open(path["dc"]) as IN:
      print("Using", path["dc"])
      for line in IN:
        m = re.match(r'E\^\{2\}\_\{(\S+)\}(\(S2\))?\(([AB])\) +(-?\d+\.\d+(E[ +-]\d+)?) +(\S+) +.*(NoReg|REG eta =) *(\d+\.\d+)?', line)
        #m = re.match(r'E\^\{2\}\_\{(\S+)\}(\(S2\))?\(([AB])\) +(-?\d+\.\d+(E[ +-]\d+)?) +(\S+) +.*(NoReg|REG eta =) *(\d+\.\d+)?', line, flags=re.I)
        if m:
          cmpnt = m.group(1)
          s2    = m.group(2)
          mol   = m.group(3)
          value = float(m.group(4))
          inunit = m.group(6)
          in_unit_conv = units[string.lower(inunit)]
          value = value*out_unit_conv/in_unit_conv
          #print(cmpnt, mol, value, inunit)
          #if unit == "CM-1":
          #  value = value/83.5935
          if m.group(7) == "NoReg":
            eta = 0.0
            i = 0
          else:
            eta = m.group(8)
            i = 1
          if cmpnt == "ind":
            key = "ind" + mol + str(i)
            energy[key] = value
            #print(key, value, s2)
          elif cmpnt == "ind,exch":
            # Special case to decide whether or not to use S2 approx for exch-ind energy:
            if (s2 == "(S2)" and not args.S2) or (s2 != "(S2)" and args.S2):
              continue
            else:
              key = "indx" + mol + str(i)
              energy[key] = value
            #print(key, value, s2)
          elif cmpnt == "disp":
            key = "disp"
            energy[key] = value
          #print(key, value, s2)
        if args.all:
          m = re.match(r'E\^\{[12]\}\_\{(\w+)\}(\(S2\))? +(-?\d+\.\d+(E[ +-]\d+)?) +(\S+)',line)
          if m:
            cmpnt = m.group(1)
            value = float(m.group(3))
            inunit = m.group(5)
            in_unit_conv = units[string.lower(inunit)]
            value = value*out_unit_conv/in_unit_conv
            # print(cmpnt, mol, value, inunit, m.group(5))
            #if unit == "CM-1":
            #  value = value/83.5935
            energy[cmpnt] = value
  
    energy["indAB0"] = energy["indA0"]+energy["indB0"]
    energy["indxAB0"] = energy["indxA0"]+energy["indxB0"]
    energy["indAB1"] = energy["indA1"]+energy["indB1"]
    energy["indxAB1"] = energy["indxA1"]+energy["indxB1"]
  
    print("kJ/mol         {:^14s} {:^14s}      total".format(molA,molB))
    if args.details:
      print("ind          {: 14.7f} {: 14.7f} {: 14.7f}".format(energy["indA0"],
                   energy["indB0"], energy["indAB0"]))
      print("exch-ind     {: 14.7f} {: 14.7f} {: 14.7f}".format(energy["indxA0"],
                   energy["indxB0"], energy["indxAB0"]))
      print("ind      reg {: 14.7f} {: 14.7f} {: 14.7f}".format(energy["indA1"],
                   energy["indB1"], energy["indAB1"]))
      print("exch-ind reg {: 14.7f} {: 14.7f} {: 14.7f}".format(energy["indxA1"],
                   energy["indxB1"], energy["indxAB1"]))
    print("true ind     {: 14.7f} {: 14.7f} {: 14.7f}".format(
      energy["indA1"]+energy["indxA1"], energy["indB1"]+energy["indxB1"],
      energy["indAB1"]+energy["indxAB1"]) )
    xctA = energy["indxA0"]-energy["indxA1"]
    xctB = energy["indxB0"]-energy["indxB1"]
    xctT = energy["indxAB0"]-energy["indxAB1"]
    if args.details:
      print("ct           {: 14.7f} {: 14.7f} {: 14.7f}".format(
        energy["indA0"]-energy["indA1"], energy["indB0"]-energy["indB1"],
        energy["indAB0"]-energy["indAB1"]))
      print("exch-ct      {: 14.7f} {: 14.7f} {: 14.7f}".format(xctA,xctB,xctT))
    ctA = energy["indA0"]+energy["indxA0"]-energy["indA1"]-energy["indxA1"]
    ctB = energy["indB0"]+energy["indxB0"]-energy["indB1"]-energy["indxB1"]
    ctT = energy["indAB0"]+energy["indxAB0"]-energy["indAB1"]-energy["indxAB1"]
    print("ct + exch-ct {: 14.7f} {: 14.7f} {: 14.7f}".format(ctA,ctB,ctT))
  
    total = energy["indAB1"]+energy["indxAB1"] + \
            energy["indAB0"]+energy["indxAB0"]-energy["indAB1"]-energy["indxAB1"]
    if "exch" in energy:
      print("exchange repulsion                      {: 14.7f}".format(energy["exch"]))
      total += energy["exch"]
    if "elst" in energy:
      print("electrostatic energy                    {: 14.7f}".format(energy["elst"]))
      total += energy["elst"]
    if "disp" in energy:
      print("dispersion                              {: 14.7f}".format(energy["disp"]))
      total += energy["disp"]
    # print("total                                      {: 14.7f}".format(total))
    done[name] += "{: 14.7f} {: 14.7f} {: 14.7f}".format(ctA,ctB,ctT)
    ct[name] += "{: 14.7f} {: 14.7f} {: 14.7f}".format(ctT-xctT,xctT,ctT)

  elif args.verbose:
    stderr.write("Can't find " + path["dc"] +"\n")
    stderr.write("Can't evaluate Misquitta13 charge-transfer energy\n")
    exit(1)
  
  if path["mc"]:
    print("\nUsing regularized induction from the mc basis")
    with open(path["mc"]) as IN:
      print("Using", path["mc"])
      for line in IN:
        m = re.match(r'E\^\{2\}\_\{(\S+)\}\(([AB])\) +(-?\d+\.\d+(E[ +-]\d+)?) +(\S+) +.*(NoReg|REG eta =) *(\d+\.\d+)?', line, flags=re.I)
        if m:
          cmpnt = m.group(1)
          mol = m.group(2)
          value = float(m.group(3))
          inunit = m.group(5)
          in_unit_conv = units[string.lower(inunit)]
          value = value*out_unit_conv/in_unit_conv
          # print(cmpnt, mol, value, inunit, m.group(5))
          #if unit == "CM-1":
          #  value = value/83.5935
          if m.group(6) == "NoReg":
            #  Ignore
            continue
          else:
            #  Replace regularized ind components
            eta = m.group(7)
            i = 1
          if cmpnt == "ind":
            key = "ind" + mol + str(i)
          else:
            key = "indx" + mol + str(i)
          energy[key] = value
          # print(key, value)
  
    energy["indAB0"] = energy["indA0"]+energy["indB0"]
    energy["indxAB0"] = energy["indxA0"]+energy["indxB0"]
    energy["indAB1"] = energy["indA1"]+energy["indB1"]
    energy["indxAB1"] = energy["indxA1"]+energy["indxB1"]
  
    print("kJ/mol         {:^14s} {:^14s}     total".format(molA,molB))
    if args.details:
      print("ind          {: 14.7f} {: 14.7f} {: 14.7f}".format(energy["indA0"],
                   energy["indB0"], energy["indAB0"]))
      print("ind x        {: 14.7f} {: 14.7f} {: 14.7f}".format(energy["indxA0"],
                   energy["indxB0"], energy["indxAB0"]))
      print("ind   reg    {: 14.7f} {: 14.7f} {: 14.7f}".format(energy["indA1"],
                   energy["indB1"], energy["indAB1"]))
      print("ind x reg    {: 14.7f} {: 14.7f} {: 14.7f}".format(energy["indxA1"],
                   energy["indxB1"], energy["indxAB1"]))
    print("true ind     {: 14.7f} {: 14.7f} {: 14.7f}".format(
      energy["indA1"]+energy["indxA1"], energy["indB1"]+energy["indxB1"],
      energy["indAB1"]+energy["indxAB1"]))
    if args.details:
      print("ct           {: 14.7f} {: 14.7f} {: 14.7f}".format(
        energy["indA0"]-energy["indA1"], energy["indB0"]-energy["indB1"],
        energy["indAB0"]-energy["indAB1"]))
      print("ct x         {: 14.7f} {: 14.7f} {: 14.7f}".format(
        energy["indxA0"]-energy["indxA1"],
        energy["indxB0"]-energy["indxB1"],
        energy["indxAB0"]-energy["indxAB1"]))
    print("ct + exchct  {:14.7f} {:14.7f} {:14.7f}".format(
      energy["indA0"]+energy["indxA0"]-energy["indA1"]-energy["indxA1"],
      energy["indB0"]+energy["indxB0"]-energy["indB1"]-energy["indxB1"],
      energy["indAB0"]+energy["indxAB0"]-energy["indAB1"]-energy["indxAB1"]))

if args.summary:
  with open(args.summary,"w") as OUT:
    pad = " " * padlen
    OUT.write("# Charge transfer summary (kJ/mol)")
    if args.sm09:
      OUT.write("""
#{p:1s}              Stone-Misquitta 2009                         Misquitta 2013
#{p:1s} {m1:^14s} {m2:^14s}     Total     {m1:^14s} {m2:^14s}     Total
""".format(p=pad,m1=molA,m2=molB))
      if args.show_xct:
        OUT.write("""#{p:1s} {x1:^14s} {x2:^14s}     Total     {x1:^14s} {x2:^14s}     Total
""".format(p=pad,x1="ct",x2="exch-ct"))
    else:
      OUT.write("""
#{p:1s}                 Misquitta 2013
#{p:1s} {m1:^14s} {m2:^14s}     Total
""".format(p=pad,m1=molA,m2=molB))
      if args.show_xct:
        OUT.write("""#{p:1s} {x1:^14s} {x2:^14s}     Total

""".format(p=pad,x1="ct",x2="exch-ct"))
      
    for name in sorted(done.keys()):
      if args.split:
        # print(args.split)
        m = re.match(args.split[0], name)
        if m:
          buffer = ""
          for i in range(1,len(args.split)):
            p = m.group(int(args.split[i]))
            buffer += "  {}".format(p)
        else:
          print(args.split[0])
          print("pattern doesn't match {}".format(name))
      else:
        buffer = name + " " * (padlen - len(name))
      OUT.write(buffer)
      OUT.write("{:40s}\n".format(done[name]))
      if args.show_xct:
        OUT.write(name + " " * (padlen - len(name)))
        OUT.write("{:40s}\n".format(ct[name]))
        OUT.write("\n")
