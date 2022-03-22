#  Python 3 module for CamCASP
#  -*-  coding:  iso-8859-1  -*-

# provides functions:
# * die
# * newdir
# * findfile
# * replace
# * make_dal
# * make_dalHF
# * make_dalMP2
# * make_dalCC
# * generate
# * monomer
# * dimer_mc
# * dimer_dc
# * dimerAB
# * include
# * include_sp
# * submit
# * read_clt
# * make_dalton_datafiles

# provides classes:
# * Job
# * Mol

import os
import readline
from sys import stderr
import re

class Mol:
    def __init__(self,name):
        self.name = name
        self.ip = 0.0        # stores the IP
        self.homo = 0.0      # stores the HOMO energy
        self.delta_ac = 0.0  # stores the AC shift parameter
        self.ac_variable = False # For DALTON: VARIABLE or FIXEX AC shift.

class Job:
    """
        Full description of a CamCASP job
    """
    def __init__(self, name):
        self.name = name
        #  Molecules in this description
        #  mols[name] is a Mol class object describing the molecule
        #  with that name
        self.mols = {}
        self.mola = None
        self.molb = None
        #  Some default values
        self.runtype = ""
        self.prefix = ""
        self.basis = ""
        self.basistype = ""
        self.auxbasis = ""
        self.auxbasistype = ""
        self.atomauxbasis = ""
        self.atomauxbasistype = ""
        self.isabasis = ""
        self.scfcode = ""
        self.method = "DFT"
        self.func = "PBE0"
        self.kernel = "ALDA+CHF"
        self.daltoncks = False
        self.nomidbond = False
        self.imports = []
        self.ac_type = ""
        self.ac_join = ""
        self.ac_p1 = 0.0
        self.ac_p2 = 0.0
        #
        # Attributes used to define the run-time environment
        #
        self.dir = name    # Directory to run the job in. Default is job name.
        self.logfile = ""  # log file name 
        self.work = ""     # work directory under scratch
        self.debug = False # Debug flag
        self.cltfile = name + ".clt" # Default name of Cluster file
        self.restart = False # Restart flag. 
        self.cores = 0     # Number of cores to use for the SCF codes
        self.cores_camcasp = 0  # Number of cores to use for CamCASP
        self.memory = 0    # Default memory in GB
        self.queue = ""    # Queue to run in  # NO LONGER USED
        self.direct = False # Run the SCF code in DIRECT mode
        self.pause = 0.0   # ??? What's this for???

    def runtime_info(self):
        """
            Print important run-time information about Class Job
        """
        s = f"""
        Class Job({self.name}):
            Job name             :  {self.name}    
            Cluster file         :  {self.cltfile} 
            Directory            :  {self.dir}     
            Work directory       :  {self.work}    
            Memory (GB)          :  {self.memory}  
            Queue                :  {self.queue}   
            Num. cores for SCF   :  {self.cores}   
            Direct integrals SCF :  {self.direct}  
            Num. cores for CamCASP : {self.cores_camcasp} 
            Restart (T/F)        :  {self.restart} 
            Imported files       :  {self.imports}
        """
        print(s)
        return

    def __str__(self):
        """
        Return string for Class Job
        """
        s = ""
        Job_dict = self.__dict__
        for item in Job_dict:
            s += f"{item} : {Job_dict[item]} \n"
        return s


queue=os.environ.get("QUEUE")
scratch=os.environ.get("SCRATCH")
camcasp=os.environ.get("CAMCASP")
basis_dir = camcasp + "/basis/dalton/"

global ghost
ghost = ""

def die(string):
    stderr.write(string + "\n")
    exit(1)

def newdir (d):

    """If a directory with the name given already exists, rename it with
    the first name in the series <d>_001, <d>_002, ..., after any that exist
    already. A new directory with the specified name is then created.
    """

    import glob
    import re

    if os.path.exists(d):
        dirs=glob.glob(d + "_[0-9][0-9][0-9]")
        if len(dirs) > 0:
            dirs.sort()
            dir = dirs[-1]
            print(f"Found  {dir}")
            root = d
            m = re.search(r'_(\d\d\d)$', dir)
            n = int(m.group(1))+1
            dir = f"{root}_{n:03d}"
        else:
            dir = d + "_001"
        try:
            os.rename(d,dir)
        except OSError:
            die(f"Can't rename directory {d} as {dir}")
        else:
            print(f"Existing directory {d} renamed as {dir}")
    os.mkdir(d)
    return d

def findfile(dir,ext,prompt="Enter number for required file"):
    """Find a file in directory dir with extension ext.

    If there is more than one, offer the user a list and wait for a choice.
    """
    import glob

    if not os.path.exists(dir):
        print(f"Can't find directory {dir}")
        return ""
    files = glob.glob(f"{dir}/*{ext}")
    if len(files) == 0:
        print(f"No file {dir}/*{ext} found")
        return None
    elif len(files) == 1:
        return files[0]
    else:
        for i in range(len(files)):
            print(i+1, files[i])
    which = input(prompt+": ")
    return files[int(which)-1]
    
def replace(infile,outfile,dict):
    """Replace constructions <name> or <name!xxx> with the associated value.

    If the dict contains an entry name: value, use that value; otherwise
    use the default value following !, which may be null. Items of the
    form <name> with no value provided are left unchanged.
    """

    import re

    with open(outfile,"w") as OUT, open(infile) as IN:
        for line in IN:
            for name, value in dict.items():
                line = re.sub(r'<{}(!.*?)?>'.format(name), value, line)
            line = re.sub(r'<\w+!(.*?)>', r'\1', line)
            #  Items of the form <name> with no value or default are left
            #  unchanged. Uncomment the next line to replace them with the
            #  null string.
            #  line = re.sub(r'<\w+>', "", line)
            OUT.write(line)

def make_dal (job, suffix, mol, ac_off=False):
    file = job.name + suffix
    scfcode = job.scfcode
    if scfcode == "dalton2006":
        type = job.ac_type
        if type == None or type == "NONE" or ac_off:
            ac = "!"
        elif type == "MULTPOLE":
            if mol.delta_ac == 0.0:
                ac="! "
            else:
                p1 = mol.p1
                if p1 == None or p1 == 0.0: p1 = 3.5
                p2 = mol.p2
                if p2 == None or p2 == 0.0: p2 = 4.7
                ac = f".DFTAC\n{mol.delta_ac:6.4f} {p1:4.2f} {p2:4.2f}"
        else:
            die(f"Asymptotic correction type {type} is incompatible with dalton-2006")
        if job.cks:
            c=""
        else:
            c="! "
        if job.direct:
            d=""
        else:
            d="! "
        with open(file, "w") as A:
            A.write(template["DFT2006"].format(FUNC=func,AC=ac,CKS=c,dir=d))
    else:
        #  Dalton 2013 or later
        type = job.ac_type
        if not type:
            type = "MULTPOLE"
        if type == "NONE" or mol.delta_ac == 0.0 or ac_off:
            ac = "!"
        elif type in ["MULTPOLE","LB94","CS00"]:
            join = job.ac_join
            #  recommended: TANH, 3.0 4.0
            if not join:
                join = "TANH"
            elif join == "TH":
                join = "LINEAR"
            if join == "LINEAR" or join == "TANH":
                p1_def = 3.5; p2_def = 4.7
            elif join == "GRAC":
                p1_def = 0.5; p2_def = 40.0
            else:
                die(f"Unrecognized asymptotic correction connection {join}")
            p1 = job.ac_p1
            if p1 == None or p1 == 0.0 : p1 = p1_def
            p2 = job.ac_p2
            if p2 == None or p2 == 0.0 : p2 = p2_def
            ac = f""".DFTAC\n{type}\n{join}\n"""
            acvar = mol.ac_variable
            if acvar:
                ac += "VARSHIFT\n"
            else:
                ac += "FIXSHIFT\n"
            # print acshift, p1, p2
            ac += f"{mol.delta_ac:8.5f} {mol.delta_ac:8.5f} {p1:4.1f} {p2:4.1f}"
        else:
            die(f"Unrecognized asymptotic correction type {type}")
        direct = job.direct
        if direct:
            d=""
        else:
            d="! "
        with open(file, "w") as A:
            A.write(template["DFT2013"].format(FUNC=job.func,AC=ac,dir=d))

def make_dalHF (file, direct):
    with open(file, "w") as A:
        if direct:
            d=""
        else:
            d="! "
        A.write(template["HF"].format(dir=d))

def make_dalMP2(file, direct):
    with open(file, "w") as A:
        if direct:
            d=""
        else:
            d="! "
        A.write(template["MP2"].format(dir=d))

def make_dalCC (file, direct):
    with open(file, "w") as A:
        if direct:
            d=""
        else:
            d="! "
        A.write(template["CC"].format(dir=d))

def generate(jobname, runtype="properties", basistype="", nomb=False,
             mono=False):
    """  Generate .mol files for a CamCASP job.

    Translates a template file generated by cluster into a Dalton .mol file.
    runtype may be properties, saptdft, delta-HF or supermol.
    basistype may be mc, mc+, dc, dc+ or mono
    nomb=True means that no mid-bond functions are to be used.
    The last two are irrelevant for a properties calculation.
    """

    ABbasis=False

    #  Set the mb
    if nomb or basistype == "mc" or basistype == "dc":
        use_midbond = False
    elif basistype == "mc+" or basistype == "dc+":
        use_midbond = True
    else:
        use_midbond = False

    #  Now for some special cases:
    if runtype == "deltahf":
    #  Only dc or dc+ basis types are allowed:
        if basistype == "dc" or basistype == "dc+":
            #  We also need the dimer AB
            ABbasis = True
        else:
            print(f"ERROR: Inappropriate basis type {basistype}")
            die("Use only DC or DC+ basis types for a Delta-HF calculation.")

    elif runtype == "supermol":
        #  Also need the dimer AB
        ABbasis = True

    basistype=str.lower(basistype)
    # print(f"Basis type = {basistype}")
    if basistype == "mono":
        pass
    elif use_midbond and (basistype == "mc+" or basistype == "dc+"):
        print("Mid-bond basis functions will be used\n")
    else:
        print("Mid-bond basis functions will not be used\n")

    with open(f"{jobname}.DALtemplate") as IN:
        lines=IN.readlines()
        # print(lines)

    if basistype == "mono":
        # print("calling monomer")
        monomer(jobname, lines)
    elif basistype == "dc" or basistype == "dc+":
        dimer_dc(jobname, lines, basistype, use_midbond)
    elif basistype == "mc" or basistype == "mc+":
        dimer_mc(jobname, lines, basistype, use_midbond)

    if ABbasis:
        dimerAB(jobname, lines, basistype, use_midbond)

    return


