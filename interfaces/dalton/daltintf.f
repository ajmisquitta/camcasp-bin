      program dalt2sapt
      parameter (mxorb = 1024)  
      double precision  space( 4*(mxorb *(mxorb +1))/2)
      integer iunit77,iunit88, iunit99, ndim, norb, nbas, nfone,nfvect
      integer nocc, nvir
      integer nscfen, nfinfo
      double precision EMCSCF
      integer NOCCT, NORBT, NBAST
      common /dalton/ EMCSCF, NOCCT, NORBT, NBAST

      
      character*8 OVERLAP, KINETINT, ONEHAMIL, NEWORB
      character*8 SIR_IPH
      logical iprtvc, runsize
      
      namelist/input/ iprtvc,
     .                nfvect, nfone, nfinfo, runsize
c      common  /inpinfo/ iunit, iblk, isecv, mtypev,
c     .                  nfvect, nfone, nfinfo, iprtvc
c
      
      common /inpinfo/ iprtvc 
      
      data OVERLAP  /'OVERLAP '/, KINETINT /'KINETINT'/
      data ONEHAMIL /'ONEHAMIL'/
      data NEWORB   /'NEWORB  '/, SIR_IPH /'SIR IPH'/

      nfone=9
      nfvect=10
      nscfen=11
      nfinfo=12
      iunit77=77
      iunit88=88
      iunit99=99
      iprtvc=.false.
      runsize=.true.

      read(*,input)
      write(*,*) 'Input/defaults from namelist INPUT '
      write(*,*) '================================== '
      write(*,'(3(a,i2/), a,l2/ a,l2 )' )
     .   ' Vector output file:                  ',  nfvect,
     .   ' One-electron integral output file:   ',  nfone,
     .   ' Information output file:             ',  nfinfo,
     .   ' Print vectors:                       ',  iprtvc,
     .   ' Full run:                            ',  runsize
c      iprtvc=.true.
      open(unit=nfinfo,file='info.data',form='formatted',
     $     access='sequential')

        OPEN(UNIT=iunit88,FILE='SIRIUS.RST',STATUS='OLD',
     &           ACCESS='SEQUENTIAL',FORM='UNFORMATTED')
     
      call readnbas(iunit88,nbas)
      
      ndim=nbas
      norb=nbas
      ndim=norb*(norb+1)/2
     
      OPEN(UNIT=iunit77,FILE='AOONEINT',STATUS='OLD',
     &           ACCESS='SEQUENTIAL',FORM='UNFORMATTED')


      call readint(iunit77,ndim,space(1),OVERLAP)  
      call readint(iunit77,ndim,space(1+ndim),KINETINT)
      call readint(iunit77,ndim,space(1+2*ndim),ONEHAMIL)
      
      open(unit=nfone ,file='onel.data',form='unformatted')
      call writeint(nfone,ndim,space(1),space(1+ndim),space(1+2*ndim),
     *                   space(1+3*ndim))

C --If doing a monoplus run, echo out the total number of basis 
C   functions to info.data for use by the transformation to calculate 
C   the number of overlapping midbond functions.   The total # of
C   basis functions in a DC+BS run - the # of basis functions in the
C   SCF A run - the # in the SCF B run should be the number of over
C   lapping functions.  Hayes
      if (.NOT.runsize) WRITE(nfinfo,*) nbas



      OPEN(UNIT=iunit99,FILE='SIRIFC',STATUS='OLD',
     &           ACCESS='SEQUENTIAL',FORM='UNFORMATTED',ERR=1000)

      call readen(iunit99, space(1), SIR_IPH)
      close(iunit99)
      OPEN(UNIT=nscfen,FILE='scfener.data.dalton',
     $     ACCESS='SEQUENTIAL',FORM='formatted',STATUS='unknown')
      WRITE(nscfen,'(d25.15)') EMCSCF
      close(nscfen)
      
      
     

      
       norb=NORBT
       nbas=NBAST
       ndim=norb*(norb+1)/2
       
       nocc=NOCCT
       nvir=norb-nocc

      write(*,'(/  2(a,i3) )' )
     .    ' Number of occupied orbitals: ', nocc,
     .    ' Number of virtual  orbitals: ', nvir
      
      
       if (runsize) then      
        write(nfinfo,*) norb, nocc, nvir
c The rest of the parameters must be written by gawk
     
        call getorben(space(1), space(ndim+1), norb)
      
     
        open(unit=nfvect ,file='vect.data',form='unformatted')
        call wrsa(norb, space(ndim+1), nfvect) ! energies to nfvect
     
     
      

        call readmo(iunit88, norb, nbas, space(1), NEWORB)
      
        close(iunit88)
      
      
      
      
        call wrsa(norb*nbas, space(1), nfvect) ! and also orbitals

        close(nfvect)
      end if
      
      goto 2000
      
