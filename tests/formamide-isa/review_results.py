#!/usr/bin/python3
#  -*-  coding:  utf-8  -*-

"""Review the results of a formamide-isa test.
"""

import argparse
import re
import os
# import string
import subprocess

this = __file__
parser = argparse.ArgumentParser(
formatter_class=argparse.RawDescriptionHelpFormatter,
description="""Review the results of a formamide-isa test.
""",epilog=f"""
{this} --scfcode {{psi4|nwchem|dalton}} [--dirname <test-dir>]
""")


parser.add_argument("--scfcode", help="SCF code used for the test")
parser.add_argument("--dirname", help="name of test directory (default test)", default="test")
parser.add_argument("--difftool", help="Difference display program", default="xxdiff")

args = parser.parse_args()

camcasp = os.getenv("CAMCASP")
base = os.path.join(camcasp,"tests","formamide-isa")
name = args.dirname

out = os.path.join(base,args.scfcode,name,"OUT")
with open(os.path.join(out,"HCONH2.log")) as LOG:
    log = LOG.read()
    print(log)
    if re.search("CamCASP finished normally", log):
        pass
    else:
        print("Calculation failed.")
        exit(1)

os.chdir(os.path.join(base,args.scfcode))
try:
    s = subprocess.check_output(f"cmp check/OUT/formamide_ISA-GRID.mom {name}/OUT/formamide_ISA-GRID.mom",
                                shell=True, encoding="iso-8859-1")
    print("Test successful")
    exit(0)
except subprocess.CalledProcessError:
    if os.path.exists(os.path.join(base,args.scfcode,name,"OUT","formamide_ISA-GRID.mom")):
        print("Test and check results differ")
        diff = args.difftool
        #  Does the specified (or default) difftool exist?
        try:
            typeout = subprocess.check_output("type {}".format(diff), shell=True,
                                      stderr=subprocess.STDOUT, encoding="iso-8859-1")
            #  Yes, it does.
            scf = args.scfcode
            subprocess.Popen(f"{diff} {base}/{scf}/check/OUT/formamide_ISA-GRID.mom "
                             f"{base}/{scf}/{name}/OUT/formamide_ISA-GRID.mom", shell=True)
        except subprocess.CalledProcessError:
            #  No, it doesn't.
            print(f"{diff} not found. Can't display differences.")
            diff = "<difftool>"
            print(f"""To display differences, execute
  {diff} {base}/{args.scfcode}/{{check/,{name}/}}OUT/formamide_ISA-GRID.mom""")
            print(f"where {diff} is a difference display program such as xxdiff, meld or vimdiff.")
        exit(2)
