#!/usr/bin/python3
#  -*-  coding:  iso-8859-1  -*-

"""Test CamCASP using CO2 isa-A-dma example.
"""

import argparse
from glob import glob
import re
import os
from pathlib import Path
import subprocess
from shutil import rmtree 

parser = argparse.ArgumentParser(
formatter_class=argparse.RawDescriptionHelpFormatter,
description="""Test CamCASP using CO2 isa-A-dma example.
""",epilog="""
Normally run via the CamCASP tests/run_tests.py script.
To run standalone, use
test_CO2-isa.py --scfcode {dalton|nwchem|psi4} [--dirname <directory>]
The default directory name for the calculation is "test".
""")


# parser.add_argument("", help="Positional argument")
parser.add_argument("--scfcode", default="psi4",
                    choices=["dalton","nwchem","psi4"],
                    help="Ab initio code to use (dalton, nwchem or psi4)")
parser.add_argument("--dirname", "-d", default="test",
                    help="Name of directory for test job (default test)")
parser.add_argument("--verbosity", help="Verbosity level", type=int,
                    default=0)
parser.add_argument("--clean", help="Delete files created by previous tests and exit",
                    action="store_true")
parser.add_argument("--debug", help="Keep scratch files for debugging purposes",
                    action="store_true")
parser.add_argument("--difftool", default="xxdiff",
                    help="Difference tool for checking results")
args = parser.parse_args()

camcasp = os.getenv("CAMCASP")
base = os.path.join(camcasp,"tests","CO2-isa")
scf = args.scfcode
name = args.dirname

#  Clean up old test files and directories
if args.clean:
    os.chdir(os.path.join(base,scf))
    files = glob("*")
    for file in files:
        if file in ["README", "CO2-isa.clt", "check", "test_report"]:
            pass
        elif Path(file).is_dir():
            rmtree(file)
        else:
            os.remove(file)
    if os.path.exists("test_report"):
        os.rename("test_report","previous_test_report")
    exit(0)

os.chdir(os.path.join(base,scf))

#  Do calculation
cmnd = ["runcamcasp.py", "CO2", "--clt", "CO2-isa.clt",
        "--directory", name, "--ifexists", "delete",
        "--verbosity", str(args.verbosity)]
if args.debug:
    cmnd.append("--debug")
rc = subprocess.call(cmnd, stderr=subprocess.STDOUT)
if rc > 0:
    print("Job failed")
    exit(4)

out = os.path.join(base,scf,name,"OUT")
with open(os.path.join(out,"CO2.log")) as LOG:
    log = LOG.read()
    if re.search("CamCASP finished normally", log):
        print("Calculation finished")
        ok = True
        done = True
    else:
        print("Calculation failed -- see log")
        ok = False

try:
    s = subprocess.check_output(f"cmp check/OUT/CO2_ISA-GRID.mom {name}/OUT/CO2_ISA-GRID.mom",
                                shell=True, encoding="iso-8859-1")
    print("Test successful")
    exit(0)
except subprocess.CalledProcessError:
    if os.path.exists(os.path.join(base,scf,name,"OUT","CO2_ISA-GRID.mom")):
        print("Test and check results differ")
        diff = args.difftool
        #  Does the specified (or default) difftool exist?
        try:
            typeout = subprocess.check_output("type {}".format(diff), shell=True,
                                      stderr=subprocess.STDOUT, encoding="iso-8859-1")
            #  Yes, it does.
            subprocess.Popen(f"{diff} {base}/{scf}/check/OUT/CO2_ISA-GRID.mom "
                             f"{base}/{scf}/{name}/OUT/CO2_ISA-GRID.mom", shell=True)
            again = " again"
        except subprocess.CalledProcessError:
            #  No, it doesn't.
            print(f"{diff} not found. Can't display differences.")
            again = ""
        diff = "<difftool>"
        print(f"""To display differences{again}, execute
  {diff} {base}/{scf}/{{check/,{name}/}}OUT/CO2_ISA-GRID.mom""")
        print(f"where {diff} is a difference display program such as xxdiff, meld or vimdiff.")
        exit(2)
