#!/usr/bin/env python3
#  -*-  coding: utf-8  -*-

from camcasp import die, findfile, replace
import argparse
import glob
import os
import re
import sys
import shutil
import string
import subprocess

bin = os.path.join(os.environ["CAMCASP"], "bin")

parser=argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
description="""
Uses the Lillestolen-Wheatley or Le Sueur-Stone procedure to localize
a set of polarizability files, then the Williams-Stone-Misquitta
procedure to refine the local polarizabilities, and finally the
standard integration over polarizabilities at imaginary frequency to
obtain dispersion coefficients.
""", epilog="""
All of the optional arguments may be omitted, so the simplest use of the
command is just
  localize.py <job>
where <job> is the CamCASP job name.

The script operates in three stages: localization, refinement and
dispersion. It runs in the directory created by a CamCASP properties
calculation. In the following, <name> is the CamCASP job name.

For the localization step, the script looks for a .pol file in the
current directory or in the OUT subdirectory. If there is more than
one, the user is asked to choose between them, or the --polfile flag
can be used to specify the required file explicitly. The --format
argument specifies the format of the polarizability file; "A" specifies
the old format, "B" the new, which is the default.

The polarizability file is split into sections, one for each
frequency. It is assumed that the static polarizabilities are
included, followed by dynamic polarizabilities at 10 frequencies.
The file names are <prefix>nnn.pol, with nnn = 000, 001, ..., 010.

The localization requires a file <name>.axes or ../<name>.axes
defining the local axes on each site. An empty <name>.axes file can be
provided if global axes are wanted. The Orient input file <infile> is
edited to specify the local-axes file and the sequence number, and
Orient is run to carry out the localization at each frequency. This is
done using global axes, and the localized polarizabilities are
transformed into local axes, if specified.

These single-frequency files are concatenated into a single file
<output-file-prefix>_0f10.pol (default <name>_L<limit>_0f10.pol).

For the refinement, the script looks for a .p2p file containing the
point-to-point polarizabilities. It also needs a file <name>.sites
containing the site specifications (usually created by cluster in the
properties calculation) and the file <name>.axes or ../<name>.axes
defining the local axes on each site. The polarizability model to be
fitted is defined in a file, optionally specified by the --model
argument, default <name>.pdef. If this file is present in the job directory
or the directory above, it is used; otherwise a new file with that name is
generated according to the options --wsmlimit, --hlimit and --isotropic.
The generated file can be modified, and the refinement repeated, to
obtain results for a different polarizability model.

The point-to-point polarizabilities are split into single-frequency
files, and the PFIT program is run for each one, to refine the local
polarizabilities. These refined single-frequency files are
concatenated into a single file.

In the dispersion step, the polarizabilities are assembled into a data
file for the casimir program, which calculates the dispersion coefficients.

The script skips the localization, refinement and/or dispersion steps
if it finds the corresponding output file, but the --force option
with any or all of the arguments loc, refine and disp forces the
specified steps to be carried out.

Cluster file commands:
----------------------
This script assumes that you have created the various input files 
needed for the Process, PFIT and ORIENT codes. This is done by including
the command

   Localization

in the RUN-TYPE block of the cluster file.

If --format OLD will be used to specify the older (pre-CamCASP 6.0.x)
format for the non-local polarizabilities, then the Cluster command file
must include the line
  ORIENT  POL-FORMAT  OLD
in the RUN-TYPE block.
""")

parser.add_argument("name", help="CamCASP job name")
group = parser.add_mutually_exclusive_group()
group.add_argument("--verbosity", type=int, help = "verbosity level (default 1)",
                    default=1)
group.add_argument("--verbose", "-v", help = "increase verbosity level",
                   action="count", dest="verbosity")
group.add_argument("--quiet", help = "set verbosity level 0",
                   action="store_const", const=0, dest="verbosity")
parser.add_argument("--axes", default="",
                    help="File containing definitions of local axes")
parser.add_argument("--sites", default="",
                    help="File containing site definitions")