1000  continue

      if (.not.runsize) then
        write(*,*)'SIRIFC not found, reading MO properties skipped'
      else
        write(*,*)'SIRIFC not found but is required! '      
        stop
      end if
      
2000  continue
      
      end
     
      subroutine getorben(fc, evalue, norb)
      double precision fc, evalue
      integer norb
      dimension fc(norb*(norb+1)/2), evalue(norb)
      
      integer i,j, ind
      
      ind=0
      do i=1,norb
        do j=1,i
	  ind=ind+1
	  if (i.eq.j) then
	    evalue(i)=fc(ind)
	  end if
	end do
      end do
      
      write(*,'(/a/a/ 5(f12.5,2x)       )')
     .    ' Orbital energies ',
     .    ' ================ ',
     .     (evalue(i),i=1,norb)

      
      end
      

      subroutine readnbas(iunit,nbas)
      character*8 label
      DATA label /'BASINFO '/
      integer ndim,i
      logical findlab
      
      if (findlab(label,iunit)) goto 100
      write(*,*) 'Error finding label', label
      STOP
100   continue
      read (iunit) NSYM,NBAS,NORB,NRHF,IOPRHF
      write(*,*)NSYM,NBAS,NORB,NRHF,IOPRHF
      end

      
      
     
      subroutine readint(iunit,ndim,v,label)
      character*8 label
      integer ndim,i
      double precision v
      dimension v(ndim)
      double precision BUF
      logical findlab
      integer IBUF, icount
      DIMENSION BUF(600), IBUF(600)
      
      do i=1,ndim
        v(i)=0
      end do
      
      if (findlab(label,iunit)) goto 100
      write(*,*) 'Error finding label', label
      STOP
100   continue
      read(iunit) buf, ibuf, icount
c      write(*,*)icount,' integrals read'
      do i=1,icount
c        write(*,*)ibuf(i), buf(i)
	v(ibuf(i))=buf(i)
      end do
      if (icount.ne.-1) go to 100
      end
    
      
      subroutine writeint(nfone,ndim,s,t,h,v)
 
C     Actual read of integrals, write to NFONE
      integer nfone, ndim
      double precision s,t,h,v
      dimension s(ndim), t(ndim), h(ndim), v(ndim)

      character*8 OVERLAP, KINETINT, POTENTAL, ONEHAMIL
      logical iprtvc
      common /inpinfo/ iprtvc 
      
      data OVERLAP  /'OVERLAP '/, KINETINT /'KINETINT'/
      data POTENTAL /'POTENTAL'/, ONEHAMIL /'ONEHAMIL'/
      
      write(nfone)   OVERLAP , ndim, s
      if (iprtvc) call chkprint(OVERLAP,ndim,s)
      write(nfone)  KINETINT , ndim, t
      if (iprtvc) call chkprint(KINETINT,ndim,t)
      do i=1,ndim
         v(i) = h(i) - t(i)
      enddo
      write(nfone)  POTENTAL , ndim, v
      if (iprtvc) call chkprint(POTENTAL,ndim,v)
      write(nfone)  ONEHAMIL , ndim, h
      if (iprtvc) call chkprint(ONEHAMIL,ndim,h)
 
      write(*,'(/a,i2  )' )
     .    ' One-electron matrices written to unit ', nfone
 
      end

      subroutine readmo(iunit, norb, nbas, cmo, label)
      
      integer iunit, norb, nbas
      double precision cmo
      dimension cmo(norb*nbas)
      logical findlab, iprtvc
      common /inpinfo/ iprtvc 
      
      character*8 label
      
      if (findlab(label,iunit)) goto 100
      write(*,*) 'Error finding label', label
      STOP
100   continue

      read (iunit) cmo
      write(*,*)norb*nbas, ' molecular orbitals read'
c     i counts MO orbitals, j AO basis functions
c      do i=1,norb
c        do j=1, nbas
c	  write(*,*)i,j,cmo((i-1)*nbas + j)
c        end do
c      end do
      
      if (iprtvc) then
         write(*,'(/1x,t40,a )') 'Orbitals'
         write(*,'( 1x,t40,a )') '========'
         call  writem(cmo,norb,nbas)    ! write them to screen
      endif

      
      end
      
      logical function findlab(label, labelunit)
      character*8 label, stars, b(4)
      parameter (stars = '********')
      
      rewind(labelunit)
10    read (labelunit, END=100, ERR=50) b
      if (b(1).ne.stars) go to 10
      if (b(4).ne.label) go to 10
      findlab=.true.
      return
50    continue
100   continue
      findlab=.false.
      return
      end
      
      subroutine writem(p,n1,n2)
 
