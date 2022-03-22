#!/usr/bin/env python3
#  -*-  coding:  utf-8  -*-

"""Submit a job to run a CamCASP calculation
"""

import argparse
import re
import os
# import string
import subprocess
from camcasp import CamRC
from headers import header, get_header


this = __file__
parser = argparse.ArgumentParser(
formatter_class=argparse.RawDescriptionHelpFormatter,
description="""Submit a job to run a CamCASP calculation.
""",epilog=f"""
Usage:
{this} [--queue <queue>] [--scheduler <sched>] <runcamcasp.py arguments>

e.g. {this} H2O -d avtz-isa

or, if it is necessary to modify the files that are automatically set up for the job:
runcamcasp.py H2O -d avtz-isa --setup
and after editing the job files:
{this} H2O -d avtz-isa --restart

The queue to which the job is to be submitted is set, in order of decreasing
priority,
from the --queue or -q flag on the command line, if present,
from the value set in the .camcasprc or camcasp.rc file, if any,
from the environment variable QUEUE, if set,
or to "batch", i.e. the Linux batch queue, if none of these is set.

If a queue management system is in use, the submitted job requires
a header giving information needed by the scheduler. Examples are in the
headers.py module; they will probably need to be edited for your particular
system. The required header can be specified by the environment variable
SCHEDULER, or by the --scheduler option on the command line. If the Linux
batch queue is to be used, ensure that the SCHEDULER variable is unset.

The --queue and --scheduler options, if present, must precede all other arguments.
The runcamcasp.py job name must be the first of the remaining (runcamcasp.py)
arguments.

""")

CamCASP = os.getenv("CAMCASP")
if not CamCASP:
    print("The environment variable CAMCASP must be set to the CamCASP base directory")
    print("Cannot continue")
    exit(1)
scheduler = os.getenv("SCHEDULER", "")

parser.add_argument("job", help="camcasp job name")
parser.add_argument("--queue", "-q", help="Job queue to use")
parser.add_argument("--scheduler", "--sched", help="Name of scheduler header to use")
                    
# runcamcasp.py arguments
parser.add_argument("arglist", nargs=argparse.REMAINDER,
                    help="Arguments to pass to the submitted runcamcasp.py process")

args = parser.parse_args()
arglist = args.arglist

if args.scheduler:
    scheduler = args.scheduler

home = os.getenv("HOME")
here = os.getcwd()

#  Read default parameters from .camcasprc or camcasp.rc
camrc = CamRC()
camrc.read_camcasprc()

#  Determine job queue
if args.queue:
    queue = args.queue
elif camrc.queue != "":
    queue = camrc.queue
elif os.getenv("QUEUE","") != "":
    queue = os.getenv("QUEUE")
else:
    # print(f"""The queue was not specified using --queue or defined in {home}/.camcasprc 
    # or in {CamCASP}/camcasp.rc or in {here}/camcasp.rc
    # or by environment variable QUEUE""")
    print("Defaulting to the Linux batch queue")
    queue = "batch"

# We additionally need the number of cores the scheduler needs to allocate
# This will be taken to be the maximum of all possible cores specified in
# .camcasprc or camcasp.rc
nproc = max(camrc.np_camcasp, camrc.np_nwchem, camrc.np_psi4, camrc.np_dalton, camrc.np_gamess,
        camrc.np_gaussian, camrc.nproc)
if nproc == 0:
    nproc = int(os.getenv("CORES","0"))

dir = args.job
memory_gb = camrc.memory_gb

#  Find items from the argument list, over-riding above values
for ix in list(range(len(arglist))):
    if arglist[ix] in ["-d","--directory"]:
        dir = arglist[ix+1]
        #  dir is only needed for the name of the job script
    elif arglist[ix] in ["-M", "--memory"]:
        memory_gb = int(arglist[ix+1])
    elif arglist[ix] == "--cores":
        nproc = int(arglist[ix+1])

#  Defaults
if nproc == 0:
    print("Could not determine the number of cores for this job. Defaulting to 2")
    print(f"  Consider defining settings in file {os.getenv('HOME')}/.camcasprc")
    nproc = 2
        
if memory_gb == 0:
    # print("Could not find memory specification. Defaulting to 8 GB")
    memory_gb = 8

#  Is the --ifexists flag present? If not, set it to "save".
if arglist.count("--ifexists") == 0:
    arglist.extend("--ifexists", "save")
    
#  Collect the runcamcasp.py arguments into a single string
argstring = " ".join(arglist)
# print argstring

#  Construct the job script
header = get_header(scheduler,args.job,queue,nproc,memory_gb)
jobscr = os.path.join(here,dir+".sh")
with open(jobscr,"w") as S:
    S.write(header)
    S.write(f"""
/bin/bash <<EOF

# Make sure that CamCASP/bin is in the PATH
[[ ":$PATH:" != *":{CamCASP}/bin:"* ]] && export PATH="{CamCASP}/bin:$PATH"
# echo $PATH

cd {here}
echo "Starting: runcamcasp.py {args.job} {argstring}"
{CamCASP}/bin/runcamcasp.py {args.job} {argstring} &> {args.job}.out

rc=$?
if (( rc > 0 )); then
    echo "Failed, error code $rc"
else
    echo "Finished"
fi

EOF
""")

print(f"Queue is {queue}")

if queue in ["batch","b"]:
    subprocess.call(f"batch < {jobscr}", shell=True)
elif queue in ["bg"]:
    subprocess.call(f"bash {jobscr}", shell=True)
else:
    # print "qsub", "-q", queue, jobscr
    subprocess.call(["qsub", "-q", queue, jobscr])