parser.add_argument("--format", choices=["A","OLD","old","B","NEW","new"],
                    default="NEW", help="Format of polarizability file (default NEW/B)")
parser.add_argument("--polfile", help="Non-local polarizability file from CamCASP")
parser.add_argument("--limit", default=2, type=int,
                    help="Maximum rank for generated local polarizabilities (default 2)")
parser.add_argument("--wsmlimit", type=int,
                    help="Maximum rank for refined local polarizabilities (default = limit)")
parser.add_argument("--hlimit", "--Hlimit", type=int,
                    help="Maximum rank for local polarizabilities on hydrogen (default = limit)")
parser.add_argument("--isotropic", action="store_true",
                    help="When refining, fit only isotropic polarizabilities")
parser.add_argument("--subdir", "-d", help="Subdirectory for localization files")
parser.add_argument("--model", "--pdef", help="Polarizability model definition file")
parser.add_argument("--loc", default="LW", choices=["LW","LS"],
                    help="Localization method (default LW)")
parser.add_argument("--cutoff", "--pol-cutoff", default="0.0001", \
    help="Cutoff to eliminate local polarizabilities from the refinement process. \
    Default = 0.0001 a.u.")
parser.add_argument("--weight", type=int, default=3, choices=list(range(0,7)),
    help="weight scheme to use in refinement (see Users' Guide) (default 3)")
parser.add_argument("--weightcoeff", type=float, default=1.0e-3, 
    help="weight coefficient used in refinement (default 1.0e-3)")
parser.add_argument("--svd", default="0.0",
                    help="Use singular value decomposition in the refinement, \
with the given value as SVD threshold (default=0.0 i.e., no SVD)")
parser.add_argument("--force", choices=["loc","refine","disp"], nargs="+", default=[],
                    help="Force the specified step or steps to be carried out, \
even if they appear to have been done already.")
parser.add_argument("--clean", action="store_true",
                    help="Clean up temporary files generated by the \
localization procedure and exit.")
parser.add_argument("--cleanall", action="store_true",
                    help="Clean up all files generated by the \
localization procedure and exit. This includes both temporary files \
and results! So use with care.")
parser.add_argument("--norefine", action="store_true",
                    help="Skip the refinement step (over-rides --force)")
parser.add_argument("--nodisp", action="store_true",
                    help="Skip the calculation of dispersion coefficients \
(over-rides --force)")
parser.add_argument("--debug", "--keep", action="store_true",
                    help="Don't delete intermediate files")
# parser.add_argument("--keep_p2p", action="store_true",
#                     help="Don't delete the individual p2p files")
parser.add_argument("-i", "--infile",
    help="alternative Orient input file name (default <name>.ornt)")
parser.add_argument("--polfile-prefix",
    help="alternative polarizability file prefix (default <name>_NL4_)")
parser.add_argument("-o", "--outfile",
    help="alternative prefix for local polarizability file (default <name>_L<limit>)")

args = parser.parse_args()

name = args.name
verbosity = args.verbosity

def write_header(FILE,prefix):
    FILE.write(f"""{prefix} Localisation settings for {args.name}
{prefix} Axes file:       {axes}
{prefix} Pol file format: {args.format}
{prefix} Limit:           {limit}
{prefix} WSM-Limit:       {wsmlimit}
{prefix} H-Limit:         {hlimit}
{prefix} Isotropic?:      {args.isotropic}
{prefix} Model file:      {pdef}
{prefix} Pol Cutoff:      {args.cutoff}
{prefix} Loc algorithm:   {args.loc}
{prefix} Weight:          {args.weight}
{prefix} Weight coeff:    {args.weightcoeff}
{prefix} SVD threshold:   {args.svd}
{prefix} NoRefine?:       {args.norefine}
{prefix}
""")


