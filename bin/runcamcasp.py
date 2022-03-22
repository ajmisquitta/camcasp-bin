#!/usr/bin/env python3
#  -*-  coding:  iso-8859-1  -*-

summary = """
Set up and carry out a CamCASP calculation.

CamCASP and related jobs can be set up using this script. A "cluster file"
must be provided, containing the molecular geometries and details of the
calculation to be carried out. See the users' guide for details. Available
calculation types, specified in the cluster file, are:
    properties: multipole moments, polarizabilities, etc. of single molecules.
    sapt-dft: symmetry-adapted perturbation theory of dimer interaction
        energies, using molecular wavefunctions obtained by density functional
        theory.
    sapt: symmetry-adapted perturbation theory using Hartree-Fock wavefunctions
        and perturbative correlation corrections.
    delta-hf: calculation of the delta-HF estimate of higher-order induction
        energy terms.
    supermolecule: standard supermolecule calculation of dimer energies, with
        counterpoise correction for BSSE.
Use "runcamcasp.py --help" for details of arguments.
"""

import os
import sys
import re
import argparse
import readline
import shutil
import string
import subprocess
from time import sleep
from camcasp import *

env_camcasp = os.environ.get("CAMCASP")
if not env_camcasp:
    print("Error: Environment variable CAMCASP has not been defined. Cannot proceed.")
    exit(1)
env_scratch = os.environ.get("SCRATCH")
if not env_scratch:
    print("Error: Environment variable SCRATCH has not been defined. Cannot proceed.")
    exit(1)

parser=argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
description = "Set up and run a CamCASP job.",
epilog = """
CamCASP and related jobs can be set up using this script. A "cluster file"
must be provided, containing the molecular geometries and details of the
calculation to be carried out. See the users' guide for details. Available
calculation types are:
  properties: multipole moments, polarizabilities, etc. of single molecules.
  sapt-dft: symmetry-adapted perturbation theory of dimer interaction
    energies, using molecular wavefunctions obtained by density functional
    theory.
  sapt: symmetry-adapted perturbation theory using Hartree-Fock wavefunctions
    and perturbative correlation corrections.
  delta-hf: calculation of the delta-HF estimate of higher-order induction
    energy terms.
  supermolecule: standard supermolecule calculation of dimer energies, with
    counterpoise correction for BSSE.

The runcamcasp.py script has several options, but in its simplest form it
can be just
  runcamcasp.py <job> [-d <directory>]
where job is a short name for the job, also used as a prefix for many of the
generated files, and the job files are placed in the specified directory.
Even the directory specification can be omitted (as indicated by the square
brackets, which are not to be typed in). If it is omitted, a directory called
<job> is used. However it is recommended that a new directory is used for
every job. 

So the files for the calculation reside in the directory specified by the
-d or --directory flag. For a restart, the directory must exist already.
Otherwise, if the directory exists, the action is specified by the
--ifexists flag:
  delete  Delete the existing directory and make a new one.
  abort   Leave the directory alone and cancel the new job.
  new, keep, save: Rename the existing directory and make a new one with the
          specified name.
  ask:    Ask what to do. This is the default action.
If the --ifexists flag is specified for a restart, it applies to the
OUT results subdirectory. In this case, new, keep, or save causes the
existing OUT subdirectory, if any, to be renamed and a new OUT
subdirectory created. Otherwise an existing OUT directory is re-used,
and files in it are overwritten.

Note that in a restarted job, this script reads the copy of the .clt
file in the job directory -- not the one in the current directory,
which may have been changed. However none of the files for the job are
regenerated. In particular, the .cks file containing the data for the
CamCASP step is not changed by this script on a restart, so it may be
edited before the restart to change options or correct errors. The
--setup-only flag can be used to stop after setting up the files, to
allow changes to the files before starting the job with the --restart flag.

The SCF code used to obtain the molecular orbitals for the system may be
specified in several ways. In order of priority, from highest to lowest,
1. --scfcode flag on the runcamcasp.py command line, if present.
2. SCFCODE entry in the cluster file, if present.
3. Environment variable CAMCASP_SCFCODE, if set.
4. Psi4, which is now recommended and the default.
""")

