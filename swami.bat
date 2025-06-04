@echo off

python swami.py %1.sw -o %* -b "-target x86_64-w64-mingw64" 
