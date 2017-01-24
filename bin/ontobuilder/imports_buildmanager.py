
#
# Manages the process of building import module OWL files from source
# ontologies and terms tables.
#

# Python imports.
import os
from tablereaderfactory import TableReaderFactory
from importmodulebuilder import ImportModuleBuilder
from ontobuilder import TRUE_STRS


# Required columns in terms files.
REQUIRED_COLS = ('Termsfile', 'IRI')

# Optional columns in terms files.
OPTIONAL_COLS = ('Ignore',)


class ImportsBuildManager:
    def __init__(self, config, builddir):
        """
        config: An OntoConfig instance.
        builddir: The path of the build directory.
        """
        self.config = config
        self.builddir = builddir

    def _checkFiles(self):
        """
        Verifies that all files and directories needed for the build exist.
        """
        # Verify that the top-level imports file exists.
        fpath = self.config.getTopImportsFilePath()
        if not(os.path.isfile(fpath)):
            raise RuntimeError(
                'The top-level imports source file could not be found: {0}.'.format(fpath)
            )
        
        # Verify that the build directory exists.
        if not(os.path.isdir(self.builddir)):
            raise RuntimeError(
                'The build directory does not exist: {0}.'.format(self.builddir)
            )

    def build(self):
        """
        Runs the imports build process and produces import module OWL files.
        """
        self._checkFiles()

        mbuilder = ImportModuleBuilder(
                        self.config.getModulesBaseIRI(), self.builddir
                    )
        
        ifpath = self.config.getTopImportsFilePath()
        outputsuffix = self.config.getImportModSuffix()

        with TableReaderFactory(ifpath) as ireader:
            for table in ireader:
                table.setRequiredColumns(REQUIRED_COLS)
                table.setOptionalColumns(OPTIONAL_COLS)
            
                for row in table:
                    if not(row['Ignore'].lower() in TRUE_STRS):
                        termsfile_path = row['Termsfile']
                        # If the termsfile path is a relative path, convert it
                        # to an absolute path using the location of the
                        # top-level imports table file as the base.
                        if not(os.path.isabs(termsfile_path)):
                            termsdir = os.path.dirname(os.path.abspath(ifpath))
                            termsfile_path = os.path.join(termsdir, termsfile_path)
                
                        if mbuilder.isBuildNeeded(row['IRI'], termsfile_path, outputsuffix):
                            print ('Building the ' + row['name'] + ' (' + row['IRI']
                                    + ') import module.')
                            mbuilder.buildModule(row['IRI'], termsfile_path, outputsuffix)
                        else:
                            print ('The ' + row['name'] + ' (' + row['IRI']
                                    + ') import module is already up-to-date.')

