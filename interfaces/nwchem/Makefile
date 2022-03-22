FC     := gfortran

FILES  := precision.f90 parameters.f90 free_format_reader.F90 read_movecs.f90
OBJ    := $(subst .F90,.o,$(subst .f90,.o,$(FILES)))
#  Note: -static fails under OS X
LDFLAGS := -static-libgfortran -static-libgcc
# LIBS = -lgfortran

vpath %.F90 ../../src
vpath %.f90 ../../src

install: readNWCHEMmos
	cp -pf $< ../../bin

readNWCHEMmos: ${OBJ} ${FRC}
	${FC} ${LDFLAGS} ${OBJ} ${LIBS} -o $@

%.o: %.F90 ${FRC}
	${FC} -c $<

%.o: %.f90 ${FRC}
	${FC} -c $<

force:

clean:
	rm -f *.mod *.o core
