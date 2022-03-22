#!/usr/bin/env python3
#  -*-  coding:  iso-8859-1  -*-

"""Script to switch between CamCASP binary versions.
"""

import argparse
from glob import glob
import os
import re
import readline
import shutil
import subprocess

home = os.environ["HOME"]
camcasp = os.environ.get("CAMCASP")
if not camcasp:
  print("The environment variable CAMCASP must be set to the base CamCASP directory")
  exit(1)
print("{} is {}".format("CAMCASP", camcasp))
PATH = os.environ["PATH"]
if not re.search(camcasp, PATH):
  print("{} should be in your PATH".format(camcasp))

arch = os.environ.get("ARCH")
 

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
description="""Switch to a diffeerent set of binaries.
""",epilog="""

""")

parser.add_argument("--compiler", help="Use binaries from this compiler",
                    choices=["gfortran","ifort"], required=True)
parser.add_argument("--debug", help="Use debug version", action="store_true")
parser.add_argument("--only", help="Specify individual binaries", default="all",
                    choices=["camcasp","cluster","process","pfit","casimir","all"],
                    nargs="+")
args = parser.parse_args()


if arch == "OSX" and args.compiler == "":
  compiler = "gfortran"
else:
  compiler = args.compiler
if arch == "OSX" and args.compiler != "gfortran":
  print("Sorry, the only compiler for OSX is gfortran")
  exit(1)

if args.only == "all":
  proglist = ["camcasp","cluster","process","pfit","casimir"]
else:
  proglist = args.only

if args.debug:
  sub = "debug"
else:
  sub = "exe"

os.chdir(os.path.join(camcasp,"bin"))
for program in proglist:
  if program == "pfit":
    path = os.path.join("..",arch,compiler,sub,"pfit","pfit")
  else:
    path = os.path.join("..",arch,compiler,sub,program)
  if os.path.exists(path):
    if  os.path.realpath(path) == os.path.realpath(program):
      print("{} already linked to {}".format(program,path))
    else:
      if os.path.exists(program):
        os.remove(program)
      os.symlink(path,program)
      print("{} -> {}".format(program,path))
  else:
    print("No binary for {} at {}".format(program,path))

