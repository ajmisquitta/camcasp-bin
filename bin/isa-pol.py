#!/usr/bin/env python2
#  -*-  coding:  iso-8859-1  -*-

"""Convert an ISA-display job into an ISA-pol job and run it.
"""
import argparse
import glob
import re
import os
# import string
import subprocess
import sys

CamCASP = os.environ["CAMCASP"]

sys.path = [os.path.join(CamCASP,"bin")] + sys.path

from camcasp import newdir


parser = argparse.ArgumentParser(
formatter_class=argparse.RawDescriptionHelpFormatter,
description="""Convert an ISA-display job into an ISA-pol job and run it.
""",epilog="""
isa-pol.py <job> -d <directory> [--clt <clt-file>] [-q <queue>]
The cluster-file need not normally be specified. The script will look
for a *.clt file in the specified directory.
The molecule name must be specified if different from the job name. 
""")


parser.add_argument("job", help="Job name")
parser.add_argument("--directory", "-d", help="Job directory")
parser.add_argument("--clt", help="cluster file name")
parser.add_argument("--molecule", "--mol", help="Molecule name")
parser.add_argument("--queue", "-q", help="Job queue", default="batch")

args = parser.parse_args()

job = args.job
here = os.getcwd()

if os.path.exists(args.directory):
  os.chdir(args.directory)
else:
  print "Can't find directory {}".format(args.directory)
  exit(1)

clt = glob.glob("*.clt")
if len(clt) == 0:
  print "Cluster file missing"
  exit(1)
elif len(clt) > 1:
  print "More than one .clt file in {}".format(args.directory)
  exit(1)
else:
  cltfile = clt[0]

if args.molecule:
  molecule = args.molecule
else:
  molecule = job

isa_file = "{}_atoms.ISA".format(molecule)

if not os.path.exists(isa_file):
  # Move it up from the OUT directory
  if os.path.exists(os.path.join("OUT",isa_file)):
    os.rename(os.path.join("OUT",isa_file),isa_file)
    # and rename OUT directory
    os.rename("OUT","OUT_isa")
  else:
    print "Can't find ISA results file {}".format(os.path.join("OUT",isa_file))
    exit(1)

# Save old output directory, if any, and make new one
newdir("OUT")

isa_pol_cmnds = os.path.join(CamCASP,"data","camcasp-cmnds",
                           "isa-pol-from-isa-restart")
if not os.path.exists(isa_pol_cmnds):
  print "Can't find isa-pol command file {}".format(isa_pol_cmnds)
  exit(1)

#  Move ISA results file up
os.rename

#  Save old .cks file and generate new one for the isa-pol calculation
cksfile = "{}.cks".format(job)
ckssave = "{}.cks.save".format(job)
if os.path.exists(cksfile) and not os.path.exists(ckssave):
  os.rename(cksfile,ckssave)
moldef = False
with open(cksfile,"w") as OUT:
  #  Read old cks file as far as the end of the molecule definition
  with open(ckssave) as IN:
    for line in IN.readlines():
      OUT.write(line)
      if re.match(r'MOLECULE', line):
        moldef = True
      if re.match(r'END', line) and moldef:
        break
  OUT.write("\n")
  #  Append isa-pol command file
  with open(isa_pol_cmnds) as CKS:
    for line in CKS.readlines():
      if re.search(r'(CamCASP-commands|coding)', line, flags=re.I):
        continue
      else:
        OUT.write(line)
    OUT.write("""
Finish
""")


os.chdir(here)
subprocess.call(["runcamcasp.py", job, "--clt", cltfile, "-d", args.directory,
                 "--restart", "-M", "4000", "-q", args.queue])

