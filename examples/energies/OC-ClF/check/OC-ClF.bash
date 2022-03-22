#!/bin/bash
echo "My LD_LIBRARY_PATH is:"
echo /usr/local/lib64:/usr/lib:/lib
export PATH=/home/ajs1/camcasp-5.7/bin:/home/ajs1/SAPT2006/bin:/usr/sbin:/sbin:/usr/local/bin:/usr/bin:/usr/X11R6/bin:/bin:/opt/gnome/bin:/opt/kde3/bin:/usr/lib/jvm/jre/bin:.:/home/ajs1/bin:/usr/local/shared/ubuntu-12.04/x86_64/bin:/usr/local/shared/ubuntu-12.04/bin:/usr/local/shared/bin
echo "PATH = " $PATH
#
echo "Starting at $(date)"

export SCRATCH=/scratch/fastscratch/ajs1


# ---------------------------
# run the job
# ---------------------------

cd /home/ajs1/camcasp-5.7/examples/energies/OC-ClF/test

# SAPT.bash -j OC-ClF --files "A B" -scratch /scratch/fastscratch/ajs1 -scfcode dalton2013 #    -w OC-ClF -M 2500

execute.py OC-ClF --parts A B --scfcode dalton2013 --scratch /scratch/fastscratch/ajs1     --work OC-ClF -M 2500 

echo "Finished at $(date)"

