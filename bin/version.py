#!/usr/bin/env python3
#  -*-  coding:  utf-8  -*-

"""Construct the version.f90 file that contains version details.
   Python 2 or 3
"""

import argparse
import re
from datetime import datetime
# import os
# import string
import subprocess

this = __file__
parser = argparse.ArgumentParser(
formatter_class=argparse.RawDescriptionHelpFormatter,
  description="""Construct the version.f90 file that contains version details,
including the git commit tag and whether it is modified.
""",epilog="""
{} args
""".format(this))


parser.add_argument("vfile", help="VERSION file path")
parser.add_argument("v90", help="version.f90 file path")
parser.add_argument("compiler", help="Compiler")

args = parser.parse_args()

with open(args.vfile) as IN:
  line = IN.readline()
  line = IN.readline().strip()
  version = re.sub(r"VERSION +:?= +", "", line)
  line = IN.readline().strip()
  patchlevel = re.sub("PATCHLEVEL +:?= +", "", line)

try:
    host = subprocess.check_output("hostname", shell=True).strip()
except subprocess.CalledProcessError as errstr:
    print(f"hostname error: {errstr}")
    host = 'UNKNOWN'

now = datetime.today().strftime('%d %B %Y at %H:%M:%S')

try:
    log = subprocess.check_output("git log -n 1 --oneline", shell=True)
    print(f"log = {log}")
    commit = str(log.split()[0])
except subprocess.CalledProcessError as errstr:
    print(f"git log error: {errstr}")
    commit = 'git-commit-UNKNOWN'

try:
    changes = subprocess.check_output("git status --porcelain -uno", shell=True)
    if len(changes) > 0:
      commit += " M"
      modified = ".true."
    else:
      modified = ".false."
except subprocess.CalledProcessError as errstr:
    print(f"git status error: {errstr}")
    modified = '.false.'

with open(args.v90,"w") as OUT:
  OUT.write(f"""MODULE version

   !  version.f90 is generated automatically by version.py
   !  CamCASP version and build date
   CHARACTER(*), PARAMETER :: situs_version = "{version}.{patchlevel}"
""")

  OUT.write(f'   CHARACTER(*), PARAMETER :: commit="{commit}"\n')
  OUT.write(f'   LOGICAL,      PARAMETER :: modified={modified}\n')
  OUT.write(f'   CHARACTER(*), PARAMETER :: compiler="{args.compiler}"\n')
  OUT.write(f'   CHARACTER(*), PARAMETER :: build_date="{now}"\n')
  OUT.write(f'   CHARACTER(*), PARAMETER :: compiled_on="{host}" ')
  
  OUT.write('\nEND MODULE version\n')
