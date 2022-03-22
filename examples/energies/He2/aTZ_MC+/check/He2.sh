#!/bin/sh

PATH=/home/ajs1/CamCASP/bin:/usr/lib/xpra:/home/ajs1/CamCASP/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:/usr/local/shared/ubuntu-16.04/x86_64/bin:/usr/local/shared/ubuntu-16.04/bin:/usr/local/shared/bin:/home/ajs1/bin:.:/home/ajs1/CamCASP/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/home/ajs1/bin:.:/home/ajs1/bin:.
export PATH
echo "PATH = " $PATH
#
# echo "Starting at $(date)"

SCRATCH=/scratch/fastscratch/ajs1
export SCRATCH

# ---------------------------
# run the job
# ---------------------------

cd /home/ajs1/CamCASP/examples/energies/He2/aTZ_MC+/test

execute.py He2 --parts A B --scfcode dalton --scratch /scratch/fastscratch/ajs1     --work He2 -M 1000 --nproc 1 --cores 2 --wait 0.5      --mpstat

echo "Finished at $(date)"

