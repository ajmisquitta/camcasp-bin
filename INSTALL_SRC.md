## CamCASP installation from source


Additional authorisation is required to download and use the source
version. Consult Alton Misquitta, a.j.misquitta@qmul.ac.uk, for further
information. 

### Libraries:


CamCASP uses BLAS and LAPACK libraries which you will
need to provide. Possibilities are:

1. MKL

   We used to not recommend the MKL libraries as these were known to exhibit
   memory leaks for large systems that were very difficult to trace. However recent
   versions of MKL have been fast and reliable. 

2. OpenBLAS

   An alternative to MKL is the OpenBLAS libraries. These can be obtained from GitHub:
   ```
   git clone https://github.com/xianyi/OpenBLAS.git
   ```
   Building them is fast and easy and we highly recommend these libraries. They are
   hand-coded and optimised for a large number of processors. Best check that your processor
   is supported before using it. Also note that the built libraries are processor
   specific, so they are not portable!

3. ATLAS

   The ATLAS libraries (http://math-atlas.sourceforge.net/) reliable but they need to be
   built from source to have the best performance on your machine. The system ATLAS libraries
   cannot normally be expected to be optimum for all processors.
   Note that you will need to build the entire LAPACK library using instructions provided at
   `http://math-atlas.sourceforge.net/atlas_install/node8.html`

  Here are the contents of the last page:

  Building a full LAPACK library using ATLAS and netlib's LAPACK

  ATLAS natively provides only a relative handful of the routines which comprise LAPACK.
  However, ATLAS is designed so that its routines can easily be added to
  netlib's standard LAPACK in order to get a full LAPACK library.
  If you want your final libraries to have all the LAPACK routines,
  then you just need to pass the -with-netlib-lapack-tarfile flag to configure,
  along with the netlib tarfile that you have previously downloaded.
  For instance, assuming you have previously downloaded the lapack tarfile to 
  `/home/whaley/dload/lapack-3.4.1.tgz`, you would add the following to your configure flags:
  ```
  --with-netlib-lapack-tarfile=/home/whaley/dload/lapack-3.4.1.tgz
  ```
  Configure then auto-builds a make.inc for LAPACK to use,
  and builds netlib LAPACK as part of the ATLAS install process.  
  ATLAS 3.10.0 was tested to work with LAPACK v3.4.1 and 3.3.1.


### Files to edit:

For a normal build you should need to edit only the file <ARCH>/<COMPILER>/exe/Flags
where 

    * ARCH     : osx, x86-64
    * COMPILER : ifort, gfortran, pgf90 (not tested pgf90)

On a Linux machine: ARCH = x86-64  
On Mac OS X: ARCH = osx  
Windows is not supported, but you should be able to get the code to work with
some effort.

We recommend one of the ifort or gfortran compilers. ifort tends to be faster.
For an AMD machine gfortran or AMD's own AOCC variant (https://developer.amd.com/amd-aocc/)
may be more suitable than gfortran but we have not yet tested this compiler suite.

The Flags file sets various compiler options that you may adjust, and it also
allows you to specify the location of the BLAS/LAPACK libraries for each MACHINE
as follows:
```
ifeq ($(MACHINE),comanche)
  FFLAGS := ${FFLAGS}  \
           -xSSE4.2 -arch=SSE4.2 -msse4.2 -funroll-loops -opt-matmul
  FFLAGS2 := ${FFLAGS2}  \
           -xSSE4.2 -arch=SSE4.2 -msse4.2 -funroll-loops -opt-matmul
  LIBS  := -L/home/alston/lib/atlas-3.8.4-gcc4.4.6/lib -llapack -lcblas -lf77blas -latlas \
    -L/usr/lib64/ -lgfortran
endif
```

In this example we have defined the compilation flags relevant for the Intel ifort compiler
in FFLAGS (used for almost all the compilation) and FFLAGS2 (used for special cases).
These will normally be the same.
We have also defined LIBS to point to the ATLAS libraries. As these flags were meant for
the ifort compiler and as ATLAS was compiled using gfortran, we have additionally
specified the location of libgfortran.a

Here MACHINE is an environment variable that is defined in the make process.

Here is an example for the gfortran compiler with OpenBLAS:

```
ifeq ($(MACHINE),pepito)
LIBDIRS := -L/home/alston/install/lib/
LIBS    := -lopenblas \ 
     -L/usr/lib/gcc/x86_64-linux-gnu/7/ -lgfortran   \ 
     -lm -ldl -lgfortran -lquadmath -lpthread
endif
```

For OpenBLAS only `-lopenblas` need be supplied. If the library is not on the system
library path then the path may need to be supplied using LIBDIRS as shown above. 
If OpenBLAS was built with gfortran then you will also need to supply the libraries 
listed above. -lpthread is needed for running threaded versions of the library. 

### Building the code:

Once the flags are defined, you should be able to build the code using:
```
  $ make COMPILER=ifort  name
```
Here we have specified the compiler and the name of the code to be
built. Options for `name` are:
  * camcasp : the main CamCASP code
  * cluster
  * process
  * pfit
  * casimir
  * all : all of the above

A simple top-level build code `makeall` is provided to help with this step. Edit it
as needed and execute to build. 

### Building the interfaces:

The interface programs are located in interfaces/ where we have provided
interfaces to 
  * DALTON
  * NWChem
  * GAMESS(US)

Build them using
  ```
  make interfaces
  ```
in the main CamCASP directory. There is also a Psi4 interface which is a Python script
and doesn't need to be compiled.

NOTE: Debug mode

To compile binaries with compiler-level debug flags switched on you have two options: 
either simply edit the Flags files to include the debugging flags specific to your
compiler and then re-build, or follow these steps to build the debug version in a 
separate directory:
1. First edit the file <ARCH>/<COMPILER>/debug/Flags. Use the instructions given
   above. Additional debug flags are provided in the example Flags files.
2. Build the code using
   ```
   make COMPILER=ifort DEBUG=yes NAME=camcasp
   ```


End Installation from source



## Set up the installation

Next, you will need to run setup.py: with $CAMCASP/bin in your PATH:
```
   setup.py
```
and follow the instructions.

You will need to have at least one of NWChem, DALTON or Psi4 installed. 
The Orient program is needed for some procedures, especially for
localization of polarizabilities.

