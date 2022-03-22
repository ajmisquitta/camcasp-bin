program readGAMESSmos
!NOTES:
!(1) Many integers are (li). This is needed for GAMESS(US) compiled with 8 byte
!integers - the default on all 64 bit machines.
!(2) Some subroutines have been borrowed directly from GAMESS(US).
!(3) This code owes a lot to the gamsintf.F program included in the SAPT2006
!suite of codes. gamsintf.F was written by Malgosia Jeziorska around 1998. 
!
use precision
use input_parser, only: die, read_line, reada, readi, uppercase, item, nitems
implicit none
!
!File access parameters:
integer, parameter :: iunitvect = 2  !output unit for MO file
integer, parameter :: iunitout  = 6  !output unit for STD I/O
character(80) :: vect_file = '', asc_file = ''
!
!Refers to the GAMESS(US) DAF (direct access file) file
!------------------------------------------------------
!DAF file name
character(80) :: DAFfilename = ''    
!unit on which GAMESS DAF file is opened.
integer, parameter :: iunitDAF  = 10 
!Seems to be used to store physical record numbers.
!GAMESS writes data to logical records in a direct access file. Each logical
!record can span more than one physical record. This array stores the start
!records (I guess) of each logical record. 
integer(li), dimension(400) :: IODA  
!record length for DAF physical records
integer, parameter :: IRECLN=4090 
!Logical record numbers for energies and MO vectors:
integer, parameter :: MOrec = 15   !record number for MOs
integer, parameter :: ENrec = 17   !and for energies
!------------------------------------------------------
!
!Storage for MOs and energies
real(dp), allocatable :: vec(:,:), evals(:), vec1D(:)
!
!Control flags:
logical :: testcode = .true.
logical :: verbose = .true.
!
!Misc:
integer :: nocc, nvir, nbas=0, nbasC=0
integer :: nelecA=0, nelecB=0, nelec=0, nmos=0
integer :: nbasC2
integer :: m, i, arg, arglen, ok, lrec
logical :: eof
character(80) :: word
character(80) :: SCFcode = 'GAMESS(US)'
character(80) :: SCFtype = '', basis_name = '', title = ''
!
integer :: info
!------------
!
if (command_argument_count()>0) then
  arg=0
  do while(arg<command_argument_count())
    arg=arg+1
    call get_command_argument(arg,word,arglen,ok)
    if (ok .ne. 0) call die("Argument too long for buffer",.true.)
    select case(uppercase(word))
    case default
      if (DAFfilename .eq. "") then
        DAFfilename=word
      else
        call die("Don't understand "//trim(word))
      end if
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
      read(word,'(i9)')nmos
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
        "readGAMESSmos <file> [--quiet] [--ascii <name>] [--binary <name>]", &
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
      case("FILE")
        call reada(DAFfilename)
        if (verbose) print "(2a)", "File ", trim(DAFfilename)
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
        call readi(nmos)
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

if (nelec==0) then
  nelec = nelecA + nelecB
  if (nelec==0) then
    write(iunitout,*)'ERROR in GAMESS interface: nelec is undefined'
    call stopinterface(info=-1)
  endif
endif
if (nbas==0.and.nbasC==0) then
  write(iunitout,*)'ERROR in GAMESS interface: nbas and nbasC are undefined'
  call stopinterface(info=-2)
endif
if (nbasC==0) then
  write(iunitout,*)'WARNING: nbasC undefined; assuming nbasC=nbas'
  nbasC = nbas
endif
if (nmos==0) then
  write(iunitout,*)'WARNING: nmos undefined; assuming nmos=nbas'
  nmos = nbas
endif

!read(5,*) nbasC  ! total number of (Cartesian) basis functions
!read(5,*) nelec  ! number of electrons
!read(5,*) nelecA ! number of alpha electrons
!read(5,*) nelecB ! number of beta electrons
!read(5,*) nbas   ! number of basis functions in variational space
!read(5,*) DAFfilename ! Name of direct-access file

!Assume closed shell:
nocc=nelec/2
if ((nocc/=nelecA).or.(nocc/=nelecB).or.(nelecA/=nelecB)) then
  write(iunitout,*)'Number of occupied orbitals not consistent!!!'
  write(iunitout,*)'Total number of electrons = ',nelec
  write(iunitout,*)'          Alpha electrons = ',nelecA
  write(iunitout,*)'          Beta  electrons = ',nelecB
endif
!Compute the true number of virtual orbitals
!This will not be nbas-nocc as the variational space may have been truncated.
!Need to figure out what variable GAMESS uses to indicate this. So for now:
nvir=nbas-nocc
nbasC2=nbasC*nbasC

if (verbose) then
  write(iunitout,"(2a)") "File ", trim(DAFfilename)
  write(iunitout,"(2a)") "Title: ", trim(title)
  write(iunitout,"(2a)") "SCF type: ", trim(SCFtype)
  write(iunitout,"(2a)") "SCF Code: ", trim(SCFcode)
  write(iunitout,"(2a)") "Basis: ", trim(basis_name)
  write(iunitout,"(a,i0)") "Basis set size: ", nbas
  write(iunitout,"(a,i0)") "Basis set size (Cartesian): ", nbasC
  write(iunitout,"(a,i0)") "Number of molecular orbitals: ",nmos
end if

!===== read direct-access file =====
!It seems like GAMESS will *always* write out MOs and energies in arrays the
!size of the Cartesian basis. This is done even if a basis of spherical GTOs
!is used. So all dimensions will be based on nbasC.
allocate(evals(nbasC),stat=info)
if (info/=0) then
  write(iunitout,*)'Allocate error for evals: nbasC=',nbasC
  call stopinterface(info)
endif
allocate(vec1D(nbasC2),stat=info)
if (info/=0) then
  write(iunitout,*)'Allocate error for vec1D: nbasC=',nbasC
  call stopinterface(info)
endif
allocate(vec(nbasC,nbasC),stat=info)
if (info/=0) then
  write(iunitout,*)'Allocate error for vec: nbasC=',nbasC
  call stopinterface(info)
endif
!
!Open the direct access data file:
call openda
!
!First the eigenvalues.
call daread(evals,nbasC,ENrec,info)
if (info/=0) then
  write(iunitout,*)'Error reading eigenvalues'
  call stopinterface(info)
endif
!write(IOUTVECT) (evals(I), I=1,nbasC)
if (testcode) then
  write(iunitout,*)'Orbital energies:'
  do i = 1, nbasC
    write(iunitout,*) i, evals(i)
  end do
endif
!
!Now the eigenvectors.
call daread(vec1D,nbasC2,MOrec,info)
!write(IOUTVECT) (vec1D(i), i=1, nbasC2)
vec(1:nbasC,1:nbasC) = reshape(vec1D(1:nbasC2),(/nbasC,nbasC/))
if (testcode) call matoutgen('MO coefficients',vec,nbasC,nbasC)

if (vect_file .ne. "") then
  inquire(iolength=lrec) vec(:,:)
  if (verbose) print "(2a,i0)", trim(vect_file), " record length = ", lrec
  open (unit=18,file=vect_file,form="unformatted",recl=lrec,iostat=ok)
  if (ok>0) call die("Can't open "//trim(vect_file))
  write(18) evals(:)
  write(18) vec(:,:)
  close (18)
end if

if (asc_file .ne. "") then
  open (unit=18,file=asc_file, recl=255,iostat=ok)
  if (ok>0) call die("Can't open "//trim(asc_file))
  write (18,"(2a)") "Source    ", trim(DAFfilename)
  write (18,"(2a)") "Title     ", trim(title)
  write (18,"(2a)") "Code      ", "gamess"
  write (18,"(2a)") "Basis     ",  trim(basis_name)
  write (18,"(a,i0)") "BFNS      ", nbas
  write (18,"(a,i0)") "NMOS      ", nmos
  write (18,"(a,i0)") "Energies  ", nmos
  write (18,"(1p,(5e24.15))") evals(1:nmos) 
  do m=1,nmos
    write (18,"(a,i0,a,1p,e24.15)") "MO ", m, "   Energy ", evals(m)
    write (18,"(1p,(5e24.15))") vec(:,m)
  end do
  write (18,"(a)") "END"
  close(18)
end if

deallocate(vec,vec1D,evals,stat=info)
if (info/=0) then
  write(iunitout,*)'Error deallocating vec,vec1D,evals in GAMESS interface'
  call stopinterface(info)
endif

contains

subroutine openda
implicit none
integer(li) :: irecst, is, ipk, ifilen(400)
!character(256) :: filenm
!------------
!call getenv('DICTNRY',filenm)
open(unit=iunitDAF, file=DAFfilename, status='unknown', &
     access='direct', form='unformatted',recl=8*IRECLN)
read(unit=iunitDAF, rec=1) irecst,IODA,ifilen,is,ipk
return
end subroutine openda

!From: *MODULE IOLIB   *DECK DAREAD
!Reads a logical record from a direct access file. The logical record may be
!stored in one or more physical records. Each physical record is of length 
!IRECLN 8 byte words.
subroutine daread(V,LEN,NREC,info)
implicit none
integer, intent(in) :: LEN, NREC
real(dp), intent(inout) :: V(LEN)
integer, intent(out) :: info
!------------
integer(li) :: N, LENT, IS, NS, NSP, LENW, IF
!------------
info = 0
!read a logical record from the daf dictionary file
!a logical record may span several physical records.
N = IODA(NREC)
if (N == -1) then
  !Error!!!
  info = -1
  write(6,9000) NREC,LEN
else
  IS = -IRECLN + 1
  NS = N
  LENT = LEN
  do while (LENT>=1)
    IS = IS + IRECLN
    IF = IS + LENT - 1
    IF ((IF-IS+1) > IRECLN) IF = IS + IRECLN - 1
    NSP = NS
    LENW = IF - IS + 1
    CALL DARD(V(IS),LENW,NSP)
    LENT = LENT - IRECLN
    NS = NS + 1
    N = NS
  enddo
endif
return
9000 format(1x,'*** ERROR *** ATTEMPT TO READ A DAF RECORD',               &
               ' THAT WAS NEVER WRITTEN.'/                                 &
            1X,'RECORD NUMBER',I5,' OF LENGTH',I10,' DOES NOT EXIST.'/     &
            1X,'CHECK -PROG.DOC- FOR A LIST OF DIRECT ACCESS FILE CONTENTS')
end subroutine daread

!From: *MODULE IOLIB   *DECK DARD
subroutine dard(V,LEN,NS)
implicit none
integer(li), intent(in) :: LEN, NS
real(dp), intent(inout) :: V(LEN)
!------------
!read a physical record from the daf
read (unit=iunitDAF, REC=NS) V
return
end subroutine dard

Subroutine stopinterface(info)
integer, intent(in) :: info
print *,'Error in the GAMESS interface. Stopping'
print *,'Info = ',info
stop
end subroutine stopinterface

subroutine matoutgen(title,f,nrow,ncol)
!--------------------------------------
!Modified from MATOUTSYM
!Writes out the GENERAL Matrix F in 6 columns (MAX) at a time.
!dimension of matrix F is NROW*NCOL
!
implicit none
integer, intent(in) :: nrow, ncol
real(dp), dimension(nrow,ncol), intent(in) :: f
character(*), intent(in) :: title
!------------
integer :: max, imax, imin, i, j
integer :: my_row, my_col
!------------
my_row = nrow
my_col = ncol
!
if (nrow.gt.100) my_row = 100
if (ncol.gt.100) my_col = 100
!
if (title.ne.'') write(iunitout,'(1x,a)') title
max=6
imax=0
do while (imax.lt.my_col)
  imin=imax+1
  imax=imax+max
  if(imax.gt.my_col) imax=my_col
  write(iunitout,'(5x,6(4x,i3,5x))') (i,i=imin,imax)
  !Write out all rows (J) for columns (I) between IMIN and IMAX
  do j=1,my_row
    write(iunitout,'(i5,6f12.4)') j,(f(j,i),i=imin,imax)
  enddo
enddo
!
return
end subroutine matoutgen

end program readGAMESSmos