def monomer(jobname,lines):

    """Monomer run. Create only one file, for molecule A."""

    import re

    # print("Entering monomer")
    with open(f"{jobname}_A.mol", "w") as OUT:
        # print(f"{jobname}_A.mol opened")
        molA=True
        molB=True
        for line in lines[:]:
            # print(line)
            if re.match(r'#molecule A', line):
                molA=True
                molB=False
            elif re.match(r'#molecule B', line):
                molA=False
                molB=True
            elif re.match(r'#midbond', line):
                molA=False
                molB=False
            elif re.match(r'#include', line) and molA:
                m = re.match(r'#include +(.+)$', line)
                include(m.group(1),OUT,False)
            elif molA:
                OUT.write(line)

def dimer_mc(jobname, lines, basistype, use_midbond):

    """Calculation using the monomer basis (mc or mc+).

    Molecule A: include basis functions for molecule A. For mc+, also
    include farbond (s & p) functions for molecule B, and midbond
    functions if specified.
    Molecule B: include basis functions for molecule B. For mc+, also
    include farbond (s & p) functions for molecule A, and midbond
    functions if specified.
    """

    import re

    global ghost
    ghost = ""
    with open(f"{jobname}_A.mol","w")as OUT:
        molA = True
        molB = True
        mb = True
        for line in lines[:]:
            if re.search(r'Atomtypes=', line):
                m=re.search(r'Atomtypes=\s+(\d+)\s+\+\s+(\d+)', line)
                if basistype == "mc+":
                    n=int(m.group(1))+int(m.group(2))
                    if use_midbond:
                        n=n+1
                else:
                    n=int(m.group(1))
                line=re.sub(r'Atomtypes=\s+(\d+)\s+\+\s+(\d+)', "Atomtypes=" + str(n), line)
                line=re.sub(r'Charge=\s+(-?\d+)\s+\+\s+(-?\d+)', r'Charge=\1', line)
                OUT.write(line)

            elif re.match(r'#molecule A', line):
                molA = True
                molB = False
                mb = False
            elif re.match(r'#molecule B', line):
                if basistype == "mc+":
                    molA = False
                    molB = True
                    mb = False
                else:
                    molA = False
                    molB = False
                    mb = False
            elif re.match(r'#midbond', line):
                if basistype == "mc+":
                    molA = False
                    molB = False
                    mb=use_midbond
                else:
                    molA = False
                    molB = False
                    mb = False
            elif re.match(r'#include', line):
                m=re.match(r'#include +(.+)$', line)
                bfn=m.group(1)
                if molA:
                    include(bfn,OUT,False)
                if basistype == "mc+":
                    if mb:
                        include(bfn,OUT,True)
                    if molB:
                        include_sp(bfn)
            elif re.match(r'Charge', line):
                m=re.match(r'Charge=\s*(\d+\.\d+)', line)
                # If the charge is 1.0 it is a hydrogen.
                # itis_h = (m.group(1) == "1.0")
                if m.group(1) == "1.0":
                    itis_h=True
                else:
                    itis_h=False
                if molA:
                    OUT.write(line)
                if mb:
                    line = re.sub(r'=\s+\d+\.', '=0.', line)
                    ghost += line
                if molB:
                    if itis_h:
                        line="Charge=0.0 Atoms=1 Blocks=1 1 \n"
                    else:
                        line="Charge=0.0 Atoms=1 Blocks=2 1 1 \n"
                    ghost += line
            else:
                if molA:
                    OUT.write(line)
                elif mb or molB:
                    ghost += line
        OUT.write(ghost)

    #  Molecule B
    ghost = ""
    with open(f"{jobname}_B.mol","w") as OUT:
        molA = True
        molB = True
        mb = True
        for line in lines[:]:
            if re.search(r'Atomtypes=', line):
                m=re.search(r'Atomtypes=\s+(\d+)\s+\+\s+(\d+)', line)
                if basistype == "mc+":
                    n=int(m.group(1))+int(m.group(2))
                    if use_midbond:
                        n=n+1
                else:
                    n=int(m.group(2))
                line=re.sub(r'Atomtypes=\s+(\d+)\s+\+\s+(\d+)', "Atomtypes=" + str(n), line)
                line=re.sub(r'Charge=\s*(-?\d+)\s+\+\s+(-?\d+)', r'Charge=\2', line)
                OUT.write(line)
            elif re.match(r'#molecule A', line):
                if basistype == "mc+":
                    molA = True
                    molB = False
                    mb = False
                else:
                    molA = False
                    molB = False
                    mb = False
            elif re.match(r'#molecule B', line):
                molA = False
                molB = True
                mb = False
            elif re.match(r'#midbond', line):
                if basistype == "mc+":
                    molA = False
                    molB = False
                    mb=use_midbond
                else:
                    molA = False
                    molB = False
                    mb = False
            elif re.match(r'#include', line):
                m=re.match(r'#include +(.+)$', line)
                bfn=m.group(1)
                if molB:
                    include(bfn,OUT,False)
                if basistype == "mc+":
                    if mb:
                        include(bfn,OUT,True)
                    if molA:
                        include_sp(bfn)
            elif re.match(r'Charge', line):
                m=re.match(r'Charge=\s*(\d+\.\d+)', line)
                # If the charge is 1.0 it is a hydrogen.
                itis_h = (m.group(1) == "1.0")
                if molA:
                    if itis_h:
                        line="Charge= 0.0 Atoms=1 Blocks=1 1 \n"
                    else:
                        line="Charge= 0.0 Atoms=1 Blocks=2 1 1 \n"
                    ghost += line
                if mb:
                    line = re.sub(r'=\s+\d+\.', '=0.', line)
                    ghost += line
                if molB:
                    OUT.write(line)
            else:
                if molB:
                    OUT.write(line)
                elif molA or mb:
                    ghost += line
        OUT.write(ghost)


def dimer_dc (jobname, lines, basistype, use_midbond):

    """Dimer basis calculation (dc or dc+).
    Molecule A: include all basis functions, with ghost nuclei for
    molecule B, and for the midbond functions if specified.
    Likewise for molecule B.
    """

    import re

    global ghost
    ghost = ""
    with open(f"{jobname}_A.mol","w") as OUT:
        molA = True
        molB = True
        mb = True
        for line in lines[:]:
            if re.search(r'Atomtypes=', line):
                m=re.search(r'Atomtypes=\s+(\d+)\s+\+\s+(\d+)', line)
                n=int(m.group(1))+int(m.group(2))
                if basistype == "dc+" and use_midbond:
                    n=n+1
                line=re.sub(r'Atomtypes=\s+(\d+)\s+\+\s+(\d+)', "Atomtypes=" + str(n), line)
                line=re.sub(r'Charge=\s*(-?\d+)\s+\+\s+(-?\d+)', r'Charge=\1', line)
                OUT.write(line)
            elif re.match(r'#molecule A', line):
                molA = True
                molB = False
                mb = False
            elif re.match(r'#molecule B', line):
                molA = False
                molB = True
                mb = False
            elif re.match(r'#midbond', line):
                if basistype == "dc":
                    molA = False
                    molB = False
                    mb = False
                else:
                    molA = False
                    molB = False
                    mb = use_midbond
            elif re.match(r'#include', line):
                m=re.match(r'#include +(.+)$', line)
                bfn=m.group(1)
                if molA:
                    include(bfn,OUT,False)
                elif molB or mb:
                    include(bfn,OUT,True)
            elif re.match(r'Charge', line):
                if molA:
                    OUT.write(line)
                elif molB or mb:
                    line = re.sub(r'=\s*\d+\.', '=  0.', line)
                    ghost += line
            else:
                if molA:
                    OUT.write(line)
                elif mb or molB:
                    ghost += line
        OUT.write(ghost)

    #  Molecule B: include all basis functions, with ghost nuclei for
    #      molecule A, and for the midbond functions if specified.
    ghost = ""
    with open(f"{jobname}_B.mol", "w") as OUT:
        molA = True
        molB = True
        mb = True
        for line in lines[:]:
            if re.search(r'Atomtypes', line):
                m=re.search(r'Atomtypes=\s+(\d+)\s+\+\s+(\d+)', line)
                n=int(m.group(1))+int(m.group(2))
                if basistype == "dc+" and use_midbond:
                    n=n+1
                line=re.sub(r'Atomtypes=\s+(\d+)\s+\+\s+(\d+)', 'Atomtypes=' + str(n), line)
                line=re.sub(r'Charge=\s*(-?\d+)\s+\+\s+(-?\d+)', r'Charge=\2', line)
                OUT.write(line)
            elif re.match('#molecule A', line):
                molA = True
                molB = False
                mb = False
            elif re.match(r'#molecule B', line):
                molA = False
                molB = True
                mb = False
            elif re.match(r'#midbond', line):
                if basistype == "dc+":
                    molA = False
                    molB = False
                    mb=use_midbond
                else:
                    molA = False
                    molB = False
                    mb = False
            elif re.match(r'#include', line):
                m=re.match(r'#include +(.+)$', line)
                bfn=m.group(1)
                if molB:
                    include(bfn,OUT,False) 
                elif molA or mb:
                    include(bfn,OUT,True) 
            elif re.match(r'Charge', line):
                if molA or mb:
                    line = re.sub(r'=\s+\d+\.', '=0.', line)
                    ghost += line
                elif molB:
                    OUT.write(line)
            else:
                if molB:
                    OUT.write(line)
                elif molA or mb:
                    ghost += line
        OUT.write(ghost)