parser.add_argument("job", help="Job name and prefix for job file names")
parser.add_argument("--clt", help="Name of cluster file (default <job>.clt)")
parser.add_argument("--directory", "-d",  help="Directory to run job in (default <job>)")
parser.add_argument("--scfcode", help="Specify scfcode",
                    choices=["dalton2006", "dalton", "dalton2013", "dalton2015",
                             "dalton2016", "nwchem", "psi4", "molpro"])
group = parser.add_mutually_exclusive_group()
group.add_argument("--verbosity", type=int, default=0,
                    help="Print additional information about the job if > 0")
group.add_argument("--verbose", "-v", action="count",
                   help="Print additional information about the job")
parser.add_argument("--ifexists", help="Action if directory exists",
                    default="ask", choices=["ask", "delete", "new", "keep",
                                            "save", "abort"])
parser.add_argument("--import", dest="imported", nargs="*", default=[],
                    help="Copy specified files into job directory")
parser.add_argument("-M", "--memory", help="Memory for job in GB",
                    type=int, default=0)
parser.add_argument("-q", "--queue",
                    help="Queue for job (bg, batch, none) DEPRECATED",
                    default="", choices=["bg", "batch", "none"])
parser.add_argument("--scratch", help="Scratch directory (default is the\
                    environment variable SCRATCH, if set)",
                    default=env_scratch)
parser.add_argument("--work", help="Work subdirectory (under scratch)",
                    default="")
parser.add_argument("--cores", help="Number of cores available for all jobs",
                    type=int, default=0)
parser.add_argument("--cores-camcasp", help="Number of cores available for CamCASP job only.",
                    type=int, default=0)
parser.add_argument("--direct", help="Use direct integral management",
                    action="store_true")
parser.add_argument("--restart", help="Restart job using existing directory",
                    action="store_true")
parser.add_argument("--debug", help="Don't delete scratch files",
                    action="store_true")
parser.add_argument("--setup", "--setup-only", help="Set up files for the job and stop",
                    action="store_true")
parser.add_argument("--log", help="Path to logfile (default OUT/jobname.log)")
parser.add_argument("--testenv", "--test-env", help="Test the environment only.",
                    action="store_true")

args = parser.parse_args()

if args.testenv:
    args.verbosity = 10

#  args.job is a required argument. Open an instance of class Job.
#  Note: job.name = args.job
job = Job(args.job)

#  Directory to run job in. Default is the job name (set in Job.__init__).
if args.directory:
    job.dir = args.directory
else:
    job.dir = args.job

# Log file name (if not defined, it will be set in execute function)
if args.log:
    job.logfile = args.log
else:
    #  Default set in execute function
    job.logfile = ""

#  The work directory under $SCRATCH
if args.work:
    job.work = os.path.join(args.scratch,args.work)
else:
    job.work = os.path.join(args.scratch,job.name)
  
job.debug = args.debug

#  Cluster fle
if args.clt:
    job.cltfile = args.clt
else:
    job.cltfile = job.name + ".clt"
job.restart = args.restart
if job.restart:
    job.cltfile = os.path.join(job.dir,job.cltfile)
if not os.path.exists(job.cltfile):
    die(f"Cluster file {job.cltfile} not found")

#  Has the SCF code been set on the command line?
if args.scfcode in ["dalton","dalton2013","dalton2015","dalton2016"]:
    job.scfcode = "dalton"
else:
    job.scfcode = args.scfcode
#  This will give None if it wasn't set, and it will be set later

#  Verbosity
if args.verbosity:
    verbosity = args.verbosity
elif args.verbose:
    verbosity = args.verbose
else:
    verbosity = 0