if args.clean or args.cleanall:
    #  Remove all generated files (except result files) and exit
    if args.subdir:
        os.chdir(args.subdir)
    for label in ["_???.prss", "_ref_wt?_L*_???.data", "_NL?_???.pol"]:
        files = glob.glob(name+label)
        for file in files:
            os.remove(file)
    if args.cleanall:
        # Also remove intermediate result files
        for label in ["_L?_???.pol","_L?_???.out","_ref_wt?_L*_???.out",
                      "_ref_wt?_L*_???.pol"]:
            files = glob.glob(name+label)
            for file in files:
                os.remove(file)
    exit(0)


#  Various options. Defaults are usually adequate.

if args.infile:
    infile = args.infile
else:
    infile = name + ".ornt"
if args.polfile_prefix:
    polfile_prefix = args.polfile_prefix
else:
    polfile_prefix = name + "_NL4_"
if args.outfile:
    outfile_prefix = args.outfile + "_"
else:
    outfile_prefix = f"{name}_L{args.limit:1d}_"

if args.sites:
    sites = arg.sites
else:
    sites = args.name + ".sites"
if os.path.exists(sites):
    pass
elif os.path.exists(os.path.join("..",sites)):
    os.symlink(os.path.join("..",sites),sites)
else:
    die(f"Can't find site definition file {sites} or ../{sites}")

if args.axes:
    axes = args.axes
else:
    axes = args.name + ".axes"
if os.path.exists(axes):
    pass
elif os.path.exists(os.path.join("..",axes)):
    os.link(os.path.join("..",axes),axes)
else:
    print(f"Can't find axis definition file {axes} or ../{axes}")
    print("Using global axes at all sites")
    #  Create empty name.axes file
    with open(axes,"w") as AXES:
        pass

if args.svd == "0.0":
    svd = "off"
else:
    svd = "threshold "+args.svd

#  Check that Orient can be found
try:
    check = subprocess.check_output("type orient", shell=True)
except subprocess.CalledProcessError:
    print("""
Can't find the Orient program, needed for the localization.
Please ensure that the directory containing the orient executable is 
in your PATH, or make a symbolic link $CAMCASP/bin/orient pointing to
the executable.
""")
    exit(1)

#  ---------------------------------
#  Unpack the p2p files if necessary.
#  ---------------------------------

if not args.norefine or "refine" in args.force:
    ok = True
    for tag in ["000", "001", "002", "003", "004", "005", "006", "007", "008", "009", "010"]:
        if not os.path.exists(name+"_"+tag+".p2p"):
            ok = False
            break
    if not ok:
        p2pfile = findfile("OUT",".p2p")
        if not p2pfile:
            die("Can't find a point-to-point (.p2p) file")
        print("Splitting the point-to-point polarizability file. Please wait ... ")
        if verbosity > 0: print(f"Using p2p file {p2pfile}")
        sys.stdout.flush()
        with open("split_p2p","w") as SPLIT:
            SPLIT.write(f"""read P2P pols for {name}
    Frequencies Static + 10
    P2P-Pols {p2pfile} SPLIT
  End
  """)
        if verbosity > 0:
            subprocess.call(["process < split_p2p"], shell=True)
        else:
            subprocess.call(["process < split_p2p > /dev/null"], shell=True)
        os.remove("split_p2p")
        if verbosity > 0: print("done")


limit = args.limit
if args.wsmlimit:
    wsmlimit = min(args.limit,args.wsmlimit)
else:
    wsmlimit = args.limit

if args.hlimit:
    hlimit = min(args.hlimit,wsmlimit)
else:
    hlimit = min(args.limit,wsmlimit)

if args.model:
    pdef = args.model
else:
    pdef = args.name + ".pdef"

weight       = args.weight
weight_coeff = args.weightcoeff
pol_cutoff   = args.cutoff
if args.isotropic:
    isotropic="isotropic"
else:
    isotropic=""

