@echo off
REM Remove all intermediate and output files.

cd ..

del /q /s /a:H *.suo
del /q /s *.dll
del /q /s *.exe
del /q /s *.pdb

del /q /s WindowsDandy\WindowsDandy\bin
del /q /s WindowsDandy\WindowsDandy\Media
del /q /s WindowsDandy\WindowsDandy\obj

del /q /s Xbox360Dandy\Xbox360Dandy\bin
del /q /s Xbox360Dandy\Xbox360Dandy\Media
del /q /s Xbox360Dandy\Xbox360Dandy\obj

cd utils