# =====================================================================
# Now read in the camcasp.rc/.camcasprc file before potentially
# overriding settings using the remainder of the command-line arguments
# =====================================================================

camrc = CamRC()
camrc.read_camcasprc(verbosity)

# ===================================================
# Now for the remainder of the command-line arguments
# In all these we first use the command-line args
# if present, else we use settings in camcasp.rc
# ===================================================

#  These values can be over-ridden on the command line:
if args.direct: 
    job.direct = True
else:
    job.direct = camrc.direct
if args.memory: 
    job.memory = args.memory
else:
    job.memory = camrc.memory_gb
if args.queue:  
    job.queue = args.queue
else:
    job.queue = camrc.queue 

# Imported files:
job.imports = args.imported

#  ==================================================
#  Some parameters are obtained from the Cluster file
#  ==================================================
read_clt(job,verbosity)

#  Check that the specified scfcode is installed
if os.path.exists(os.path.join(camcasp,"bin",f"no_{job.scfcode}")):
    print(f"It appears that {job.scfcode} is not installed")
    print("If it is, please re-run setup.py")
    exit(1)

if args.cores:  
    job.cores = args.cores
else:
    if job.scfcode == "nwchem":
        job.cores = camrc.np_nwchem
    elif job.scfcode == "psi4":
        job.cores = camrc.np_psi4
    elif "dalton" in job.scfcode:  # since many dalton options exist
        job.cores = camrc.np_dalton
    elif job.scfcode == "molpro":
        job.cores = camrc.np_molpro
    else:
        job.cores = camrc.nproc

if args.cores_camcasp:  
    job.cores_camcasp = args.cores_camcasp
else:
    if camrc.np_camcasp > 0:
        job.cores_camcasp = camrc.np_camcasp
    elif camrc.nproc > 0:
        job.cores_camcasp = camrc.nproc

#  =============================
#  Default values if still unset
#  Either set a sensible default
#  or use an environment var
#  =============================

if job.memory == 0:
    # Set memory in GB
    job.memory = 8

if job.cores == 0: 
    if os.environ.get("CORES"):
        job.cores = int(os.environ.get("CORES"))
    else:
        job.cores = 2

if job.cores_camcasp == 0:
    if os.environ.get("CORES_CAMCASP"):
        job.cores_camcasp = int(os.environ.get("CORES_CAMCASP"))
    else:
        job.cores_camcasp = 2

if job.queue == "":
    if os.environ.get("QUEUE"): 
        job.queue = os.environ.get("QUEUE")
    else:
        print("Environment variable QUEUE has not been defined. This is not fatal.")
        print("  However either supply a queue using -q or define it in $HOME/.camcasprc")
        print("  or in $CAMCASP/camcasp.rc or in $PWD/camcasp.rc")
        print("  DEFAULTING to batch")
        job.queue = "batch"


if verbosity > 0:
    print(job.runtime_info)
    print(f"Action if directory exists: {args.ifexists}")

if args.testenv:
    print("This is a test of the CamCASP environment so the code will stop here.")
    print(job.__str__())
    exit(0)

#  ========================
#  End of job specification
#  ========================

camcasp_bin = env_camcasp + "bin"

#  Find a directory to run the job in
d = job.dir
#  Remove any trailing slashes from directory name
d = d.rstrip("/")
if args.restart:
    #  In this case the directory must exist.
    if os.path.exists(d):
        job.dir = os.path.abspath(d)
    else:
        die(f"Directory {d} not found")
    try:
        os.chdir(d)
    except IOError as e:
        if e.errno == errno.EACCES:
            die("Can't open " + d)
        else:
            die("Error for " + d)
    if os.path.exists("OUT"):
        if args.ifexists in ["new","keep","save"]:
            newdir("OUT")
        elif args.ifexists == "delete":
            shutil.rmtree("OUT")
            print("Existing OUT subdirectory deleted")
        elif args.ifexists == "abort":
            print("Subdirectory OUT exists; aborting job")
            exit(2)

