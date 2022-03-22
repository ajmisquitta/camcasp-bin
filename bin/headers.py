#!/usr/bin/env python3
#  -*-  coding:  iso-8859-1  -*-


"""
Python module containing headers for PBS and GE schedulers, for use with
submit_camcasp.py. They may need to be modified according to local requirements.

Any number of headers can be defined, with arbitrary names. Set the SCHEDULER
environment variable to the name of the one you want to use.
"""

import os
CamCASP = os.getenv("CAMCASP")

header = {"PBS": """
##############################################################################
# start of PBS directives (irrelevant for background jobs)
##############################################################################
# set the name of the job
#PBS -N {job}
#
# Queue to use.
#PBS -q {q}
#
# Output and error filenames. These are relative to the directory you
# submitted the job from so make sure it was a shared filesystem, or
# give an absolute path. Currently commented out.
##PBS -o out
##PBS -e error

#
# Use this to adjust required job time, up to the maximum for the queue
# It is better to use walltime than CPU time as this enables the scheduler
# to optimize.
#PBS -l walltime=4:00:00,ncpus={np},mem={mem}gb
#
##############################################################################
# Start of shell script proper. Do not put PBS directives after this point.
##############################################################################
#
# Here is where you should set any environment variables your job requires,
# because PBS won't read your shell startup files. The most common one is
# LD_LIBRARY_PATH, required so that binaries can find their library files if
# they're in odd places. qsub will pass the job whatever LD_LIBRARY_PATH you
# had at submit time, so most people won't need this.
#
# export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH
""",

"GE": """# ---------------------------
# set the name of the job
#$ -N {job}
#$ -pe openmpi {np}
#

#----------------------------
# set up the parameters for qsub
# ---------------------------

#  Mail to user at beginning/end/abort/on suspension
#$ -m beas
#  By default, mail is sent to the submitting user 
#  Use  $ -M username    to direct mail to another userid 

# Execute the job from the current working directory
# Job output will appear in this directory
#$ -cwd
#   can use -o dirname to redirect stdout 
#   can use -e dirname to redirect stderr

#to request resources at job submission time 
# use #-l resource=value
# For instance, the commented out 
# lines below request a resource of 'express'
# and a hard CPU time of 10 minutes 
####$ -l express
####$ =l h_cpu=10:00

#  Export the following environment variables
#$ -v PATH 
"""}


def get_header(scheduler,job_name,queue,nproc,memory_gb):
    """Return the header for the specified scheduler with the parameters supplied"""

    if not scheduler:
        #  SCHEDULER unset or ""
        return("")
    elif scheduler in header:
        return header[scheduler].format(job=job_name,q=queue,np=nproc,mem=memory_gb)
    else:
        print(f'''Scheduler {scheduler} not recognised. To install a new one, edit
{os.path.join(CamCASP,"bin","headers.py")}
using the existing headers as examples.''')
        exit(1)

