#!/usr/bin/env python
import sys
from cx_Freeze import setup, Executable
 
includefiles = ['README.md','CHANGELOG.md']
 
# GUI applications require a different base on Windows (the default is for
# a console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"
 
setup(  name = "bpc",
        version = "0.9.0",
        description = "Bitbucket Python Client",
        options = {'build_exe': {'include_files':includefiles}},
        executables = [Executable("bpc.py", base=base)])
