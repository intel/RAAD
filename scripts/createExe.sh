#!/usr/bin/env sh
echo "RAAD binary creator."

# Parameters
EXE_CANDIDATE=src/main.py
ICONFILE=src/software/Intel_IntelligentSystems.ico

SAVEPATH=data/binary
TMPPATH=$SAVEPATH/tmp

TOKENNAME=RADEngine
FILENAME=$TOKENNAME.run

KEY=RADEngineTesting123456
KEYFILE=$SAVEPATH/key_for_program.txt

ZIPFILE=$SAVEPATH/$TOKENNAME.zip

LOGFILE=$SAVEPATH/pyinstaller.log

echo "Removing old files"
rm -r $SAVEPATH

echo "Creating folders"
mkdir -p $SAVEPATH $TMPPATH

echo "Creating main exe file"
pyinstaller --windowed --noconfirm --log-level=DEBUG --clean --onefile --icon=$ICONFILE --key=$KEY --workpath=$TMPPATH --distpath=$SAVEPATH --specpath=$SAVEPATH --name=$FILENAME $EXE_CANDIDATE 2>&1 | sed -r 's/'$(echo -e "\033")'\[[0-9]{1,2}(;([0-9]{1,2})?)?[mK]//g' | tee $LOGFILE

echo "Creating key file $KEYFILE"
echo "$KEY" > $KEYFILE

echo "Creating zip file $ZIPFILE with files $SAVEPATH/$FILENAME $KEYFILE "
# High compression with a flat folder structure and no root directory
zip -9 -j -D $ZIPFILE $SAVEPATH/$FILENAME $KEYFILE

echo "Modifying permissions"
chmod 755 -R $SAVEPATH