def dimerAB(jobname, lines, basistype, use_midbond):

    """Set up the data file for dimer AB.

    Needed only for supermolecular and Delta-HF calculations.
    """

    import re

    # print("Entering dimerAB")
    with open(f"{jobname}_AB.mol", "w") as OUT:
        molA = True
        molB = True
        mb = False
        for line in lines[:]:
            # print(line, end="")
            if re.search(r'Atomtypes', line):
                m=re.search(r'Atomtypes=\s+(\d+)\s+\+\s+(\d+)', line)
                n=int(m.group(1))+int(m.group(2))
                if use_midbond:
                    n=n+1
                line = re.sub(r'Atomtypes=\s+(\d+)\s+\+\s+(\d+)', 'Atomtypes=' + str(n), line)
                # Set dimer charge to the sum of the monomer charges
                m = re.search(r'Charge=\s*(-?\d+)\s+\+\s+(-?\d+)', line)
                if m:
                    Qtot = int(m.group(1))+int(m.group(2))
                else:
                    Qtot = 0
                line = re.sub(r'Charge=\s+(-?\d+)\s+\+\s+(-?\d+)', 'Charge=' + str(Qtot), line)
                OUT.write(line)
            elif re.match(r'#molecule A', line):
                molA = True
                molB = False
                mb = False
            elif re.match(r'#molecule B', line):
                molA = False
                molB = True
                mb = False
            elif re.match(r'#midbond', line):
                if basistype == "dc":
                    molA = False
                    molB = False
                    mb = False
                else:
                    molA = False
                    molB = False
                    mb=use_midbond
            elif re.match(r'#include', line):
                m=re.match(r'#include +(.+)$', line)
                if molA or molB or mb:
                    include(m.group(1),OUT,False)
            elif re.match(r'Charge', line):
                if mb:
                    line = re.sub(r'=\s+\d+\.', '=0.', line)
                if molA or molB or mb:
                    OUT.write(line)
            elif molA or mb or molB:
                OUT.write(line)



def include(name,F,gh):
    """Copy basis "name" to output stream F or to the ghost atom defn."""
    global ghost
    with open(basis_dir + name) as BASIS: 
        if gh:
            ghost = ghost + BASIS.read()
        else:
            F.write(BASIS.read())


def include_sp(name):
    """Copy basis "name" to ghost lines, including only s and p
    functions."""
    global ghost
    with open(basis_dir + "sp/" + name) as BASIS: 
        ghost = ghost + BASIS.read()


              
#-----------------------------------------------------------------------

#  Templates for Dalton .dal files
template = {}

template["DFT2006"]="""**DALTON INPUT
.RUN WAVE FUNCTION
{dir}.DIRECT
**INTEGRALS
.NOSUP
.PRINT
    1
**WAVE FUNCTIONS
.DFT
{FUNC}
.INTERFACE
*AUXILIARY INPUT
.NOSUPMAT
*ORBITALS
.NOSUPSYM
.AO DELETE
    1.0E-6
.CMOMAX
    1000.0
*DFT INPUT
{CKS}.CKS
.DFTELS
0.01
{AC}
.RADINT
1.0E-13
.ANGINT
35
*SCF INPUT
.THRESH
1.0D-6
*ORBITAL INPUT
*END OF INPUT
"""

# 2021: Removed the .NOSUPSYM commands from the *ORBITALS block as it is no longer
#  supported.
template["DFT2013"] = """**DALTON INPUT
.RUN WAVE FUNCTION
{dir}.DIRECT
**INTEGRALS
.NOSUP
.PRINT
    1
**WAVE FUNCTIONS
.DFT
{FUNC}
.INTERFACE
*AUXILIARY INPUT
.NOSUPMAT
*ORBITALS
.AO DELETE
    1.0E-6
.CMOMAX
    1000.0
*DFT INPUT
! .CKS
.DFTELS
0.01
{AC}
.RADINT
1.0E-13
.ANGINT
35
*SCF INPUT
.THRESH
1.0D-6
*ORBITAL INPUT
*END OF INPUT
"""

template["HF"] = """**DALTON INPUT
.RUN WAVE FUNCTION
{dir}.DIRECT
**INTEGRALS
.NOSUP
.PRINT
    1
**WAVE FUNCTIONS
.HF
.INTERFACE
*AUXILIARY INPUT
.NOSUPMAT
.NOSUPSYM
.AO DELETE
    1.0E-6
.CMOMAX
    1000.0
*SCF INPUT
.THRESH
1.0D-6
*ORBITAL INPUT
*END OF INPUT
"""

template["MP2"] = """**DALTON INPUT
.RUN WAVE FUNCTION
{dir}.DIRECT
**INTEGRALS
.NOSUP
.PRINT
    1
**WAVE FUNCTIONS
.HF
.MP2
.INTERFACE
*AUXILIARY INPUT
.NOSUPMAT
*ORBITALS
*SCF INPUT
.THRESH
1.0D-6
*ORBITAL INPUT
*END OF INPUT
"""

template["CC"] = """**DALTON INPUT
.RUN WAVE FUNCTION
{dir}.DIRECT
**INTEGRALS
.NOSUP
.PRINT
    1
**WAVE FUNCTIONS
.CC
*CC INPUT
.CC(T)
*SCF INPUT
.THRESH
1.0D-6
*ORBITAL INPUT
*END OF INPUT
"""


