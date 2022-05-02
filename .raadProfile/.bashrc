# ~/.bashrc: executed by bash(1) for non-login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples
################################################################################        
# Intel Compiler
################################################################################
#INTEL_LICENSE_FILE=/opt/intel/licenses
alias intelCompiler='(ISS_ROOT=/opt/intel/system_studio_2020;
			INTEL_LIB_PATH=${ISS_ROOT}/lib/intel64_lin;
			CPATH=${ISS_ROOT}/compilers_and_libraries/linux/include;
			CPATH_MORE=${ISS_ROOT}/compilers_and_libraries/linux/daal/include;
			DAALROOT=${ISS_ROOT}/compilers_and_libraries/linux/daal;
			TBBROOT=${ISS_ROOT}/compilers_and_libraries/linux/tbb;
			IE_COMPILER=${ISS_ROOT}/compilers_and_libraries/linux/bin/intel64/icc;
			source ${ISS_ROOT}/bin/compilervars.sh -arch intel64 -platform linux;
			source ${ISS_ROOT}/iss_env.sh)'
################################################################################        
# Intel Compiler and V-Tune
################################################################################
alias intelSystemStudio='sh ${ISS_ROOT}/iss_ide_eclipse-launcher.sh'
echo "Intel Compiler command: intelSystemStudio"
#if [ -d "${ISS_ROOT}/vtune_profiler_2020/" ]; then
#    echo "Setting up VTune"
#    source ${ISS_ROOT}/vtune_profiler_2020/amplxe-vars.sh
#fi
################################################################################        
# Put ERRFILE=$HOME/.xsession-errors to dev/null
################################################################################  
## ERRFILE=/dev/null
# If the .xsession-errors file is not a symbolic link, delete it and create it as such
if [ ! -h $HOME/.xsession-errors ]; then
 rm -f $HOME/.xsession-errors
 ln -s /dev/null $HOME/.xsession-errors
fi
################################################################################
# Xilinx Setup
################################################################################
#export XIL_HOME=/opt/Xilinx/Vivado/2018.2/
#export XIL_SHOME=/opt/Xilinx/SDK/2018.2/
#export PATH=${PATH}:${XIL_HOME}/bin:${XIL_SHOME}/bin
#source /opt/Xilinx/Vivado/2018.2/settings64.sh
#source /opt/Xilinx/SDK/2018.2/settings64.sh
#alias xFPGA='/opt/Xilinx/Vivado/2018.2/bin/vivado -mode gui'
#echo '    Xilinx Commands: xFPGA'
#ISE 10 Setup and start
#alias ise10='source /opt/Xilinx/10.1/ISE/settings64.sh'
#alias edk10='source /opt/Xilinx/10.1/EDK/settings64.sh'
#alias ise10_start='./opt/Xilinx/10.1/ISE/bin/lin64/ise'
#alias xps10_start='./opt/Xilinx/10.1/EDK/bin/lin64/xps'
#Other ISEs
#echo "Xilinx 12 commands: ise12.4 ise xps xspdk"
#alias ise12.4='source /opt/Xilinx/12.4/ISE_DS/settings64.sh'
#alias ise='ise > /dev/null 2>&1 &'
#alias xps='xps > /dev/null 2>&1 &'
#alias xsdk='xsdk > /dev/null 2>&1 &'
################################################################################
# Altera Setup
################################################################################
##START if the host is specialName#
#HOST=`hostname -s`
#if [ "${HOST}" == 'specialName' ]; then
#  # Altera Setup
#  # Turn on 64-bit computing
#  if [ "`uname -m`" = "x86_64" ]; then
#    QUARTUS_64BIT=1
#    export QUARTUS_64BIT
#  fi
#  QUARTUS_ROOTDIR=/opt/altera/11.1/quartus
#  export QUARTUS_ROOTDIR
#  QUARTUS=/opt/altera/11.1/quartus/bin
#  SOPCBUILDER=/opt/altera/11.1/quartus/sopc_builder/bin
#  NIOSEDS=/opt/altera/11.1/nios2eds/bin
#  PATH=$QUARTUS:$SOPCBUILDER:$NIOSEDS:$PATH
#  export PATH
#  # allow niosII gcc
#  alias altera_nios='source /opt/altera/11.1/nios2eds/nios2_command_shell.sh'
#fi
alias compilerFPGA='(export ALTERAPATH="/opt/intel/FPGA_pro/20.2"
			export INTELFPGAOCLSDKROOT="${ALTERAPATH}/hld";
			export ALTERAOCLSDKROOT="${ALTERAPATH}/hld";
			export QSYS_ROOTDIR="${ALTERAPATH}/qsys/bin";
			export QUARTUS_ROOTDIR="${ALTERAPATH}/quartus";
			export QUARTUS_ROOTDIR_OVERRIDE="${QUARTUS_ROOTDIR}";
			export PATH=${PATH}:${ALTERAPATH}/quartus/bin;
			export PATH=${PATH}:${ALTERAPATH}/nios2eds/bin;
			export PATH=${PATH}:${ALTERAPATH}/modelsim_ase/bin;
			export PATH=${PATH}:${ALTERAPATH}/quartus/sopc_builder/bin;
			export PATH=${PATH}:${QSYS_ROOTDIR})'

	# Turn on 64-bit computing
	#if [ "`uname -m`" = "x86_64" ]; then
	#QUARTUS_64BIT=1
	#  export QUARTUS_64BIT
	#fi
