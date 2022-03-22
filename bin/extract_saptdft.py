#!/usr/bin/env python3
# -*- coding: latin-1 -*-

"""
    Extract sapt-dft energy terms from CamCASP summary files.
"""

import os
import re
import sys
import argparse
from camcasp import die, findfile

parser=argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
description="""Extract sapt-dft energy terms from CamCASP summary files.
""",epilog="""

There may be any number of job directory paths in the argument list.
Path arguments that are not directories are silently ignored.
The script looks for CamCASP summary files, which are expected to have
names of the form <path>/OUT/<job><suffix>. The default suffix is
"-data-summary.data", which is the usual form used by CamCASP. The job
name does not have to be the same for every path.

If a directory <path>_dHF is present in the argument list, it is assumed
to contain a delta-HF calculation, and the delta-HF energy is extracted
from it. If there are directories <path> and <path>_dHF with the same
<path>, they are assumed to refer to the same system and the energy
components are displayed together. However the script will handle cases
where only the SAPT-DFT calculation or only the delta-HF calculation has
been done.

Energy values in the input file are converted to the specified unit,
default kJ/mol.

If --ab is specified, the induction terms for molecules A and B are shown
separately. In the short layout, the ind, exind and delta-HF components are
printed as a total ind term, while disp and exdisp are printed as a total
disp term. In the long layout they are all printed separately.

If --reg is specified, the regularised second-order induction and exchange-induction
energies will be used to calculate the total interaction energy. The default
regularization parameter is eta = 3.0 a.u. This can be changed using
  --regeta  <value>

If --ct is specified, the second-order charge-transfer, CT(2), and 
second-order polarization energy, POL(2), will be calculated using the regularized
induction and exchange-induction energies. As above, the default
regularization parameter is eta = 3.0 a.u., but this can be changed
using --regeta.

If the optional --split flag is used, it should provide a re.match pattern
for the directory names, and a list of matched groups that are to be output
as data columns. E.g.
extract_saptdft.py  H2O-HOH_*_dc{,_dHF} --split 'H2O-HOH_(.....)_(...)_dc' 1 2
where the actual directory names are of the form, e.g., H2O-HOH_1.957_135_dc
Note that the pattern will be substituted by the shell.

ERROR HANDLING:
===============
If --errors is specified, errors in any calculation --- delta-HF or E2int SAPT(DFT)
--- are indicated by ERR, and a summary of all errors is provided at the 
end of the output. 
    * Only if both dHF and E2int are defined is Eint = E2int + dHF reported. 
    * If either E2int or dHF have failed then Eint = 0.0
    * If any part of dHF is not defined then dHF = 0.0
    * If any part of E2int is not defined then E2int = 0.0
"""
)
# parser.add_argument("--job", help="job file prefix", default="")
parser.add_argument("paths", metavar="path", nargs="+",
                    help="path to job directory (may be repeated)")
parser.add_argument("--verbosity", type=int, default=0,
                    help="Print additional information about the job if > 0") 
parser.add_argument("--verbose", "-v", help="verbose output",
                    action="count", default=0)
parser.add_argument("--unit", "--units", help="Unit for output (default kJ/mol)",
                    choices=["cm-1","kJ/mol","au","hartree","eV","meV","K","kelvin","kcal/mol"],
                    default="kJ/mol")
parser.add_argument("--reg", help="Use regularized induction and exchange-induction",
                    action="store_true")
parser.add_argument("--ct", "--CT", help="Compute the CT(2) energy using regularized induction",
                    action="store_true")
parser.add_argument("--regeta", help="Value of regularization parameter \eta (normally 3.0)",
                    default=3.0, type=float)
layout_group = parser.add_mutually_exclusive_group()
layout_group.add_argument("--short", help="Short output layout",
                    action="store_true")
layout_group.add_argument("--long", help="Long output layout",
                    action="store_true")
parser.add_argument("--S2", help="Use S2 approximation for E(1)exch and E(2)exind",
                    action="store_true")
parser.add_argument("--ab", help="Show A and B induction separately",
                    action="store_true")