def read_clt(job,verbosity):
    """Extract job and molecule information from the cluster file"""

    #  Defaults
    job.runtype = ""
    job.prefix = ""
    job.method = "DFT"
    job.func = "PBE0"
    job.basis = ""
    job.basistype = ""
    job.auxbasis = ""
    job.auxbasistype = ""
    job.atomauxbasis = ""
    job.atomauxbasistype = ""
    job.isabasis = ""
    job.count = 0
    job.kernel = "ALDA+CHF"
    job.daltoncks = False
    job.nomidbond = False


    with open(job.cltfile) as CLT:
        #  Look for molecule definitions
        #mols = {}
        count = 0
        for line in CLT:
            # print(line, end="")
            #  Skip comment
            if re.match(r' *!', line):
                continue
 
            # Molecules are normally defined using the
            # MOLECULE <name>
            #   ...
            # END
            # block.
            m = re.match(r' *(MOLECULE|ATOM)\s+([\w-]+)', line, flags=re.I)
            if m:
                #  Molecule definition starts
                name = m.group(2)
                mol = Mol(name)
                job.mols[name] = mol
                continue
            m = re.match(r' *I\.?P\.? +(\d*(\.\d+)?) *((ev)?)', line, flags=re.I)
            if m:
                #  Ionization potential, in a.u. unless eV specified
                mol.ip = float(m.group(1))
                unit = m.group(3)
                if re.match(r'ev',unit,flags=re.I):
                    mol.ip = mol.ip/27.21136
                if verbosity > 0: print(f"{name}, IP = {mol.ip:6.4f}")
                continue
            m = re.match(r' *HOMO +(energy +)?(-?\d*(\.\d+)?) *((ev)?)', line, flags=re.I)
            if m:
                #  HOMO energy, in a.u.
                mol.homo = float(m.group(2))
                if m.group(4):
                    unit = m.group(4)
                    if re.match(r'ev',unit,flags=re.I):
                        mol.homo = mol.homo/27.21136
                if verbosity > 0: print(f"{name}, HOMO energy = {mol.homo:6.4f}")
                continue
            m = re.match(r' *AC-SHIFT +(\d*(\.\d+)?) *((ev)?)',line,flags=re.I)
            if m:
                #  AC-SHIFT: AC shift in a.u.
                mol.delta_ac = float(m.group(1))
                unit = m.group(3)
                if re.match(r'ev',unit,flags=re.I):
                    mol.delta_ac = mol.delta_ac/27.21136
                if verbosity > 0: print(f"{name}, AC-SHIFT = {mol.delta_ac:6.4f}")
                continue
      
            # But they can also be defined from pre-defined molecules using
            # the JOIN command which takes the form:
            # JOIN <list of molecules> INTO <NEW MOLECULE name>
            # In this case we cannot (yet) assign an IP to the molecule.
            m = re.match(r' *(JOIN)\s+([\w,\s]+)\s+(INTO)\s+([\w,-]+)',line,flags=re.I)
            if m:
                print("group 4 ",m.group(4))
                name = m.group(4)
                mol = Mol(name)
                job.mols[name] = mol
                continue

            m = re.match(r' *(RUN-?(TYPE|DESC|DESCRIPTION)?|JOB|FILES)(.*)$',line,flags=re.I)
            if m:
                if m.group(3):
                    job.runtype = m.group(3).strip().lower()
                #  Exit from molecule definition loop
                break

        #  Look for calculation details
        #  Count of molecules used in calculation
        mol_count = 0
        for line in CLT:
            # print(line, end="")
            #  Skip comment
            if re.match(r' *!', line):
                continue
            if re.match(r'FINISH\s*$', line, flags=re.I):
                break
      
            #  Molecules in calculation
            m = re.match(r'^ *(MOLECULES?|MOLS?|ATOMS?)\s+(\S+)\s*', line, flags=re.I)
            if m:
                s = m.group(2)
                if s not in list(job.mols.keys()):
                    die(f"Molecule {s} has not been defined")
                job.mola = job.mols[s]
                mol_count += 1
                line = re.sub(m.group(0), "", line, flags=re.I)
                # 
                m = re.match(r'((and\s+)?)(\S+)', line, flags=re.I)
                if m:
                    s = m.group(3)
                    if s not in list(job.mols.keys()):
                        die(f"Molecule {s} has not been defined")
                    job.molb = job.mols[s]
                    mol_count += 1
                    # print mola.name, molb.name
                else:
                    job.molb = None
                continue
    
            #  Runtype
            m = re.match(r' *((PSI4-)?SAPT(-?DFT|\(DFT\))|DFT-?SAPT|D(ELTA)?.?HF|SAPT|'\
                   'SUPERMOL(ECULE)?|PROPERT(Y|IES)|CAMCASP) *$',line,flags=re.I)
            if m:
                job.runtype = m.group(1).lower()
                continue
  
            # SCF code
            m = re.match(r'\s*SCF(-)?CODE +(\w+[- ]?(\d+)?)( +(direct))?',line,flags=re.I)
            #  Ignore if already set on the command line
            if m and not job.scfcode:
                job.scfcode = str.lower(m.group(2))
                if re.match(r'dalton[-]?2006', job.scfcode):
                    job.scfcode = "dalton2006"
                elif re.match(r'dalton([-]?201[356])?', job.scfcode):
                    job.scfcode = "dalton"
                elif re.match(r'psi4', job.scfcode):
                    job.scfcode = "psi4"
                elif re.match(r'nwchem', job.scfcode):
                    job.scfcode = "nwchem"
                elif re.match(r'molpro', job.scfcode):
                    scfcode = "molpro"                     
                # print(f"scfcode = {job.scfcode}")
                if m.group(5):
                    if m.group(5).lower() == "direct":
                        job.direct = True
                continue

            #  Basis and type
            m = re.match(r'\s*((MAIN-|AUX-|ATOMAUX-|ISA-)?)BASIS\s+([\w-]+)',line,flags=re.I)
            if m:
                word = m.group(1).upper()
                basis = m.group(3).lower()
                m = re.search(r'TYPE\s+([md]c\+?|mono)',line,flags=re.I)
                if m:
                    xc = m.group(1).lower()
                else:
                    xc = None
                if word in ["MAIN-", ""]:
                    job.basis = basis_map[basis]
                    job.basistype = xc
                    if job.auxbasis == "": job.auxbasis = job.basis
                    if job.auxbasistype == "": job.auxbasis = job.basis
                    if verbosity > 0: print(f"main basis = {job.basis}, type = {job.basistype}")
                elif word == "AUX-":
                    job.auxbasis = basis
                    job.auxbasistype = xc
                    if verbosity > 0: print(f"aux basis = {job.auxbasis}, type = {job.auxbasistype}")
                elif word == "ATOMAUX-":
                    job.atomauxbasis = basis
                    job.atomauxbasistype = xc
                    if verbosity > 0: print(f"atomaux basis = {job.atomauxbasis}, type = {job.atomauxbasistype}")
                elif word == "ISA-":
                    job.isabasis = basis
                    if verbosity > 0: print(f"isa basis = {job.isabasis}")
                else:
                    print(f"Basis keyword {word}BASIS not recognised")
                    exit(1)
                if verbosity > 0: print(f"basis = {job.basis}  type = {job.basistype}")
                continue

            #  Other basis specification lines ignored here -- handled by cluster

            m = re.match(r'\s*MIDBOND\s+([\w]+)',line,flags=re.I)
            if m:
                if str.upper(m.group(1)) == "NONE":
                    nomidbond = True
                #  Otherwise handled by cluster
                continue
  
            #  Method
            m = re.search(r'METHOD +(\w+)',line,flags=re.I)
            if m:
                job.method = m.group(1)
                if verbosity > 0: print(f"Method = {job.method}")
                continue
   
            #  Functional
            m = re.search(r'FUNC(TIONAL)? +(\w+)',line,flags=re.I)
            if m:
                job.func = m.group(2)
                if verbosity > 0: print(f"Functional = {job.func}")
                continue
  
            #  Data for asymptotic correction. These entries may be repeated if
            #  required for more than one molecule. Only needed for constructed
            #  molecules (JOIN command), since these properties are normally
            #  specified in the molecule definition.
            #  {HOMO|IP|I\.P\.|AC-SHIFT} mol value [eV]
            #  An I.P may be given in eV; otherwise values must be in a.u.
            m = re.match(r'\s*(homo|ip|i\.p\.|ac-shift) +(\S+) +(-?\d+\.\d+) *((ev)?)', line, flags=re.I)
            if m:
                key = m.group(1).lower
                name = m.group(2)
                value = float(m.group(3))
                if name in list(job.mols.keys()):
                    mol = job.mols[name]
                else:
                    mol = Mol(name)
                    job.mols[name] = mol
                ix = molnames.index(name)
                if key == "homo":
                    mol.homo = value
                elif key == "ip" or key == "i.p.":
                    mol.ip = value
                    if re.match(r'ev', m.group(4),flags=re.I):
                        mol.ip /= 27.21136
                elif key == "ac-shift":
                    mol.delta_ac = value
                continue
    
            #  Asymptotic correction
            #  {AC|ASYMP[TOTIC][ CORR[ECTION]]}  [type] [join [p1 p2]] 
            #  where type = CS00, LB94, MULTPOLE, NONE or OFF
            #  join = TH (i.e. Tozer-Handy), T-H, LINEAR or TANH or GRAC
            m = re.match(r'^\s*(ac\s+|(asymp\w*(-| +)(corr\w* +)?))', line, flags=re.I)
            if m:
                job.ac_type = "LB94"
                job.ac_join = "TANH"
                # Remove AC or ASYMPTOTIC-CORRECTION from the start of the line.
                line = re.sub(r'^\s*(ac\s+|(asymp\w*(-| +)(corr\w* +)?)) *', "", line, flags = re.I)
                while True:
                    # print(f"1 AC line: {line}", end="")
                    m = re.match(r'\s*(\w+) *', line, flags = re.I)
                    if m:
                        key = m.group(1).upper()
                        # print( "key =", key)
                        line = re.sub(r'^\s*(\w+) *', "", line, count=1)
                        # print line,
                        if key in ["CS00","LB94","MULTPOLE","MULTIPOLE"]:
                            if key == "MULTIPOLE":
                                job.ac_type = "MULTPOLE"
                            else:
                                job.ac_type = key
                            # print("ac_type = ", job.ac_type)
                        elif key in ["NONE","NO","OFF"]:
                            job.ac_type = "NONE"
                        elif key in ["TH","T-H","LINEAR","TANH","GRAC"]:
                            job.ac_join = key
                            # print("ac_join = ", job.ac_join)
                            mm = re.match(r'(\d+\.\d*) +(\d+\.\d*)', line)
                            if mm:
                                job.ac_p1 = float(mm.group(1))
                                job.ac_p2 = float(mm.group(2))
                                line = re.sub(r'(^\d+\.\d*) +(\d+\.\d*) *', "", line)
                                # print("2 AC line: ", line, end="")
                    else:
                        break
                # print(f"AC settings: type = {job.ac_type}, join = {job.ac_join}, "
                #      f"p1 = {job.ac_p1:5.2f}, p2 = {job.ac_p2:5.2f}")
  
                continue
  
            #  Kernel
            #  KERNEL (ALDA(X)?)(+CHF)?([-, ]DALTON) 
            m = re.match(r' *KERNEL\s+(.*)',line,flags=re.I)
            if m:
                m = re.search(r'(ALDA(X?))?(\+\w+)? *$', line, flags=re.I)
                if m:
                    job.kernel = m.group(0)
                    if verbosity > 0: print(f"kernel = {job.kernel}")
                    #  ALDA kernel no longer requires CKS integrals from Dalton
                    # if not re.match(r'^ALDAX',kernel,flags=re.I):
                    if re.search('DALTON',line,flags=re.I):
                        job.daltoncks=True
                    else:
                        job.daltoncks=False
                    if verbosity > 0: print(f"DALTON CKS: {job.daltoncks}")
                    continue
                else:
                    print(line, end=' ')
                    die("Unrecognised entry in KERNEL line. Options: (ALDA(X)?)(+CHF)([-, ]DALTON)")
                continue
  
            #  File prefix (job name): Allow '-' and '.' in the prefix. This is useful
            #  for names like NH3-OH-R6.0. It must match the job name and need not be
            #  specified here.
            m = re.match(r'\s*(FILE-?)?PREFIX\s+([\w.-]+)',line,flags=re.I)
            if m:
                prefix = m.group(2)
                if prefix != job.name:
                    print(line, end=' ')
                    die("The file prefix, if specified, must be the same as the job name")
                continue
  
            #  Files to import
            m = re.match(r'\s*IMPORT', line, flags=re.I)
            if m:
                job.imports.extend(line.split()[1:])

    #  End of cluster file scan


    #  Some sanity checks
  
    #  Properties calculation if only one molecule specified
    if job.runtype == "":
        if mol_count == 1:
            job.runtype = "properties"
        elif mol_count == 2:
            job.runtype = "saptdft"
        if verbosity > 0:
            print(f"Run-type {job.runtype} assumed")
    if mol_count == 1 and job.runtype != "properties":
        print(f"{job.runtype} calculation was specified but only one molecule")
        die("Job abandoned")
    elif mol_count == 0:
        print("No molecules specified for calculation (MOLECULES A [and B] line omitted)")
        die("Job abandoned")

    #  Basis type defaults to mono for properties, otherwise undefined.
    # print(job.basistype)
    if job.basistype == "":
        if re.match(r'propert(y|ies)',job.runtype,flags=re.I):
            job.basistype = "mono"
        else:
            die("Basis set type not specified")
  
  
    #  Apply default asymptotic correction if necessary
    # print(f"ac_type = {job.ac_type}, SCF code = {job.scfcode}")
    if job.ac_type == "":
        if job.scfcode == "nwchem":
            job.ac_type = "CS00"
        elif job.scfcode == "psi4":
            job.ac_type = "GRAC"
        elif job.scfcode == "molpro":
            job.ac_type = "GRAC"            
        else:
            job.ac_type = "LB94"
            if not job.ac_join: job.ac_join = "TANH"  
    #  Set AC shift and fixed/variable 
    # print(f"ac_type = {job.ac_type}, SCF code = {job.scfcode}")
    if job.ac_type != "NONE":
        for mol in [job.mola,job.molb]:
            if mol:
                # Decide on the AC-shift (mol.delta_ac) and type of shift: Variable or fixed.
                # mol.ac_variable is used only for DALTON command files. 
                if mol.delta_ac:
                    mol.ac_variable = False
                elif mol.ip and mol.homo:
                    mol.delta_ac = mol.ip + mol.homo
                    mol.ac_variable = False
                elif mol.ip:
                    if job.ac_type == "CS00":
                        mol.delta_ac == 0.0
                    else:
                        mol.delta_ac = mol.ip
                        mol.ac_variable = True
                elif job.ac_type == "CS00":
                    mol.delta_ac == 0.0
                else:
                    job.ac_type = "NONE"
                # print( mol.name, mol.ip, mol.homo, mol.delta_ac)

    #  Standardize run-type
    if re.match(r'(saptdft|sapt(-dft|\(dft\))|dft-?sapt)', job.runtype):
        job.runtype = "saptdft"
    elif re.match(r'sapt', job.runtype):
        job.runtype = "sapt"
    elif re.match(r'(d(elta)?.?hf)', job.runtype):
        job.runtype = "deltahf"
    elif re.match(r'propert(y|ies)', job.runtype):
        job.runtype = "properties"
    elif re.match(r'supermol(ecule)?', job.runtype):
        job.runtype = "supermol"
    elif re.match(r'camcasp', job.runtype):
        job.runtype = "camcasp"
    elif re.match(r'psi4-sapt(\(dft\)|-dft)', job.runtype):
        job.runtype = "psi4-saptdft"
    else:
        die(f"Run-type '{job.runtype}' not understood")

    #  Default SCF code if not set yet
    if not job.scfcode:
        if os.environ.get("CAMCASP_SCFCODE"):
            job.scfcode = os.environ.get("CAMCASP_SCFCODE").lower()
        else:
            job.scfcode = "psi4"

    if job.scfcode not in ["dalton2006", "dalton", "nwchem", "psi4", "molpro"]:
        print(f"Error: unrecognised SCF code: {job.scfcode}")
        die("Available programs are Dalton2006, Dalton (i.e. Dalton2013 or later), NWChem, Psi4 and Molpro")
    if verbosity > 0:
        print(f"""basis = {job.basis}
basis type = {job.basistype}
runtype = {job.runtype}
scfcode = {job.scfcode}
""")
        print(f"AC options: type = {job.ac_type}, join = {job.ac_join},",
          f"p1 = {job.ac_p1:3.1f}, p2 = {job.ac_p2:3.1f}")
        if job.ac_type != "NONE":
            print("AC shifts: ")
            for mol in [job.mola,job.molb]:
                if mol:
                    print(f"{mol.name}: shift = {mol.delta_ac:7.4f} ", end=' ')
                    if mol.ac_variable:
                        print("  variable")
                    else:
                        print("  fixed")


    #  End of read_clt

