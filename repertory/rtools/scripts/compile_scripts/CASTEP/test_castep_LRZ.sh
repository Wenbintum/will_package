#!/usr/bin/env bash

# this scripts avoids the makefile as this is rather unflexible

# crucial!
export OMP_NUM_THREADS=1

# catch the extend from the command line
EXTEND=$@

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

# full path to the binary
CASTEPEXE="${HOME}/code/CASTEP-16.1/obj/linux_x86_64_ifort15--mpp2-login6-openblas-fftw3-mpi/castep.mpi"

# path to the testcode relative to the test folder!
TESTCODE="../bin/testcode.py"

# number of cpu (no hyperthreading!)
# no, do not use the entire login node
#NPROC=`nproc`
NPROC=16

PARALLEL="--processors=${NPROC} --total-processors=${NPROC}"

# the call string 
CALL_TEST="${TESTCODE} ${PARALLEL} -c ${EXTEND}"

echo $CALL_TEST

ORIGIN=$(pwd)

## run the test
cd Test
ln -sf ${CASTEPEXE} castep

${CALL_TEST}

## run the summary
${TESTCODE} compare

## clean
${TESTCODE} --older-than=0 tidy

cd ${ORIGIN}