parser.add_argument("--suffix", help="summary file suffix (default -data-summary.data)",
                    default="-data-summary.data")
parser.add_argument("--dhf", help="default delta-HF energy",
                    action="store_true")
parser.add_argument("--split", nargs="*",
                    help="Split directory name to provide variable data")
parser.add_argument("--title", help="Optional title for output")
parser.add_argument("--errors", help="Print a summary of the jobs which contain errors.",
                    action="store_true")

args = parser.parse_args()
# job = args.job

#  Verbosity
if args.verbosity:
    verbosity = args.verbosity
elif args.verbose:
    verbosity = int(args.verbose)
else:
    verbosity = 0

ct_reg     = args.ct
regularize = args.reg
# print("ct_reg and regularize ",ct_reg, regularize)
reg_eta    = float(args.regeta)
if regularize or ct_reg:
    if reg_eta==0.0:
        reg_eta = 3.0 # this is the default value for E(2)IND(reg)

# Define terms in Eint:
if regularize:
    saptdft = ["elst","exch","indRA","indRB","exindRA","exindRB","disp","exdisp"]
else:
    saptdft = ["elst","exch","indA","indB","exindA","exindB","disp","exdisp"]

show_dhf = False
if args.dhf: # (and later if any _dHF directories are encountered)
    saptdft.append(["dHF"])
    show_dhf = True

if args.split:
    print("directory name pattern:", args.split)


units = {
"kj/mol": 2625.5,
"cm-1":   219475.0,
"au":          1.0,
"hartree":     1.0,
"ev":      27.2113,
"mev":     27211.3,
"k":       315773.0,
"kelvin":  315773.0,
"kcal/mol":627.510,
}
unit = units[args.unit.lower()]
# print(unit)

name_len = 0
energy = {}
stderr = sys.stderr

if args.title:
    print(args.title)

