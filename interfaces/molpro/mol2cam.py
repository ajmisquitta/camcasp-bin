#!/usr/bin/env python
import sys

outfil=sys.argv[1]
wfu=sys.argv[2]

def read_nmos(wfu):
    f=open(wfu)
    line=f.readline()
    line=f.readline()
    data=line.split()
    nmos=int(data[0])
    f.close()
    return nmos

def read_eigs(wfu,nmos):
    eigs=[]
    f=open(wfu)
    lread=False
    for line in f.readlines():
        if "EIG" in line and "CANONICAL" in line:
            lread=True
            continue
        if not lread:
            continue
        if lread and len(eigs)==nmos:
            lread=False
            break
        line=line.strip()        
        data=line.split(",")
        data=data[:-1]
        data=[d.replace("D","E") for d in data]
        data=[float(d) for d in data]
        eigs=eigs+data
    f.close()
    if len(eigs)!=nmos:
        sys.exit("could not read eigenvalues from wfu file")
    return eigs

def read_mos(wfu,nmos):
    orbs=[]
    f=open(wfu)
    lread=False
    for line in f.readlines():
        if "ORBITALS" in line and "CANONICAL" in line:
            lread=True
            continue
        if not lread:
            continue
        if lread and len(orbs)==nmos*nmos:
            lread=False
            break
        line=line.strip()        
        data=line.split(",")
        data=data[:-1]
        data=[d.replace("D","E") for d in data]
        data=[float(d) for d in data]
        orbs=orbs+data
    f.close()
    if len(orbs)!=nmos*nmos:
        sys.exit("could not read orbitals from wfu file")
    return orbs

def read_aos(outfil):
    f=open(outfil,"r")
    lread=False
    nmos=None
    aos=[]
    for line in f.readlines():
        if "BASIS DATA" in line:
            lread=True
            continue
        if "NUMBER OF CONTRACTIONS" in line:
            data=line.split()
            nmos=int(data[3])
            continue
        if not lread or "Nr Sym  Nuc" in line:
            continue
        data=line.split()
        if "NUCLEAR CHARGE" in line:
            lread=False
            continue
        if len(data)<4:
            continue
        if "s" in data[3] or "p" in data[3] or "d" in data[3] or \
           "f" in data[3] or "g" in data[3] or "h" in data[3]:
            aos.append(data[3])
            continue
        elif data[1]=="A": #contracted func
            lastFunc=aos[-1]
            aos.append(lastFunc)
        #print line
    f.close()    
    if len(aos)!=nmos:
        print aos
        print len(aos)
        sys.exit("could not read aos correctly")
    return aos,nmos


