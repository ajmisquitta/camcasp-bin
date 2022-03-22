#!/usr/bin/python3
#  -*-  coding:  iso-8859-1  -*-

"""Test CamCASP using He2 examples.
"""

import argparse
from glob import glob
import re
import os
from pathlib import Path
import string
import subprocess
from shutil import rmtree
from sys import stdout

parser = argparse.ArgumentParser(
formatter_class=argparse.RawDescriptionHelpFormatter,
description="""Test procedure using He2 examples.
""",epilog="""
This test runs the He2 test examples for each basis set type (MC, MC+, DC, DC+)
and compares the result summaries with the results in the check directories,
using extract_saptdft.py to obtain the result summaries.

It's only necessary to use the --clean option to tidy up when testing is finished.

""")


parser.add_argument("--dirname", "-d", help="Name for test directories",
                    default="test")
parser.add_argument("--verbosity", help="verbosity level",
                    type=int, default=0)
parser.add_argument("--clean", action="store_true",
                    help="Delete files created by previous tests and exit")
parser.add_argument("--debug", help="Keep scratch files for debugging purposes",
                    action="store_true")
args = parser.parse_args()


ok = True
camcasp = os.getenv("CAMCASP")
if not camcasp:
    print("""Environment variable CAMCASP must be set to the base CamCASP directory
If that hasn't been done you probably also need to run the setup.py script""")
    ok = False
cores = os.getenv("CORES")
if not cores:
    print("""Environment variable CORES must be set to the number of processors
available to CamCASP""")
    ok = False
if not ok:
    exit(1)

basis_types = ["DC+", "DC", "MC+", "MC"]

base = os.path.join(camcasp,"tests","He2")
dirname = args.dirname

if args.clean:
    os.chdir(base)
    if os.path.exists("test_results"):
        os.rename("test_results","previous_test_results")
    for type in basis_types:
        name = "aTZ_" + type
        os.chdir(os.path.join(base,name))
        files = glob("*")
        for file in files:
            if file in ["README", "He2.clt", "check"]:
                pass
            elif Path(file).is_dir():
                rmtree(file)
            else:
                os.remove(file)
    exit(0)

failed = 0
test_results = os.path.join(base,"test_results")
if os.path.exists(test_results):
    os.remove(test_results)
results = ""
#  Set jobs running
for type in basis_types:
    os.chdir(base)
    name = "aTZ_" + type
    print(f"\n\nHelium dimer, basis type {name}\n")
    stdout.flush()
    os.chdir(name)
    arglist = ["runcamcasp.py", "He2", "--directory", dirname,
               "--ifexists", "delete", "--work", "He2_"+type]
    if args.verbosity > 0:
        arglist.extend(["--verbosity", "{:1d}".format(args.verbosity)])
    if args.debug: arglist.append("--debug")
    rc = subprocess.call(arglist, stderr=subprocess.STDOUT)
    if rc > 0:
        print(f"{name} job failed")
        print("See ", os.path.join(base,name,name+".log"))
        exit(4)

    out = os.path.join(base,name,dirname,"OUT")
    if os.path.exists(out):
        os.chdir(out)
        if os.path.exists(os.path.join(out,"He2.log")):
            with open(os.path.join(out,"He2.log")) as LOG:
                log = LOG.read()
                if re.search("CamCASP finished normally", log):
                    results += "\nBasis type {}:\n".format(type)
                    os.chdir(os.path.join(base,name))
                    with open("/tmp/temp","w") as Z:
                        subprocess.call(["extract_saptdft.py",
                             "--unit", "kelvin", "check", dirname], stdout=Z)
                    with open("/tmp/temp") as Y:
                        results += Y.read()
                elif re.search(r'CamCASP finished with error|Task abandoned', log):
                    results += f"\nBasis type {type}\:\nCalculation failed -- see log"
                    failed += 1

print("Finished")
print(results)

lines = results.split("\n")

ok = True
while len(lines) > 0:
    line = lines.pop(0)
    if re.match(r'Basis', line):
        print(line)
    elif re.match(r'check', line):
        check = re.sub(r'check', "", line)
    elif re.match(r'test ', line):
        test = re.sub(r'test ', "", line)
        if test == check:
            print("Test successful")
        else:
            checkvalue = [float(g) for g in check.split()]
            testvalue = [float(g) for g in test.split()]
            dmax = 0.0
            for n in range(len(checkvalue)):
                dmax = max(dmax, abs(testvalue[n] - checkvalue[n]))
            ok = False
            print(check)
            print(test)
            print(f"Differences between test and check values up to {dmax:10.2e}")
if ok and failed == 0:
    print("All He2 tests completed successfully")
    exit(0)
elif failed == 0:
    print("All He2 tests completed. Some results were different from check results")
    exit(3)
else:
    print(f"{failed:1d} of the 4 tests failed. See full report for details")
    exit(2)
