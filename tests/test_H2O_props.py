#!/usr/bin/python3
#  -*-  coding:  iso-8859-1  -*-

"""Test CamCASP using H2O distributed-polarizability example.
"""

import argparse
import re
from glob import glob
import os.path
from pathlib import Path
import subprocess
from time import sleep
from shutil import rmtree
from sys import stdout

parser = argparse.ArgumentParser(
formatter_class=argparse.RawDescriptionHelpFormatter,
description="""Test CamCASP using H2O distributed-polarizability example.
""",epilog="""
Normally run via the CamCASP tests/run_tests.py script.
""")


parser.add_argument("--scfcode", default="dalton",
                    choices=["dalton","nwchem","psi4"],
                    help="Ab initio code to use (dalton, nwchem or psi4)")
# parser.add_argument("--done", help="Main calculation already complete",
#                     action="store_true")
parser.add_argument("--clean", help="Delete files created by previous tests and exit",
                    action="store_true")
parser.add_argument("--dirname", "-d", default="test",
                    help="Name of directory for test job (default test)")
parser.add_argument("--verbosity", help="Verbosity level", type=int,
                    default=0)
parser.add_argument("--difftool", default="xxdiff",
                    help="Difference tool for checking results")
args = parser.parse_args()


camcasp = os.getenv("CAMCASP")

base = os.path.join(camcasp,"tests","H2O_props",args.scfcode)
name = args.dirname

#  Clean up old test files and directories
if args.clean:
    os.chdir(base)
    files = glob("*")
    for file in files:
        if file in ["README", "H2O-avtz.clt", "check",
                    "H2O.axes", "test_report"]:
            pass
        elif Path(file).is_dir():
            rmtree(file)
        else:
            os.remove(file)
    if os.path.exists("test_report"):
        os.rename("test_report","previous_test_report")
    exit(0)

os.chdir(base)

#  Run CamCASP calculation

rc = subprocess.call(["runcamcasp.py", "H2O", "--clt", "H2O-avtz.clt",
                      "--directory", name, "--ifexists", "delete",
                      "--verbosity", str(args.verbosity)],
                      stderr=subprocess.STDOUT)
if rc:
    print("Job failed")
    exit(4)

#  Localize polarizabilities and obtain dispersion coefficients
#  Make sure that the Orient program can be found
# try:
#   s = subprocess.check_output("type orient", stderr=subprocess.STDOUT, shell=True)
# except subprocess.CalledProcessError:
#   print """
# Can't find the Orient program, needed for the localization procedure.
# Please ensure that the orient executable is in your PATH, or make a link
# to it in the $CAMCASP/bin directory.
# """
#   exit(1)

print("\nPerforming localization\n")
stdout.flush()
os.chdir(name)
rc = subprocess.call(["localize.py", "H2O", "--limit", "2", "--hlimit", "1",
                      "--subdir", "L2H1"], stderr=subprocess.STDOUT)
if rc:
    print(f"Error in localization -- see {base}/{name}/H2O_loc.log")
    exit(1)

os.chdir(base)
potfile = "H2O_ref_wt3_L2_Cn.pot"
try:
    s = subprocess.check_output(f"cmp check/L2H1/{potfile} {name}/L2H1/{potfile}", shell=True)
    print("Test successful")
except subprocess.CalledProcessError:
    print("Test and check results differ")
    diff = args.difftool
    #  Does the specified (or default) difftool exist?
    try:
        typeout = subprocess.check_output("type {}".format(diff),
                                      stderr=subprocess.STDOUT, shell=True)
        subprocess.Popen(f"{diff} check/L2H1/{potfile} {name}/L2H1/{potfile}", shell=True)
    except subprocess.CalledProcessError:
        #  No, it doesn't.
        print("{} not found. Can't display differences.".format(diff))
        diff = "<difftool>"
        print(f"""To display differences, execute
    {diff} {base}/{{check/,{name}/}}L2H1/{potfile}""")
        print("where <difftool> is a difference display program such as xxdiff, meld or vimdiff.")

    #  Find maximum difference between check and test coefficient values
    with open(os.path.join("check","L2H1",potfile)) as CHK, open(os.path.join("test","L2H1",potfile)) as TEST:
        maxdiff = 0.0
        chk = "--"
        while True:
            chk = CHK.readline()
            t = TEST.readline()
            if chk == "":
                #  end of file
                break
            if t == chk:
                pass
            else:
                vc = chk.split()
                vt = t.split()
                for p in range(3,len(vc)):
                    if vc[p] != vt[p]:
                        maxdiff = max(maxdiff,abs(float(vc[p]) - float(vt[p])))
        print(f"Maximum difference between check and test coefficients = {maxdiff:10.2e}")
    exit(2)

