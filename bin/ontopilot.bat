@echo off

setlocal 

rem The location of the main OntoPilot program, relative to this launch script.
set ONTOPILOTPATH=..\python-src\ontopilot_main.py

rem The location of the Jython run-time JAR, relative to this launch script.
set JYTHONPATH=..\java-lib\jython-full.jar

rem The location of the Java run-time binary.  If no location is set, we assume
rem that "java" is in the user's PATH somewhere.
set JAVAPATH=java

rem Get the location of this launch script.  If the script was not run from a
rem symlink, the next two lines are all we need.
set SRCPATH=%~f0
set SRCDIR=%~dp0

rem If SRCPATH is a symlink, resolve the link (and any subsequent links) until we
rem arrive at the actual script location.
:while
dir "%SRCPATH%" | find "<SYMLINK>" >nul && (
 	for /f "tokens=2 delims=[]" %%i in ('dir "%SRCPATH%"* ^| find "<SYMLINK>"') do set link=%%i

 	set SRCPATH=%link%

 	rem If the link target is a relative path, it is relative to the original
	rem symlink location, so we must construct a new path for the link target
	rem based on SRCDIR (the original symlink location).
 	if "%SRCPATH:~1,1%" neq ":" (
 		set SRCPATH=%SRCDIR%\%SRCPATH%
 	)

 	for %%m in ("%link%") do (
 		set SRCDIR=%%~dpm
 	)

 	dir "%SRCPATH%" | find "<SYMLINK>" >nul && (
 		goto :while
 	)
)

endlocal

rem Check if java is installed.
where java >nul 2>&1
if %ERRORLEVEL% neq 0 (
	echo ERROR: The Java run-time environment appears to be missing.
	echo Please install Java in order to run OntoPilot.
	exit 1
)

rem Run OntoPilot, passing on all command-line arguments.
%JAVAPATH% -jar "%SRCDIR%%JYTHONPATH%" "%SRCDIR%%ONTOPILOTPATH%" %*