
from ConfigParser import RawConfigParser
import os.path as path
import glob
import urllib, urlparse
from rfc3987 import rfc3987
from ontobuilder import logger, TRUE_STRS


class ConfigError(Exception):
    """
    A basic exception class for reporting errors in the build configuration
    file.
    """
    def __init__(self, msg):
        msg = 'Configuration file error:\n  ' + msg
        Exception.__init__(self, msg)


class OntoConfig(RawConfigParser):
    """
    Parses ontology build configuration files and provides convenient access to
    the configuration values.  Convenience methods are provided that retrieve
    specific configuration values.  To ensure robust error handling, all
    configuration settings should normally be accessed with the convenience
    methods, but configuration values can also be accessed generically using
    the usual ConfigParser methods (e.g., get(), getint(), etc.).
    """
    def __init__(self, filename):
        """
        Reads the configuration information and checks that the configuration
        file contains all required information.
        """
        # Call the superclass constructor.
        RawConfigParser.__init__(self)

        # Call the superclass read() method.
        filesread = RawConfigParser.read(self, filename)

        if len(filesread) == 0:
            raise IOError(
                'The configuration file, ' + filename
                + ', could not be opened.'
            )

        self.conffile = filename
        self.confdir = path.dirname(path.abspath(filename))

        self.checkConfig()

    def _getAbsPath(self, pathstr):
        """
        Given a path string, returns an equivalent absolute path.  If pathstr
        is relative, it is interpreted relative to the location of the parsed
        configuration file.
        """
        if path.isabs(pathstr):
            return path.normpath(pathstr)
        else:
            return path.normpath(path.join(self.confdir, pathstr))

    def getOntFileBase(self):
        """
        Returns the name of the ontology file without the file extension.
        """
        ontfname = path.basename(self.getOntologyFilePath())

        return path.splitext(ontfname)[0]

    def getConfigFilePath(self):
        return path.abspath(self.conffile)

    def getCustom(self, section, option, default=''):
        """
        Equivalent to the standard get() method, except getCustom() includes a
        default return value ('' by default).  If the specified option does not
        exist or is empty, the default value is returned.  Option values are
        also trimmed of all leading and trailing whitespace.
        """
        if self.has_option(section, option):
            optval = self.get(section, option).strip()
            if optval == '':
                optval = default
        else:
            optval = default

        return optval

    def checkConfig(self):
        """
        Performs some basic checks to make sure the configuration file is
        valid.  If any problems are found, a ConfigError exception is thrown.
        """
        if not(self.has_section('Ontology')):
            raise ConfigError(
                'The "Ontology" section was not found in the build \
configuration file.  This section is required and must contain the variables \
"termsfiles" and "ontologyIRI".  To correct this error, add the line \
"[Ontology]" to your configuration file.  See the example configuration file \
for more information.'
            )

        # The only setting that is always required is the path to the compiled
        # ontology file.
        self.getOntologyFilePath()

    def getOntologyIRI(self):
        """
        Returns the IRI for the main ontology file.
        """
        iristr = self.getCustom('Ontology', 'ontologyIRI', '')

        if iristr != '':
            # Verify that we have a valid absolute IRI string.
            if rfc3987.match(iristr, rule='absolute_IRI') == None:
                raise ConfigError(
                    'Invalid ontology IRI string in the build configuration file: "'
                    + iristr + '".'
                )

        return iristr

    def getLocalOntologyIRI(self):
        """
        Returns a local file:// IRI for the compiled ontology document.  This
        can be used, e.g., if no IRI is provided for the ontology.
        """
        abs_ontpath = self.getOntologyFilePath()
        ontIRIstr = urlparse.urljoin(
            'file://localhost', urllib.pathname2url(abs_ontpath)
        )

        return ontIRIstr

    def getOntologyFilePath(self):
        """
        Returns the full path to the compiled ontology file.  If no name was
        provided in the configuration file, the name will be extracted from the
        ontology's IRI, if possible.
        """
        ontfname = self.getCustom('Ontology', 'ontology_file', '')

        if ontfname == '':
            raise ConfigError(
                    'An ontology file name was not provided.  Please set the \
value of the "ontology_file" setting in the build configuration file.'
            )

        return self._getAbsPath(ontfname)

    def getTermsDir(self):
        """
        Returns the path to the directory of the terms/entities source files.
        """
        pathstr = self.getCustom('Ontology', 'termsdir', 'src/terms')
        
        return self._getAbsPath(pathstr)

    def getTermsFilePaths(self):
        """
        Returns a list of full paths to all input terms/entities files.
        """
        tfilesraw = self.getCustom('Ontology', 'termsfiles', '').split(',')

        # Remove any empty terms file names.
        tfileslist = []
        for tfnameraw in tfilesraw:
            if tfnameraw.strip() != '':
                tfileslist.append(tfnameraw.strip())

        # Generate the locations of all terms files.
        termsfolder = self.getTermsDir()
        pathslist = [path.join(termsfolder, fname) for fname in tfileslist]

        return pathslist

    def getDoInSourceBuilds(self):
        """
        Returns True if builds should be in source; returns False otherwise.
        """
        insource_str = self.getCustom('Build', 'insource_builds', 'False')

        return insource_str.lower() in TRUE_STRS

    def getBuildDir(self):
        """
        Returns the path to the build directory.
        """
        default = 'build'
        pathstr = self.getCustom('Build', 'builddir', default)
        pathstr = self._getAbsPath(pathstr)

        return pathstr

    def getBaseOntologyPath(self):
        """
        Returns the path to the base ontology file.  If no such value is
        explicitly provided in the configuration file, a sensible default is
        used.
        """
        default = 'src/' + self.getOntFileBase() + '-base.owl'
        baseontpath = self.getCustom('Ontology', 'base_ontology_file', default)
        baseontpath = self._getAbsPath(baseontpath)

        return baseontpath

    def getImportsSrcDir(self):
        """
        Returns the path to the directory of the import modules sources.
        """
        default = 'src/imports'
        pathstr = self.getCustom('Imports', 'imports_src', default)
        pathstr = self._getAbsPath(pathstr)

        return pathstr

    def getImportsDir(self):
        """
        Returns the path to the compiled import modules.
        """
        default = 'imports'
        pathstr = self.getCustom('Imports', 'imports_dir', default)
        pathstr = self._getAbsPath(pathstr)

        return pathstr

    def getTopImportsFilePath(self):
        """
        Returns the path to the top-level imports source file.
        """
        pathstr = self.getCustom('Imports', 'top_importsfile', '')
        if pathstr != '':
            pathstr = self._getAbsPath(pathstr)
        else:
            pattern = path.join(self.getImportsSrcDir(), 'imported_ontologies.*')
            plist = glob.glob(pattern)
            if len(plist) > 0:
                pathstr = plist[0]
            else:
                pathstr = path.join(self.getImportsSrcDir(), 'imported_ontologies.csv')

        return pathstr
    
    def getLocalModulesBaseIRI(self):
        """
        Returns a local file:// base IRI for the compiled import modules.  This
        can be used, e.g., if no IRI is explicitly provided for either the
        ontology or the import modules, or if a modules base IRI cannot be
        automatically generated from the ontology IRI.
        """
        abs_path = self.getImportsDir()
        ontIRIstr = urlparse.urljoin(
            'file://localhost', urllib.pathname2url(abs_path)
        )

        return ontIRIstr

    def getModulesBaseIRI(self):
        """
        Returns the base IRI to use when generating import modules.
        """
        iristr = self.getCustom('Imports', 'mod_baseIRI', '')
        ontIRI = self.getOntologyIRI()

        if iristr != '':
            # Verify that we have a valid absolute IRI string.
            if rfc3987.match(iristr, rule='absolute_IRI') == None:
                raise ConfigError(
                    'Invalid modules base IRI string in the build configuration file: "'
                    + iristr + '".  Please check the value of the "mod_baseIRI" variable.'
                )
        elif ontIRI != '':
            # Attempt to generate a suitable modules base IRI from the main
            # ontology IRI.

            # Get the relative path to the ontology document.
            ontpath = path.relpath(self.getOntologyFilePath(), self.confdir)

            # Get the relative path to the imports modules.
            importspath = path.relpath(self.getImportsDir(), self.confdir)

            # Get the path portion of the ontology IRI.
            parts = rfc3987.parse(ontIRI, rule='absolute_IRI')
            iripath = parts['path']

            # See if the local, relative ontology document path matches the end
            # of the IRI path.  If so, we can generate the imports IRI path.
            if iripath.endswith(ontpath):
                index = iripath.rfind(ontpath)
                iripath = path.join(iripath[:index], importspath)

                parts['path'] = iripath
                iristr = rfc3987.compose(**parts)
            else:
                logger.warning(
                    'Unable to automatically generate a suitable base IRI for \
the import modules because the path in the main ontology IRI does not appear \
to follow the project folder structure.  Please set the value of the \
"mod_baseIRI" setting in the build configuration file.'
                )

        # If all other attempts to get a modules base IRI failed, use a local
        # file system IRI.
        if iristr == '':
            iristr = self.getLocalModulesBaseIRI()

        return iristr

    def getImportModSuffix(self):
        """
        Returns the suffix string to use for generating import module file
        names.
        """
        default = '_' + self.getOntFileBase() + '_import_module.owl'
        suffix = self.getCustom('Imports', 'import_mod_suffix', default)

        return suffix

