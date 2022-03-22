#!/usr/bin/python
#  -*-  coding:  utf-8  -*-

"""
Compare the results of the H2O_dimer_scan test with previous check results.
"""

import argparse
# import re
import os
# import string
import subprocess

this = __file__
parser = argparse.ArgumentParser(
formatter_class=argparse.RawDescriptionHelpFormatter,
description="""Compare the results of the test with previous check results.
""",epilog="""
{} args
""".format(this))


parser.add_argument("--scfcode", help="SCF code used for the test",
                    choices=["dalton","nwchem","psi4"], default="psi4")
parser.add_argument("--difftool", help="Difference display program", default="xxdiff")

args = parser.parse_args()

camcasp = os.environ.get("CAMCASP")
if not camcasp:
    print("""The environment variable CAMCASP must be set to the CamCASP 
base directory""")
    exit(1)

os.chdir(os.path.join(camcasp,"tests","H2O_dimer_scan",args.scfcode))

with open("test_results","w") as TEST:
    subprocess.call("extract_saptdft.py *", stdout=TEST,
                    stderr=subprocess.STDOUT, shell=True)

subprocess.call([args.difftool, "check_results", "test_results"])