def make_dalton_datafiles(job,verbosity):
    """ Set up data files for a Dalton job"""
    #  job.scfcode may be dalton or dalton2006
    mola = job.mola
    molb = job.molb
    
    if job.runtype == "saptdft":
        #  SAPT(DFT)
        generate(job.name, runtype="saptdft", basistype=job.basistype, nomb=job.nomidbond)
        if job.method == "HF":
            make_dalHF(f"{job.name}_A.dal", job.direct)
            make_dalHF(f"{job.name}_B.dal", job.direct)
        else:
            make_dal(job, "_A.dal", mola)
            make_dal(job, "_B.dal", molb)

    elif job.runtype == "deltahf":
        generate(job.name, runtype="deltahf", basistype=job.basistype, nomb=job.nomidbond)
        make_dalHF(f"{job.name}_AB.dal", job.direct)
        make_dalHF(f"{job.name}_A.dal", job.direct)
        make_dalHF(f"{job.name}_B.dal", job.direct)

    elif job.runtype == "sapt":
        generate(job.name, runtype="sapt", basistype=job.basistype, nomb=job.nomidbond)
        make_dalHF(f"{job.name}_A.dal", job.direct)
        make_dalHF(f"{job.name}_B.dal", job.direct)
    
    elif job.runtype == "properties":
        generate(job.name, runtype="properties", basistype="mono")
        if job.method == "HF":
            make_dalHF(f"{job.name}_A.dal", job.direct)
        else:
            make_dal(job, "_A.dal", mola)
      
    elif job.runtype == "supermol":
        generate(job.name, runtype="supermol", basistype=job.basistype, nomb=job.nomidbond)
        if job.method == "HF":
            make_dalHF(f"{job.name}_A.dal", job.direct)
            make_dalHF(f"{job.name}_B.dal", job.direct)
            make_dalHF(f"{job.name}_AB.dal", job.direct)
        elif job.method == "MP2":
            make_dalMP2(f"{job.name}_A.dal", job.direct)
            make_dalMP2(f"{job.name}_B.dal", job.direct)
            make_dalMP2(f"{job.name}_AB.dal", job.direct)
        elif job.method == "CC":
            make_dalCC(f"{job.name}_A.dal", job.direct)
            make_dalCC(f"{job.name}_B.dal", job.direct)
            make_dalCC(f"{job.name}_AB.dal", job.direct)
        elif job.method == "DFT":
            # Here we do not use the AC so ac_off is set
            # and the mol class data is irrelevant
            make_dal(job, "_A.dal", mola, ac_off=True)
            make_dal(job, "_B.dal", molb, ac_off=True)
            make_dal(job, "_AB.dal", mola, ac_off=True)

    #  End of make_dalton_datafiles

def make_psi4_datafile(job, verbosity):
    mola = job.mola
    molb = job.molb
    with open(f"{job.name}.psi4") as IN, open(f"{job.name}_AB.in","w") as OUT:
        if verbosity > 0:
            print(f"AC shifts: {mola.delta_ac:7.4f}, {molb.delta_ac:7.4f}")
            print(f"Basis {job.basis}, Aux basis {job.auxbasis},",
                  f"Atomaux basis {job.atomauxbasis}, functional {job.func}")
        for line in IN.readlines():
            if re.search(r'JK_BASIS', line):
                line = line.format(JK_BASIS=auxbasis_list[auxbasis_map[job.auxbasis]])
            elif re.search(r'RI_BASIS', line):
                line = line.format(RI_BASIS=auxbasis_list[auxbasis_map[job.auxbasis]])
            elif re.search(r'BASIS', line):
                line = line.format(BASIS=basis_map[job.basis])
            elif re.search(r'FUNC', line):
                line = line.format(FUNC=job.func)
            elif re.search(r'DO_DHF', line):
                line = line.format(DO_DHF="True")
            elif re.search(r'AC_SHIFT_A', line):
                line = line.format(AC_SHIFT_A=str(mola.delta_ac))
            elif re.search(r'AC_SHIFT_B', line):
                line = line.format(AC_SHIFT_B=str(molb.delta_ac))
            OUT.write(line)


#  This table translates various basis-set abbreviations into the names
#  used by Psi4
basis_map = {
  "user-def": "user-def",
  "sadlej":           "sadlej-pvtz",
  "adz":              "aug-cc-pvdz",
  "avdz":             "aug-cc-pvdz",
  "aug-cc-pvdz":      "aug-cc-pvdz",
  "atz":              "aug-cc-pvtz",
  "avtz":             "aug-cc-pvtz",
  "aug-cc-pvtz":      "aug-cc-pvtz",
  "aqz":              "aug-cc-pvqz",
  "avqz":             "aug-cc-pvqz",
  "aug-cc-pvqz":      "aug-cc-pvqz",
  "dz":               "cc-pvdz",
  "vdz":              "cc-pvdz",
  "cc-pvdz":          "cc-pvdz",
  "tz":               "cc-pvtz",
  "vtz":              "cc-pvtz",
  "cc-pvtz":          "cc-pvtz",
  "datz":             "d-aug-cc-pvtz",
  "davtz":            "d-aug-cc-pvtz",
  "d-aug-cc-pvtz":    "d-aug-cc-pvtz",
  "2-tzvp":           "def2-tzvp",
  "tzvp-2":           "def2-tzvp",
  "def2tzvp":         "def2-tzvp",
  "def2-tzvp":        "def2-tzvp",
  "2-tzvpp":          "def2-tzvpp",
  "tzvpp-2":          "def2-tzvpp",
  "def2tzvpp":        "def2-tzvpp",
  "def2-tzvpp":       "def2-tzvpp",
  "dz-pp":            "cc-pvdz-pp",
  "vdz-pp":           "cc-pvdz-pp",
  "cc-pvdz-pp":       "cc-pvdz-pp",
  "tz-pp":            "cc-pvtz-pp",
  "vtz-pp":           "cc-pvtz-pp",
  "cc-pvtz-pp":       "cc-pvtz-pp",
  "qz-pp":            "cc-pvqz-pp",
  "vqz-pp":           "cc-pvqz-pp",
  "cc-pvqz-pp":       "cc-pvqz-pp",
  "adz-pp":           "aug-cc-pvdz-pp",
  "avdz-pp":          "aug-cc-pvdz-pp",
  "aug-cc-pvdz-pp":   "aug-cc-pvdz-pp",
  "atz-pp":           "aug-cc-pvtz-pp",
  "avtz-pp":          "aug-cc-pvtz-pp",
  "aug-cc-pvtz-pp":   "aug-cc-pvtz-pp",
  "aqz-pp":           "aug-cc-pvqz-pp",
  "avqz-pp":          "aug-cc-pvqz-pp",
  "aug-cc-pvqz-pp":   "aug-cc-pvqz-pp",
  "aug-sadlej":       "aug-sadlej-pvtz",
  "aug-sadlej-pvtz":  "aug-sadlej",
  "auga-sadlej":      "auga-sadlej-pvtz",
  "auga-sadlej-pvtz": "auga-sadlej-pvtz",
  "augb-sadlej":      "augb-sadlej-pvtz",
  "augb-sadlej-pvtz": "augb-sadlej-pvtz",
  "def2-qzvpp":       "def2-qzvpp",
}                   

