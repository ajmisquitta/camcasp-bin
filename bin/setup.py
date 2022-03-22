#!/usr/bin/env python3
#  -*-  coding:  iso-8859-1  -*-

"""Script to set up links to CamCASP helper applications.
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
print(f"CAMCASP is {camcasp}")
PATH = os.environ["PATH"]
if not re.search(camcasp, PATH):
  print(f"{camcasp} should be in your PATH")
arch = os.environ.get("ARCH")

os.chdir(camcasp)

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
description="""Set up links to CamCASP helper applications.
""",epilog="""
It is not necessary to provide any arguments. The script will request
information as required. File and directory pathnames can include shell
metacharacters.
""")

# parser.add_argument("--base", help="Full path to the CamCASP base directory",
#                     default=camcasp)
# parser.add_argument("--arch", help="Machine architecture", default=link["arch"],
#                     choices=["x86-64","osx"])
# parser.add_argument("--compiler", help="select from available binaries",
#                     default="gfortran", choices=["gfortran","ifort","pgf90"])
# parser.add_argument("--dalton-dir", help="Full path to the Dalton executable",
#                     default=link["dalton"])
# parser.add_argument("--dalton-version", choices=["2.0","2006","2013"],
#                     help="(2.0 and 2006 are the same)")
# parser.add_argument("--nwchem-dir", help="Full path to the NWChem executable",
#                     default=link["nwchem"])
# parser.add_argument("--orient", help="Full path to the base directory for Orient",
#                     default=link["orient"])
#
#  This statement is needed to set up the --help argument. 
args = parser.parse_args()

global archs, compilers
archs = ["x86-64", "osx"]

compilers = {}
compilers["x86-64"] = ["gfortran", "ifort"]
compilers["osx"] = ["gfortran"]
scflist = ["dalton","dalton2006","nwchem","psi4","molpro"]
installed = {}

def fullpath(s):
  """Find a full pathname by expanding shell characters."""
  #  glob.glob doesn't recognize tilde
  s = re.sub(r'^~/', home + "/", s)
  ss = glob(s)
  if len(ss) > 1:
    print("Ambiguous:")
    for s in ss:
      print(s)
    return ""
  elif len(ss) == 0:
    print(f"{s} not found")
    return ""
  else:
    return ss[0]
  

def base ():
  """Find the base directory."""

  global link, camcasp
  ok = False
  while not ok:
    string = input(f"\nFull path to the CAMCASP base directory [{camcasp}]: ")
    if string == "" or re.match(r'y', string, flags=re.I):
      pass
    else:
      camcasp = os.path.abspath(string)
    if camcasp == "":
      pass
    elif not os.path.exists(camcasp):
      print(f"{camcasp} doesn't exist")
    elif not os.path.isdir(camcasp):
      print(f"{camcasp} isn't a directory")
    elif not os.path.exists(os.path.join(camcasp,"bin","setup.py")):
      print(f"Sorry, {camcasp} can't be right")
    else:
      ok = True
      os.environ["CAMCASP"] = camcasp
    if not ok:
      string = input("Try again? [Yn] ")
      if re.match(r'n', string, flags=re.I):
        exit(1)
  print(f"CAMCASP -> {os.environ['CAMCASP']}")
  #  Is $CAMCASP/bin in the PATH?
  paths = os.environ["PATH"].split(":")
  if os.path.join(camcasp,"bin") not in paths:
    print(f"{os.path.join(camcasp,'bin')} should be in your PATH")

  print("""
Before proceeding, please ensure that for each SCF code that you wish to
use (any or all of dalton, dalton2006, nwchem, psi4), either
  (i) the directory containing the executable is in your PATH, or
  (ii) there is a symbolic link dalton or dalton2006 or nwchem or psi4 in
       $CAMCASP/bin to the executable, or
  (iii) there is a shell script dalton.sh or nwchem.sh or psi4.sh or molpro.sh in
        $CAMCASP/bin that can be invoked to execute the program.
        (See nwchem.sh.example or psi4.sh.example in $CAMCASP/bin.)