for path in args.paths:
    path = os.path.normpath(path)
    if not os.path.isdir(path):
        continue
    if not os.path.exists(os.path.join(path,"OUT")):
        continue
    if re.search(r'_dHF$', path):
        name = re.sub(r'_dHF$', '', path)
        isdhf = True
        if not show_dhf:
            saptdft.append("dHF")
        show_dhf = True
    else:
        name = path
        isdhf = False
    summary = findfile(os.path.join(path,"OUT"),args.suffix)
    if not summary:
        continue
    job = re.sub(args.suffix, "", os.path.basename(summary))

    if verbosity > 0: print(path, name)
    if name not in energy:
        energy[name] = {}
        name_len = max(name_len,len(name))

    if isdhf:
        #  Delta-HF
        ok = True
        for suffix in ["A","B","AB"]:
            file = os.path.join(path, "OUT", job + "_" + suffix + ".out")
            if not os.path.exists(file):
                ok = False
                if verbosity > 0: stderr.write("No file " + file + "\n")
                break
        if not ok:
            continue
        ehf = {}
        for suffix in ["A","B","AB"]:
            ok = False
            file = os.path.join(name + "_dHF", "OUT", job + "_" + suffix + ".out")
            if not os.path.exists(file):
                print( "Can't find file", file)
                exit(1)
            if verbosity > 0:
                print(file)
            with open(file) as IN:
                for line in IN:
                    m = re.match(r'\@? +(Final HF energy:|Total SCF energy =|Total Energy =) +(-?\d+\.\d+)',line)
                    if m:
                        ehf[suffix] = float(m.group(2))
                        ok = True
                        break
                if not ok:
                    die("Can't find HF energy in " + file)
        ehf_diff = (ehf["AB"] - ehf["A"] - ehf["B"])*unit
        if verbosity > 1:
            print( "E_AB =", ehf["AB"]*unit, "E_A =", ehf["A"]*unit, "E_B =", ehf["B"]*unit)
    
        with open(summary) as IN:
            for line in IN:
                #  Ignore regularized energy terms
                if re.search(r' REG ', line):
                    continue
                                                                  # Groups
                energies = re.compile(r'''E\^\{[12]\}             #     E^{n} where n = 1 or 2 
                                          \_\{(\w+)(\,exch)?\}    # 1 2 _{component} or _{component,exch}
                                          (\(S2\))?               # 3   match (S2) if present
                                          (\((A|B)\))?            # 4 5 match (A) or (B) if present
                                          \s+                     #     space. group(5) will be A or B.
                                          (-?\d+\.\d+(E[+-]\d+)?) # 6 7 match a floating point number of the
                                                                  #     form (-)mmmm.nnnnE(+|-)pp
                                                                  #     The exponential is optional and
                                                                  #     will be group(7)
                                          \s+                     #     space
                                          (\S+)                   # 8   text
                                          \s+                     #     more space
                                          ([\S,\s]*)              # 9   text with space
                                          ''',re.I|re.VERBOSE)
                m = energies.search(line)

                if m:
                    # print('dHF GOT LINE ',line)
                    # print('Groups  1: ',m.group(1),' 2: ',m.group(2),' 3: ',m.group(3))
                    # print('Groups  4: ',m.group(4),' 5: ',m.group(5),' 6: ',m.group(6))
                    # print('Groups  7: ',m.group(7),' 8: ',m.group(8),' 9: ',m.group(9))
                    cmpnt = m.group(1)
                    # Special case to decide whether or not to use S2 approx for exchange energy:
                    if cmpnt == "exch":
                        if (m.group(3) == "(S2)" and not args.S2) or (m.group(3) != "(S2)" and args.S2):
                            continue
                    if m.group(2) == ",exch":
                        cmpnt = "ex" + cmpnt
                    # Another special case to decide whether or not to use S2 approx for exch-ind energy:
                    if cmpnt == "exind":
                        if (m.group(3) == "(S2)" and not args.S2) or (m.group(3) != "(S2)" and args.S2):
                            continue
                    if m.group(5) != "":
                        if m.group(5) in ["A","B"]:
                            cmpnt = cmpnt + m.group(5)
                    value = float(m.group(6))
                    inunit = m.group(8)
                    if verbosity > 0: print(f"{cmpnt:6s} {value:10.3f} {inunit:3s}")
                    u = units[inunit.lower()]
                    value = value*unit/u
                    ehf[cmpnt] = value
        #  Old output files may not have the full E^(1)_exch as well as E^(1)_exch(S2)
        if "exch" in ehf:
            try:
                energy[name]["dHF"] = ehf_diff \
                    - ehf["elst"] - ehf["exch"] - ehf["ind"] -ehf["exind"]
                energy[name]["err_dHF"] = False
            except:
                energy[name]["dHF"] = 0.0
                energy[name]["err_dHF"] = True
        else:
            if args.S2:
                print("No exch(S2) value in", path)
            else:
                print("No full exch value in", path)

    else:
        #  Normal sapt-dft
        with open(summary) as IN:
            for line in IN:
                                                                # Groups
                energies = re.compile(r'''E\^\{[12]\}             #     E^{n} where n = 1 or 2 
                                          \_\{(\w+)(\,exch)?\}    # 1 2 _{component} or _{component,exch}
                                          (\(S2\))?               # 3   match (S2) if present
                                          (\((A|B)\))?            # 4 5 match (A) or (B) if present
                                          \s+                     #     space. group(5) will be A or B.
                                          (-?\d+\.\d+(E[+-]\d+)?) # 6 7 match a floating point number of the
                                                                  #     form (-)mmmm.nnnnE(+|-)pp
                                                                  #     The exponential is optional and
                                                                  #     will be group(7)
                                          \s+                     #     space
                                          (\S+)                   # 8   text
                                          \s+                     #     more space
                                          ([\S,\s]*)              # 9   text with space
                                          ''',re.I|re.VERBOSE)
                m = energies.search(line)
                if m:
                    # print('GOT LINE ',line)
                    # print('Groups  1: ',m.group(1),' 2: ',m.group(2),' 3: ',m.group(3))
                    # print('Groups  4: ',m.group(4),' 5: ',m.group(5),' 6: ',m.group(6))
                    # print('Groups  7: ',m.group(7),' 8: ',m.group(8),' 9: ',m.group(9))
                    cmpnt = m.group(1)
                    # Special case to decide whether or not to use S2 approx for exchange energy:
                    if cmpnt == "exch":
                        if (m.group(3) == "(S2)" and not args.S2) or (m.group(3) != "(S2)" and args.S2):
                            continue
                    if m.group(2) == ",exch":
                        cmpnt = "ex" + cmpnt
                    # Another special case to decide whether or not to use S2 approx for exch-ind energy:
                    if cmpnt == "exind":
                        if (m.group(3) == "(S2)" and not args.S2) or (m.group(3) != "(S2)" and args.S2):
                            continue
                    # Special case for ind and exind: 
                    if cmpnt == "ind" or cmpnt == "exind":
                        # Search group(10) for the string: REG eta = <value>
                        if re.search(r' REG ', line):
                            reg = re.compile(r'''
                                REG\s+eta\s+=\s+         #    REG eta = 
                                (-?\d+\.\d+(E[+-]\d+)?)  # 1  value
                                              ''',re.I|re.VERBOSE)
                            mm = reg.search(m.group(9))
                            if mm:
                                if mm.group(1):
                                    eta = float(mm.group(1))
                                    if reg_eta == eta:
                                        cmpnt = cmpnt + "R"
                                    else:
                                        continue
                                else:
                                    continue
                            else:
                                continue
                    if m.group(5) != "":
                        if m.group(5) in ["A","B"]:
                            cmpnt = cmpnt + m.group(5)
                    value = float(m.group(6))
                    inunit = m.group(8)
                    if verbosity > 0: print(f"{cmpnt:6s} {value:10.3f} {inunit:3s}")
                    u = units[inunit.lower()]
                    value = value*unit/u
                    energy[name][cmpnt] = float(value)
        if args.dhf and "dHF" not in energy[name]:
            energy[name]["dHF"] = float(args.dhf)
        if "exch" not in energy[name]:
            if args.S2:
                print("No exch(S2) value in", path)
            else:
                print("No full exch value in", path)


