#!/usr/bin/env bash

###############################################################################
# Disclaimer:                                                                 #
# -----------                                                                 #
# Please, read the README.INSTALL file provided with your CASTEP distribution #
# before changing any options in this file. Moreover, if you want to          #
# specifically tackle very particular options, have a look into the Makefiles.#
#                                                                             #
#                                                                             #
# On SuperMUC/LRZ cluster, make sure to to first load ifort 15 and the        #
# mkl/fftw3 if you need it.                                                   #
#                                                                             #
# Simon P. Rittmeyer (TUM), 2016                                              #
# simon.rittmeyer(at)tum.de                                                   #
###############################################################################

# make the module system available and go for ifort 15.0
source /etc/profile.d/modules.sh

module unload intel
module load intel/15.0

# define the make target from the command line
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
#TARGETCPU="portable"
# compile with -xHost flag... do not use this for inhomogeneous clusters
TARGETCPU="host"

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
    MATH_LIB_DIR="${HOME}/opt/lib" # wherever your library is located at
    MATH_LIBS="${MATH_LIB_DIR}/libopenblas.a"
    MATHLIBDIR=${MATH_LIB_DIR}

elif [ "${MATHLIB}" ==  'mkl' ]; then
    module load mkl/11.3
    #---MKL10 OPTIONS---
    MATHLIBS="mkl10"
    MATHLIBDIR="${MKL_LIBDIR}"
        
    # Shouldn't use the mkl threading as it interfers with the castep
    # parallelization scheme
    MATH_LIBS=" -mkl=sequential -static-intel"

fi

# -----------------------------------------------------------------------------
# FFT LIBRARY (optional)
# -----------------------------------------------------------------------------

# either use 'fftw3' or 'mkl'
FFTLIB='mkl'
#

if [ "${FFTLIB}" == 'fftw3' ]; then
    # ---SYSTEM DEFAULT FFTW3---
    # FFT routines from the FFTW library --> statically
    # explicitely go for mpi version?
    module load fftw/mpi/3.3
    FFT="fftw3"
    FFTLIBDIR="${FFTW_LIBDIR}"

elif [ "${FFTLIB}" == 'mkl' ]; then
    #---FFT ROUTINES FROM THE MKL---
    # FFT routines from the MKL Library --> as static as possible
    module load mkl/11.3
    #---MKL10 OPTIONS---
    FFT="mkl"
    FFTLIBDIR="${MKL_LIBDIR}"
        
fi

# -----------------------------------------------------------------------------
# MISCELLANEOUS
# -----------------------------------------------------------------------------
# include the host name in the ${SUBARCH} folder
HOSTNAME=`/bin/hostname`

# all the compiled stuff will end in obj/${ARCH}--${SUBARCH}
SUBARCH="${HOSTNAME}-${MATHLIBS}-${FFT}-${COMMS_ARCH}"

# number of parallel processes
# nope, we cannot occupy the entire login node...
#NPROC=`nproc`
NPROC=4

# just make sure that the checks do not kill each other performance-wise
export OMP_NUM_THREADS=1
export MKL_SERIAL=yes

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
