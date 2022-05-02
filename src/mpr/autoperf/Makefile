# !/usr/bin/make
# * THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# * INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
# * AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# * THE CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# * OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# * OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# * ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# *
# * @file Makefile
# * @author Skynet
# * @brief AutoPerf.
# * @see https://github.com
# * @benchmark: N/A
# * @researcher: Joseph David Tarango
# * @website http://www.josephtarango.com
# * @affiliation: Intel, Colorado University Boulder, University of California Riverside
# * @date: October 1, 2021
# *
# To generate the everything, type "make all".
# To run other commands type "make <command>". I.E. "make turnin".
# To remove the executable and any extraneous files type "make clean" at
# the command prompt.
###############################################################################
# General extension information.
###############################################################################
# Linux extension    |Windows Equivalent    |Short description
#  ------------------------------------------------------------
#  .so, .o            | .dll                 | Object that can be loaded at runtime (Similar to DLL)
#  .a                 | .lib                 | Static library
#  [none], .elf(rare),| .exe, .com(rare)     | Linux executables
#    .bin(rare)       |                      |
#  .sh                | .bat                 | Shell script
#  .exe               | .exe                 | Mono application, Wine application
#  .deb               | .msi                 | Installer package for Debian/Ubuntu releases
#                     |                      |   (Though .deb is much more powerful with
#                     |                      |   native support for dependencies and repos). Note that .deb is actually a .ar archive with a special control file, a special file order, and a different extension.
#  .rpm               | .msi                 | Installer package for RedHat/CentOS releases.
#  .tar.gz, .tar, .gz | .zip                 | Compressed files that can contain a program or any other data, like images, documents, etc
#  .ko                | .sys                 | Drivers and kernel modules are loaded into the Linux kernel and have more hardware access than other programs.
#  .sh, .php, .py, etc| .bat, .cmd, .vbs,    | Linux is capable of running any file that it has an interpreter for.
#                     |   .js                |   A line at the top of the file called the shebang specifies what interpreter to run the file with.
#                     |                      |   Windows only supports .bat and .cmd files as Batch files, and .vbs (vbscript) and .js (JScript, not to be confused with JavaScript) via the Windows Script Host (WSH).
###############################################################################
# Exe files
###############################################################################
PYTHON_ANACONDA := ~/anaconda3/bin/python3.7
PYTHON_DEFAULT := /usr/bin/python
MD := /usr/bin/mkdir
MV := /usr/bin/mv
RM := /usr/bin/rm
TEST := /usr/bin/test
A2PS := /usr/bin/a2ps
ENSCRIPT:= /usr/bin/enscript
TR := /usr/bin/tar
# Ubuntu-Linux unlimited heap and stack
UNLIMITED_POWER := ulimit -s unlimited &&
###############################################################################
# Variable to hold Revision number
###############################################################################
REVNUM=1
TAR_NAME_PREFIX=autoperf

# Variable of Tarball generated
TARNAME=$(TAR_NAME_PREFIX)_$(REVNUM).tgz

#Variable of Post Script generated
PSPRINT=$(TAR_NAME_PREFIX)_$(REVNUM).ps
PDFPRINT=$(TAR_NAME_PREFIX)_$(REVNUM).pdf

# File hierarchy is $(TAR_NAME_PREFIX)_$(REVNUM)_$(PART)$(SUBPART)$(TESTBENCH).$(EXTENSION)
# $(REVNUM)= Revision number
# $(PART)= if a lab part exists in order from 1 to infinity
# $(SUBPART)= if other components were used to make this component that were
#            not included then put them here in order from a to z. If "a"
#            requires sub parts then put "a"$(subsubpart) I.E. "a1" now
#            numbering. Continue letter/number trend to infinity.
# $(TESTBENCH)= if this is a test bench file then put "tb" to indicate it
#              is test bench for this part
#$(EXTENSION)= is the character file extension
###############################################################################
# Paths
###############################################################################
# Source directory
SRC_DIR=autoperf

path := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
cwd  := $(shell pwd)
CURRENT_PATH := $(subst $(lastword $(notdir $(MAKEFILE_LIST))),,$(subst $(space),\$(space),$(shell realpath '$(strip $(MAKEFILE_LIST))')))

