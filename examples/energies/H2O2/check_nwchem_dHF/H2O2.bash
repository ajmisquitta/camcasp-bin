#!/bin/bash
echo "My LD_LIBRARY_PATH is:"
echo /usr/local/lib64:/usr/lib:/lib
export PATH=/usr/local/ecce-builder-v7.0/scripts:/home/ajs1/camcasp-5.7/bin:/home/ajs1/SAPT2006/bin:/usr/sbin:/sbin:/usr/local/bin:/usr/bin:/usr/X11R6/bin:/bin:/opt/gnome/bin:/opt/kde3/bin:/usr/lib/jvm/jre/bin:.:/home/ajs1/bin:/usr/local/shared/ubuntu-10.04/x86_64/bin:/usr/local/shared/ubuntu-10.04/bin:/usr/local/shared/bin:/usr/local/shared/intel/composer_xe_2013_sp1.1.106/bin/intel64
echo "PATH = " $PATH
#
echo "Starting at $(date)"

export SCRATCH=/scratch/fastscratch/ajs1


# ---------------------------
# run the job
# ---------------------------

cd /home/ajs1/camcasp-5.7/examples/energies/H2O2/test_dHF

# SAPT.bash -j H2O2 --files "A B AB" -scratch /scratch/fastscratch/ajs1 -scfcode nwchem #    -w H2O2 -M 2500

execute.py H2O2 --parts A B AB --scfcode nwchem --scratch /scratch/fastscratch/ajs1     --work H2O2 -M 2500 

echo "Finished at $(date)"