else:
    if os.path.exists(d):
        #  Delete or rename existing directory according to --ifexists
        #  argument or interactive response
        if args.ifexists == "delete":
            shutil.rmtree(d)
            print(f"Directory {d} exists; now deleted")
        elif args.ifexists == "abort":
            print(f"Directory {d} exists; aborting job")
            exit(2)
        elif args.ifexists in ["new","keep","save"]:
            print(f"Directory {d} exists; saving it and creating another")
        else:
            print(f"Directory {d} already exists.")
            try:
                ans = input("Delete it and its contents, Save it and make a new one, or Abort job? [dSa]: ")
            except (RuntimeError, TypeError, NameError):
                print("Error with input. Defaulting to save the old directory.")
                ans = "s"
            except:
                print("Unexpected error with input. Defaulting to save the old directory.")
                ans = "s"

            # print(ans)
            if ans in ["D","d"]:
                shutil.rmtree(d)
            elif ans in ["S","s",""]:
                # print("Not deleted.")
                pass
            elif ans in ["A","a"]:
                exit(0)

    #  At this point, if the specified directory d still exists, it will be
    #  renamed as d_nnn, where d_nnn is the first directory of the form
    #  d_001, d_002, etc. beyond any that already exist. Then a new
    #  directory with the specified name is opened for the new job.
    newdir(d)

    #  Copy files specified by --import into the job directory
    for file in job.imports:
        try:
            shutil.copy2(file, d)
        except IOError:
            die(f"Can't import file {file} into {d}")

    #  Copy the cluster file into the job directory, chdir to it
    #  and run the cluster program
    print(f"Setting up files in directory {d}")
    shutil.copy(job.cltfile, d)
    job.dir = os.path.abspath(d)
    os.chdir(d)
    print(f"See {job.dir}/{job.cltfile}.clout for output of CLUSTER")
    #cluster_command = f"{camcasp_bin}/cluster --scfcode {job.scfcode} --job {job.name} < {job.cltfile} > {job.cltfile}.clout"
    #print(f"Command : {cluster_command}")
    #rc = subprocess.call(cluster_command, shell=True)
    with open(job.cltfile + ".clout","w") as OUT, open(job.cltfile) as IN:
        rc = subprocess.call(["cluster","--scfcode",job.scfcode,"--job",job.name], stdin=IN, stdout=OUT, stderr=OUT)
    #rc = subprocess.call(f"cluster --scfcode {job.scfcode} --job {job.name} \
    #        < {job.cltfile} > {job.cltfile}.clout",shell=True)
    if rc > 0:
        print(f"Error {rc:1d} from cluster -- job aborted")
        exit(1)

    if job.scfcode in ["dalton", "dalton2006"]:
        make_dalton_datafiles(job,verbosity)
    elif job.scfcode == "psi4":
        if os.path.exists(job.name+".psi4"):
            #  This file needs to be processed into a jobname_AB.in file
            make_psi4_datafile(job, verbosity)


jobtype = {
  "saptdft": "SAPT(DFT)",
  "deltahf": "Delta-HF",
  "sapt": "SAPT",
  "properties": "properties",
  "supermol": "supermolecule",
  "psi4-saptdft": "Psi4-SAPT(DFT)",
}

if args.setup:
    print(f"""Job files set up.
Use
  runcamcasp.py {job.name} --clt {job.cltfile} -d {d} [options] --restart [&]
or
  submit_camcasp.py [--queue <queue>]  {job.name} --clt {job.cltfile} -d {d} [options] --restart
(--queue option first if present) to execute the job.""")
    exit(0)
elif args.restart:
    print(f"Restarting job in directory {d}")
else:
    print(f"This is a {jobtype[job.runtype]} calculation with SCF program {job.scfcode}")

sys.stdout.flush()
rc = 0
# print("Calling execute")
rc = execute(job, verbosity)

exit(rc)