#  This table translates the Psi4 names into the names used by Dalton
dalton_map = {
"user-def":         "user-def",
"sadlej-pvtz":      "sadlej",
"aug-cc-pvdz":      "aug-cc-pVDZ",
"aug-cc-pvdz":      "aug-cc-pVTZ",
"aug-cc-pvqz":      "aug-cc-pVQZ",
"cc-pvdz":          "cc-pVDZ",
"cc-pvtz":          "cc-pVTZ",
"d-aug-cc-pvtz":    "d-aug-cc-pVTZ",
"def2-tzvp":        "def2-TZVP",
"def2-tzvpp":       "def2-TZVPP",
"cc-pvdz-pp":       "cc-pVDZ-PP",
"cc-pvtz-pp":       "cc-pVTZ-PP",
"cc-pvqz-pp":       "cc-pVQZ-PP",
"aug-cc-pvdz-pp":   "aug-cc-pVDZ-PP",
"aug-cc-pvtz-pp":   "aug-cc-pVTZ-PP",
"aug-cc-pvqz-pp":   "aug-cc-pVQZ-PP",
"aug-sadlej":       "aug-sadlej",
"auga-sadlej-pvtz": "augA-sadlej",
"augb-sadlej-pvtz": "augB-sadlej",
"def2-qzvpp":       "def2-qzvpp",
}
#  This table translates the Psi4 names into the names used by NWChem
nwchem_map = {
"user-def":         "user-def",
"sadlej-pvtz":      "sadlej_pVTZ",
"aug-cc-pvdz":      "aug-cc-pVDZ",
"aug-cc-pvdz":      "aug-cc-pVTZ",
"aug-cc-pvqz":      "aug-cc-pVQZ",
"cc-pvdz":          "cc-pVDZ",
"cc-pvtz":          "cc-pVTZ",
"d-aug-cc-pvtz":    "d-aug-cc-pVTZ",
"def2-tzvp":        "def2-TZVP",
"def2-tzvpp":       "def2-TZVPP",
"cc-pvdz-pp":       "cc-pVDZ-PP",
"cc-pvtz-pp":       "cc-pVTZ-PP",
"cc-pvqz-pp":       "cc-pVQZ-PP",
"aug-cc-pvdz-pp":   "aug-cc-pVDZ-PP",
"aug-cc-pvtz-pp":   "aug-cc-pVTZ-PP",
"aug-cc-pvqz-pp":   "aug-cc-pVQZ-PP",
"aug-sadlej":       "aug-sadlej_pvtz",
"auga-sadlej-pvtz": "augA-sadlej_pvtz",
"augb-sadlej-pvtz": "augB-sadlej_pvtz",
"def2-qzvpp":       "def2-qzvpp",
}

#  This is the list of auxiliary basis sets
auxbasis_list = [
  "user-def",
  "aug-cc-pvdz",
  "aug-cc-pvtz",
  "aug-cc-pvqz",
  "cc-pvdz",
  "cc-pvtz",
  "cc-pvqz",
  "dgauss-a1-c",
  "dgauss-a1-x",
  "dgauss-a2-c",
  "dgauss-a2-x",
  "j-basis/tzvpp",
  "j-basis/svp",
  "jk-basis/tzvp-2",
  "jk-basis/tzvpp",
  "jk-basis/tzvpp-2",
  "jk-basis/qzvp-2",
  "jk-basis/qzvpp-2",
  "def2-tzvp",
  "def2-tzvpp",
  "aug-cc-pvdz-pp",
  "aug-cc-pvtz-pp",
  "aug-cc-pvqz-pp",
  "cc-pvdz-pp",
  "cc-pvtz-pp",
  "cc-pvqz-pp",
  "def-tzvpp",
  "def-qzvpp",
  "weigend-coulomb",
]

#  This table maps various abbreviated auxiliary basis set names onto
#  the index of proper names above.
auxbasis_map = {
  'user-def': 0,
  'adz': 1,'avdz': 1,'aug-cc-pvdz': 1,
  'sadlej': 2,'sadlej-pvtz': 2,'atz': 2,'avtz': 2,'aug-cc-pvtz': 2,
  'aug-sadlej': 2,'aug-sadlej-pvtz': 2,
  'auga-sadlej': 2,'auga-sadlej-pvtz': 2,
  'augb-sadlej': 2,'augb-sadlej-pvtz': 2,
  'aqz': 3,'avqz': 3,'aug-cc-pvqz': 3,
  'dz': 4,'vdz': 4,'cc-pvdz': 4,
  'tz': 5,'vtz': 5,'cc-pvtz': 5,
  'qz': 6,'vqz': 6,'cc-pvqz': 6,
  'dgauss-a1-c': 7,'a1-c': 7,
  'dgauss-a1-x': 8,'a1-x': 8,
  'dgauss-a2-c': 9,'a2-c': 9,
  'dgauss-a2-x': 10,'a2-x': 10,
  'j-tzvpp': 11,
  'j-svp': 12,
  'jk-tzvp-2': 13,
  'jk-tzvpp': 14,
  'jk-tzvpp-2': 15,
  'jk-qzvp-2': 16,
  'jk-qzvpp-2': 17,
  'datz': 3,'davtz': 3,'d-aug-cc-pvtz': 3,
  'def2-tzvp': 18,
  'def2-tzvpp': 19,
  'adz-pp': 20,'avdz-pp': 20,'aug-cc-pvdz-pp': 20,
  'atz-pp': 21,'avtz-pp': 21,'aug-cc-pvtz-pp': 21,
  'aqz-pp': 22,'avqz-pp': 22,'aug-cc-pvqz-pp': 22,
  'dz-pp': 23,'vdz-pp': 23,'cc-pvdz-pp': 23,
  'tz-pp': 24,'vtz-pp': 24,'cc-pvtz-pp': 24,
  'qz-pp': 25,'vqz-pp': 25,'cc-pvqz-pp': 25,
  'def-tzvpp': 26,
  'def-qzvpp': 27,
  'weigend-coulomb': 28,
}

