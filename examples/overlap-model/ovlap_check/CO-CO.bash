#!/bin/bash

export PATH=/home/ajs1/camcasp/trunk/bin:/home/ajs1/SAPT2006/bin:/usr/sbin:/sbin:/usr/local/bin:/usr/bin:/usr/X11R6/bin:/bin:/opt/gnome/bin:/opt/kde3/bin:/usr/lib/jvm/jre/bin:.:/home/ajs1/bin:/usr/local/shared/ubuntu-12.04/x86_64/bin:/usr/local/shared/ubuntu-12.04/bin:/usr/local/shared/bin:/usr/local/shared/intel/composer_xe_2013_sp1.2.144/bin/intel64
echo "PATH = " $PATH
#
echo "Starting at $(date)"

export SCRATCH=/scratch/fastscratch/ajs1


# ---------------------------
# run the job
# ---------------------------

cd /home/ajs1/camcasp/trunk/examples/overlap-model/ovlap

# SAPT.bash -j CO-CO --files "A B" -scratch /scratch/fastscratch/ajs1 -scfcode dalton2013 #    -w CO-CO -M 2500

execute.py CO-CO --parts A B --scfcode dalton2013 --scratch /scratch/fastscratch/ajs1     --work CO-CO -M 2500 

echo "Finished at $(date)"

