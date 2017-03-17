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

