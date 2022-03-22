#!/usr/bin/python3
#  -*-  coding:  utf-8  -*-

"""Update check result files for test scripts.
"""

import argparse
import re
import os.path
# import string
import subprocess

this = __file__
parser = argparse.ArgumentParser(
formatter_class=argparse.RawDescriptionHelpFormatter,
description="""Update check values for test scripts.
""",epilog=f"""
{this} [test [test ...]] [--scfcode code ...]

Update the git-listed check files in each specified test's check
directory with the corresponding files in the test directory, if
they exist and are newer. Default is to do this for all tests.

If one or more scfcodes are specified, only the files for those code
are updated. Otherwise the files for all scfcodes are updated.

Each file to be copied is listed. The --verbose flag applies to the
rsync commands used to do the copy. It doesn't actually do anything
except confirm that the copy was done.
""")

camcasp = os.getenv("CAMCASP")
if not camcasp:
    print("Environment variable CAMCASP is unset. Can't continue")
    exit(1)

parser.add_argument("tests", help="Positional argument", nargs="*")
parser.add_argument("--scfcode", help="Apply only for the listed scfcodes", nargs="*")
parser.add_argument("--verbose", "-v", help="verbose", action="store_true")

args = parser.parse_args()

all_tests = ["He2", "CO2-isa", "H2O_dimer", "H2O_props", "formamide-isa",
             "H2O_dimer_scan"]
if args.tests:
    tests = args.tests
    for test in tests:
        if test not in all_tests:
            print(f"No test {test}")
            exit(1)
else:
    tests = all_tests

if args.scfcode:
    scfcodes = args.scfcode
else:
    scfcodes = ["psi4", "nwchem", "dalton"]

if args.verbose:
    flags = "-av"
else:
    flags = "-a"

os.chdir(os.path.join(camcasp,"tests"))
with open("check_files","w") as CF:
    subprocess.call("git ls-tree -r --name-only HEAD", stdout=CF, shell=True)
with open("check_files") as CF:
    lines = CF.readlines()
    for line in lines:
        if re.search(r'check', line):
            check_file = line.rstrip()
            test_file = re.sub(r'check', r'test', check_file)
            m = re.match(r'(.*?)/(.*?)/', line)
            if m:
                (test, scfcode) = (m.group(1),m.group(2))
                if test in tests and scfcode in scfcodes:
                    #  Update this one
                    if os.path.exists(test_file): 
                        if os.path.exists(check_file):
                            copy = os.stat(test_file).st_mtime > os.stat(check_file).st_mtime
                        else:
                            copy = True
                        if copy:
                            print(f"{test_file} -> {check_file}")
                            subprocess.call(["rsync", flags, test_file, check_file])
                    else:
                        if not os.path.exists(check_file):
                            print(f"""ERROR: {check_file} is required
but is not in either check or test directory""")
                            
