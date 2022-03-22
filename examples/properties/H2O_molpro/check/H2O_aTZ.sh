#!/bin/sh

PATH=/home/andreas/programs/CamCasp/CamCASP-dev-ajm-6.0/x86-64/ifort:/home/andreas/programs/nwchem/nwchem-6.8.1/bin/LINUX64:/home/andreas/programs/orient/Orient-5.0/bin:/home/andreas/programs/CamCasp/CamCASP-dev-ajm-6.0/bin:/home/andreas/programs/CamCasp/CamCASP-dev-ajm-6.0/x86-64/ifort:/home/andreas/programs/nwchem/nwchem-6.8.1/bin/LINUX64:/home/andreas/programs/orient/Orient-5.0/bin:/home/andreas/programs/CamCasp/CamCASP-dev-ajm-6.0/bin:/home/andreas/programs/julia/julia-0.6.0/bin:/home/andreas/programs/intel/intel17/compilers_and_libraries_2017.2.174/linux/bin/intel64:/home/andreas/programs/intel/intel17/compilers_and_libraries_2017.2.174/linux/mpi/intel64/bin:/home/andreas/programs/intel/intel17/debugger_2017/gdb/intel64_mic/bin:/home/andreas/programs/lyx/bin:.:/home/andreas/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/home/andreas/bin:/home/andreas/programs/tinker/tinker-8.4.4/bin:/home/andreas/programs/tinker/tinker-8.4.4/source:/home/andreas/programs/gdma/gdma-2.2.06/bin:/home/andreas/programs/gromacs/bin:/home/andreas/programs/plumed/bin:/home/andreas/programs/mopac/MOPAC2016:/home/andreas/programs/maple/maple9/bin
export PATH
echo "PATH = " $PATH
#
# echo "Starting at $(date)"

SCRATCH=/home/andreas/tmp
export SCRATCH

# ---------------------------
# run the job
# ---------------------------

cd /home/andreas/programs/CamCasp/CamCASP-dev-ajm-6.0/examples/properties/H2O/H2O_aTZ

execute.py H2O_aTZ --parts A --scfcode molpro --scratch /home/andreas/tmp     --work H2O_aTZ -M 500 --nproc 1 --cores 8 --wait 0.5      --mpstat

echo "Finished at $(date)"