#fi
alias aFPGA='${QUARTUS_ROOTDIR}/bin/qpro --64bit'
echo "Altera Commands: aFPGA"
################################################################################        
# Synplify_Pro
################################################################################
# source /usr/synopsys/D-2010.03/settings.sh
# source /usr/synopsys/2010_09-3/fpga_e201009sp3/settings.sh
################################################################################
# RISC V specific
################################################################################
# export JAVA_HOME=/opt/jdk1.8.0_192
# export PATH=${PATH}:${JAVA_HOME}/bin
export RISCV_GCCHOME=/opt/RISC-V/tools/riscv64-unknown-elf-gcc-8.2.0-2019.02.0-x86_64-linux-ubuntu14
export RISCV_OCDHOME=/opt/RISC-V/riscv-openocd-0.10.0-2019.02.0-x86_64-linux-ubuntu14
export RISCV=${RISCV_GCCHOME}
export RISCV_OPENOCD=${RISCV_OCDHOME}
echo "RISC-V"
echo "    $RISCV"
echo "    $RISCV_OPENOCD"
################################################################################        
# CUDA
################################################################################
#export PATH=/usr/local/cuda-10.2/bin${PATH:+:${PATH}}
#export LD_LIBRARY_PATH=/usr/local/cuda-10.2/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
################################################################################        
# Anaconda
################################################################################
# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
function function_CondaLoad() {
__conda_setup="$('/opt/anaconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/opt/anaconda3/etc/profile.d/conda.sh" ]; then
        . "/opt/anaconda3/etc/profile.d/conda.sh"
    else
        export PATH="/opt/anaconda3/bin:$PATH"
    fi
