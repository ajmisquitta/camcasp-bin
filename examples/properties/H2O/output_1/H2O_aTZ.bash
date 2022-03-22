#!/bin/bash
echo "My LD_LIBRARY_PATH is:"
echo /usr/local/lib64:/usr/lib:/lib
export PATH=/home/ajs1/camcasp/trunk/bin:/home/ajs1/SAPT2006/bin:/usr/sbin:/sbin:/usr/local/bin:/usr/bin:/usr/X11R6/bin:/bin:/opt/gnome/bin:/opt/kde3/bin:/usr/lib/jvm/jre/bin:.:/home/ajs1/bin:/usr/local/shared/ubuntu-12.04/x86_64/bin:/usr/local/shared/ubuntu-12.04/bin:/usr/local/shared/bin
echo "PATH = " $PATH
#
echo "Starting at $(date)"

export SCRATCH=/scratch/fastscratch/ajs1


# ---------------------------
# run the job
# ---------------------------

cd /home/ajs1/camcasp/trunk/examples/properties/H2O/H2O_aTZ

# SAPT.bash -j H2O_aTZ --files "A" -scratch /scratch/fastscratch/ajs1 -scfcode dalton2013 #    -w H2O_aTZ -M 500

execute.py H2O_aTZ --parts A --scfcode dalton2013 --scratch /scratch/fastscratch/ajs1     --work H2O_aTZ -M 500 

echo "Finished at $(date)"