print(f"""
Localisation settings for {args.name}
Sub-directory    {args.subdir}
Axes file:       {axes}
Pol file format: {args.format}
Limit:           {limit}
WSM-Limit:       {wsmlimit}
H-Limit:         {hlimit}
Isotropic?:      {isotropic}
Model file:      {pdef}
Pol Cutoff:      {args.cutoff}
Loc algorithm:   {args.loc}
Weight:          {weight}
Weight coeff:    {weight_coeff}
SVD threshold:   {args.svd}
NoRefine?:       {args.norefine}
""")

newformat = args.format in ["B","NEW","new"]

#  --------------------
#  Set up sub-directory
#  --------------------

here = os.getcwd()
if args.subdir:
    subdir = args.subdir
    if not os.path.exists(subdir):
        os.mkdir(subdir)
    os.chdir(subdir)
    for ext in [".prss",".ornt",".sites","_casimir.prss",".axes"]:
        if not os.path.exists(name+ext):
            os.symlink(os.path.join("..",name+ext),name+ext)
    if args.axes:
        # In this case the axis file name may not be of the form name.axes,
        # so use the name provided using --axes
        if not os.path.exists(args.axes):
            os.symlink(os.path.join("..",args.axes),args.axes)
    else:
        # Else try an axis filename in the name.axes format:
        ext = ".axes"
        if not os.path.exists(name+ext):
            os.symlink(os.path.join("..",name+ext),name+ext)
    if not os.path.exists("OUT"):
        os.symlink("../OUT","OUT")
    if os.path.exists(os.path.join("..",pdef)):
        shutil.copy2(os.path.join("..",pdef),pdef)
 

#  ----------------
#  Site definitions
#  ----------------

#  Check for existence of site definition file, either here or in
#  directory above. Normally created automatically by runcamcasp.py. 
if args.sites:
    sites = arg.sites
else:
    sites = args.name + ".sites"
if os.path.exists(sites):
    pass
elif os.path.exists(os.path.join("..",sites)):
    os.symlink(os.path.join("..",sites),sites)
else:
    die(f"Can't find site definition file {sites} or ../{sites}")
  
#  Check that the sites listed all have different names
with open(sites) as S:
    check = False
    for line in S.readlines():
        if re.match(r' *end *$', line, flags=re.I):
            check = False
        if re.match(r' *sites *$', line, flags=re.I):
            check = True
            site_list = []
        elif check:
            m = re.match(r' *(\S+) *', line)
            if m:
                s = m.group(1)
                if s in site_list:
                    print("There is more than one site named", s)
                    die("Every site must have a different name")
                else:
                    site_list.append(s)

#  ------------
#  Localization
#  ------------

if os.path.exists(outfile_prefix+"0f10.pol") and "loc" not in args.force:
    print(f"File {outfile_prefix}0f10.pol present -- localization already done")
