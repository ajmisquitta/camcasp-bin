# CamCASP  version 7.0

**Alston Misquitta, Anthony Stone and Andreas Hesselmann**


## Instructions for obtaining and installing the CamCASP program

1. CamCASP is now available from github.com. The recommended procedure
   is to change to a suitable directory and run the command, e.g.
   > git clone git@github.com:ajmisquitta/camcasp-bin.git/camcasp.git camcasp-7.0

   which will clone the code into a new camcasp-7.0 subdirectory.

   The binary files in x86-64/ifort/ and x86-64/gfortran/ are gzipped
   to reduce their size. Before proceeding, gunzip them using:
   > cd camcasp-7.0

   > gunzip x86-64/{ifort,gfortran}/\*.gz

2. It is no longer necessary to apply for a licence to use CamCASP,
   but your use of the program is subject to the licence that is to be
   found in the LICENCE file in the CamCASP directory.

3. Set the CAMCASP environment variable to point to the new CamCASP
   directory, for example by using (from the CamCASP base directory):
   >    export CAMCASP=$PWD

   though usually you will want to set this variable in your startup
   script. 

4. Add the CAMCASP bin directory to your path, e.g. using
   > export PATH=$CAMCASP/bin:$PATH

   Again, this is most conveniently done in your startup directory.

5. CamCASP needs at least one of the SCF codes Dalton or NWChem or
   Psi4. For each of these that you wish to use, provide either
   a symbolic link dalton or nwchem or psi4 in the CamCASP/bin directory
   that points to the corresponding executable, or a shell script
   dalton.sh or nwchem.sh or psi4.sh that can be executed to invoke
   the program. There are example files CamCASP/bin/psi4.sh.example
   etc. that explain what is needed.

6. Run the command 
   >    setup.py

   (You will need Python, version 3.6 or later, for this and other
   CamCASP scripts.) This script will ask for information about the
   SCF codes that you have installed. It will also ask for
   information about the Orient program, which is needed for some
   CamCASP procedures. Orient is also available from gitlab.com; see
   `http://gitlab/anthonyjs/orient/-/wikis/home` for details.

   The setup.py script can be run again at any time, if for example
   you install another SCF program.

7. Run the tests in the CamCASP/tests directory. See the README in
   that directory for details, or run
   >    run\_tests.py --help

Once all this is done, you are ready to submit CamCASP jobs. See the
User's Guide, in $CAMCASP/doc/users\_guide.pdf, for full details. There
are several examples in $CAMCASP/examples that you can use as tests of
the program and as examples for your own calculations.



## Installation from source:


Additional authorisation is required to download and use the source
version. Consult Alton Misquitta, a.j.misquitta@qmul.ac.uk, for further
information, and see INSTALL\_SRC.md for installation details.
