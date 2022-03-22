#!/usr/bin/env python3

"""Extract and print the binding energy from a supermolecule calculation."""

import re
import os
import argparse
from camcasp import die

parser=argparse.ArgumentParser()
parser.add_argument("job", help="CamCASP job name")
parser.add_argument("directory", help="directory that job was run in")

args = parser.parse_args()

os.chdir(args.directory)
energy={}

for M in ["A", "B", "AB"]:
  with open("{job}_{M}.out".format(job=args.job,M=M)) as IN:
    line=IN.readline()
    while line:
      m=re.search(r'Final DFT energy:\s+([ -]?\d+\.\d+)', line)
      if m:
        print(" {:3s}  ".format(M), m.group(1))
        # print(line,)
        energy[M]=float(m.group(1))
      line=IN.readline()

print("Energy = {diff:.5f} kJ/mol".format(diff=2625.5*(energy["AB"]-energy["A"]-energy["B"])))

