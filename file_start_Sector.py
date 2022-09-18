'''
Deciphers the starting sector of a given file by automatically parsing the files root volumes stats, drive parameters, and file inode information.
Requirements:
    -Python 3.5 or newer
    Additional Modules Required:
        -elevate
            (pip install elevate)
        
'''
from pathlib import Path
import datetime
import subprocess
from subprocess import Popen
from subprocess import STDOUT
from subprocess import PIPE
from builtins import input
from builtins import str
from builtins import object
import sys      #Imports the Standard Python sys module.
import time     #Imports the Standard Python time module.
import os       #Imports the Standard Python os module.
import stat     #Imports the Standard Python stat module.
import ctypes
import re
from elevate import elevate 
from tkinter import Tk  			    #Imports the standard Python Tkinter module as the alias Tk.
from tkinter.filedialog import askopenfilename      #Import just askopenfilename from tkFileDialog

###Check for admin privilages
def rootCheck():
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    
    print (f'Root Privilages = {is_admin}')
    if is_admin == False:
        elevate()    

##Call the check for root and auto escalate if not root
rootCheck()

##Add some sudoconstants
cwd = os.getcwd() 
volumePath = ''
mftstartSector = ''
timeguid = (str(int(time.time())))

##################################################
#Begin resource_path
##################################################
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


TSK_path = resource_path("TSK/bin")
TSK_path = TSK_path.replace("/", "\\")
os.environ['PATH'] += os.path.pathsep + TSK_path
##################################################
#End resource_path
##################################################

##################################################
#Begin runCommand
##Runs os level terminal command using subprocess in new Shell
##################################################
def runCommand(cmd, timeout=None, window=None):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
    output = ''
    for line in p.stdout:
        line = line.decode(errors='replace' if (sys.version_info) < (3, 5) else 'backslashreplace').rstrip()
        output += line
        print(line)
        window.Refresh() if window else None        # yes, a 1-line if, so shoot me
    retval = p.wait(timeout)
    return (retval, output)                         # also return the output just for fun
##################################################
#End runCommand
##################################################

##################################################
#Begin getCommandSTDOUT
##Runs os level terminal command and returns STDOUT directly back to function.
##################################################
def getCommandSTDOUT(command):
    process = Popen(
        args=command,
        stdout=PIPE,
        encoding='utf-8',
        shell=True
    )
    return process.communicate()[0]
##################################################
#End getCommandSTDOUT
##################################################
##################################################
#Start getDriveParameters
##################################################
def getDriveParameters(targetFile):
    #####################
    global timeguid
    tdlogfsstat = (workDirectory + '\\' + timeguid + '_FSStatdiskanalysis.log')
    ##Takes the targetFile and uses pathlib 'drive' module to get the drive letter file resids on.
    fpath = Path(targetFile)
    fileDriveLetter = fpath.drive
    print(fileDriveLetter)
    ##Build fsstat Command for verbose output  of specific partition stat to log files for parsing later
    global volumePath
    volumePath = '\\\.\\' + fileDriveLetter

    cmd = 'fsstat.exe ' + volumePath + ' > "' + str(tdlogfsstat) + '"'
    
    print (cmd)
    runCommand(cmd)
    #os.system(cmd)
    
    
    ##Open the FSStat output and grab FS Typed ID'd from first line
    print('Parsing FSSTAT Value')
    try:
        
        with open(tdlogfsstat) as f:
            fstype = f.readline().rstrip()
            for line in f:
                #print(str(line))
                if 'File System Type:' in line:
                    global FSType
                    FSType = line[18:26].strip()
                    print(f'File System Detected: {FSType}')
                
                if 'Sector Size:' in line:
                    global sectorSize
                    sectorSize = line[13:18].strip()
                    print(f'Sector Size Detected: {sectorSize}')
                    
                if 'Cluster Size:' in line:
                    global clusterSize
                    clusterSize = line[14:20].strip()
                    print(f'Cluster Size Detected: {clusterSize}')
    
                    

                
    except:
        print('Unable to parse ' + str(tdlogfsstat))
        pass
        
    ##Get the Sectors per cluster value
    try:
        global sectorspercluster
        sectorspercluster = int(int(clusterSize) / int(sectorSize))  
        print(f'{sectorspercluster} Sectors per Cluster')
    except Exception:
        print('Unable to Calculate SPS value')
        pass       