# Files to be included in the PS/PDF print
FILES := $(wildcard $(SRC_DIR)/*.h) $(wildcard $(SRC_DIR)/*.c) $(wildcard $(SRC_DIR)/*.hpp) $(wildcard $(SRC_DIR)/*.cpp) $(wildcard $(SRC_DIR)/*.py) Makefile

# Lib Dir
LIBDIR=$(BDIR)/libs

# Objects folder
ODIR=$(BDIR)/obj

# Include Dir
IDIR=$(CURRENT_PATH)/src/include
ILDIR=$(IDIR)/lib
PLTDIR=$(CURRENT_PATH)/src/plots
###############################################################################
# Parallel Execution
#  Query the total number of processors, then execute make in parallel to max capabilities.
###############################################################################
DIV_VALUE = 1
ZERO_VALUE = 0
NPROCS = $(shell grep -c 'processor' /proc/cpuinfo)
NPROCS_DIV := $(shell echo ${NPROCS}/${DIV_VALUE} | bc)
NPROCS_GREATEREQ_ZERO := $(shell echo ${NPROCS_DIV}\>${ZERO_VALUE} | bc)
ifeq ($(NPROCS_GREATEREQ_ZERO),0)
NPROCS_DIV = 1
endif
# MAKEFLAGS += -j$(NPROCS)
$(info Make runs in parallel, set to $(NPROCS), half is $(NPROCS_DIV). Comment out MAKEFLAGS is you want serial.)
###############################################################################
# Make Targets
###############################################################################
help:
	@echo "Usage: make all"
	$(info Please note. To create all please do the following sequence.)
	$(info AutoPerf Benchmarks)
	$(info  make test_example)

# Do all, except run and debugging...
all:
	$(info Making all. Fin.)
    $(info MAKEFILE_LIST: $(MAKEFILE_LIST))
    $(info          path: $(path))
    $(info           cwd: $(cwd))
    $(info  current path: $(CURRENT_PATH))
.PHONY: all

# Create directories
create_dirs:
	$(MD) -p $(BDIR)
	$(MD) -p $(ODIR)
	$(MD) -p $(LIBDIR)
	$(MD) -p $(IDIR)
	$(MD) -p $(ILDIR)
	$(MD) -p $(PLTDIR)
.PHONY: create_dirs

# Remove unnecessary files
clean:
	$(RM) -rf *~ $(BDIR)/*.a $(ODIR)/*.o $(LIBDIR)/*.so $(IDIR)/*.so $(ILDIR)/*.so $(PSPRINT) $(PDFPRINT) $(TARNAME) *.pdf *.ps $(FILES_TO_CLEAN) $(FILES_TO_CLEAN_MOVED)
.PHONY: clean

########################################################################################################################
# PDF and zip file generation.
########################################################################################################################
# Print files to a .ps document
print:
	$(A2PS) -M letter --line-numbers=1 --pro=color --highlight-level=light --pretty-print -o $(PSPRINT) $(FILE_FILTER)
.PHONY: print

printpdf:
	$(ENSCRIPT) -2 --fancy-header --line-numbers=1 --truncate-lines \
	--word-wrap --style=emacs --tabsize=3 --landscape $(FILE_FILTER) \
	-o - | ps2pdfwr - $(PDFPRINT)
.PHONY: printpdf

# Create a tar ball for project
turnin: print printpdf
	$(TR) -czvf $(TARNAME) $(PSPRINT) $(PDFPRINT) $(FILES)
.PHONY: turnin

autoperf_install:
	sudo apt update
	sudo apt install build-essential apt-transport-https aptitude ca-certificates cscope valgrind gdb -y
	sudo apt install wget tar unzip p7zip-full p7zip-rar dtrx a2ps enscript python3 libncurses5-dev libipt-dev -y
	sudo apt install fakeroot msr-tools linux-tools linux-tools-common linux-tools-virtual -y
	sudo apt install libpapi-dev libpapi-dev papi-examples papi-tools libpthread-stubs0-dev -y
.PHONY: autoperf_install

# Set the LD_LIBRARY_PATH environment variable as follows:
# $ export LD_LIBRARY_PATH=<path_to_libVTsample>:<path_to_PAPI>
# Add libVTsample.so to the link line in front of the Intel® Trace Collector library. The link line will look as follows:
# $ mpiicc ctest.c -L$VT_SLIB_DIR -L. -L$PAPI_ROOT -lVTsample -lVT -lpapi $VT_ADD_LIBS -o ctest
# To view the counters in Intel® Trace Analyzer, use Counter Timeline.
autoperf_install_tar: autoperf_install:
	mkdir -p archives
	ARCHIEVES=$(shell realpath archives)
	PAPI_NAME=papi-5.5.1.tar.gz
	PAPI_UNPACK=papi_5-5-1
	wget -c http://icl.utk.edu/projects/papi/downloads/papi-5.5.1.tar.gz $(ARCHIEVES)/$(PAPI_NAME)
	tar -xf $(PAPI_NAME) -C $(ARCHIEVES)/$(PAPI_UNPACK)
	pushd $(ARCHIEVES)
	chmod +x -R $(PAPI_UNPACK)
	pushd src
	./configure
	$(MAKE) install-all
	popd
	popd
.PHONY: autoperf_install_tar

profilelib:
	$(MAKE) -C autoperf/proflier
.PHONY: profilelib
########################################################################################################################
# Python Code helper for semi-automation.
########################################################################################################################
pyDataAnalysis:
	$(PYTHON_ANACONDA) $(SRCDIR)/run_profiler.py
	$(PYTHON_ANACONDA) $(SRCDIR)/autoperf.py
.PHONY: pyDataAnalysis

########################################################################################################################
# Run the entire experiment end to end with default configs. Note: debugProfile
########################################################################################################################
runExperiment: clean create_dirs pyDataAnalysis
    $(info Entire controlled experiment...)
.PHONY: runExperiment