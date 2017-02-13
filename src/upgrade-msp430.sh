#! /bin/sh
#################################################################
# This script compiles the msp43-gcc 4.7.0                      #
# The instructions are based on an email from Aragosystems, the #
# manufacturer of the WiSMote platform. It has been tested on   #
# Ubuntu 12 and MAC OS 10.6.                                    #
# The running time of this script is depending on your system   #
# and it can take about 30 minutes.                             #
#                                                               #
# NOTE ON RECENT PLATFORMS: Using recent compiler (e.g. gcc-5.3)#
# or recent versions of texinfo (e.g. texinfo-6.0) with this    #
# script seems to be non-working. It has been tested with       #
# gcc-4.6.4 and texinfo-4.13.                                   #
#                                                               #
# IMPORTANT: This script is very simple and requires you        #
# understanding it and modifying it according to your needs.    #
#                                                               #
# IMPORTANT: The ouput file for the new compiler is defined in  #
# INSTALL_PREFIX and it set to /opt/mspgccx in this script. You #
# can later move this dicrectory. However, you MUST create this #
# directory before starting the script, e.g.:                   #
# $ mkdir ~/mspgccx && mv ~/mspgccx /opt/                       #
#                                                               #
# IMPORTANT: Your system might require root priviliege for      #
# modifying the defined installion directory, e.g. if is in     #
# /opt/ make sure INSTALL_PREFIX has the correct access rights. #
#                                                               #
# IMPORTANT: This script creates a tempral directory tmp in     #
# the current path, remeber to remove it afterwarts.            #
#                                                               #
# Author:                                                       #
#         Hossein Shafagh (hossein.shafagh@rwth-aachne.de)      #
# Created: Nov. 19 2012                                         #
#################################################################

INSTALL_PREFIX="/tmp/mspgccx"
echo The installatoin prefix:$INSTALL_PREFIX
# Switch to the tmp directory
mkdir tmp
cd tmp

# Getting
wget http://sourceforge.net/projects/mspgcc/files/mspgcc/DEVEL-4.7.x/mspgcc-20120911.tar.bz2
wget http://sourceforge.net/projects/mspgcc/files/msp430mcu/msp430mcu-20120716.tar.bz2
wget http://sourceforge.net/projects/mspgcc/files/msp430-libc/msp430-libc-20120716.tar.bz2
wget http://sourceforge.net/p/mspgcc/bugs/352/attachment/0001-SF-352-Bad-code-generated-pushing-a20-from-stack.patch
wget http://sourceforge.net/p/mspgcc/bugs/_discuss/thread/fd929b9e/db43/attachment/0001-SF-357-Shift-operations-may-produce-incorrect-result.patch
wget http://ftpmirror.gnu.org/binutils/binutils-2.22.tar.bz2
wget http://mirror.ibcp.fr/pub/gnu/gcc/gcc-4.7.0/gcc-4.7.0.tar.bz2

# Unpacking the tars
tar xvfj binutils-2.22.tar.bz2        > /dev/null
tar xvfj gcc-4.7.0.tar.bz2            > /dev/null
tar xvfj mspgcc-20120911.tar.bz2      > /dev/null
tar xvfj msp430mcu-20120716.tar.bz2   > /dev/null
tar xvfj msp430-libc-20120716.tar.bz2 > /dev/null

# 1) Incorporating the changes contained in the patch delievered in mspgcc-20120911
cd binutils-2.22
patch -p1<../mspgcc-20120911/msp430-binutils-2.22-20120911.patch
cd ..

# 2) Incorporating the changes contained in the patch delievered in mspgcc-20120911
cd gcc-4.7.0
patch -p1<../mspgcc-20120911/msp430-gcc-4.7.0-20120911.patch
patch -p1<../0001-SF-352-Bad-code-generated-pushing-a20-from-stack.patch
patch -p1<../0001-SF-357-Shift-operations-may-produce-incorrect-result.patch
cd ..

# 3) Creating new directories
mkdir binutils-2.22-msp430
mkdir gcc-4.7.0-msp430

# 4) installing binutils in INSTALL_PREFIX
cd binutils-2.22-msp430/
../binutils-2.22/configure --target=msp430 --program-prefix="msp430-" --prefix=$INSTALL_PREFIX > /dev/null
make > /dev/null
make install > /dev/null

# 5) Download the prerequisites
cd ../gcc-4.7.0
./contrib/download_prerequisites

# 6) compiling gcc-4.7.0 in INSTALL_PREFIX
cd ../gcc-4.7.0-msp430
../gcc-4.7.0/configure --target=msp430 --enable-languages=c --program-prefix="msp430-" --prefix=$INSTALL_PREFIX > /dev/null
make > /dev/null
make install > /dev/null

# 7) compiping msp430mcu in INSTALL_PREFIX
cd ../msp430mcu-20120716
MSP430MCU_ROOT=`pwd` ./scripts/install.sh ${INSTALL_PREFIX}/

# 8) compiling the msp430 lib in INSTALL_PREFIX
cd ../msp430-libc-20120716
cd src
PATH=${INSTALL_PREFIX}/bin:$PATH
make
make PREFIX=$INSTALL_PREFIX install

# cleanup
# no need since every thing created in tmp
echo Reminder: remove tmp