else:
    if args.polfile:
        if os.path.exists(args.polfile):
            polfile = args.polfile
        elif os.path.exists(os.path.join("OUT",args.polfile)):
            polfile = os.path.join("OUT",args.polfile)
        else:
            die(f"Can't find {args.polfile} or OUT/{args.polfile}")
    else:
        if args.format in ["new", "NEW", "B"]:
            suffix = "NL4_fmtB.pol"
        else:
            suffix = "NL4_fmtA.pol"
        polfile = findfile("OUT",suffix,
          prompt = f"Enter number for required {args.format} format file")
        if not polfile:
            die("Can't find a polarizability (.pol) file.")
    if verbosity > 0: print(f"Using polarizability file {polfile}")

    #  Split polarizability file into individual frequencies
    if verbosity > 0: print(f"Splitting {polfile} into individual frequencies ...", end=' ')
    if newformat:
        with open(polfile) as POL:
            freq2 = ""
            p = 0
            for line in POL.readlines():
                if re.match(r'POL ', line):
                    m = re.search(r'FREQ2 +(-?\d+\.\d+E[-+]\d+)', line)
                    # Compare the value of FREQ2 with the saved value in freq2. If they are
                    # unequal then we have a new frequency block. 
                    if m.group(1) != freq2:
                        # print freq2, m.group(1)
                        # Close the OUT file handle if freq2 is non-null. We need this test
                        # as freq2 will be null for the first squared-frequency.
                        if freq2 != "":
                            OUT.write("ENDFILE\n")
                            OUT.close()
                        OUT = open(f"{polfile_prefix}{p:03d}.pol","w")
                        freq2 = m.group(1)
                        p += 1
                    line = re.sub("POL",f"ALPHA INDEX {p:03d}",line)
                OUT.write(line)
            OUT.write("ENDFILE\n")
            OUT.close()
    else:
        subprocess.call(["/usr/bin/csplit", "--prefix", polfile_prefix,
                 "--suffix-format", "%03d.pol", "--elide-empty-files",
                 "--quiet", polfile, "/# INDEX/", '{*}'])
    # shutil.copyfile(polfile_prefix +"000.pol",polfile_prefix +"static.pol")
    if verbosity > 0: print(" done")

    #  Carry out localization for each frequency in turn
    if verbosity > 0: print(f"Localizing polarizabilities using {args.loc} procedure ...")
    if os.path.exists(f"{outfile_prefix}0f10.pol"):
        os.remove(f"{outfile_prefix}0f10.pol")
    if os.path.exists("orient.error"):
        os.remove("orient.error")
  
    for ix in range(11):
        tag = f"{ix:03d}"
        if verbosity > 0: print(tag, end=' ')
        sys.stdout.flush()
        if os.path.exists(polfile_prefix + tag + ".pol"):
            #  Localize the polarizabilities, up to rank limit, for this frequency index
            #  Write them to <outfile_prefix><tag>.pol
            with open(f"{name}.ornt") as IN, open(f"{name}.temp{tag}","w") as TEMP:
                if newformat:
                    TEMP.write(IN.read().format(PAIRS="pairs", AXES=axes, PREFIX=polfile_prefix,
                     INDEX=tag, LIMIT=limit, LOC=args.loc))
                else:
                    TEMP.write(IN.read().format(PAIRS="", AXES=axes, PREFIX=polfile_prefix,
                     INDEX=tag, LIMIT=limit, LOC=args.loc))

            # replace(f"{name}.ornt",f"{name}.temp{tag},
            #         {"AXES": axes, "PREFIX": polfile_prefix, "INDEX": tag,
            #             "LIMIT": str(limit), "LOC": args.loc})
            with open(name+".temp"+tag) as TEMP:
                with open(f"{outfile_prefix}{tag}.out","w") as OUT:
                    subprocess.call(["orient"], stdin=TEMP, stdout=OUT)
            if os.path.exists("orient.error"):
                die ("Error in localization")
            if not args.debug:
                os.remove(name+".temp"+tag)
            # if tag == "000":
            #   shutil.copyfile(outfile_prefix+tag+".pol", outfile_prefix+"static.pol")
        else:
            if tag == "000":
                print("Warning -- no static polarizabilities found")
            else:
                die(f"Can't find polarizability file {polfile_prefix}{tag}.pol")
  
    if verbosity > 0: print(" ... done")
    # os.remove(name+".temp")

    if verbosity > 1:
        print(f"Output files for localization procedure are {outfile_prefix}nnn.out")
        print(f"Localized polarizabilities are in {outfile_prefix}nnn.pol (binary)")
        print(f"The binary file {outfile_prefix}0f10.pol contains the polarizabilities at all frequencies.")
    #  Concatenate individual localized polarizability files into single file.
    with open(outfile_prefix + "0f10.pol","w") as ALL:
        for ix in range(11):
            tag = f"{ix:03d}"
            with open(f"{outfile_prefix}{tag}.pol") as SINGLE:
                ALL.write(SINGLE.read())
            if not args.debug:
                # pass
                #  Delete intermediate files
                os.remove(f"{outfile_prefix}{tag}.pol")
                # os.remove(f"{outfile_prefix}{tag}.out")

