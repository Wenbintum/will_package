#!/usr/bin/env bash

###############################################################################
# Disclaimer:                                                                 #
# -----------                                                                 #
# Please, read the README.INSTALL file provided with your CASTEP distribution #
# before changing any options in this file. Moreover, if you want to          #
# specifically tackle very particular options, have a look into the Makefiles.#
#                                                                             #
# Tested with CASTEP 7.0.X, CASTEP 8 and CASTEP 16.1                          #
#                                                                             #
# Simon P. Rittmeyer (TUM), 2016                                              #
# simon.rittmeyer(at)tum.de                                                   #
###############################################################################

# define the make target from the command line 
# "" (default - build catep binary), "tools", "check" or "clean"
TARGET=$@

# -----------------------------------------------------------------------------
# ARCHITECTURE and COMPILER FLAGS
# -----------------------------------------------------------------------------

# either 'mpi' or 'serial'
COMMS_ARCH="mpi"

# not necessary, as this is detected by makefile. If you want to change the 
# default compiler, however, you might want to adjust this variable (and 
# pass it to the makfile)
#export F90="ifort"

# BUILD=fast is a synonym for ``OPT = -O3 -debug minimal -traceback''
# But this enters the header information in the *castep File
# Further useful option is DEBUG
BUILD="fast"
#BUILD="debug"

# no CPU specific settings / as portable as possible with regard to CPU
# instructions
TARGETCPU="portable"
# compile with -xHost flag... do not use this for inhomogeneous clusters
#TARGETCPU="host"

# Only use these flags if you know, what you are doing:
# Directly adressing the compiler vectorization flags
#export OPT_CPU="-xHOST"
#export OPT_CPU=" -axSSE4.2 -xSSE2"

# -----------------------------------------------------------------------------
# MATH LIBRARY (crucial)
# -----------------------------------------------------------------------------

# either use 'openblas' (compile first) or 'mkl'
MATHLIB='mkl'

if [ "${MATHLIB}" == 'openblas' ]; then
    #---OpenBLAS OPTIONS---
    # uncomment all flags below if you want to use openblas
    MATHLIBS="openblas"
    MATH_LIB_DIR= # wherever your library is
    MATH_LIBS="${MATH_LIB_DIR}/libopenblas.a"
    MATHLIBDIR=${MATH_LIB_DIR}

elif [ "${MATHLIB}" ==  'mkl' ]; then
    #---MKL10 OPTIONS---
    # This exports the MKLROOT variable
    MKLFILE=/usr/local/share/intel/mkl/bin/mklvars.sh
    if [ -f "$MKLFILE" ]; then
        source $MKLFILE intel64
    fi
    MATHLIBS="mkl10"
    MATHLIBDIR="${MKLROOT}/lib/intel64"
        
    # Shouldn't use the mkl threading as it interfers with the castep
    # parallelization scheme
    MATH_LIBS=" -mkl=sequential -static-intel"

fi

# -----------------------------------------------------------------------------
# FFT LIBRARY (optional)
# -----------------------------------------------------------------------------

# either use 'fftw3' or 'mkl'
FFTLIB='mkl'


if [ "${FFTLIB}" == 'fftw3' ]; then
    # ---SYSTEM DEFAULT FFTW3---
    # FFT routines from the FFTW library --> dynamically
    FFT="fftw3"
    FFTLIBDIR="/usr/lib/x86_64-linux-gnu"

elif [ "${FFTLIB}" == 'mkl' ]; then
    #---FFT ROUTINES FROM THE MKL---
    # FFT routines from the MKL Library --> as static as possible

    # This exports the MKLROOT variable
    MKLFILE=/usr/local/share/intel/mkl/bin/mklvars.sh
    if [ -f "$MKLFILE" ]; 
        then
            source $MKLFILE intel64
    fi
    FFT="mkl"
    FFTLIBDIR="${MKLROOT}/lib/intel64/"
fi

# -----------------------------------------------------------------------------
# MISCELLANEOUS
# -----------------------------------------------------------------------------
# include the host name in the ${SUBARCH} folder
HOSTNAME=`/bin/hostname`

# all the compiled stuff will end in obj/${ARCH}--${SUBARCH}
SUBARCH="${HOSTNAME}-${MATHLIBS}-${FFT}-${COMMS_ARCH}"

# number of parallel processes
NPROC=`nproc`

# just make sure that the checks do not kill each other performance-wise
export OMP_NUM_THREADS=1

# -----------------------------------------------------------------------------
# CALLING THE ACTUAL MAKEFILE
# -----------------------------------------------------------------------------
make -j ${NPROC} -f Makefile ${TARGET} \
    BUILD="${BUILD}"\
    TARGETCPU="${TARGETCPU}"\
    SUBARCH="${SUBARCH}"\
    COMMS_ARCH="${COMMS_ARCH}"\
    FFT="${FFT}"\
    FFTLIBDIR="${FFTLIBDIR}"\
    MATHLIBS="${MATHLIBS}"\
    MATH_LIBS="${MATH_LIBS}"\
    MATHLIBDIR="${MATHLIBDIR}"
