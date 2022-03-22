#!/usr/bin/env python3

"""
Carry out a batch of SAPT-DFT or delta-HF calculations on a dimer system,
as specified by a cluster-file template and a geometry file.
"""

import os
import re
import sys
import argparse
import subprocess


parser=argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
description="""
Carry out a batch of SAPT-DFT or delta-HF calculations.
""", epilog="""
The job argument is the file prefix for all the files used by the job.
It is modified by the suffix "_<index>", where the index is read from the
geometry file.
The template is a cluster file containing any or all of the geometry
variables Rx, Ry, Rz, alpha, Nx, Ny and Nz, each enclosed in braces.
For example (for the helium dimer):

Rotate He2 by {alpha} about {Nx} {Ny} {Nz}
Place  He2 at {Rx} {Ry} {Rz}

It may also contain the variables {task}, {basis} and {type}, which can be
set by command-line options.

The geomfile contains geometry data, one line for each job,
in the order
  index  Rx  Ry  Rz  alpha  Nx  Ny  Nz
This is as output by the ENERGY-SCAN module. (Rx,Ry,Rz) is the vector
position of the origin of molecule B, and alpha is a rotation of B
about the vector (Nx,Ny,Nz), Each job is identified as
{job}_{index}, with the geometry variables substituted into the
cluster file template. Lines in the geometry file beginning with "!" are
ignored. The job is run either in a directory <job> (for sapt-dft
calculations) or <job>_dHF (for delta-HF calculations). 

The -q or --queue may be set to "bg", "batch" or "none". The last of
these may be used to check that the files have been set up correctly.
The jobs will not be run in this case. It is strongly recommended that
"batch" is used for the actual calculations; then the jobs will be
queued and a new job will be started only when the load average falls
below a certain level (usually 1.5).

When the calculations have completed, the extract_saptdft.py script
will extract a table of the energies for all dimer geometries:
extract_saptdft.py <job>_*

If any of the jobs fail, delete just their directories, and run the
whole set again when the problems have been fixed. Any jobs for which
the directories are present will be skipped.
"""
)

parser.add_argument("job", help="job name")
parser.add_argument("template", help="cluster file template")
parser.add_argument("geomfile", help="file containing geometry data")
parser.add_argument("--dHF", action="store_true",
                    help="run delta-HF calculations instead of sapt-dft")
parser.add_argument("-b", "--basis", default="avtz",
                    help="basis set for calculation (default aug-cc-pVTZ)"),
parser.add_argument("-t", "--type", help="basis type (default mc+)", default="mc+",
                    choices=["mc", "mc+", "dc", "dc+"])
parser.add_argument("--direct", default=False, action="store_true",
                   help="Use direct integral management"),
parser.add_argument("--memory", "-M", default="",
                    help="Specify memory for job in MB")
parser.add_argument("-q", "--queue", help="Specify queue for job")
parser.add_argument("--scfcode", help="Force use of scfcode",
                    choices=["dalton2006","dalton","dalton2013","nwchem","psi4",""], default="")
parser.add_argument("--nproc", help="Number of processors to use")
parser.add_argument("--cores", help="Number of cores on machine")
parser.add_argument("-v", "--verbose", action="store_true",
                    help="print additional information about the job")

args = parser.parse_args()

if args.dHF:
    task = "delta-hf"
    suffix = "_dHF"
    type = "dc"
else:
    task = "sapt-dft"
    suffix = ""
    type = args.type

here = os.getcwd()
scheduler = os.getenv("SCHEDULER")
if args.queue:
    queue = args.queue
else:
    queue = os.getenv("QUEUE")
    if not scheduler and not queue:
        #  Use the Linux batch queue unless overridden
        queue = "batch"

#  Read template file
with open(args.template) as T:
    template = T.read()

skip = 0
g = []
with open(args.geomfile) as GEOM:
    for line in GEOM:
        #  Skip blank lines and lines starting with "!" or "#".
        if re.match(r'\s*(!|#|$)', line):
            pass
        #  Exit if line starts with "end"
        elif re.match(r' *end', line, flags=re.I):
            break
        else:
            #  Check for "skip nn" line
            m = re.match(r' *skip +(\d+)', line, flags=re.I)
            if m:
                #  Skip lines
                skip = int(m.group(1))
                continue
            if skip > 0:
                skip -= 1
                continue
            g = line.split()
            job = f"{args.job}_{g[0]}"
            if os.path.exists(job+suffix):
                #  Directory already exists for this job.
                #  We assume that this job has been completed.
                pass
            else:
                with open(f"{job}{suffix}.clt","w") as CLT:
                    CLT.write(template.format(job=job, Rx=g[1], Ry=g[2], Rz=g[3],
                                              alpha=g[4], Nx=g[5], Ny=g[6], Nz=g[7],
                                              basis=args.basis, type=type, task=task))

                arguments = ["submit_camcasp.py", "-q", args.queue, job,
                             "--clt", f"{job}{suffix}.clt", "-d", job+suffix,
                             "--ifexists", "abort"]
                if args.direct:
                    arguments.extend(["--direct"])
                if args.memory:
                    arguments.extend(["-M", args.memory])
                if args.scfcode:
                    arguments.extend(["--scfcode", args.scfcode])
                if args.verbose:
                    arguments.extend(["--verbose"])
                    print(" ".join(arguments))

                subprocess.call(arguments)
      
