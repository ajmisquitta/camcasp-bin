#!/usr/bin/python3
#  -*-  coding:  iso-8859-1  -*-

"""Test CamCASP using water dimer example.
"""

import argparse
from datetime import date
from glob import glob
import re
import os.path
from pathlib import Path
# import string
import subprocess
from shutil import rmtree 
from sys import stdout
from time import strftime

parser = argparse.ArgumentParser(
formatter_class=argparse.RawDescriptionHelpFormatter,
description="""Test CamCASP using water dimer example.
""",epilog="""
Normally called by the run_tests.py script.
This version uses the SAPT(DFT) procedure in the Psi4 package; note that
this procedure is not currently guaranteed to give reliable results.
""")


parser.add_argument("--scfcode", default="psi4",
                    help="Ab initio code to use (must be psi4)")
# parser.add_argument("--done", help="List of completed CamCASP tasks",
#                     nargs="*", default=["none"],
#                     choices=["none","all","sapt-dft","delta-hf"])
parser.add_argument("--verbosity", help="Verbosity level", type=int,
                    default=0)
parser.add_argument("--debug", action="store_true",
                    help="Don't delete working files")
parser.add_argument("--clean", action="store_true",
                    help="Delete files created by previous tests and exit")
parser.add_argument("--dirname", "-d", help="Name for test directories",
                    default="test")
parser.add_argument("--done", help="Tasks already completed", default=[],
                    choices=["sapt-dft", "delta-hf"], nargs="*")

args = parser.parse_args()


ok = True
camcasp = os.getenv("CAMCASP")
if not camcasp:
    print("""Environment variable CAMCASP must be set to the base CamCASP directory
If that hasn't been done you probably also need to run the setup.py script""")
    ok = False
# cores = os.getenv("CORES")
# if not cores:
#   print """Environment variable CORES must be set to the number of processors
# available to CamCASP"""
#   ok = False
if not ok:
    exit(1)

scfcode = args.scfcode.lower()
if args.scfcode != "psi4":
    print("This test can only run with the Psi4 SCF code")
    exit(1)

base = os.path.join(camcasp,"tests","H2O_dimer_psi4",scfcode)
# print base
os.chdir(base)

tasks = ["sapt-dft"]
name = args.dirname
logfile = os.path.join(base,"sapt-dft.log")
                       
#  Clean up old test files and directories
if args.clean:
    os.chdir(base)
    files = glob("*")
    for file in files:
        if file in ["README", "test_report"] + glob("sapt-dft*.clt"):
            pass
        elif Path(file).is_dir():
            rmtree(file)
        else:
            os.remove(file)
    if os.path.exists("test_report"):
        os.rename("test_report","previous_test_report")
    exit(0)

print(f"Water dimer test starting at " \
      f"{strftime('%H:%M:%S')} on {date.isoformat(date.today())}")
stdout.flush()

for task in tasks:
    os.chdir(base)
    cmnd = ["runcamcasp.py", "H2O2", "--clt", "sapt-dft.clt",
                     "--verbosity", str(args.verbosity),
                     "--directory", name, "--ifexists", "delete",
            "--log", logfile]
    if args.debug:
        cmnd.append("--debug")
    rc = subprocess.call(cmnd, stderr=subprocess.STDOUT)
    if rc > 0:
        print("runcamcasp.py failed with rc = {:1d}".format(rc))

os.chdir(base)
E = {"es": 0., "exrep": 0., "ind": 0., "exind": 0., "dhf": 0.,
     "disp": 0., "exdisp": 0., "total": 0.}
with open(os.path.join(base,name,"OUT","H2O2_AB.out")) as OUT:
    while True:
        line = OUT.readline()
        if re.match(r' *SAPT\(DFT\) Results', line) or line == "":
            break
    while True:
        line = OUT.readline()
        if line == "":
            break
        if re.match(r' *Electrostatics', line):
            m = re.search(r' +(-?\d+\.\d+) +\[kJ/mol\]', line)
            if m: E["es"] = float(m.group(1))
        elif re.match(r' *Exch1 +', line):
            m = re.search(r' +(-?\d+\.\d+) +\[kJ/mol\]', line)
            if m: E["exrep"] = float(m.group(1))
        elif re.match(r' *Ind2,r +', line):
            m = re.search(r' +(-?\d+\.\d+) +\[kJ/mol\]', line)
            if m: E["ind"] = float(m.group(1))
        elif re.match(r' *Exch-Ind2,r +', line):
            m = re.search(r' +(-?\d+\.\d+) +\[kJ/mol\]', line)
            if m: E["exind"] = float(m.group(1))
        elif re.match(r' *delta HF,r +', line):
            m = re.search(r' +(-?\d+\.\d+) +\[kJ/mol\]', line)
            if m: E["dhf"] = float(m.group(1))
        elif re.match(r' *Disp2,r +', line):
            m = re.search(r' +(-?\d+\.\d+) +\[kJ/mol\]', line)
            if m: E["disp"] = float(m.group(1))
        elif re.match(r' *Exch-Disp2,u +', line):
            m = re.search(r' +(-?\d+\.\d+) +\[kJ/mol\]', line)
            if m: E["exdisp"] = float(m.group(1))
        elif re.match(r' *Total SAPT\(DFT\) +', line):
            m = re.search(r' +(-?\d+\.\d+) +\[kJ/mol\]', line)
            if m: E["total"] = float(m.group(1))
            break
total = E["es"] + E["exrep"] + E["ind"] + E["exind"] + E["dhf"] + E["disp"] + E["exdisp"]
print("""
kJ/mol      elst        exch         ind        exind        dHF        disp       exdisp       Eint
check   -29.28310    26.57633   -12.25912     7.84229    -3.83979   -10.66446     1.96455   -19.66330""")
print(f"test  {E['es']:11.5f} {E['exrep']:11.5f} {E['ind']:11.5f} {E['exind']:11.5f}",
      f"{E['dhf']:11.5f} {E['disp']:11.5f} {E['exdisp']:11.5f} {E['total']:11.5f}")
print(f"(test total {total:11.5f})")
print("The check results are from a CamCASP calculation using the Psi4 SCF code.")
exit(3)