if args.short:
    exind = []
    disp = ["DISP2"]
    if regularize:
        if args.ab:
            ind = ["IND2RA", "IND2RB"]
        else:
            ind = ["IND2R"]
    else:
        if args.ab:
            ind = ["IND2A", "IND2B"]
        else:
            ind = ["IND2"]
else:
    disp = ["disp","exdisp"]
    if regularize:
        if args.ab:
            ind = ["indRA","exindRA","indRB","exindRB"]
        else:
            ind = ["indR","exindR"]
    else:
        if args.ab:
            ind = ["indA","exindA","indB","exindB"]
        else:
            ind = ["ind","exind"]

display = ["elst","exch"] + ind
if show_dhf:
    display.append("dHF")
display += disp + ["E2int","Eint"]

if ct_reg:
    if args.ab:
        display_extra = ["ct2A","ct2B","CT2","pol2A","pol2B","POL2"]
    else:
        display_extra = ["CT2","POL2"]
else:
    display_extra = []

#  Output header
buffer = f"{args.unit:2s} " + " " * (max(name_len-len(args.unit)+4,0))
for s in display:
    if args.S2:
        if s == "exch":
            s = "exch(S2)"
        if s == "exind":
            s = "exind(S2)"
        if args.short:
            if s == "IND2":
                s = "IND2(S2)"
            if s == "IND2A":
                s = "IND2A(S2)"
            if s == "IND2B":
                s = "IND2B(S2)"
    buffer += f"{s:^9s}   "

for s in display_extra:
    buffer += f"{s:^9s}   "

if args.errors:
    buffer += "  err-dHF   err-E2int"

print(buffer.rstrip())

def add_energies(energy,name,elabel,elist,sign):
    """
        energy[name][elabel] = sum_i sign[i] * energy[name][i], i in elist
        if any energies are un-defined then
        energy[name]["err_E2int"] = True
    """
    energy[name][elabel] = 0.0
    for indx, e in enumerate(elist):
        if e in energy[name]:
            energy[name][elabel] += sign[indx] * energy[name][e]
        else:
            energy[name]["err_E2int"] = True
            break
    return

