# OntoPilot: An Ontology Development and Build System

## Introduction

OntoPilot is a system for managing the development of ontologies.  The key idea behind OntoPilot is the use of simple, familiar, tabular data formats, such as spreadsheet files or CSV files, to manage the specification and development of an ontology.  Ontology components are described as rows in tabular data files, and these files then become the "source code" for "compiling" the ontology.  This has multiple benefits, including:

1. Familiar spreadsheet software, such as LibreOffice Calc and Excel, become tools for writing ontologies.
2. Ontology development is easily modularized by organizing terms into separate source files.
3. Anyone with basic spreadsheet skills can contribute to ontology development without investing a great deal of time in learning specialized ontology editing tools or ontology implementation languages.  This makes it much easier for domain experts to directly participate in the process of creating and reviewing an ontology.

OntoPilot is intended to manage three major tasks in ontology development: 1) importing existing terms from other ontologies; 2) defining new terms in a new ontology; and 3) generating release versions of an ontology.  These tasks are controlled by a simple project configuration file and a set of tabular data files that act as the source code for building a new, complete ontology.


## How to develop ontologies with OntoPilot

To develop an ontology with OntoPilot, follow these steps:

1. [Install OntoPilot](../../wiki/Installation)
1. [Create a new ontology project](../../wiki/Creating-a-new-ontology-project)
1. [Define new terms for the ontology](../../wiki/Ontology-development)
1. [Define the ontology's import modules](../../wiki/Managing-imports)
1. [Build the ontology](../../wiki/Building-an-ontology)
1. [Make a release version of the ontology](../../wiki/Releasing-an-ontology)


################################################################################
## Based on the example project: https://github.com/jsbruneau/jython-selfcontained-jar/
################################################################################

This package is organized as follows:

 * /etc 
    Placeholder for config files. All files here will be copied over the /dist
	folder.
	
 * /java-lib 
    Put all of your external java libraries (.jar) here

 * /java-src
	All java source code you might need in your app. For now we have a launcher (Main.java) and a trust provider that disable certificate validation for SSL connections to force Jython's behaviour to resemble more CPython
	
 * /python-lib
	Placeholder for any pure python external libraries. They will be added to the sys.path

 * /python-src
	Your python code. When the jar gets executed, a file called entrypoint.py will be executed.
	

Building the app:

    You need Apache Ant installed. It should be sufficient to just 
    run 'ant' in the same directory as build.xml
    
    Ant should create a new jar file called dist/OntoApp.jar
    which you can then run:

        java -jar dist/OntoApp.jar


Building Jython:
  
    Jython is already included in this distribution, but when new
    versions of Jython come out, you may wish to upgrade. These are
    the instructions you'll need for modifying the Jython jar that the
    Jython installer builds so that it will work in a One-Jar
    environment:

    * Download the latest Jython standalone installer (right now it's 2.7.0) :

        wget http://search.maven.org/remotecontent?filepath=org/python/jython-installer/2.7.0/jython-installer-2.7.0.jar

    * Extract the installer, there's no need to run it:
        
	mkdir jython-exploded
	cd jython-exploded
	unzip ../jython-installer-2.7.0.jar

    * Add the Lib/ folder to a new jython jar:
        
	cp jython.jar jython-full.jar
	zip -r jython-full.jar Lib/

    * jython-full.jar is now a complete Jython install in a single jar
      file.
      
      Should be about 11MB. Simply place it inside the /java-lib directory or edit the build.xml accordingly.

    