C     Print matrix of dimension n1 x n2 in lines.
 
      implicit double precision (a-h,o-z)
      parameter (lline = 5)          ! length print line
      dimension p(n1,n2)
 
      n = 0
      do m=1,n2,lline
         n = min( n + lline,  n2 )
         write(*, '(/3x,8i14)' ) (i,i=m,n)
         do j=1,n1
            write(6,'(3x,i3,8f14.7 )') j, (p(j,i),i=m,n)
         enddo
      enddo
      write(*, '(/)')
 
      end
      subroutine wrsa(n, p, nf)
C --Write P to a sequential access file.
      double precision p(n)
      write(nf) p
      end
      subroutine rdsa(n, p, nf)
C --read P from a sequential access file.
      double precision p(n)
      read(nf) p
      end
C
      
      
      SUBROUTINE CHKPRINT(NAME, NUMBER, A)
      double precision a
      CHARACTER*8 NAME
      DIMENSION A(*)
 
      WRITE(*,*) '   ',NAME
      WRITE(*,*) '================='
      WRITE(*,*) '  *** OUTPUT *** '
      WRITE(*,*) 'NUMBER OF ELEMENTS', NUMBER
      WRITE(*,23) (A(I), I=1,NUMBER)
23             FORMAT(1X,4D18.7)
      RETURN
      END


      subroutine readen(iunit, space, label)
      implicit double precision (a-h,o-z)
      integer iunit
      double precision space
      dimension space(*)
      character*8 label
      character*8 lab123, lbsifc
      
      double precision EMCSCF
      integer NOCCT, NORBT, NBAST
      common /dalton/ EMCSCF, NOCCT, NORBT, NBAST
      
      
c mostly uninteresting parameters
c except
c POTNUC = nuclear energy
c EMCSCF = SCF energy
c NOCCT  = number of occupied orbitals
c NORBT  = total number of orbitals
c NBAST  = total number of basis functions

      read (iunit) LAB123,LBSIFC
      read (iunit) POTNUC,EMY,EACTIV,EMCSCF,
     *               ISTATE,ISPIN,NACTEL,LSYM
      read (iunit) NISHT,NASHT,NOCCT,NORBT,NBAST,NCONF,NWOPT,NWOPH,
     *               NCDETS, NCMOT,NNASHX,NNASHY,NNORBT,N2ORBT,
     *               NSYM,MULD2H, NRHF,NFRO,
     *               NISH,NASH,NORB,NBAS,
     *               NELMN1, NELMX1, NELMN3, NELMX3, MCTYPE,
     *               NAS1, NAS2, NAS3

      WRITE (*,*) LAB123,LBSIFC
      WRITE (*,*) POTNUC,EMY,EACTIV,EMCSCF,
     *               ISTATE,ISPIN,NACTEL,LSYM
      WRITE (*,*) NISHT,NASHT,NOCCT,NORBT,NBAST,NCONF,NWOPT,NWOPH,
     *               NCDETS, NCMOT,NNASHX,NNASHY,NNORBT,N2ORBT,
     *               NSYM,MULD2H, NRHF,NFRO,
     *               NISH,NASH,NORB,NBAS,
     *               NELMN1, NELMX1, NELMN3, NELMX3, MCTYPE,
     *               NAS1, NAS2, NAS3


C
C 880920-hjaaj: later write label here for orbitals
C
      NC4    = MAX(4,NCONF)
      NW4    = MAX(4,NWOPT)
      NWH4   = MAX(4,NWOPH)
      NCMOT4 = MAX(4,NCMOT)
      MMORBT = MAX(4,NNORBT)
      M2ORBT = MAX(4,N2ORBT)
      MMASHX = MAX(4,NNASHX)
      MMASHY = MAX(4,NNASHY)
      M2ASHY = MAX(4,NNASHX*NNASHX)
C
c      CALL rdsa (NCMOT4,space(1),iunit)
c      call chkprint('CMO     ',ncmot4,space(1))
c      CALL rdsa (MMASHX,space(1), iunit)
c      call chkprint('DV      ',mmashx,space(1))
c      CALL rdsa (M2ORBT,space(1),iunit)
c      call chkprint('FOCK    ',m2orbt,space(1))
c      CALL rdsa (M2ASHY,space(1), iunit)
c      call chkprint('PV      ',m2ashy,space(1))
      read(iunit)
      read(iunit)
      read(iunit)
      read(iunit)
c comment the line below for Dalton 1.2      
      read(iunit)
      CALL rdsa (MMORBT,space(1), iunit)
c The above matrices are not used
c The orbital energies are on the diagonal of the Fock matrix below
c      call chkprint('FC      ',mmorbt,space(1))
      
      if (norbt*(norbt+1)/2 .ne. nnorbt) then
        write(*,*) 'Size mismatch reading Dalton orbital energies'
	stop
      end if
      
      end