#  ----------
#  Refinement
#  ----------

  
refined = f"{name}_ref_wt{weight:1d}_L{wsmlimit:1d}_0f10.pol"
if args.norefine:
    if verbosity > 0: print("Skipping refinement")
elif os.path.exists(refined) and "refine" not in args.force:
    if verbosity > 0: print(f"File {refined} present -- refinement already done")
else:
    if verbosity > 0: print("Preparing to refine the local polarizabilities")
  
    #  Check for existence of local axes definition file.
    #  If a file name.axes is present in this directory, use it, or if in
    #  the one above, link to that.
    if args.axes:
        axes = args.axes
    else:
        axes = args.name + ".axes"
    if os.path.exists(axes):
        pass
    elif os.path.exists(os.path.join("..",axes)):
        os.symlink(os.path.join("..",axes),axes)
    else:
        die(f"Can't find axis definition file {axes} or ../{axes}")
    print("Using axis definition file", axes)
  
    if verbosity > 0: print("Refining the local polarizabilities")
    #  Polarizability model definition
    #  The default model definition file pdef is <name>.pdef, but a different
    #  name can be specified using the --model or --pdef flag.
    #  If a file named by pdef is present in this directory, use it, or if in
    #  the one above, link to that. Otherwise the process call will create
    #  one.
    if not os.path.exists(pdef) and os.path.exists("../"+pdef):
        pdef = "../"+pdef
    if os.path.exists(pdef):
        print("Using polarizability model definition file", pdef)
    else:
        print("Creating new polarizability model definition file", pdef)

    if args.isotropic:
        refine = f"{name}_ref_wt{weight:1d}_L{wsmlimit:1d}iso_"
    else:
        refine = f"{name}_ref_wt{weight:1d}_L{wsmlimit:1d}_"

    outfile = refine+"0f10.pol"
    if os.path.exists(outfile):
        os.remove(outfile) 
    if verbosity > 1:
        print(f"Refinement data files are {refine}nnn.data")
        print(f"Refinement output files are {refine}nnn.out")

    for ix in range(11):
        tag = f"{ix:03d}"
        if verbosity > 0: print(tag, end=' ')
        sys.stdout.flush()
        #  Link to the p2p file if necessary.
        p2pfile = f"{name}_{tag}.p2p"
        if not os.path.exists(p2pfile) and os.path.exists(os.path.join("..",p2pfile)):
            os.symlink(os.path.join("..",p2pfile),p2pfile) 
        if not os.path.exists(p2pfile):
            print(f"p2p file {p2pfile} not found")
            exit(1)

        prss = f"{name}_{tag}.prss"
        refine_data = f"{refine}{tag}.data"
        refine_datatemp = f"{refine}{tag}.datatemp"
        refine_out = f"{refine}{tag}.out"
        if os.path.exists("error_file"):
            os.remove("error_file")
        #  Replace the placeholders {INDEX} etc. in the <name>.prss file with the
        #  values for this job to get the <name>_<tag>.prss file for this frequency.
        with open(name+".prss") as IN, open(prss,"w") as PRSS:
            PRSS.write(IN.read().format(PDEF=pdef,INDEX=tag,LIMIT=limit,HLIMIT=hlimit,
                                        WSMLIMIT=wsmlimit,ISOTROPIC=isotropic,
                                        WEIGHT=weight,WEIGHT_COEFF=weight_coeff,
                                        SVD=svd,CUTOFF=pol_cutoff))
        #  Run the <name>_<tag>.prss file through process to generate the input file
        #  for Pfit.
        with open(prss) as IN, open(refine_data,"w") as DATA:
            subprocess.call(["process"], stdin=IN, stdout=DATA)
        if os.path.exists("error_file") or os.path.exists("error_log"):
            die("Error in process")
        # Replace the placeholders in the file refine_data:
        with open(refine_data) as PFIT_DATA, open(refine_datatemp,"w") as PFIT_DATATEMP:
            PFIT_DATATEMP.write(PFIT_DATA.read().format(PDEF=pdef,AXES=axes,SITES=sites))
        #  Finally feed the data file to Pfit.
        with open(refine_datatemp) as PFITIN, open(refine_out,"w") as PFITOUT:
            subprocess.call("pfit", stdin=PFITIN, stdout=PFITOUT, stderr=subprocess.STDOUT)
        #  Clean up
        if os.path.exists("pfit_error"):
            die("Error in pfit -- see file pfit.error")
        elif os.path.exists("error_file"):
            die("Error in pfit -- see file error_file")
        if not args.debug:
            os.remove(prss)
            os.remove(refine_datatemp)

    if verbosity > 0: print("\nRefinement finished")
    #  Concatenate polarizability files
    with open(outfile,"w") as OUT:
        write_header(OUT,"# ")
        for tag in ["000", "001", "002", "003", "004", "005", "006", "007", "008", "009", "010"]:
            OUT.write(f"\n# INDEX {tag}\n")
            with open(f"{refine}{tag}.pol") as POL:
                OUT.write(POL.read())
            if args.subdir:
                os.remove(f"{name}_{tag}.p2p")
    print(f"""Refined localized polarizabilities, static and at imaginary frequency,
are in {outfile}""")