def order_sphericals(aos):
    """Molpro has orders
          d0,d2-,d1+,d2+,d1-
          f1+,f1-,f0,f3+,f2-,f3-,f2+
          g0,g2-,g1+,g4+,g1-,g2+,g4-,g3+,g3-
          h1+,h1-,h2+,h3+,h4-,h3-,h4+,h5-,h0,h5+,h2-
       iorder to, e.g.:
         d2-,d1-,d0,d1+,d2+          
    """
    n=len(aos)
    iorder=n*[None]
    for i in range(n):
        ao=aos[i]
        #print i,ao
        if "s" in ao or "p" in ao:
            iorder[i]=i
        elif "d0" in ao:
            iorder[i]=i+2
        elif "d2-" in ao:
            iorder[i]=i-1
        elif "d1+" in ao:
            iorder[i]=i+1
        elif "d2+" in ao:
            iorder[i]=i+1
        elif "d1-" in ao:
            iorder[i]=i-3

        elif "f1+" in ao:
            iorder[i]=i+4
        elif "f1-" in ao:
            iorder[i]=i+1
        elif "f0" in ao:
            iorder[i]=i+1
        elif "f3+" in ao:
            iorder[i]=i+3
        elif "f2-" in ao:
            iorder[i]=i-3
        elif "f3-" in ao:
            iorder[i]=i-5
        elif "f2+" in ao:
            iorder[i]=i-1
            
        elif "g0" in ao:
            iorder[i]=i+4
        elif "g2-" in ao:
            iorder[i]=i+1
        elif "g1+" in ao:
            iorder[i]=i+3
        elif "g4+" in ao:
            iorder[i]=i+5
        elif "g1-" in ao:
            iorder[i]=i-1
        elif "g2+" in ao:
            iorder[i]=i+1
        elif "g4-" in ao:
            iorder[i]=i-6
        elif "g3+" in ao:
            iorder[i]=i
        elif "g3-" in ao:
            iorder[i]=i-7

        elif "h1+" in ao:
            iorder[i]=i+6
        elif "h1-" in ao:
            iorder[i]=i+3
        elif "h2+" in ao:
            iorder[i]=i+5
        elif "h3+" in ao:
            iorder[i]=i+5
        elif "h4-" in ao:
            iorder[i]=i-3
        elif "h3-" in ao:
            iorder[i]=i-3
        elif "h4+" in ao:
            iorder[i]=i+3
        elif "h5-" in ao:
            iorder[i]=i-7
        elif "h0" in ao:
            iorder[i]=i-3
        elif "h5+" in ao:
            iorder[i]=i+1
        elif "h2-" in ao:
            iorder[i]=i-7
        else:
            sys.exit("ao type not implemented: ",ao)        
    iorderInv=n*[None]
    for i in range(n):
        iorderInv[iorder[i]]=i
    if False:
        for i in range(n):
            j=iorderInv[i]
            print i,j,aos[j]
        print iorder
    return iorderInv    

def reorder_coeffVec(vec,iorder):
    n=len(vec)
    vecOrd=n*[None]
    for i in range(n):
        j=iorder[i]
        vecOrd[i]=vec[j]
    return vecOrd

def reorder_coeffMat(coeff,iorder):
    n=len(iorder)
    for i in range(n):
        c=reorder_coeffVec(coeff[i],iorder)
        coeff[i]=c[:]
    return coeff

def write_movecs(eigs,orbs,name):
    nmos=len(eigs)
    f=open(name,"w")
    f.write("Source \n")
    f.write("Title \n")
    f.write("Code      Molpro \n")
    f.write("BFNS      %i\n" % (nmos))
    f.write("NMOS      %i\n" % (nmos))
    f.write("Energies  %i\n" % (nmos))
    j=0
    for i in range(nmos):
        f.write("%24.15E" % (eigs[i]))
        j+=1
        if j==5:
            j=0
            f.write("\n")
    if j!=0:
        f.write("\n")
    for imo in range(nmos):
        f.write("MO %i   Energy %24.15E\n" % (imo+1,eigs[imo]))
        j=0
        for i in range(nmos):
            f.write("%24.15E" % (orbs[imo][i]))
            j+=1
            if j==5:
                j=0
                f.write("\n")
        if j!=0:
            f.write("\n")
    f.write("END\n")
    f.close()

def main():
    if len(outfil.split('_A'))>1:
        name=outfil.split('_A')[0]
        mon="A"
        name=name+"-"+mon
    elif len(outfil.split('_B'))>1:
        name=outfil.split('_B')[0]
        mon="B"
        name=name+"-"+mon
    else:
        name=outfil.split('.')[0]
    nmos=read_nmos(wfu)
    print "Number of MOs: ",nmos

    eigs=read_eigs(wfu,nmos)
    orbs=read_mos(wfu,nmos)
    orbs=[orbs[i:i+nmos] for i in range(0,len(orbs),nmos)]

    aos,n=read_aos(outfil)
    if n!=nmos: sys.exit("number of MOs in output and wfu file differ")
    #print aos
    print "Transform Molpro orbital coeffs to CamCasp format..."

    #reorder ao coeffs
    iorder=order_sphericals(aos)
    orbs=reorder_coeffMat(orbs,iorder)
    #print orbs[0]
    write_movecs(eigs,orbs,name+"-asc.movecs")
    
main()



