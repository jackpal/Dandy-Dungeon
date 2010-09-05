@if "%_echo%"=="" echo off

setlocal

REM Configure the sample, i.e. where to find the F# compiler and C# compiler.

if "%FSHARP_HOME%"=="" ( set FSHARP_HOME=..\..\..)
if "%FSC%"=="" ( set FSC=%FSHARP_HOME%\bin\fsc.exe )


REM -----------------------------------------
REM Build the sample

%FSC% --target-winexe --define COMPILE -g dandy.fs
if ERRORLEVEL 1 goto Exit

echo *** 
echo *** You can now run dandy.exe
echo *** 

:Exit
endlocal

exit /b %ERRORLEVEL%