#  -----------------------
#  Dispersion coefficients
#  -----------------------

if args.nodisp:
    exit(0)
if args.norefine:
    if args.isotropic:
        prefix = f"{name}_L{limit}iso"
    else:
        prefix = f"{name}_L{limit}"
else:
    if args.isotropic:
        prefix = f"{name}_ref_wt{weight}_L{wsmlimit}iso"
    else:
        prefix = f"{name}_ref_wt{weight}_L{wsmlimit}"
    limit = wsmlimit
casimir_in = f"{prefix}_casimir.data"
casimir_out = f"{prefix}_casimir.out"
if "disp" not in args.force and os.path.exists(casimir_out) and os.stat(casimir_out).st_size > 0:
    print(f"File {casimir_out} present -- dispersion coefficients already calculated")
    exit(0)
else:
    casimir_temp = name+"_casimir.temp"
    if verbosity > 0: print("Calculating the dispersion coefficients ... ", end=' ')
    sys.stdout.flush()
    if os.path.exists("casimir_error"):
        os.remove("casimir_error")
    if args.wsmlimit == 1:
        maxN = "6"
    elif args.wsmlimit == 2:
        maxN = "10"
    elif args.wsmlimit == 3:
        maxN = "12"
    else:
        maxN = "n"
    if args.isotropic:
        potfile = f"{prefix}_C{maxN}iso.pot"
    else:
        potfile = f"{prefix}_C{maxN}.pot"
    with open(name+"_casimir.prss") as PRSS, open(casimir_temp,"w") as TEMP:
        TEMP.write(PRSS.read().format(PREFIX=prefix,LIMIT=limit,HLIMIT=hlimit))
    with open(casimir_temp) as TEMP, open(casimir_in,"w") as DATA:
        if subprocess.call(["process"], stdin=TEMP, stdout=DATA, stderr=sys.stderr) > 0:
            die("Error in process")
    if not args.debug: os.remove(name+"_casimir.temp")
    with open(casimir_in) as IN, open(casimir_out,"w") as OUT:
        if subprocess.call(["casimir"], stdin=IN, stdout=OUT, stderr=sys.stderr) > 0:
            die("Error in casimir")
    if os.stat(casimir_out).st_size == 0 or os.path.exists("casimir_error"):
        die("Dispersion coefficient calculation failed")
    else:
        #  Copy dispersion potential definition to potfile
        with open(potfile,"w") as OUT, open(casimir_out) as IN:
            write_header(OUT,"! ")
            for line in IN:
                if re.match(r'Dispersion coefficients', line):
                    OUT.write("! "+line)
                    break
            for line in IN:
                OUT.write(line)
        if verbosity > 0: print(" done")
        print(f"""Dispersion coefficients are in {casimir_out}.
The dispersion potential, in Orient form, is in {potfile}.""")

