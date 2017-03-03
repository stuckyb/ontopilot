
#
# Manages the process of building import module OWL files from source
# ontologies and terms tables.
#

# Python imports.
import os
from ontobuilder import logger
from tablereaderfactory import TableReaderFactory
from tablereader import TableRowError
from importmodulebuilder import ImportModuleBuilder
from ontobuilder import TRUE_STRS
from rfc3987 import rfc3987
from buildtarget import BuildTargetWithConfig
from basic_buildtargets import BuildDirTarget
from collections import namedtuple

# Java imports.


# Define a simple "struct"-like type for storing imports module file name/IRI
# pairs.
ModuleInfo = namedtuple('ModuleInfo', ['filename', 'iristr'])


# Required columns in terms files.
REQUIRED_COLS = ('Termsfile', 'IRI')

# Optional columns in terms files.
OPTIONAL_COLS = ('Ignore',)


class ImportsBuildTarget(BuildTargetWithConfig):
    """
    A build target for compiling the imports modules.
    """
    def __init__(self, args, config=None):
        """
        args: A "struct" of configuration options (typically, parsed
            command-line arguments).  The only required member is 'config_file'
            (string).
        config: An OntoConfig instance.
        """
        BuildTargetWithConfig.__init__(self, args, config)

        self.addDependency(BuildDirTarget(args, self.config))

        # The string builddir is the path to a build directory where, at a
        # minimum, source ontologies can be cached.  If we are doing an
        # out-of-source build, this will also be the location for the compiled
        # imports modules, specified by outputdir.  For in-source builds,
        # outputdir will be the final destination for the imports modules.
        self.builddir = self.config.getBuildDir()
        if self.config.getDoInSourceBuilds():
            self.outputdir = self.config.getImportsDir()
        else:
            self.outputdir = self.builddir

        self._checkFiles()
        self._readImportsSource()

        # Initialize the ImportModuleBuilder.
        self.mbuilder = ImportModuleBuilder(
                        self.config.getImportsDevBaseIRI(),
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

        # Verify that a terms file was provided.  If not, we will import the
        # entire source ontology, so just return an empty string.
        if termsfile_path == '':
            return ''

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

    def getImportsInfo(self):
        """
        Returns a list of ModuleInfo objects that contain file name/IRI pairs
        for all import modules defined for the ontology (that is, imports that
        are defined in the top-level imports source file).  For cases where the
        entire source ontology will be imported, the IRI of the source ontology
        is included.
        """
        modinfos = []
        for row in self.tablerows:
            if row['abs_tfilepath'] == '':
                modinfo = ModuleInfo(filename='', iristr=row['IRI'])
            else:
                modinfo = ModuleInfo(
                    filename=self.mbuilder.getModulePath(row['IRI']),
                    iristr=self.mbuilder.getModuleIRIStr(row['IRI'])
                )

            modinfos.append(modinfo)

        return modinfos

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
        # Create the destination directory, if needed.  We only need to check
        # this for in-source builds, since the BuildDirTarget dependency will
        # take care of this for out-of-source builds.
        if self.config.getDoInSourceBuilds():
            if not(os.path.isdir(self.outputdir)):
                self._makeDirs(self.outputdir)

        for row in self.tablerows:
            termsfile_path = row['abs_tfilepath']

            if termsfile_path != '':
                if self.mbuilder.isBuildNeeded(row['IRI'], termsfile_path):
                    logger.info(
                        'Building the {0} ({1}) import module.'.format(
                            row['name'], row['IRI']
                        )
                    )
                    self.mbuilder.buildModule(row['IRI'], termsfile_path)
                else:
                    logger.info(
                        'The {0} ({1}) import module is already up to '
                        'date.'.format(row['name'], row['IRI'])
                    )

