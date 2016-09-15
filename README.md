# Ontobuilder: An Ontology Development and Build System

Ontobuilder is a system for managing the development of ontologies.  It began as the development/build system for the [Plant Phenology Ontology (PPO)](https://github.com/PlantPhenoOntology/PPO), but because its use has expanded beyond the PPO, ontobuilder is now maintained as a separate project.

The key idea behind ontobuilder is the use of simple, familiar, tabular data formats, such as CSV files, to manage the specification and development of an ontology.  Ontology components are described as rows in tabular data files, and these files then become the "source code" for "compiling" the ontology.  This has multiple benefits, including:

1. Familiar spreadsheet software, such as LibreOffice Calc and Excel, become tools for writing ontologies.
2. Ontology development is easily modularized by organizing terms into separate source files.
3. Anyone with basic spreadsheet skills can contribute to ontology development without investing a great deal of time in learning specialized ontology editing tools or ontology implementation languages.  This makes it much easier for domain experts to directly participate in the process of creating an ontology.

For detailed information about using ontobuilder for ontology development, please see the user documentation:

* [Building the PPO](../../wiki/Building-the-PPO): How to buld the import modules and compile the PPO.
* [Managing imports](../../wiki/Managing-imports): How to edit existing import modules and create new ones.
* [Ontology development](../../wiki/Ontology-development): How to edit and create PPO classes.
* [Creating a new release](../../wiki/Creating-a-release): How to generate a new PPO release.

