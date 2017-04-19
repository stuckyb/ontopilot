@echo off

:: The location of the main OntoPilot program, relative to this launch script.
set ONTOPILOTPATH=..\python-src\ontopilot_main.py

:: The location of the Jython run-time JAR, relative to this launch script.
set JYTHONPATH=..\java-lib\jython-full.jar

:: The location of the Java run-time binary.  If no location is set, we assume
:: that "java" is in the user's PATH somewhere.
set JAVAPATH=java

:: Check if java is installed.
if "%JAVA_HOME%"=="" (
	echo ERROR: The Java run-time environment appears to be missing.
	echo Please install Java in order to run OntoPilot.
	exit
)

:: Run OntoPilot, passing on all command-line arguments.
%JAVAPATH% -jar "%~dp0%JYTHONPATH%" "%~dp0%ONTOPILOTPATH%" %*