Also ensure that either (i) or (ii) is satisfied for the Orient program.
""")
  q = input("Are you ready to proceed? [Yn] ")
  if q in ["Y", "y", ""]:
    pass
  else:
    print("Please rerun setup.py when you are ready.")
    exit(0)

def architecture():
  """Find the machine operating system."""
  arch = os.environ.get("ARCH")
  if arch: arch = arch.lower()
  uname = subprocess.check_output("uname", shell=True, encoding="iso-8859-1").strip()
  # out = subprocess.run("uname", shell=True, text=True, capture_output=True)
  # uname = out.stdout.strip()
  if uname == "Linux" or uname == b"Linux":
    print("Running under Linux")
    if arch == "x86-64":
      pass
    else:
      print("Please set the environment variable ARCH to 'x86-64'")
      arch = "x86-64"
  elif uname == "Darwin":
    print("Running under Darwin (OSX)")
    if arch == "osx":
      pass
    else:
      print("Please set the environment variable ARCH to 'osx'")
      arch = "osx"
  else:
    print(f"Running under {uname} -- not supported, sorry.")
    exit(1)
  return arch

def binaries(arch):
  """Find the binaries."""
  global compilers
  if arch == "osx":
    compiler = "gfortran"
  else:
    compiler = "gfortran,ifort"
  ok = False
  while not ok:
    string = input(f"\nFind binaries from compiler (RETURN to skip this step) [{compiler}]: ")
    if string == "":
      print("Skipped")
      return
    elif re.match(r'y', string, flags=re.I):
      ok = True
    else:
      compiler = string.lower()
      if compiler not in compilers[arch]:
        print(f"Supported compilers for {arch} are {compilers[arch]}")
        compiler = ""
      else:
        ok = True
  root = os.path.join(os.environ["CAMCASP"],arch,compiler)
  print(f"Looking for binaries from compiler {compiler}")
  allok = True
  for program in ["camcasp","cluster","process","casimir","pfit"]:
    ok = True
    if os.path.islink(os.path.join("bin",program)):
      os.remove(os.path.join("bin",program))
    path = os.path.join(root,program)
    if not os.path.exists(path):
      #  Look in root/exe/program (root/exe/pfit/pfit for pfit)
      if program == "pfit":
        path = os.path.join(root,"exe/pfit/pfit")
      else:
        path = os.path.join(root,"exe",program)
      if not os.path.exists(path):
        #  Look in root/program
        path = os.path.join(root,program)
        if not os.path.exists(path):
          print(f"Can't find a {program} binary for OS {arch} and compiler {compiler}")
          ok = False
          allok = False
    if ok:
      os.symlink(path,os.path.join("bin",program))
      print(f"bin/{program} -> {path}")
  if allok: print("All found")


def verify():
  """Verify execution arrangements for scfcodes etc."""

  installed = {}
  for name in ["dalton","dalton2006","nwchem","psi4","molpro","orient","sapt"]:
    q = input(f"\nIs the {name} program installed [yN]? ")
    if q in ["", "N", "n"]:
      #  Not installed
      installed[name] = False
      link = os.path.join(camcasp,"bin",name)
      if os.path.exists(link):
        os.remove(link)
      sh =  os.path.join(camcasp,"bin",f"{name}.sh")
      if os.path.exists(sh):
        os.rename(sh,sh+".save")
      subprocess.call(f'touch {os.path.join(camcasp,"bin",f"no_{name}")}', shell=True)
      continue
    #  Installed.
    installed[name] = True
    if os.path.exists(os.path.join(camcasp,"bin",f"no_{name}")):
      os.remove(os.path.join(camcasp,"bin",f"no_{name}"))
    #  Check for link or bin/{name}.sh execution script.
    if os.path.exists(os.path.join(camcasp,"bin",f"{name}.sh")):
      print(os.path.join(camcasp,"bin",f"{name}.sh"), \
            f"will be invoked to execute {name}.")
      print("Please check that it is set up correctly for your system.")
    else:
      # Is this program in the PATH?
      try:
        typeout = subprocess.check_output(f"type {name}", shell=True,
                                          stderr=subprocess.STDOUT, encoding="iso-8859-1")
      except subprocess.CalledProcessError:
        print(f"{name} not found.")
        print("Ensure that the directory containing the program executable is in your PATH")
        print("or make a symbolic link to the executable in the CAMCASP/bin directory.")
        print("Then rerun setup.py.")
      else:
        # If so, print details
        print(typeout.strip())
        s = typeout.split()[-1]
        filetype = subprocess.check_output(f"file {s}", shell=True,
                                          stderr=subprocess.STDOUT, encoding="iso-8859-1")
        print(filetype.strip())
        installed[name] = True
        
    #  Special checks
    if name == "dalton" and installed[name]:
        if os.path.islink("bin/readDALTONmos"):
          os.remove("bin/readDALTONmos")
        print("""