def execute(job,verbosity):

    """Run a SAPT(DFT) calculation"""
    version = "6.5"

    summary="""
    execute is a function to carry out a CamCASP calculation. It is
    normally used by the runcamcasp.py script.
  
    The argument 'job' is an instance of class Job, and contains all
    information about the job. job.name identifies the files needed for
    the job -- they all have names that start with the specified name.
    Normally a scratch directory will be specified by the environment
    variable SCRATCH, but a different directory can be specified if
    required. An attempt is made to create it if it doesn't exist. A
    subdirectory of this directory will be used for temporary files
    needed by the job.
  
    Details of the scheduling:
    job.cores = number of cores on the machine available to be used.
  
    Normally job.cores = os.environ["CORES"], but this can be adjusted
    from the runcamcasp.py command line using the --cores option. This
    can be used, for example, to restrict the jobs to use only part
    of a multicore computer.
  
    At present, the CamCASP program itself runs in parallel, but use of more
    than two cores is inefficient. Dalton is not parallelized.
  
    """

    from time import strftime, time
    import argparse
    import glob
    import os
    import re
    import shutil
    import subprocess
  
  
    camcasp = os.environ["CAMCASP"]
  
    cores = job.cores
    cores_camcasp = job.cores_camcasp
    memory = job.memory  # in GB
    memoryMB = f"{memory*1024:1d}"
  
  
    jobname = job.name
    #  maindir is the directory created by runcamcasp.py for this job,
    #  and is the current directory at this point.
    maindir = job.dir
    os.chdir(maindir)
    # maindir = os.environ["PWD"]
    resdir = os.path.join(maindir,"OUT")
    if not os.path.isdir(resdir):
        try:
            os.mkdir(resdir)
        except OSError:
            write(f"Can't create results directory {resdir}")
            exit(1)
  
    # yesno = {True: "", False: "not "}
    if job.logfile:
        logfile = job.logfile
    else:
        logfile = os.path.join(resdir,f"{jobname}.log")
    with open(logfile,"w") as LOG:
  
        LOG.write(f"execute.py version {version}\n")
  
        def write(string):
            """Write the string both to OUT/<job>.log and to standard output"""
            LOG.write(string+"\n")
            LOG.flush()
            os.fsync(LOG.fileno())
            print(string)
  
        # if verbosity > 0:
        #   write(repr(args))
  
        work = job.work
        ix = 0
        wrk = work
        while os.path.exists(work):
            #  Don't delete existing directories -- they may be in use by other jobs.
            ix += 1
            work = f"{wrk}_{ix:02d}"
        try:
            os.mkdir(work)
        except OSError:
            write(f"Can't create working directory {work}")
            exit(1)
    
        dalton = (job.scfcode in ["dalton","dalton2006"])
    
        write(f"""Job {jobname} starting at {strftime('%H:%M:%S')}
    Working directory = {work}
    Main directory    = {maindir}
    Results directory = {resdir}
    """)
        no_camcasp = False
    
        #  Copy contents of main directory to workspace, omitting OUT directories and their contents
        cmnd = f"find -L {maindir} -maxdepth 1 -type f -name \\* -exec /bin/cp {{}} {work} \\;"
        # write(cmnd)
        try:
            subprocess.call(cmnd, shell=True)
        except OSError:
            write("Error executing command : " + cmnd)
            exit(1)
        #  Copy contents of main directory to workspace
        # subprocess.call(["cp -fpL " + maindir + "/* " + work], shell=True)
        os.chdir(work)
        # subprocess.call(["ls"], shell=True)
        os.mkdir("camcasp")
        wrkcc = os.path.join(work,"camcasp")
        #  Delete unnecessary files
        files = glob.glob("*")
        for f in files:
            for ext in [".prss",".ornt",".DALtemplate",".bash",".clt",".cltout",".sh","~"]:
                if re.match(r'.+'+ext+'$', f):
                    # print(f)
                    os.remove(f)
        # Uncomment to see which files remain.
        # subprocess.call(["ls"], shell=True)
        # Link data files to CamCASP scratch directory
        cwd = os.getcwd()
        print( os.listdir() )
        write(f"cwd = {cwd}")
        os.chdir(wrkcc)
        subprocess.call(["ln -s ../* ."], shell=True)
        # Remove circular link to this subdirectory
        os.remove("camcasp")
        # subprocess.call(["ls -l"], shell=True)
        # shutil.move(job+".cks",wrkcc)
        os.chdir("..")
  
        scf = {}
        done = {}
        out = {}
        pid = {}
        if job.runtype == "psi4-saptdft":
            parts = ["AB"]
        elif job.runtype == "saptdft" or job.runtype == "sapt":
            parts = ["A", "B", "C"]
        elif job.runtype == "properties":
            parts = ["A", "C"]
        elif job.runtype == "deltahf":
            parts = ["A", "B", "AB", "C"]
        else:
            write(f"Unsupported run-type {job.runtype}")
            exit(1)
        write(f"Parts: {parts}")

        #  M identifies the system: A, B, AB or C. Not all of these are needed in
        #  every calculation; the list job.parts specified which are needed. 
        crash = 0
        for M in parts:
            if M == "C":
                done[M] = False
            else:
                movecs = f"{jobname}-{M}-asc.movecs"
                done[M] = os.path.exists(movecs)
                if done[M]:
                    # shutil.move(movecs,wrkcc)
                    #  No need to recalculate this part
                    continue
  
            if M == "C":
                #  If A and B calculations are complete we can start CamCASP
                os.chdir(wrkcc)
                #  Mark the start time.
                subprocess.call(["touch started"], shell=True)
  
                if not os.path.exists(f"{jobname}-A-asc.movecs"):
                    write(f"Eigenvector file {jobname}-A-asc.movecs is missing.")
                    exit(1)
                if "B" in parts and not os.path.exists(f"{jobname}-B-asc.movecs"):
                    write(f"Eigenvector file {jobname}-B-asc.movecs is missing.")
                    exit(1)
    
                write(f"Starting CamCASP with {cores_camcasp} threads...")
                os.environ["OMP_NUM_THREADS"] = str(cores_camcasp)
                with open(f"{jobname}.out","w") as OUT, open(f"{jobname}.cks") as IN:
                    rc = subprocess.call(["camcasp"], stdin=IN, stdout=OUT)
                    os.chdir(work)
                    if rc == 0:
                        write(f"CamCASP finished normally at {strftime('%H:%M:%S')}")
                    else:
                        write(f"CamCASP finished with error code {rc:1d} at {strftime('%H:%M:%S')}")
                        crash = 2
            
            #  Not C. Start the M (A, B or AB) SCF calculation. 
            elif dalton:
                with open(f"{jobname}_{M}.out","w") as OUT:
                    jobM = f"{jobname}_{M}"
                    if os.path.exists(os.path.join(camcasp,"bin","dalton.sh")):
                        #    cmnd = [os.path.join(camcasp,"bin","dalton.sh"),
                        #"-omp", str(cores), "-M", memoryMB, "-t", work, jobM, jobM]
                        cmnd = [os.path.join(camcasp,"bin","dalton.sh"),
                                jobM, jobM, work, str(cores), memoryMB]
                        print(cmnd)
                    else:
                        cmnd = [os.path.join(camcasp,"bin",job.scfcode),
                        "-D", "-M", memoryMB, "-t", work, jobM, jobM]
                    # Run the code:
                    rc = subprocess.call(cmnd, stdout=OUT)
                    # ============
                    if rc > 0:
                        write(f"Part {M} failed, rc = {rc}")
                        crash = 1
                        break
                # This scf completed successfully.
                # Recent change for Dalton 2016 moves the scratch files into
                # {jobM}.tar.gz, so we have to extract SIRIUS.RST and SIRIFC
                if os.path.exists(f"{jobM}.tar.gz"):
                    subprocess.call(f"tar xzf {jobM}.tar.gz SIRIUS.RST SIRIFC", shell=True)
                # DALTON2006 puts all temp files in $WORK/${job}_$M. DALTON2013 onwards put
                # them in $WORK/DALTON_scratch_$USER/${job}_$M
                else:
                    if os.path.isdir("DALTON_scratch_" + os.environ["USER"]):
                        dir = os.path.join("DALTON_scratch_" + os.environ["USER"], jobM)
                        # Dalton2013 patch 2 added the process ID to the directory name,
                        # but here the directory is already unique, so ...
                        if not os.path.exists(dir):
                            dir = glob.glob(f"{dir}*")[0]
                        # print dir
                    else:
                        #  Dalton2006
                        dir = jobM
                        # write(f"Moving files up from {dir}")
                        # First delete any files already present in the work directory
                        for name in ["SIRIUS.RST", "SIRIFC"]:
                            if os.path.exists(name):
                                os.remove(name)
                            if os.path.exists(os.path.join(dir,name)):
                                shutil.copy(os.path.join(dir,name),work)
                #  Now run the DALTON interface program to extract the MOs and Orbital
                #  energies from SIRIUS.RST and SIRIFC and put them in
                #  {jobname}-{M}-asc.movecs.
                if os.path.exists("SIRIUS.RST") and os.path.exists("SIRIFC"):
                    if job.scfcode == "dalton2006":
                        readDALTONmos = "readDALTON2006mos"
                    else:
                        readDALTONmos = "readDALTONmos"
                    movecs = f"{jobname}-{M}-asc.movecs"
                    out = f"{jobM}.out"
                    with open(out,"a") as OUT:
                        subprocess.call([readDALTONmos, "--ascii", movecs], stdout=OUT)
                    shutil.copy(out, resdir)
                    shutil.copy(movecs, maindir)
                    shutil.move(movecs, wrkcc)
                    if os.path.exists(f"{jobname}.tar.gz"):
                        shutil.copy(f"{jobname}.tar.gz", maindir)
                else:
                    write(f"Dalton {jobname}_{M} calculation appears to have failed")
                    no_camcasp = True

            elif job.scfcode == "nwchem":
                datafile = f"{jobname}_{M}.nw"
                with open(datafile) as NW:
                    data = NW.read()
                    data = re.sub(r'<SCRATCHDIR>',work,data)
                    with open(datafile,"w") as NW:
                        NW.write(data)
        
                if os.path.exists(os.path.join(camcasp,"bin","nwchem.sh")):
                    cmnd = [os.path.join(camcasp,"bin","nwchem.sh"), datafile, str(cores)]
                else:
                    cmnd = ["nwchem", datafile]
                with open(f"{jobname}_{M}.out","w") as NWOUT:
                    rc = subprocess.call(cmnd, stdout=NWOUT, stderr=subprocess.STDOUT)
                if rc > 0:
                    write(f"Part {M} failed, rc = {rc:1d}")
                    crash = 1
                    break
        
                shutil.copy(f"{jobname}_{M}.out", resdir) 
                # Now run the interface program:
                movecs = f"{jobname}-{M}-asc.movecs"
                subprocess.call(["readNWCHEMmos", f"{jobname}_{M}.movecs", "--quiet",
                         "--ascii", movecs])
                shutil.copy(movecs, maindir)
                shutil.move(movecs, wrkcc)
            
  
            elif job.scfcode == "psi4":
                datafile = f"{jobname}_{M}.in"
                outfile = f"{jobname}_{M}.out"
                if os.path.exists(os.path.join(camcasp,"bin","psi4.sh")):
                    cmnd = [os.path.join(camcasp,"bin","psi4.sh"), datafile, outfile, str(cores)]
                else:
                    psi4_home = os.getenv("PSI4_HOME")
                    if not psi4_home:
                        write("PSI4_HOME is not set -- can't run psi4 calculations")
                        crash = 1
                        break
                    cmnd = ["psi4", datafile, outfile]
                # print(cmnd)
                rc = subprocess.call(cmnd,stdout=LOG)
                shutil.copy(outfile, resdir) 
                if rc > 0:
                    write(f"Part {M} failed, rc = {rc:1d}")
                    crash = 1
                    break
                if job.runtype == "psi4-saptdft":
                    #  This is a sapt(dft) calculation carried out entirely by Psi4.
                    #  Just clean up and exit
                    write(f"Part {M} finished")
                    write(f"Job {jobname} finished at {strftime('%H:%M:%S')}")
                    #  Clean up working directory unless save was specified or a calculation failed
                    if os.path.exists(work) and not job.debug and crash == 0:
                        shutil.rmtree(work)
                    return
                else:
                    # Run the interface program:
                    fchk = f"{jobname}_{M}.fchk"
                    sitenames = f"{jobname}_{M}.sitenames"
                    prefix = f"{jobname}-{M}"
                    movecs = f"{prefix}-asc.movecs"
                    basis = f"{prefix}.basis"
                    shutil.copy(fchk,maindir)
                    rc = subprocess.call(["readfchk.py", fchk, "--prefix", prefix,
                              "--labels", sitenames, "--dalton"])
                    if rc > 0:
                        write("Error from readfchk.py")
                        crash = 1
                        break
                    shutil.copy(movecs, maindir)
                    shutil.copy(basis, maindir)
                    shutil.move(movecs,wrkcc)
                    shutil.move(basis,wrkcc)


            elif job.scfcode == "molpro":
                datafile = f"{jobname}_{M}.molp"
                outfile = f"{jobname}_{M}.out"
                with open(datafile) as MOL:
                    data = MOL.read()
                    data = re.sub(r'<SCRATCHDIR>',work,data)
                    with open(datafile,"w") as MOL:
                        MOL.write(data)
        
                if os.path.exists(os.path.join(camcasp,"bin","molpro.sh")):
                    cmnd = [os.path.join(camcasp,"bin","molpro.sh"), datafile, outfile, str(cores)]
                else:
                    molpro_home=os.getenv("MOLPRO_HOME")
                    if not molpro_home:
                        write("MOLPRO_HOME is not set -- can't run Molpro calculations")
                        crash = 1
                        break
                    cmnd = ["molpro", datafile]

                with open(f"{jobname}_{M}.out","w") as MOLOUT:
                    rc = subprocess.call(cmnd, stdout=MOLOUT, stderr=subprocess.STDOUT)
                if rc > 0:
                    write(f"Part {M} failed, rc = {rc:1d}")
                    crash = 1
                    break
        
                shutil.copy(f"{jobname}_{M}.out", resdir) 
                # Now run the interface program:
                movecs = f"{jobname}-{M}-asc.movecs"
                subprocess.call(["mol2cam.py",  f"{jobname}_{M}.out", f"{jobname}_{M}.movecs".lower()])
                shutil.copy(movecs, maindir)
                shutil.move(movecs, wrkcc)

            else:
                write(f"Error: Unrecognised SCF code: {job.scfcode}")
                write("Allowed programs are Dalton2013 or later, Dalton2006, NWChem, Psi4 and Molpro")
                crash = 1

                ###########to be done...##################
                
                
                


        #  All now done, or something has crashed

        #  Copy available output to the results directory
        os.chdir(wrkcc)
        #  Copy CamCASP data file for the record
        if os.path.exists(f"{jobname}.cks"): 
            shutil.copy(f"{jobname}.cks",resdir)
        #  Copy result files
        if os.path.exists("data-summary.data"):
            shutil.copy("data-summary.data", os.path.join(resdir, f"{jobname}-data-summary.data"))
        # The other results files will be copied by the subprocess call using the find
        # command. 
        #==============================================================================
        #if os.path.exists(f"{jobname}.out"): 
        #    shutil.copy(f"{jobname}.out",resdir)
        # if os.path.exists("TMP_Memory_usage.dat"):
        #   shutil.move("TMP_Memory_usage.dat", os.path.join(resdir, "TMP_Memory_usage.dat"))
        #  Remove other temporary files (if any)
        subprocess.call(["find . -name TMP\\* -exec rm {} \\;"], shell=True)
        #  Copy new files to results directory: 
        #  This bit of code is needed to copy any other kind of output file over to the
        #  results directory.
        if os.path.exists("started"):
            subprocess.call(["find . -newer started -type f -exec cp -fp '{}' " + resdir + " \\;"], shell=True) 
        #==============================================================================
        os.chdir(maindir)
        #  Clean up working directory unless save was specified or a calculation failed
        if os.path.exists(work) and not job.debug and crash == 0:
            shutil.rmtree(work)

        if crash > 0:
            write(f"Job {jobname} failed at {strftime('%H:%M:%S')}\n")
            exit(1)
        else:
            write(f"Job {jobname} finished at {strftime('%H:%M:%S')}\n")

    rc = crash
    return rc
    # End of execute()


