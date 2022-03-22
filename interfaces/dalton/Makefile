FC     := gfortran

FILES  := precision.f90 parameters.f90 free_format_reader.F90# readDALTONmos${V}.F90
OBJ    := $(subst .F90,.o,$(subst .f90,.o,$(FILES)))
#  Note: -static fails under OS X
LDFLAGS := -static-libgfortran -static-libgcc

vpath %.F90 ../../src
vpath %.f90 ../../src

install: readDALTON64mos readDALTON32mos
	cp -pf $^ ../../bin

readDALTON32mos: ${OBJ} readDALTONmos.o ${FRC}
	${FC} ${LDFLAGS} readDALTONmos.o ${OBJ} -o $@
#	${MAKE} clean

readDALTON64mos: ${OBJ} readDALTONmos64.o ${FRC}
	${FC} ${LDFLAGS} readDALTONmos64.o ${OBJ} -o $@
#	${MAKE} clean

%.o: %.F90 ${FRC}
	${FC} -c $<

%.o: %.f90 ${FRC}
	${FC} -c $<

force:

clean:
	rm -f *.mod *.o core
