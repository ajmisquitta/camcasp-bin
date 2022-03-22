#!/usr/bin/python3
#  -*-  coding:  iso-8859-1  -*-

"""Test CamCASP using water dimer example.
"""

import argparse
from datetime import date
import re
from glob import glob
import os
from pathlib import Path
import subprocess
from shutil import rmtree 
from sys import stdout
from time import strftime

parser = argparse.ArgumentParser(
formatter_class=argparse.RawDescriptionHelpFormatter,
description="""Test CamCASP using water dimer example.
""",epilog="""
Normally called by the run_tests.py script.
This version uses the standard CamCASP SAPT(DFT) calculation when
called with the Psi4 scfcode.
""")


parser.add_argument("--scfcode", default="dalton",
                    choices=["dalton","nwchem","psi4"],
                    help="Ab initio code to use (dalton, nwchem or psi4)")
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
if not ok:
    exit(1)

scfcode = args.scfcode.lower()
base = os.path.join(camcasp,"tests","H2O_dimer",scfcode)
# print base

#  Clean up old test files and directories
if args.clean:
    os.chdir(base)
    files = glob("*")
    for file in files:
        if file in ["README", "sapt-dft.clt", "delta-hf.clt", "check",
                    "check_dHF", "test_report"]:
            pass
        elif Path(file).is_dir():
            rmtree(file)
        else:
            os.remove(file)
    if os.path.exists("test_report"):
        os.rename("test_report","previous_test_report")
    exit(0)

# if args.scfcode == "psi4":
#   tasks.remove("delta-hf")
# if args.done:
#     for task in args.done:
#         tasks.remove(task)

tasks = ["sapt-dft", "delta-hf"]
name = {
  "sapt-dft": args.dirname,
  "delta-hf": args.dirname+"_dHF",
}
logfile = {
  "sapt-dft": os.path.join(base,"sapt-dft.log"),
  "delta-hf": os.path.join(base,"delta-hf.log"),
}

print("Water dimer test starting at " \
      f"{strftime('%H:%M:%S')} on {date.isoformat(date.today())}")
stdout.flush()

for task in tasks:
    os.chdir(base)
    cmnd = ["runcamcasp.py", "H2O2", "--clt", task+".clt",
                     "--verbosity", str(args.verbosity),
                     "--directory", name[task], "--ifexists", "delete",
            "--log", logfile[task]]
    if args.debug:
        cmnd.append("--debug")
    rc = subprocess.call(cmnd, stderr=subprocess.STDOUT)
    if rc > 0:
        print(f"runcamcasp.py failed with rc = {rc:1d}")

test_results = os.path.join(base,"test_results")
if os.path.exists(test_results):
    os.remove(test_results)

os.chdir(base)
#  Analyse results
results = ""
with open(test_results,"w") as Z:
    subprocess.call(["extract_saptdft.py", "check", "check_dHF", name["sapt-dft"],
                 name["delta-hf"], "--title", "SCF code {}".format(scfcode)],
                stdout=Z)
print("Finished")
with open(test_results) as R:
    results = R.read()
print(results)

#  Compare with check results
lines = results.split("\n")
while len(lines) > 0:
    line = lines.pop(0)
    if re.match(r'kJ/mol', line):
        header = line
        check = re.sub(r'check +', " ", lines.pop(0))
        test = re.sub(name["sapt-dft"], "", lines.pop(0))
        test = re.sub("^ *", " ", test)
        if test == check:
            print(f"{scfcode} test successful")
        else:
            checkvalue = [float(g) for g in check.split()]
            testvalue = [float(g) for g in test.split()]
            # print checkvalue
            # print testvalue
            dmax = 0.0
            for n in range(len(checkvalue)):
                dmax = max(dmax, abs(testvalue[n] - checkvalue[n]))
            ok = False
            # print "{:8s}\ncheck{}\n{:8s} {}".format(header,check,name["sapt-dft"],test)
            print(f"Maximum difference between {name['sapt-dft']} and check values is {dmax:8.2e}")
            # print "{} test completed".format(scfcode)
            if dmax > 0.001:
                exit(3)
            else:
                exit(0)
