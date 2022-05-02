# !/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Daniel Garces, Joseph Tarango
# *****************************************************************************/
import os, datetime, traceback, optparse, shutil
import PyInstaller.__main__


def main():
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--installer", dest='installer', action='store_true',
                      default=False, help='Boolean to create installer executable. If false, GUI executable is created '
                                          'instead')
    (options, args) = parser.parse_args()

    if options.installer is True:
        print("Generating Installer...")
        pwd = os.getcwd()
        dirPath = os.path.join(pwd, 'data/installer')
        if os.path.exists(dirPath) and os.path.isdir(dirPath):
            print("Previous executable exists. Removing it before generating the new one")
            shutil.rmtree(dirPath)

        PyInstaller.__main__.run([
            'src/installer.py',
            '--onefile',
            '--clean',
            '--debug=all',
            # '--windowed',
            '--key=RAADEngineTesting123456',
            '--workpath=data/installer/temp',
            '--distpath=data/installer',
            '--specpath=data/installer'
        ])
    else:
        print("Generating main GUI...")
        pwd = os.getcwd()
        dirPath = os.path.join(pwd, 'data/binary')
        if os.path.exists(dirPath) and os.path.isdir(dirPath):
            print("Previous executable exists. Removing it before generating the new one")
            shutil.rmtree(dirPath)
        logoLocation = '{0}/src/software/{1}'.format(os.getcwd(), 'Intel_IntelligentSystems.png')
        newLocation = '{0}/data/binary/software'.format(os.getcwd())
        PyInstaller.__main__.run([
            'src/software/gui.py',
            '--onefile',
            '--clean',
            '--debug=all',
            # '--windowed',
            '--add-data=' + logoLocation + os.pathsep + ".",
            '--key=RAADEngineTesting123456',
            '--workpath=data/binary/temp',
            '--distpath=data/binary',
            '--specpath=data/binary',
        ])
        os.mkdir(newLocation)
        shutil.copyfile(logoLocation, newLocation + '/Intel_IntelligentSystems.png')


if __name__ == '__main__':
    """Performs execution delta of the process."""
    pStart = datetime.datetime.now()
    try:
        main()
    except Exception as errorMain:
        print("Fail End Process: {0}".format(errorMain))
        traceback.print_exc()
    qStop = datetime.datetime.now()
    print("Execution time: " + str(qStop - pStart))
