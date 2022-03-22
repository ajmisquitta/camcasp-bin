#!/bin/bash
#
# ---------------------------
# set the name of the job
#$ -N He_aTZ
#

#----------------------------
#  Set up the parameters for qsub. This part may need to be
#  changed if some other job scheduler is in use.
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

#  Export these environment variables
#$ -v PATH 

export SCRATCH=/scratch/fastscratch/ajs1
export CAMCASP=/home/ajs1/camcasp-5.5
export PATH=/home/ajs1/camcasp-5.5/bin:$PATH
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/Cluster-Apps/pgi/6.1-1/linux86-64/6.1/libso:/usr/lib64

echo Running on $HOSTNAME

echo "TMPDIR = $SCRATCH/test"
echo "PATH = $PATH"
echo "LD_LIBRARY_PATH = $LD_LIBRARY_PATH"
echo "JOB ID = $JOB_ID"


# ---------------------------
# run the job
# ---------------------------

if [[ -z $JOB_ID ]]; then
  # Environment variable  is not defined so don't use it:
  DALTON_CamCASP.bash  -j He_aTZ -M 2000
else
  DALTON_CamCASP.bash  -j He_aTZ -id "$JOB_ID" -M 2000
fi

