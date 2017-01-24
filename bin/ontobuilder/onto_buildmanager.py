
#
# Manages the process of building an ontology from a base ontology file and
# zero or more input terms files.
#

# Python imports.
import os
from tablereaderfactory import TableReaderFactory
from owlontologybuilder import OWLOntologyBuilder, TermDescriptionError
from ontobuilder import TRUE_STRS


# Required columns in terms files.
REQUIRED_COLS = ('Type', 'ID')

# Optional columns in terms files.
OPTIONAL_COLS = (
    'Comments', 'Parent', 'Subclass of', 'Equivalent to', 'Disjoint with',
    'Ignore'
)
        
class OntoBuildManager:
    def __init__(self, config, expanddefs=True):
        """
        config: An OntoConfig instance.
        expanddefs: Whether to add IDs to term references in definitions.
        """
        self.config = config
        self.expanddefs = expanddefs
        self.builddir = config.getBuildDir()

    def _checkFiles(self):
        """
        Verifies that all files and directories needed for the build exist.
        """
        # Verify that the base ontology file exists.
        fpath = self.config.getBaseOntologyPath()
        if not(os.path.isfile(fpath)):
            raise RuntimeError(
                'The base ontology file could not be found: {0}.'.format(fpath)
            )
        
        # Verify that the terms files exist.
        for fpath in self.config.getTermsFilePaths():
            if not(os.path.isfile(fpath)):
                raise RuntimeError(
                    'The source terms/entities file could not be found: {0}.'.format(fpath)
                )

        # Verify that the build directory exists.
        if not(os.path.isdir(self.builddir)):
            raise RuntimeError(
                'The build directory does not exist: {0}.'.format(self.builddir)
            )

    def _getOutputFilePath(self):
        """
        Returns the path of the compiled ontology file.
        """
        return os.path.join(
            self.builddir, self.config.getOntologyFileName()
        )

    def isBuildNeeded(self):
        """
        Checks if the compiled ontology already exists, and if so, whether file
        modification times indicate that the compiled ontology is already up to
        date.  Returns True if the compiled ontology needs to be updated.
        """
        foutpath = self._getOutputFilePath()

        if os.path.isfile(foutpath):
            mtime = os.path.getmtime(foutpath)

            # If the configuration file is newer than the compiled ontology, a
            # new build might be needed if new terms files have been added or
            # other ontology-related changes were made.
            if mtime < os.path.getmtime(self.config.getConfigFilePath()):
                return True

            # Check the modification time of the base ontology.
            if mtime < os.path.getmtime(self.config.getBaseOntologyPath()):
                return True

            # Check the modification time of each terms file.
            for termsfile in self.config.getTermsFilePaths():
                if mtime < os.path.getmtime(termsfile):
                    return True

            return False
        else:
            return True

    def build(self):
        """
        Runs the build process and produces a compiled OWL ontology file.
        """
        self._checkFiles()

        ontbuilder = OWLOntologyBuilder(self.config.getBaseOntologyPath())
        
        # Process each source file.  In this step, entities and label
        # annotations are defined, but processing of all other axioms (e.g.,
        # text definitions, comments, equivalency axioms, subclass of axioms,
        # etc.) is deferred until after all input files have been read.  This
        # allows forward referencing of labels and term IRIs and means that
        # entity descriptions and source files can be processed in any
        # arbitrary order.
        for termsfile in self.config.getTermsFilePaths():
            with TableReaderFactory(termsfile) as reader:
                print 'Parsing ' + termsfile + '...'
                for table in reader:
                    table.setRequiredColumns(REQUIRED_COLS)
                    table.setOptionalColumns(OPTIONAL_COLS)
        
                    for t_row in table:
                        if not(t_row['Ignore'].lower() in TRUE_STRS):
                            typestr = t_row['Type'].lower()
            
                            if typestr == 'class':
                                ontbuilder.addClass(t_row)
                            elif typestr == 'dataproperty':
                                ontbuilder.addDataProperty(t_row)
                            elif typestr == 'objectproperty':
                                ontbuilder.addObjectProperty(t_row)
                            elif typestr == 'annotationproperty':
                                ontbuilder.addAnnotationProperty(t_row)
                            elif typestr == '':
                                raise TermDescriptionError(
                                    'The entity type (e.g., "class", "data property") was not specified.',
                                    t_row
                                )
                            else:
                                raise TermDescriptionError(
                                    'The entity type "' + t_row['Type']
                                    + '" is not supported.', t_row
                                )

        # Define all deferred axioms from the source entity descriptions.
        print 'Defining all remaining entity axioms...'
        ontbuilder.processDeferredEntityAxioms(self.expanddefs)
        
        # Set the ontology ID, if a new ID was provided.
        ontbuilder.getOntology().setOntologyID(self.config.getOntologyIRI())
        
        # Write the ontology to the output file.
        fileoutpath = self._getOutputFilePath()
        print 'Writing compiled ontology to ' + fileoutpath + '...'
        ontbuilder.getOntology().saveOntology(fileoutpath)

