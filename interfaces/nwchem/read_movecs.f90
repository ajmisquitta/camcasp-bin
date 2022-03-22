PROGRAM read_movecs

!  Program to read an NWChem .movecs file, print out the information
!  if required, and generate a vectA.data file for CamCASP if required.
!  Based on the NWChem movecs_read_header and movecs_read functions
!  in the ddscf/vectors.F file of NWChem.

!  Usage:
!  read_movecs <file> [-to <vect.data file>] [--ascii <asc.data file>] [-quiet]

USE input_parser, ONLY: die, read_line, reada, uppercase, item, nitems

IMPLICIT NONE

CHARACTER(LEN=80) ::  &
    filename="",      &    ! File to read header from
    vect_file="",     &    ! Name of vect.data file to create
    asc_file="",      &    ! Name of ascii vect.data file to create
    title,            &    ! Title of job that created vectors
    basis_name             ! Name of basis set
CHARACTER(LEN=20) :: scftype   ! The SCF type of the vectors
CHARACTER(LEN=80) :: word
INTEGER  ::  &
    nbf,     &    ! No. of functions in basis
    nsets         ! No. of functions in each set
INTEGER, ALLOCATABLE :: nmo(:)        ! No. of vectors in each set
DOUBLE PRECISION, ALLOCATABLE :: occ(:), evals(:), vec(:,:)

INTEGER, PARAMETER :: unitno=17,  &           ! Unit no. for reading
    lenbuf=524287                             ! 4*1024*1024/8 - 1

INTEGER :: lentitle, lenbas, ok, ioerr, set, mo, m, start, remaining,  &
    buf, nbuf, arg, arglen, lrec

LOGICAL :: verbose=.true., eof

if (command_argument_count()>0) then
  arg=0
  do while(arg<command_argument_count())
    arg=arg+1
    call get_command_argument(arg,word,arglen,ok)
    if (ok .ne. 0) call die("Argument too long for buffer",.true.)
    select case(uppercase(word))
    case default
      if (filename .eq. "") then
        filename=word
      else
        call die("Don't understand "//trim(word))
      end if
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
      print "(a)", "Usage:",                                                  &
          "  read_movecs <file> [--quiet] [--ascii <name>] [--binary <name>", &
          "MOs can be written out in ASCII and/or BINARY format using the   ",&
          "--ascii and --binary options together with file names.           "
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
        call reada(filename)
        if (verbose) print "(2a)", "File ", trim(filename)
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

ok = 0

open(unitno, status='old', form='unformatted', file=filename,          &
    iostat=ioerr)
if (ioerr .ne. 0) call die ("Can't open "//trim(filename),.true.)
read(unitno, err=1001, end=2001) ! SKIP convergence info
if (verbose) print "(a)", "First record skipped"
read(unitno, err=1001, end=2001) scftype
if (verbose)  print "(2a)", "SCF type: ", trim(scftype)
read(unitno, err=1001, end=2001) lentitle
if (len(title) .lt. lentitle) then
  print "(a,i0,a)", "Title too long (", lentitle," chars)"
  call die("Stopping")
end if
title = ""
read(unitno, err=1001, end=2001) title(1:lentitle)
if (verbose)  print "(2a)", "Title: ", trim(title)
read(unitno, err=1001, end=2001) lenbas
if (len(basis_name) .lt. lenbas) then
  print "(a,i0,a)", "Basis name too long (", lenbas," chars)"
  call die("Stopping")
end if
basis_name = ""
read(unitno, err=1001, end=2001) basis_name(1:lenbas)
read(unitno, err=1001, end=2001) nsets
read(unitno, err=1001, end=2001) nbf
allocate(nmo(nsets))
read(unitno, err=1001, end=2001) nmo(1:nsets)

if (verbose) then
  print "(2a)", "File ", trim(filename)
  print "(2a)", "Title: ", trim(title)
  print "(2a)", "SCF type: ", trim(scftype)
  print "(2a)", "Basis: ", trim(basis_name)
  print "(a,i0)", "Basis set size: ", nbf
  print "(a,i0)", "Number of sets: ", nsets
  print "(a)", "Number of vectors in each set:"
  print "(10i8)", nmo(1:nsets)
end if

allocate (occ(nbf),evals(nbf),vec(nbf,nbf))
vec=0d0

do set=1,nsets
  if (verbose) print "(a,i0)", "Set ", set
  read(unitno, err=1001, end=2001) occ(1:nbf)
  if (verbose) print "(10f7.2)", occ(1:nmo(set))
  read(unitno, err=1001, end=2001) evals(1:nbf)
  if (nmo(set)<nbf) then
    evals(nmo(set)+1:nbf)=huge(1d0)
  end if
  if (verbose) print "(5f15.8)", evals(1:nmo(set))

  do mo = 1, nmo(set)
    if (verbose) then
      print "(/a,i0,a,f5.2,a,f14.8)", "MO ", mo, "  occ. no.", occ(mo), &
          "  orbital energy ", evals(mo)
    end if
    remaining=nbf
    nbuf=1+(nbf-1)/lenbuf
    start=1
    do buf=1,nbuf
      m=min(lenbuf,remaining)
      read(unitno, err=1001, end=2001) vec(start:start+m-1,mo)
      start=start+m
      remaining=remaining-m
    end do
    if (remaining .ne. 0) call die("Mistake in vector count")
    if (verbose) then
      print "(5f15.8)", vec(:,mo)
    end if
  end do
end do
close(unitno)

if (vect_file .ne. "") then
  if (nsets>1) call die("MOvecs file contains more than one set")
  inquire(iolength=lrec) vec(:,:)
  if (verbose) print "(2a,i0)", trim(vect_file), " record length = ", lrec
  open (unit=18,file=vect_file,form="unformatted",recl=lrec,iostat=ok)
  if (ok>0) call die("Can't open "//trim(vect_file))
  write(18) evals(1:nbf)
  write(18) vec(:,:)
  close (18)
end if

if (asc_file .ne. "") then
  if (nsets>1) call die("MOvecs file contains more than one set")
  set=1
  open (unit=18,file=asc_file, recl=255,iostat=ok)
  if (ok>0) call die("Can't open "//trim(asc_file))
  write (18,"(2a)") "Source    ", trim(filename)
  write (18,"(2a)") "Title     ", trim(title)
  write (18,"(2a)") "Code      ", "NWChem"
  ! write (18,"(2a)") "Basis     ",  trim(basis_name)
  write (18,"(a,i0)") "BFNS      ", nbf
  write (18,"(a,i0)") "NMOS      ", nmo(set)
  write (18,"(a,i0)") "Energies  ", nmo(set)
  write (18,"(1p,(5e24.15))") evals(1:nmo(set)) 
  do m=1,nmo(set)
    write (18,"(a,i0,a,1p,e24.15)") "MO ", m, "   Energy ", evals(m)
    write (18,"(1p,(5e24.15))") vec(:,m)
  end do
  write (18,"(a)") "END"
  close(18)
end if

stop

 1001 print "(2a)", "Error reading from ", trim(filename)
stop
 2001 print "(2a)", "Unexpected end of file ", trim(filename)

END PROGRAM read_movecs
