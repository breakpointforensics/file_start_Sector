# file_start_Sector
Example Module that leverages several TSK binaries to determine starting sector value for given file.

Deciphers the starting sector of a given file by automatically parsing the files root volumes stats, drive parameters, and file inode information.

Requirements:
    -Python 3.5 or newer
    Additional Modules Required:
        -elevate
            (pip install elevate)

Use:
1. Download whole repo including TSK folder to same directory as 'file_start_Sector.py'.
2. Execute 'file_start_Sector.py'.
3. Follow prompts to select target file.
