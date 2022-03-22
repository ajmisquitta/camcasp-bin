#             CamCASP

##   An electronic structure program for studying intermolecular interactions
 
Alston J. Misquitta,
Anthony J. Stone, and Andreas Hesselmann

with many important modules and contributions from
Robert Bukowski, Wojciech Cencek and others.

CamCASP (Cambridge package for Calculation of Anisotropic Site
Properties) is a collection of scripts and programs written by
Alston Misquitta and Anthony Stone for the calculation ab initio of
distributed multipoles, polarizabilities, dispersion coefficients and
repulsion parameters for individual molecules, and interaction
energies between pairs of molecules using SAPT(DFT). The program is
still being actively developed. In addition to the programs included
in the package, CamCASP uses some other programs: Orient, and an ab
initio program, normally Dalton or NWChem or Psi4. 

* **Older Binary releases** can be obtained at the GitLab site maintained by Prof Anthony Stone at https://gitlab.com/anthonyjs/camcasp
* **The CamCASP Wiki** https://wiki.ph.qmul.ac.uk/ccmmp/AJMPublic/camcasp contains a large number of tutorials.

License [![license](https://img.shields.io/github/license/psi4/psi4.svg)](https://opensource.org/licenses/LGPL-3.0)
=======

CamCASP: an open-source software package for intermolecular interactions, molecular properties, and model building.

Copyright (c) 2004-2022 The CamCASP Developers.

The copyrights for code used from other parties are included in
the corresponding files.

CamCASP is free software; you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, version 3.

CamCASP is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along
with Psi4; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

The full text of the GNU Lesser General Public License (version 3) is included in the
COPYING.LESSER file of this repository, and can also be found
[here](https://www.gnu.org/licenses/lgpl.txt).


Citation [![doi](https://img.shields.io/badge/doi-10.1063/5.0006002-5077AB.svg)](https://pubs.acs.org/doi/abs/10.1021/acs.jctc.5b01241)
========
The main authors of CamCASP are:
* Alston J. Misquitta
* Anthony J. Stone
* Andreas Hesselmann

When using CamCASP please cite the following paper:

Ab Initio Atom–Atom Potentials Using CamCASP: Theory and Application to Many-Body Models for the Pyridine Dimer, Alston J Misquitta, Anthony J Stone, Journal of chemical theory and computation **12**, 4184-4208 (2016).

Installation
============

For a BINARY install see the
[INSTALL_BIN.md](https://gitlab.com/anthonyjs/camcasp/-/wikis/INSTALL_BIN.md)
file for installation instructions.
See the User's Guide in the docs directory for detailed instructions
on using the program.

Directory structure
===================

Some directory information:

 directory | contains
 --- | ---
basis/    | Basis set libraries  
docs/     | Documentation  
bin/      | Scripts and binaries  
examples/ | Examples  
data/     | Data needed by some of the programs.  
methods/  | CamCASP data for various procedures, and template cluster files.  
tests/    | Test scripts. See tests/README for details.  

Version information is in: VERSION

Record of changes is in:   ChangeLog

