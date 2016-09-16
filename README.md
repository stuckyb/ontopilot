# Ontobuilder: An Ontology Development and Build System

## Introduction

Ontobuilder is a system for managing the development of ontologies.  It began as the development/build system for the [Plant Phenology Ontology (PPO)](https://github.com/PlantPhenoOntology/PPO), but because its use has expanded beyond the PPO, ontobuilder is now maintained as a separate project.

The key idea behind ontobuilder is the use of simple, familiar, tabular data formats, such as CSV files, to manage the specification and development of an ontology.  Ontology components are described as rows in tabular data files, and these files then become the "source code" for "compiling" the ontology.  This has multiple benefits, including:

1. Familiar spreadsheet software, such as LibreOffice Calc and Excel, become tools for writing ontologies.
2. Ontology development is easily modularized by organizing terms into separate source files.
3. Anyone with basic spreadsheet skills can contribute to ontology development without investing a great deal of time in learning specialized ontology editing tools or ontology implementation languages.  This makes it much easier for domain experts to directly participate in the process of creating an ontology.

Ontobuilder is intended to manage two major tasks in ontology development: importing existing terms from other ontologies, and defining new terms in a new ontology.  As mentioned, both of these tasks are controlled by a set of simple, tabular data files that act as the source code for building a new, complete ontology.


## How to develop ontologies with ontobuilder

To begin developing a new ontology with ontobuilder, follow these steps:

* [Install ontobuilder](../../wiki/Installation)
* [Create a new ontology project](../../wiki/Creating-a-new-ontology-project)
* [Define new terms for the ontology](../../wiki/Ontology-development)
* [Define the ontology's import modules](../../wiki/Managing-imports)
* [Build the ontology](../../wiki/Building-an-ontology)

