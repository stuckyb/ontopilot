
from ConfigParser import RawConfigParser
import os.path as path
import glob
from rfc3987 import rfc3987


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
    def read(self, filename):
        """
        Reads the configuration information and checks that the configuration file
        contains all required information.
        """
        # Call the superclass read() method.
        filesread = RawConfigParser.read(self, filename)

        if len(filesread) == 0:
            raise ConfigError(
                'The configuration file ' + filename + ' could not be opened.'
            )

        self.checkConfig()

        self.confdir = path.dirname(path.abspath(filename))

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

    def _getOntFileBase(self):
        """
        Returns the name of the ontology file without the file extension.
        """
        return path.splitext(self.getOntologyFileName())[0]

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
        if not(self.has_section('Main')):
            raise ConfigError(
                'The "Main" section was not found in the build configuration \
file.  This section is required and must contain the variables "termsfiles" \
and "ontologyIRI".  To correct this error, add the line "[Main]" to your \
configuration file.  See the example configuration file for more information.'
            )

    def getOntologyIRI(self):
        """
        Returns the IRI for the main ontology file.
        """
        iristr = self.getCustom('Main', 'ontologyIRI', '')

        if iristr == '':
            raise ConfigError(
                'No ontology IRI was provided.  Please set the value of the \
"ontologyIRI" setting in the build configuration file.'
            )

        # Verify that we have a valid absolute IRI string.
        if rfc3987.match(iristr, rule='absolute_IRI') == None:
            raise ConfigError(
                'Invalid ontology IRI string in the build configuration file: "'
                + iristr + '".'
            )

        return iristr

    def getOntologyFileName(self):
        """
        Returns the name of the compiled ontology file.  If no name was
        provided in the configuration file, the name will be extracted from the
        ontology's IRI, if possible.
        """
        ontfname = self.getCustom('Ontology', 'ontology_file', '')

        if ontfname == '':
            parts = rfc3987.parse(self.getOntologyIRI(), rule='absolute_IRI')
            ontfname = path.basename(parts['path'])

            if ontfname == '':
                raise ConfigError(
                    'An ontology file name was not provided, and a suitable \
name could not be automatically extracted from the ontology IRI.  Please set \
the value of the "ontology_file" setting in the build configuration file.'
                )

        return ontfname

    def getTermsFilePaths(self):
        """
        Returns a list of full paths to all input terms/entities files.
        """
        tfilesraw = self.getCustom('Main', 'termsfiles', '').split(',')

        # Remove any empty terms file names.
        tfileslist = []
        for tfnameraw in tfilesraw:
            if tfnameraw.strip() != '':
                tfileslist.append(tfnameraw.strip())

        if len(tfileslist) == 0:
            raise ConfigError(
                'No ontology entities/terms files were provided.  Please \
set the value of the "termsfiles" setting in the build configuration file.'
            )

        # Get the location of the terms files.
        termsfolder = ''
        if self.has_option('Ontology', 'termsdir'):
            termsfolder_raw = self.get('Ontology', 'termsdir')
            termsfolder = self._getAbsPath(termsfolder_raw)
        else:
            termsfolder = path.join(self.confdir, 'src/terms')

        pathslist = [path.join(termsfolder, fname) for fname in tfileslist]

        return pathslist

    def getBaseOntologyPath(self):
        """
        Returns the path to the base ontology file.  If no such value is
        explicitly provided in the configuration file, a sensible default is
        used.
        """
        default = 'src/' + self._getOntFileBase() + '-base.owl'
        baseontpath = self.getCustom('Ontology', 'base_ontology_file', default)
        baseontpath = self._getAbsPath(baseontpath)

        return baseontpath

    def getImportsDir(self):
        """
        Returns the path to the directory of the import modules sources.
        """
        default = 'src/imports'
        pathstr = self.getCustom('Imports', 'importsdir', default)
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
            pattern = path.join(self.getImportsDir(), 'imported_ontologies.*')
            plist = glob.glob(pattern)
            if len(plist) > 0:
                pathstr = plist[0]
            else:
                pathstr = path.join(self.getImportsDir(), 'imported_ontologies.csv')

        return pathstr

    def getModulesBaseIRI(self):
        """
        Returns the base IRI to use when generating import modules.
        """
        iristr = self.getCustom('Imports', 'mod_baseIRI', '')

        if iristr != '':
            # Verify that we have a valid absolute IRI string.
            if rfc3987.match(iristr, rule='absolute_IRI') == None:
                raise ConfigError(
                    'Invalid modules base IRI string in the build configuration file: "'
                    + iristr + '".'
                )
        else:
            # Attempt to generate a suitable modules base IRI from the main
            # ontology IRI.
            # Get the name of the containing directory of the ontology
            # document.
            parts = rfc3987.parse(self.getOntologyIRI(), rule='absolute_IRI')
            pathparts = path.split(path.dirname(parts['path']))

            if pathparts[1] == 'ontology':
                parts['path'] = pathparts[0] + '/' + 'imports'
                iristr = rfc3987.compose(**parts)
            else:
                raise ConfigError(
                    'Unable to automatically generate a suitable base IRI for \
the import modules because the path in the main ontology IRI does not appear \
to follow the default project folder structure.  Please set the value of the \
"mod_baseIRI" setting in the build configuration file.'
                )

        return iristr

    def getImportModSuffix(self):
        """
        Returns the suffix string to use for generating import module file
        names.
        """
        default = '_' + self._getOntFileBase() + '_import_module.owl'
        suffix = self.getCustom('Imports', 'import_mod_suffix', default)

        return suffix