Dalton can be compiled with the --int64 option to use 64-bit integers.
However the default and recommendation is to use 32-bit integers.""")
        string = input("Was Dalton compiled with 64-bit integers? [yN] ")
        if string in ["n", "N", ""]:
          os.symlink("readDALTON32mos","bin/readDALTONmos")
        else:
          os.symlink("readDALTON64mos","bin/readDALTONmos")

    elif name == "dalton2006" and installed[name]:  
        if os.path.islink("bin/readDALTON2006mos"):
          os.remove("bin/readDALTON2006mos")
          os.symlink("readDALTON32mos","bin/readDALTON2006mos")

    elif name == "psi4" and installed[name] and not os.path.exists(os.path.join(camcasp,"bin","psi4.sh")):
        #  Check environment variables
        print("\nChecking psi4 environment variables:")
        psi4home = os.environ.get("PSI4_HOME")
        if psi4home:
          if os.path.isdir(psi4home):
            print(f"PSI4_HOME = {psi4home}")
          else:
            print("PSI4_HOME appears to be set incorrectly")
        else:
          if os.path.exists("psi4.sh"):
            print ("Ensure that your psi4.sh script sets PSI4_HOME")
          else:
            print("PSI4_HOME is unset")
        #  The PSIPATH variable must include $CAMCASP/basis/psi4
        pathok = False
        camcasp_psi4 = os.path.join(camcasp,"basis","psi4")
        if "PSIPATH" in os.environ:
          paths = os.environ["PSIPATH"].split(":")
          if camcasp_psi4 in paths and os.path.join(camcasp_psi4,"for-psi4-lib") in paths:
            pathok = True
        if pathok:
          print(f'PSIPATH includes {camcasp_psi4}{{,"for-psi4-lib"}}: ok')
        else:
          if os.path.exists("psi4.sh"):
            print (f"""Ensure that your psi4.sh script sets PSIPATH to include
{camcasp_psi4} and
{os.path.join(camcasp_psi4,"for-psi4-lib")}\n""")
          else:
            print(f"""The environment variable PSIPATH must be set to include
{camcasp_psi4} and
{os.path.join(camcasp_psi4,"for-psi4-lib")}\n""")
        # Psi4 scratch directory
        psi_scratch = os.environ.get("PSI_SCRATCH")
        if psi_scratch and os.path.isdir(psi_scratch):
          print(f"PSI_SCRATCH = {psi_scratch}")
        else:
          if os.path.exists("psi4.sh"):
            print ("Ensure that your psi4.sh script sets PSI_SCRATCH to a suitable scratch directory")
          else:
            print("The environment variable PSI_SCRATCH must be set to a suitable scratch directory")
    elif name == "molpro" and installed[name]:
        #  Check environment variables
        print("\nChecking molpro environment variables:")
        molprohome = os.environ.get("MOLPRO_HOME")
        if molprohome:
          if os.path.isdir(molprohome):
            print(f"MOLPRO_HOME = {molprohome}")
          else:
            print("MOLPRO_HOME appears to be set incorrectly")
        else:
          if os.path.exists("molpro.sh"):
            print ("Ensure that your molpro.sh script sets MOLPRO_HOME")
          else:
            print("MOLPRO_HOME is unset")
        #  The MOLPROPATH variable must include $CAMCASP/basis/molpro
        pathok = False
        camcasp_molpro = os.path.join(camcasp,"basis","molpro")
        if "MOLPROPATH" in os.environ:
          paths = os.environ["MOLPROPATH"].split(":")
          if camcasp_molpro in paths:
            pathok = True
        if pathok:
          print(f"MOLPROPATH includes {camcasp_molpro}: ok")
        else:
          if os.path.exists("molpro.sh"):
            print (f"Ensure that your molpro.sh script sets MOLPROPATH to include \n{camcasp_molpro}")
          else:
            print(f"The environment variable MOLPROPATH must be set to include \n{camcasp_molpro}")
        # Molpro scratch directory
        molpro_scratch = os.environ.get("MOLPRO_SCRATCH")
        if molpro_scratch and os.path.isdir(molpro_scratch):
          print(f"MOLPRO_SCRATCH = {molpro_scratch}")
        else:
          if os.path.exists("molpro.sh"):
            print ("Ensure that your molpro.sh script sets MOLPRO_SCRATCH to a suitable scratch directory")
          else:
            print("The environment variable MOLPRO_SCRATCH must be set to a suitable scratch directory")
        # MO coeff transformation script
        if not os.path.exists(camcasp+"/bin/mol2cam.py"):
          os.symlink(camcasp+"/interfaces/molpro/mol2cam.py","bin/mol2cam.py")
  # End of loop over helper programs

  present = [installed[g] for g in ["dalton","dalton2006","nwchem","psi4","molpro"]]
  if any(present):
    pass
  else:
    print("""
IMPORTANT
You need to have at least one of the following SCF packages installed:
  Dalton 2013 or later
  Dalton 2006 (Dalton 2.0)
  NWChem
  Psi4
  Molpro
""")
  if not installed["orient"]:
    print("""The Orient program is needed for some procedures, in particular to
localize polarizabilities and obtain dispersion coefficients.""")


base()
os.chdir(camcasp)
print(f"Setting up links for {camcasp}")

arch = architecture()
binaries(arch)
verify()
