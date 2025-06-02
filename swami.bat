@echo off

python swami.py %1.sw -o %* -b "-target x86_64-w64-mingw32 -static -Os -s" 
