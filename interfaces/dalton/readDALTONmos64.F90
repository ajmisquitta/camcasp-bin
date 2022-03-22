program readDALTONmos
!--------------------
!A. J. Misquitta
!--------------------
!This interface uses files: SIRIUS.RST and SIRIFC
!Based on the interface written by Rafal Podeszwa
!
use precision, only: dp, si, li
use input_parser, only: die, read_line, reada, readi, uppercase, item, nitems
implicit none

!  Long (64-bit) integers. Use ki=si for 32-bit integers.
integer, parameter :: ki=li
! The Fock matrix should be diagonal for canonical MOs
! We use only the diagonal part of the matrix which will contain the MO energies
! fock is a 2-d matrix stored as 1-D in upper-triangular form.
real(dp), dimension(:), allocatable :: fock, En
!MO coefficients go here:
real(dp), dimension(:,:), allocatable :: Cmo
!
integer(ki)  :: NOCCT, NORBT, NBAST ! number of occupied MOs, MOs and basis funcs
real(dp) :: EMCSCF !SCF energy
real(dp) :: POTNUC !Nuclear potential energy
integer(ki) :: ndim, norb, nbas, nocc, nvir
integer :: nbasC, nelec, nelecA, nelecB
!Unit numbers
integer, parameter :: iunit88=88, iunit99=99
integer, parameter :: iunitvect = 2  !output unit for MO file
integer, parameter :: iunitout  = 6  !output unit for STD I/O
character(80) :: vect_file = '', asc_file = ''
!Default data file names:
character(80) :: RSTfile    = 'SIRIUS.RST'
character(80) :: SIRIFCfile = 'SIRIFC'
!Other data:
character(80) :: SCFcode = 'DALTON'
character(80) :: SCFtype = '', basis_name = '', title = ''
!Control flags:
logical :: testcode = .true.
logical :: verbose = .true.
!
integer :: info, arg, arglen, ok, lrec, m
logical :: eof, err, debug=.false.
character(80) :: word
!------------

print "(/a/)", "Dalton interface to CamCASP"

