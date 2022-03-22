#!/usr/bin/python3
#  -*-  coding:  iso-8859-1  -*-

"""Test CamCASP using formamide-isa example.
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
description="""Test CamCASP using formamide isa-A example.
""",epilog="""
Normally run via the CamCASP tests/run_tests.py script.
To run standalone, use
test_formamide-isa.py --scfcode {dalton|nwchem|psi4} [--dirname <directory>]
The default directory name for the calculation is "test". Specify --done
if the calculation has already been done and you just wish to repeat the
analysis.
""")


# parser.add_argument("", help="Positional argument")
parser.add_argument("--scfcode", default="dalton",
                    choices=["dalton","nwchem","psi4"],
                    help="Ab initio code to use (dalton, nwchem or psi4)")
# parser.add_argument("--done", help="CamCASP calculation already complete",
#                     action="store_true")
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
base = os.path.join(camcasp,"tests","formamide-isa")
name = args.dirname

if args.clean:
    #  Clean up old test files and directories and exit
    os.chdir(os.path.join(base,args.scfcode))
    files = glob("*")
    for file in files:
        if file in ["README", "HCONH2-isa.clt", "check", "test_report", "HCONH2.out"]:
            pass
        elif Path(file).is_dir():
            rmtree(file)
        else:
            os.remove(file)
    if os.path.exists("test_report"):
        os.rename("test_report","previous_test_report")
    exit(0)

os.chdir(os.path.join(base,args.scfcode))

#  Do calculation
cmnd = ["submit_camcasp.py", "--queue", "batch", "HCONH2", "--clt", "HCONH2-isa.clt",
        "--directory", name, "--ifexists", "delete",
        "-M", "2", "--verbosity", str(args.verbosity)]
if args.debug:
    cmnd.append("--debug")
rc = subprocess.call(cmnd, stderr=subprocess.STDOUT)
if rc > 0:
    print("Job submission failed")
    exit(4)

print("Job submitted")
print(f"""
When the job has completed, the batch job output will be in
{base}/{args.scfcode}/HCONH2.out

To compare the results of the test calculation with the check results,
use""")
if name == "test":
    print(f"{base}/review_results.py --scfcode {args.scfcode}")
else:
    print(f"{base}/review_results.py --scfcode {args.scfcode} --dirname {name}")