##################################################
#End getDriveParameters
##################################################

##################################################
#Start getFileInode
##################################################
def getFileInode(targetFile):
    #####################
    ##seperate drive letter from remaining filepath per ifind spec
    drive, fpath = os.path.splitdrive(targetFile)
    fpath = fpath.strip("\\")
    fpath = fpath.replace("\\","/")
    #print(fpath)
    timeguid = (str(int(time.time())))
    tdlogifind = (workDirectory + '\\' + '_inode#.log')

    ##Build ifind cmd syntax
    cmd = 'ifind.exe -a -n "' + fpath + '" ' + volumePath
    
    #print (cmd)
    fileInode = int(getCommandSTDOUT(cmd))

    #print(f'File Inode #: {fileInode}')

    return fileInode
       
    
##################################################
#End getFileInode
##################################################


##################################################
##Begin getStartSector 
##################################################

def getStartSector(targetFile,workDirectory):
    
    global mftstartSector
    
    EFIDetected = False
    MBRDetected = False
    print('Begin getStartSector')
    timeguid = (str(int(time.time())))
    targetFile = targetFile.replace("/", "\\")
    tdlogerror = (workDirectory + '\\' + timeguid + '_diskanalysisV.log')

    #print('---------------------------------------------')
    #print (tdlogfile)
    #print (targetFile)
    #print('---------------------------------------------')
    print('---------------------------------------------')
    print('Analyzing Disk Structure...')
    print('---------------------------------------------')
    
    #####################

    getDriveParameters(targetFile)
    fileInode = getFileInode(targetFile)
    print(f'File Inode # for {targetFile} is : {fileInode}')
    
      
    ####################    

    ##Build istat cmd syntax for to get targetfile stats
    cmd = 'istat -r ' + volumePath + ' ' + str(fileInode) + ' > istat.temp'
    runCommand(cmd)
    startaddress = 'resident'
    with open('istat.temp', 'r') as f:
        for line in f:
            if 'Starting address' in line:
                print(line)
                startaddress = line[19:29].strip()
                head,sep,tail = startaddress.partition(',')
                startaddress = (int(head))
                filestartSector = sectorspercluster * startaddress
    
    ##If file is resident do some parsing of MFT location and which is inode 0 and do some math to locate starting sector of targetfile mft file record
    if startaddress == 'resident':
        if mftstartSector == "":
            print('Need to Get MFT Lccation')
            cmd = 'istat -r ' + volumePath + ' ' + '0' + ' > istat.temp'
            runCommand(cmd)
            with open('istat.temp', 'r') as f:
                for line in f:        
                    if 'Starting address' in line:
                        print(line)
                        startaddress = line[19:29].strip()
                        head,sep,tail = startaddress.partition(',')
                        startaddress = (int(head))
                        mftstartSector = sectorspercluster * startaddress
                        print (f'MFT Starts at {mftstartSector}')
                        break
        else:
            print(f'Using previously identifed MFT location: {mftstartSector}')
        global sectorSize             
        filestartSector = int(((fileInode * 1024)/int(sectorSize)) + int(mftstartSector))
    
    print(f'Start Sector: {filestartSector}')

    
  
    return filestartSector       
##################################################
##End getStartSector
##################################################


workDirectory = cwd

def getInputFile():
    global targetFile
    Tk().withdraw() 
    print('Opening file selction window...')
    print('Please select a File to Analyze:')            
    #Call GUI based file open window using Tkinter.
    targetFile = askopenfilename(title='Please select file to identify starting sector of:', filetypes=[("Files","*")]) # show an "Open" dialog box and return the path to the selected file
    targetFile = targetFile.replace("/", "\\")


##Start while loop that will prompt for next file to get location of after previous locate completes.
while True:
    
    ##Call TK Window to get file
    getInputFile()
    if targetFile =="":
        ##The TK File Get window was closed without picking a file.  Close the program.
        sys.exit()
    
    ##Pass file input to getStartSector function
    getStartSector(targetFile,workDirectory)

