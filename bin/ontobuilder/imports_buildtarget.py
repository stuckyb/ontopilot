
#
# Manages the process of building import module OWL files from source
# ontologies and terms tables.
#

# Python imports.
import os
from tablereaderfactory import TableReaderFactory
from tablereader import TableRowError
from importmodulebuilder import ImportModuleBuilder
from ontobuilder import TRUE_STRS
from rfc3987 import rfc3987
from buildtarget import BuildTarget
from basic_buildtargets import BuildDirTarget

# Java imports.


# Required columns in terms files.
REQUIRED_COLS = ('Termsfile', 'IRI')

# Optional columns in terms files.
OPTIONAL_COLS = ('Ignore',)


class ImportsBuildTarget(BuildTarget):
    """
    A build target for compiling the imports modules.
    """
    def __init__(self, config):
        """
        config: An OntoConfig instance.
        """
        BuildTarget.__init__(self)

        self.config = config
        self.addDependency(BuildDirTarget(self.config))

        # The string builddir is the path to a build directory where, at a
        # minimum, source ontologies can be cached.  If we are doing an
        # out-of-source build, this will also be the location for the compiled
        # imports modules, specified by outputdir.  For in-source builds,
        # outputdir will be the final destination for the imports modules.
        self.builddir = config.getBuildDir()
        if config.getDoInSourceBuilds():
            self.outputdir = config.getImportsDir()
        else:
            self.outputdir = self.builddir

        self._checkFiles()
        self._readImportsSource()

        # Initialize the ImportModuleBuilder.
        self.mbuilder = ImportModuleBuilder(
                        self.config.getModulesBaseIRI(),
                        self.config.getImportModSuffix(), self.builddir,
                        self.outputdir
                    )
        
    def _checkFiles(self):
        """
        Verifies that all files and directories needed for the build exist.
        Checking the build directory is taken care of by the BuildDirTarget
        build dependency.
        """
        # Verify that the top-level imports file exists.
        fpath = self.config.getTopImportsFilePath()
        if not(os.path.isfile(fpath)):
            raise RuntimeError(
                'The top-level imports source file could not be found: {0}.'.format(fpath)
            )
        
        # Check the imports directory if we are doing an in-source build.
        if self.config.getDoInSourceBuilds():
            if not(os.path.isdir(self.outputdir)):
                raise RuntimeError(
                    'The destination directory does not exist: {0}.'.format(self.builddir)
                )

    def _readImportsSource(self):
        """
        Reads the top-level imports source file (that is, the file that defines
        from which ontologies to generate import modules).  For each row, the
        source IRI is checked for errors, the absolute termsfile path is
        determined, and the row is added to self.tablerows.
        """
        ifpath = self.config.getTopImportsFilePath()

        self.tablerows = []

        with TableReaderFactory(ifpath) as ireader:
            for table in ireader:
                table.setRequiredColumns(REQUIRED_COLS)
                table.setOptionalColumns(OPTIONAL_COLS)
            
                for row in table:
                    if not(row['Ignore'].lower() in TRUE_STRS):
                        self._checkSourceIRI(row)
                        row['abs_tfilepath'] = self._getAbsTermsFilePath(row)

                        self.tablerows.append(row)

    def _getAbsTermsFilePath(self, trow):
        """
        Gets the absolute path to a terms file from an input table row.

        trow: An input table row.
        """
        termsfile_path = trow['Termsfile']

        # Verify that a terms file was provided.
        if termsfile_path == '':
            raise TableRowError(
                'No input terms file was provided.  Check the value of the "Termsfile" column.',
                trow
            )

        # If the termsfile path is a relative path, convert it to an absolute
        # path using the location of the top-level imports file as the base.
        if not(os.path.isabs(termsfile_path)):
            topfilepath = self.config.getTopImportsFilePath()
            termsdir = os.path.dirname(os.path.abspath(topfilepath))
            termsfile_path = os.path.join(termsdir, termsfile_path)

        # Verify that the terms file exists.
        if not(os.path.isfile(termsfile_path)):
            raise TableRowError(
                'Could not find the input terms file "{0}".'.format(termsfile_path),
                trow
            )

        return termsfile_path

    def _checkSourceIRI(self, trow):
        """
        Verifies that the source IRI string in an input table row (in the 'IRI'
        field) is a valid IRI.  Raises an exception if it is invalid.
        """
        # Verify that the source IRI is valid.
        if rfc3987.match(trow['IRI'], rule='absolute_IRI') == None:
            raise TableRowError(
                'Invalid source ontology IRI string: {0}.'.format(trow['IRI']),
                trow
            )

    def getImportsIRIs(self):
        """
        Returns a list of the IRIs for all import modules defined for the
        ontology (that is, import modules that are (or will be) generated by
        the import module build process).
        """
        mIRIs_list = []
        for row in self.tablerows:
            mIRIs_list.append(self.mbuilder.getModuleIRIStr(row['IRI']))

        return mIRIs_list

    def getBuildNotRequiredMsg(self):
        return 'All import modules are already up to date.'

    def _isBuildRequired(self):
        """
        Returns True if one or more of the import modules needs to be compiled.
        """
        for row in self.tablerows:
            if self.mbuilder.isBuildNeeded(row['IRI'], row['abs_tfilepath']):
                return True

        return False

    def _run(self):
        """
        Runs the imports build process and produces import module OWL files.
        """
        for row in self.tablerows:
            termsfile_path = row['abs_tfilepath']
    
            if self.mbuilder.isBuildNeeded(row['IRI'], termsfile_path):
                print ('Building the ' + row['name'] + ' (' + row['IRI']
                        + ') import module.')
                self.mbuilder.buildModule(row['IRI'], termsfile_path)
            else:
                print ('The ' + row['name'] + ' (' + row['IRI']
                        + ') import module is already up to date.')