if (command_argument_count()>0) then
  arg=0
  do while(arg<command_argument_count())
    arg=arg+1
    call get_command_argument(arg,word,arglen,ok)
    if (ok .ne. 0) call die("Argument too long for buffer",.true.)
    select case(uppercase(word))
    case default
      call die("Don't understand "//trim(word))
    case('--RST')
      arg=arg+1
      call get_command_argument(arg,RSTfile,arglen,ok)
      if (ok .ne. 0) call die("Argument too long for buffer",.true.)
    case('--SIRIFC')
      arg=arg+1
      call get_command_argument(arg,SIRIFCfile,arglen,ok)
      if (ok .ne. 0) call die("Argument too long for buffer",.true.)
    case('--TITLE')
      arg=arg+1
      call get_command_argument(arg,title,arglen,ok)
      if (ok .ne. 0) call die("Argument too long for buffer",.true.)
    case('--NELECA','--ALPHA')
      arg=arg+1
      call get_command_argument(arg,word,arglen,ok)
      if (ok .ne. 0) call die("Argument too long for buffer",.true.)
      read(word,'(i9)')nelecA
    case('--NELECB','--BETA')
      arg=arg+1
      call get_command_argument(arg,word,arglen,ok)
      if (ok .ne. 0) call die("Argument too long for buffer",.true.)
      read(word,'(i9)')nelecB
    case('--NELEC')
      arg=arg+1
      call get_command_argument(arg,word,arglen,ok)
      if (ok .ne. 0) call die("Argument too long for buffer",.true.)
      read(word,'(i9)')nelec
    case('--NBAS','--BASIS-SIZE')
      arg=arg+1
      call get_command_argument(arg,word,arglen,ok)
      if (ok .ne. 0) call die("Argument too long for buffer",.true.)
      read(word,'(i9)')nbas
    case('--NBAS-CART','--CART-BASIS-SIZE')
      arg=arg+1
      call get_command_argument(arg,word,arglen,ok)
      if (ok .ne. 0) call die("Argument too long for buffer",.true.)
      read(word,'(i9)')nbasC
    case('--NMOS')
      arg=arg+1
      call get_command_argument(arg,word,arglen,ok)
      if (ok .ne. 0) call die("Argument too long for buffer",.true.)
      read(word,'(i9)')norb
    case('--BASIS-NAME')
      arg=arg+1
      call get_command_argument(arg,basis_name,arglen,ok)
      if (ok .ne. 0) call die("Argument too long for buffer",.true.)
    case("--TO","--BINARY")
      !  Create vect.data file
      arg=arg+1
      call get_command_argument(arg,vect_file,arglen,ok)
      if (ok .ne. 0) call die("Argument too long for buffer",.true.)
    case("--ASCII")
      arg=arg+1
      call get_command_argument(arg,asc_file,arglen,ok)
      if (ok .ne. 0) call die("Argument too long for buffer",.true.)
    case("--QUIET")
      verbose=.false.
    case("--HELP")
      print "(a)", "Usage:",                                                 &
        "readDALTONmos --rst <SIRIUS.RST> --sirifc <SIRIFC>               ", &
        "[--quiet] [--ascii <name>] [--binary <name>]                     ", &
        "--nelec <num electrons> --nbas <num basis funcs>                 ", &
        "--nbas-cart <num Cartesian basis funcs> --nmos <number of MOs>   ", &
        "MOs can be written out in ASCII and/or BINARY format using the   ", &
        "--ascii and --binary options together with file names.           "
      stop
    end select
  end do
else
  input_loop: do
    call read_line(eof)
    if (eof) exit input_loop
    do while (item<nitems)
      call reada(word)
      select case(uppercase(word))
      case("RST")
        call reada(RSTfile)
        if (verbose) print "(2a)", "File ", trim(RSTfile)
      case("SIRIFC")
        call reada(SIRIFCfile)
        if (verbose) print "(2a)", "File ", trim(SIRIFCfile)
      case('NELECA','ALPHA')
        call readi(nelecA)
      case('NELECB','BETA')
        call readi(nelecB)
      case('NELEC')
        call readi(nelec)
      case('NBAS')
        call readi(nbas)
      case('NBAS-CART')
        call readi(nbasC)
      case('NMOS')
        call readi(norb)
      case('BASIS-NAME')
        call reada(basis_name)
      case("TO","BINARY")
        call reada(vect_file)
      case("ASCII")
        call reada(asc_file)
      case("QUIET")
        verbose=.false.
      case("GO")
        exit input_loop
      case default
        call die("Don't understand "//trim(word),.true.)
      end select
    end do
  end do input_loop
end if
!
!-----------------------------------------------------------------------------
!
open(unit=iunit88,file=RSTfile,status='old',access='sequential',form='unformatted')
!Read in the number of basis functions and the number of MOs. These will not be
!equal if the basis had linear dependencies that had to be removed. In all cases
!we should have norb <= nbas
call readnbas(iunit88,nbas,norb,debug,info)
if (info/=0) then
  write(*,*)'ERROR in DALTON interface program: sub readnbas  info=',info
  stop
endif
!  print "(a, 2i6)", "nbas,norb: ", nbas,norb
!  The above subroutine may or may not read norb and nbas correctly.
!  (They may be the wrong way round.) So we read them from the SIRIFC file.
!  Read in the Fock matrix fock():
open(unit=iunit99,file=SIRIFCfile,status='old',access='sequential',form='unformatted')
call readen(iunit99,POTNUC,EMCSCF,NOCCT,NORBT,NBAST,info)
close(iunit99)
!  print "(a, 3i6)", "NOCCT,NORBT,NBAST: ", NOCCT,NORBT,NBAST
if (info/=0) then
  write(*,*)'ERROR in DALTON interface program: sub readen  info=',info
  stop
endif
!
norb = NORBT
nbas = NBAST
!
!  Now we have nbas and norb so we can read in the orbital coefficients.
!  These will be in an array: nbas x norb. 
allocate(Cmo(nbas,norb),stat=info)
if (info/=0) then
  write(*,*)'ALLOCATION ERROR: Cmo (nbas,norb)=',nbas,norb,'  info=',info
  stop
endif
call readmo(iunit88,norb,nbas,Cmo,debug,info)
close(iunit88)
if (info/=0) then
  write(*,*)'ERROR in DALTON interface program: sub readmo  info=',info
  stop
endif
!
err = .false.
! if (nbas/=NBAST) then
!   write(*,*)'ERROR: Number of basis functions in SIRIUS.RST <> SIRIFC'
!   write(*,*)'       nbas in SIRIUS.RST = ',nbas
!   write(*,*)'       nbas in SIRIFC     = ',NBAST
!   err = .true.
! endif
! if (norb/=NORBT) then
!   write(*,*)'ERROR: Number of MOs in SIRIUS.RST <> SIRIFC'
!   write(*,*)'       norb in SIRIUS.RST = ',norb
!   write(*,*)'       norb in SIRIFC     = ',NORBT
!   err = .true.
! endif
if (nbas<norb) then
  write(*,*)'ERROR: Number of basis functions less than MOs'
  write(*,*)'       nbas = ',nbas
  write(*,*)'       norb = ',norb
  err = .true.
endif
if (err) then
  write(*,*)'Stopping in DALTON interface'
  stop
endif
!
!nocc=NOCCT
!norb=NORBT
!nbas=NBAST
!nvir=norb-nocc
!ndim=norb*(norb+1)/2
nocc=NOCCT
nvir=norb-nocc
ndim=norb*(norb+1)/2
!
write(*,'(a)')'Summary:'
write(*,'(a,i6)')' Number of occupied orbitals : ', nocc
write(*,'(a,i6)')' Number of virtual  orbitals : ', nvir
write(*,'(a,i6)')' Number of molecular orbitals: ', norb
write(*,'(a,i6)')' Number of basis functions   : ', nbas
write(*,'(a,e14.6,a)')' SCF energy                 : ', EMCSCF,' Hartree'
write(*,'(a,e14.6,a)')' Nuclear potential energy   : ', POTNUC,' Hartree'

!Now fill in the orbital energies which are on the diagonal of the Fock matrix:      
allocate(En(norb),stat=info)
if (info/=0) then
  write(*,*)'ALLOCATION ERROR: En norb=',norb,'  info=',info
  stop
endif
call getorben(fock,En,norb,debug)
!
!==============================================================================
!Now we have all the information we need. Write this out in the BINARY or ASCII-2 formats
!
if (vect_file .ne. "") then
  inquire(iolength=lrec) Cmo(:,:)
  if (verbose) print "(2a,i0)", trim(vect_file), " record length = ", lrec
  open (unit=18,file=vect_file,form="unformatted",recl=lrec,iostat=ok)
  if (ok>0) call die("Can't open "//trim(vect_file))
  write(18) En(:)
  write(18) Cmo(:,:)
  close (18)
end if

if (asc_file .ne. "") then
  open (unit=18,file=asc_file, recl=255,iostat=ok)
  if (ok>0) call die("Can't open "//trim(asc_file))
  write (18,"(2a)") "Source    ", trim(RSTfile)//" and "//trim(SIRIFCfile)
  write (18,"(2a)") "Title     ", trim(title)
  write (18,"(2a)") "Code      ", trim(SCFcode)
  write (18,"(2a)") "Basis     ",  trim(basis_name)
  write (18,"(a,i0)") "BFNS      ", nbas
  write (18,"(a,i0)") "NMOS      ", norb
  write (18,"(a,i0)") "Energies  ", norb
  write (18,"(1p,(5e24.15))") En(1:norb) 
  do m=1,norb
    write (18,"(a,i0,a,1p,e24.15)") "MO ", m, "   Energy ", En(m)
    write (18,"(1p,(5e24.15))") Cmo(:,m)
  end do
  write (18,"(a)") "END"
  close(18)
end if
     
contains

  subroutine getorben(fc,evalue,norb,debug)
  !Obtain orbital energies from Fock Matrix (upper triangle)
  implicit none
  integer(ki), intent(in) :: norb
  real(dp), dimension (:), intent(in) :: fc
  real(dp), dimension(:), intent(out) :: evalue
  logical, intent(in) :: debug
  !------------
  integer(ki) i,j, ind
  !------------
  ind=0
  do i=1,norb
    do j=1,i
      ind=ind+1
      if (i.eq.j) then
        evalue(i)=fc(ind)
      end if
    end do
  end do
  if (debug) then
    write(*,'(/a/a/ 5(f12.5,2x)       )') &
     ' Orbital energies ', &
     ' ================ ', &
      (evalue(i),i=1,norb)
  endif
  return 
  end subroutine getorben
     
  subroutine readnbas(iunit,nbas,norb,debug,info)
  !Read basis size from file.
  implicit none
  integer, intent(in) :: iunit
  integer(ki), intent(out) :: nbas, norb
  logical, intent(in) :: debug
  integer, intent(out) :: info
  !------------
  character(8), parameter :: label = 'BASINFO '
  integer :: nsym, dummy(26)
  !------------
  info = 0
  if (.not.findlab(label,iunit)) then
    write(*,*) 'Error finding label', label
    info = -1
    return
  else
    read (iunit) dummy
    nsym=dummy(1)
    nbas=dummy(2)
    norb=dummy(10)
  endif
  if (debug) then
    write(*,*)'Number of symmetry orbitals : ',NSYM
    write(*,*)'Number of basis functions   : ',NBAS
    write(*,*)'Number of orbitals          : ',NORB
    ! write(*,*)' NRHF,IOPRHF                : ',NRHF,IOPRHF
  endif
  return
  end subroutine readnbas

  subroutine readmo(iunit,norb,nbas,Cmo,debug,info)
  implicit none      
  integer, intent(in) :: iunit
  integer(ki), intent(in) :: norb, nbas
  real(dp), dimension(:,:), intent(out) :: Cmo
  logical, intent(in) :: debug
  integer, intent(out) :: info
  !------------
  integer(ki) :: i, m
  character(8), parameter :: label = 'NEWORB  '
  !------------
  if (.not.findlab(label,iunit)) then
    write(*,*) 'ERROR reading MOs: Error finding label', label
    info = -1
    return
  else
    read (iunit) ((Cmo(m,i),m=1,nbas),i=1,norb)
  endif
  if (debug) then
     write(*,'(/1x,t40,a )') 'Orbitals'
     write(*,'( 1x,t40,a )') '========'
     call  writem(Cmo,nbas,norb)
  endif
  return
  end subroutine readmo
     
  subroutine writem(p,n1,n2)
  !Print matrix of dimension n1 x n2 in lines.
  implicit none
  integer(ki), intent(in) :: n1, n2
  real(dp), dimension(n1,n2), intent(in) :: p
  !------------
  integer, parameter :: lline = 5    ! length print line
  integer :: n, m, i, j
  !------------
  n = 0
  do m=1,n2,lline
     n = min( n + lline,  n2 )
     write(*, '(/3x,8i14)' ) (i,i=m,n)
     do j=1,n1
        write(6,'(3x,i3,8f14.7 )') j, (p(j,i),i=m,n)
     enddo
  enddo
  write(*, '(/)')
  return
  end subroutine writem

  subroutine wrsa(n, p, nf)
  !Write P to a sequential access file.
  implicit none
  integer(ki), intent(in) :: n, nf
  real(dp), dimension(n), intent(out) :: p
  !------------
  write(nf) p
  return
  end subroutine wrsa

  subroutine rdsa(n, p, nf)
  !Read P from a sequential access file.
  implicit none
  integer(ki), intent(in) :: n
  integer, intent(in) :: nf
  real(dp), dimension(n), intent(out) :: p
  !------------
  read(nf) p
  return
  end subroutine rdsa
      
  subroutine readen(iunit,POTNUC,EMCSCF,NOCCT,NORBT,NBAST,info)
  ! Output:
  ! POTNUC = nuclear energy
  ! EMCSCF = SCF energy
  ! NOCCT  = number of occupied orbitals
  ! NORBT  = total number of orbitals
  ! NBAST  = total number of basis functions
  !Will also define and fill up the Fock matrix fock()
  implicit none
  integer, intent(in) :: iunit
  real(dp), intent(out) :: POTNUC, EMCSCF
  integer(ki), intent(out) :: NOCCT, NORBT, NBAST
  integer, intent(out) :: info
  !------------
  character(8), parameter :: SIR_IPH = 'SIR IPH'
  character(8) lab123, lbsifc
  !Dummy variables
  real(dp) :: EMY,EACTIV
  integer :: ISTATE,ISPIN,NACTEL,LSYM
  integer(ki) :: NISHT,NASHT,NCONF,NWOPT,NWOPH
  integer(ki) :: NCDETS, NCMOT,NNASHX,NNASHY,NNORBT,N2ORBT
  integer(ki) :: NSYM,MULD2H, NRHF,NFRO,NISH,NASH,NORB,NBAS
  integer(ki) :: NELMN1, NELMX1, NELMN3, NELMX3, MCTYPE,NAS1, NAS2, NAS3
  integer(ki) :: MMORBT
  !------------
  info = 0
  !
  read(iunit) LAB123,LBSIFC
  read(iunit) POTNUC,EMY,EACTIV,EMCSCF,ISTATE,ISPIN,NACTEL,LSYM
  read(iunit) NISHT,NASHT,NOCCT,NORBT,NBAST,NCONF,NWOPT,NWOPH, &
      NCDETS, NCMOT,NNASHX,NNASHY,NNORBT,N2ORBT,NSYM,MULD2H,   &
      NRHF,NFRO, NISH,NASH,NORB,NBAS,NELMN1, NELMX1,           &
      NELMN3, NELMX3, MCTYPE, NAS1, NAS2, NAS3
  !
  write(*,*) LAB123,LBSIFC
  write (*,"(/4f24.16/4i6)") POTNUC,EMY,EACTIV,EMCSCF,ISTATE,ISPIN,NACTEL,LSYM
  write (*,"(8i6)") NISHT,NASHT,NOCCT,NORBT,NBAST,NCONF,NWOPT,NWOPH, &
      NCDETS, NCMOT,NNASHX,NNASHY,NNORBT,N2ORBT,NSYM,MULD2H,   &
      NRHF,NFRO,NISH,NASH,NORB,NBAS,NELMN1, NELMX1,            &
      NELMN3, NELMX3, MCTYPE, NAS1, NAS2, NAS3
  !
  !Relevant parameter here is NNORBT = NORBT(NORBT+1)/2
  !---> What happens if the basis space has been truncated? 
  !     In that case, I would have thought that we should determine
  !     sizes using the number of basis functions and not the number
  !     of MOs. On the other hand, the Fock matrix would still be 
  !     norb x norb. So this should be OK. It's the MOs which will be
  !     norb x nbas.
  MMORBT = MAX(4,NNORBT)
  allocate(fock(MMORBT),stat=info)
  if (info/=0) return
  !
  read(iunit)
  read(iunit)
  read(iunit)
  read(iunit)
  !
  !comment this line for Dalton 1.2      
  read(iunit)
  !
  !And now read in the Fock matrix:
  call rdsa(MMORBT,fock,iunit)
  !The above matrices are not used
  !The orbital energies are on the diagonal of the Fock matrix below
  if (norbt*(norbt+1)/2 /= NNORBT) then
     write(*,"(a,(a,i0))") 'Size mismatch reading Dalton orbital energies', &
         'norbt = ',norbt, ' norbt*(norbt+1)/2 = ',norbt*(norbt+1)/2,   &
         'NNORBT = ',NNORBT
     write(*,"(a)") ' The last two should have been equal.',            &
         "You may be using the 64-bit interface with 32-bit Dalton or vice versa."
     stop 11
  end if
  !
  return
  end subroutine readen

      function findlab(label, labelunit)
      implicit none
      character(8), intent(in) :: label
      integer, intent(in) :: labelunit
      logical :: findlab
      !------------
      character(8), parameter :: stars = '********'
      character(8), dimension(4) :: b
      !------------
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
      end function findlab
      
end program readDALTONmos