class CamRC:
    """
        Class for camcasp.rc/.camcasprc file
    """
    def __init__(self):
        self.nproc = 0
        self.np_psi4 = 0
        self.np_nwchem = 0
        self.np_molpro = 0        
        self.np_dalton = 0
        self.np_gamess = 0
        self.np_gaussian = 0
        self.np_camcasp = 0
        self.memory_gb = 0
        self.direct = False
        self.queue = ""

    def __str__(self):
        """
        Return string for Class CamRC
        """
        s = ""
        CamRC_dict = self.__dict__
        for item in CamRC_dict:
            s += f"{item} : {CamRC_dict[item]} \n"
        return s

    def read_camcasprc(self,verbosity=0):
        """
            Find a suitable camcasp.rc or .camcasprc file and read its contents into
            CamRC

            CamCASP.rc file
            ================
            .camcasprc will be in $HOME 
            camcasp.rc will be in $CAMCASP and/or in the working directory.
           
            Various options that may be set in a .camcasprc/camcasp.rc file
            Look for a .camcasprc file in the current directory, or else in the
            user's home directorY Or the $CAMCASP directory.
            
            Order of lookup:
            1) camcasp.rc in current work dir
            2) .camcasprc in $HOME
            3) camcasp.rc in $CAMCASP
         
        """
        dot_camcasprc  = ".camcasprc"   # hidden file in HOME directory
        camcasp_dot_rc = "camcasp.rc"   # regular file in $CAMCASP or work dir
        
        # Search for camcasp.rc in work directory
        camcasprc = camcasp_dot_rc
        if not os.path.exists(camcasprc):
            #  Look for .camcasprc in the users' home directory
            camcasprc = os.path.join(os.environ["HOME"],dot_camcasprc)
            if not os.path.exists(camcasprc):
                # Try looking for camcasp.rc in the CamCASP directory
                camcasprc = os.path.join(os.environ["CAMCASP"],camcasp_dot_rc)
                if not os.path.exists(camcasprc):
                    camcasprc = None

        if not camcasprc:
            print("ERROR: Could not find either camcasp.rc or .camcasprc.")
            print("  Place camcasp.rc in $CAMCASP or in $PWD or .camcasprc in $HOME")
            return
        
        # Some basic defaults:
        self.nproc = 1
        self.np_psi4    = self.nproc
        self.np_nwchem  = self.nproc
        self.np_molpro  = self.nproc
        self.np_dalton  = self.nproc
        self.np_camcasp = self.nproc
        #
        if camcasprc:
            print(f"Found CamCASP.rc file in {camcasprc}")
            with open(camcasprc) as RC:
                for line in RC:
                    if re.match(r' *#', line) or re.match(r' *$', line):
                        continue
                    if re.match(r' *\w+', line):
                        item = line.split()
                        word = item[0].lower()
                        if word == "memory" or word == "memory_gb":
                            #  Maximum memory in GB
                            self.memory_gb = int(item[1])
                        if word == "memory_mb":
                            #  Maximum memory in MB
                            self.memory_gb = int(int(item[1])/1024)
                        elif word == "direct":
                            if item[1].lower() in ["yes", "on", "true"]:
                                self.direct = True
                            elif item[1].lower() in ["no", "off", "false"]:
                                self.direct = False
                        elif word == "nproc":
                            #  Number of processors available for SCFcodes generally
                            self.nproc = int(item[1])
                            self.np_psi4    = self.nproc
                            self.np_nwchem  = self.nproc
                            self.np_molpro  = self.nproc
                            self.np_dalton  = self.nproc
                            self.np_camcasp = self.nproc
                        elif word == "np_nwchem":
                            #  Number of processors available for NWChem
                            self.np_nwchem = int(item[1])
                        elif word == "np_psi4":
                            #  Number of processors available for Psi4
                            self.np_psi4 = int(item[1])
                        elif word == "np_dalton":
                            #  Number of processors available for Dalton
                            self.np_dalton = int(item[1])
                        elif word == "np_molpro":
                            #  Number of processors available for Molpro
                            self.np_molpro = int(item[1])                            
                        elif word == "np_camcasp":
                            #  Number of processors available for CamCASP
                            self.np_camcasp = int(item[1])
                        elif word == "queue":
                            self.queue = item[1].lower()
            if verbosity > 0: 
                print(f"Finished reading {camcasprc}")
                print("Summary of data read:")
                print(self.__str__())


#  ################################################################
#  Headers for PBS and GE schedulers. Both may need to be modified.
#  ################################################################

pbs_header="""
#!/bin/bash
#
##############################################################################
# start of PBS directives (irrelevant for background jobs)
##############################################################################
# set the name of the job
#PBS -N {JOB}
#
#  Queue to use.
#PBS -q {QUEUE}
#
#  Output and error filenames. These are relative to the directory you
#  submitted the job from so make sure it was a shared filesystem, or
#  give an absolute path. Currently commented out.
##PBS -o out
##PBS -e error
#
#  Request that your login shell variables be available to the job
#PBS -V
#
#  Use this to adjust required job time, up to the maximum for the queue
#  It is better to use walltime than CPU time as this enables the scheduler
#  to optimize.
#PBS -l walltime=4:00:00,ncpus={NPROC},mem={MEMORY}gb
#
##############################################################################
# Start of shell script proper. Do not put PBS directives after this point.
##############################################################################
#
# Here is where you should set any environment variables your job requires,
# because PBS won't read your shell startup files. The most common one is
# LD_LIBRARY_PATH, required so that binaries can find their library files if
# they're in odd places. qsub will pass the job whatever LD_LIBRARY_PATH you
# had at submit time, so most people won't need this.
#
# export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH
"""

ge_header = """
# ---------------------------
# set the name of the job
#$ -N {JOB}
#$ -pe openmpi {NPROC}
#

#----------------------------
# set up the parameters for qsub
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
"""

