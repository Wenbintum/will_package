#!/usr/bin/env bash

# this scripts avoids the makefile as this is rather unflexible

# crucial!
export OMP_NUM_THREADS=1

# catch the extend from the command line
EXTENT=$@

# available options are listed in Test/jobconfig:
# -----------------------------------------------
# spe-simple           = Electronic/*
# bs-simple            = Excitations/*
# phonon-simple        = Phonon/*
# geom-simple          = Geometry/*
# md-simple   	       = MD/*
# magres-simple        = Magres/*
# XC-simple            = XC/XC-*
# NLXC-simple          = XC/NLXC-*
# misc-simple          = Misc/*
# otf-simple           = Pseudo/OTF-Library-C8-LDA Pseudo/OTF-Library-C8-PBE
# pseudo-simple        = Pseudo/Realspace Pseudo/OTF-Gen
# tddft-simple         = Excitations/TDDFT-*
# simple               = spe-simple bs-simple phonon-simple geom-simple md-simple magres-simple XC-simple NLXC-simple misc-simple pseudo-simple otf-simple
# _default_            = simple
# geom-full            = Longer/Mg2SiO4-geom
# phonon-full          = Longer/Brucite-Phon
# full                 = geom-full phonon-full

# full(!) path to the binary
CASTEPEXE= # Adjust accordingly. Full path required

# path to the testcode
TESTCODE="../bin/testcode.py"

# number of cpu (no hyperthreading!)
# please adjust on superMUC!
NPROC=`nproc`
PARALLEL="--processors=${NPROC} --total-processors=${NPROC}"

# run the test (must be called from the folder containing userconfig)
cd Test

# link the executable (also superMUC safe)
ln -sf ${CASTEPEXE} castep

CALL_TEST="${TESTCODE} ${PARALLEL} -c ${EXTENT}"
echo $CALL_TEST

${CALL_TEST}

# run the summary
../bin/testcode.py compare

# clean
../bin/testcode.py --older-than=0 tidy

cd ..