fi
unset __conda_setup
}
# <<< conda initialize <<<
################################################################################        
# Anti-Virus and malware
################################################################################
function function_UpdateClamav() {
sudo ps ax | grep freshclamd
sudo ps ax | grep [c]lamd
sudo apt-get update
sudo apt-get install clamav clamav-daemon
sudo chown -R clamav:clamav /var/log/clamav
sudo killall clamav
sudo killall freshclam
sudo service clamav-daemon stop
sudo service clamav-freshclam stop
sudo freshclam
sudo service clamav-freshclam start
sudo service clamav-daemon start
sudo service --status-all | grep clamav
sudo ps ax | grep freshclamd
sudo ps ax | grep [c]lamd
}
################################################################################        
# Echo Bash
################################################################################
echo 'sudo bash profile at /root/.bash_profile'
echo 'Bash location is /etc/bash.bashrc'
echo 'Path view by echo PATH variable'
# echo $PATH
# echo '/etc/enviroment has proxy info'
echo 'To run Desktop Icons: exo-open Quartus_Prime_Pro_19.2.desktop'
################################################################################        
# Alias
################################################################################
# You know what I meant keys
alias cd..='cd ..'
alias pdw="pwd"
alias ping='ping -c 5'
alias mkdir='mkdir -p '
alias grep='grep --color=auto'
alias diff='colordiff'
alias d='date +%F'
alias now='date +"%T"'
alias nowtime=now
alias nowdate='date +"%m-%d-%Y"'
alias wget='wget -c'
alias tgz='tar -zxvf'
alias tbz='tar -jxvf'
alias untar='tar -zxvf '
alias unrar='rar e' # Unrar alias
# MS-DOS
alias cls=clear
alias dir="ls"
alias copy="cp"
alias rename="mv"
alias md="mkdir"
alias rd="rmdir"
alias del="rm -i"
# Nice ls format (flags)
alias ls="ls -F --color=tty -T 0"
alias lla='ll -A' # hidden
# Simple
alias ip='/sbin/ifconfig eth0'
alias ipMore="nmcli dev show | grep 'IP'"
# History search (use: hs sometext)
alias hs='history | grep $1'
# Opens current directory in a file explorer
alias explore='nautilus .'
# Opens current directory in a file explorer with super user privileges
alias suexplore='sudo nautilus .'
# Opens current directory in Ubuntu's Disk Usage Analyzer GUI with super user privileges in the background
alias analyze='gksudo baobab . &'
## Get top process eating memory
alias psmem='ps auxf | sort -nr -k 4'
alias psmem10='ps auxf | sort -nr -k 4 | head -10'
## Get top process eating cpu ##
alias pscpu='ps auxf | sort -nr -k 3'
alias pscpu10='ps auxf | sort -nr -k 3 | head -10'
## Get GPU ram on desktop / laptop##
alias gpumeminfo='grep -i --color memory /var/log/Xorg.0.log'
# Disk Usage Commands
alias du='du -h'
alias usage='du -smh ~'
alias usagelist='du -skh * .[a-zA-Z0-9]* | sort -n'
# Redshift
echo 'Reduce Eye Strain by using runFluxReset runFluxOne runFluxTwo'
alias runFluxReset='redshift -x&'
alias runFluxOne='redshift -c ~/.config/redshift.conf &'
alias runFluxTwo='redshift -c ~/.config/redshift_external.conf &'
# Updates repo cache and installs all kinds of updates
alias updateOS='sudo apt-get update && sudo apt-get upgrade -y'
alias upgradeOS='sudo apt-get update && sudo apt-get upgrade -y && sudo apt-get dist-upgrade -y'
alias updateBoot='sudo update-initramfs -u'
alias condaLoad='function_CondaLoad'
alias updateAnaconda='conda update --force conda -y && conda update anaconda -y && conda update --all && conda update anaconda-navigator && conda update python'
# Remote SSH
export LOCALHOST="host `hostname` | awk '{print $4}'"
alias loginSelf='ssh -X $(USER)@$(LOCALHOST)'
alias loginPort='ssh -fN -R *:4000:localhost:4000 $(USER)@$(LOCALHOST)'
alias updateDefrag='e4defrag -c /home'
alias goPlaid='sudo tuned-adm profile latency-performance'
alias goSnail='sudo tuned-adm profile laptop-battery-powersave'
alias updateAV='function_UpdateClamav'
alias scanAV='sudo clamscan --max-filesize=3999M --max-scansize=3999M --exclude-dir=/sys/* --exclude-dir=/mnt/* -i -r /'
alias VROCiWatch='watch cat /proc/mdstat'
alias VROCiViewDetails='sudo mdadm --detail --scan'
################################################################################        
# Nil
################################################################################