#  Output for each job (directories <d> and <d>_dHF together under <d>)
for name in sorted(energy.keys()):
    energy[name]["err_E2int"] = False
    energy[name]["err_dHF"]   = False

    buffer = ""
    if args.split:
        # print(args.split)
        m = re.match(args.split[0], name)
        if m:
            buffer = ""
            for i in range(1,len(args.split)):
                p = m.group(int(args.split[i]))
                buffer += f"  {p}"
    else:
        buffer = name
    buffer += " " * (name_len-len(buffer))
    if args.short:
        add_energies(energy,name,"IND2", ["ind","exind"],  [+1,+1])
        add_energies(energy,name,"IND2A",["indA","exindA"],[+1,+1])
        add_energies(energy,name,"IND2B",["indB","exindB"],[+1,+1])
        add_energies(energy,name,"DISP2",["disp","exdisp"],[+1,+1])
        if regularize:
            add_energies(energy,name,"IND2R", ["indR","exind"],   [+1,+1])
            add_energies(energy,name,"IND2RA",["indRA","exindRA"],[+1,+1])
            add_energies(energy,name,"IND2RB",["indRB","exindRB"],[+1,+1])
        #if not args.ab and "dHF" in energy[name]:
        #  energy[name]["IND"] += energy[name]["dHF"]
    if ct_reg:
        if "indRA" in energy[name] and "exindRA" in energy[name]:
            energy[name]["pol2A"] = energy[name]["indRA"] + energy[name]["exindRA"]
            energy[name]["ct2A"]  = energy[name]["indA"]  + energy[name]["exindA"] - energy[name]["pol2A"]
        else:
            energy[name]["pol2A"] = 0.0
            energy[name]["ct2A"]  = 0.0
        if "indRB" in energy[name] and "exindRB" in energy[name]:
            energy[name]["pol2B"] = energy[name]["indRB"] + energy[name]["exindRB"]
            energy[name]["ct2B"]  = energy[name]["indB"]  + energy[name]["exindB"] - energy[name]["pol2B"]
        else:
            energy[name]["pol2B"] = 0.0
            energy[name]["ct2B"]  = 0.0
        energy[name]["POL2"]  = energy[name]["pol2A"]  + energy[name]["pol2B"]
        energy[name]["CT2"]   = energy[name]["ct2A"]   + energy[name]["ct2B"]
    # Define the SAPT(DFT) interaction energy:
    E2int = 0.0
    Eint  = 0.0
    for cmpnt in saptdft:
        if cmpnt in energy[name]:
            Eint += energy[name][cmpnt]
        else:
            Eint = 0.0
            energy[name]["err_E2int"] = True
            break
    if "dHF" in energy[name]:
        E2int = Eint - energy[name]["dHF"]
    else:
        E2int = Eint
    # Check to see if we had an error in delta-HF:
    if energy[name]["err_dHF"]: 
        Eint = 0.0
    for cmpnt in display:
        if cmpnt == "E2int":
            buffer += f" {E2int:11.5f}"
        elif cmpnt == "Eint":
            buffer += f" {Eint:11.5f}"
        else:
            if cmpnt in energy[name]:
                if verbosity > 0: print(cmpnt, energy[name][cmpnt])
                buffer += f" {energy[name][cmpnt]:11.5f}"
            else:
                buffer += "       ---- "
    if ct_reg:
        for cmpnt in display_extra:
            if cmpnt in energy[name]:
                if verbosity > 0: print(cmpnt, energy[name][cmpnt])
                buffer += f" {energy[name][cmpnt]:11.5f}"
            else:
                buffer += "       ---- "

    if args.errors:
        if energy[name]["err_dHF"]:
            buffer += "       ERR"
        else:
            buffer += "       ..."
        if energy[name]["err_E2int"]:
            buffer += "       ERR"
        else:
            buffer += "       ..."

    print(buffer)

if args.errors:
    print("Summary of failures: ")
    print(" Error-dHF  Error-E2int :  Job name      ")
    for name in sorted(energy.keys()):
        if energy[name]["err_dHF"] or energy[name]["err_E2int"]:
            print(f' {energy[name]["err_dHF"]}       {energy[name]["err_E2int"]}       :  {name}  ')

