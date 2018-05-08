# Copyright (C) 2017 Brian J. Stucky
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# Python imports.
from __future__ import unicode_literals
from ConfigParser import RawConfigParser
import os.path
import glob
import urllib, urlparse
from rfc3987 import rfc3987
from ontopilot import logger, TRUE_STRS
from ontology import OUTPUT_FORMATS
from inferred_axiom_adder import INFERENCE_TYPES
from documentation_writers import DOC_FORMAT_TYPES

# Java imports.


# Strings for identifying supported OWL reasoners.
REASONER_STRS = ('HermiT', 'ELK', 'Pellet', 'JFact')

# The inference types to use by default.
DEFAULT_INFERENCE_TYPES = (
    'subclasses', 'equivalent classes', 'types', 'subdata properties',
    'subobject properties'
)


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
    def __init__(self, filename=None):
        """
        Reads a configuration file and checks that the file contains all
        required information.  If filename is None, an OntoConfig object will
        be created that returns only default values.
        """
        # Call the superclass constructor.
        RawConfigParser.__init__(self)

        if filename is not None:
            # Call the superclass read() method.
            filesread = RawConfigParser.read(self, filename)

            if len(filesread) == 0:
                raise IOError(
                    'The configuration file, ' + filename
                    + ', could not be opened.'
                )

            self.confdir = os.path.dirname(
                os.path.abspath(
                    os.path.realpath(os.path.expanduser(filename)))
            )
        else:
            # Use the current working directory as the configuration directory.
            self.confdir = os.path.dirname(
                os.path.abspath(
                    os.path.realpath(os.path.expanduser(os.getcwd())))
            )

        self.conffile = filename

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
    
    def getProjectDir(self):
        """
        Returns the path to the project's root directory, as determined by the
        location of the configuration file.
        """
        return self.confdir

    def getConfigFilePath(self):
        if self.conffile is not None:
            return os.path.abspath(os.path.realpath(os.path.expanduser(
                self.conffile
            )))
        else:
            return None

    def _getAbsPath(self, pathstr):
        """
        Given a path string, returns an equivalent absolute path with all
        symbolic links resolved and home directory references expanded.  If
        pathstr is relative, it is interpreted relative to the location of the
        parsed configuration file.
        """
        if os.path.isabs(pathstr):
            abspath = os.path.abspath(os.path.realpath(os.path.expanduser(
                pathstr
            )))
        else:
            abspath = os.path.abspath(os.path.realpath(os.path.expanduser(
                os.path.join(self.confdir, pathstr)
            )))

        return abspath

    def _isSubpathInPath(self, path, subpath):
        """
        Tests whether path is a parent path to subpath.  If so, returns True.
        If path is not a parent path to subpath, or the two paths are the same,
        returns False.
        """
        path = self._getAbsPath(path)
        subpath = self._getAbsPath(subpath)

        # If the parent path is the root directory ('/') or otherwise already
        # ends in a separator character, we need to strip the separator from
        # the end so we don't double it when we do the containment check.
        if path.endswith('/') or path.endswith('\\'):
            path = path[:-1]

        # Check for identical paths, either with or without a trailing
        # directory separator.
        if (
            (subpath == path) or
            (subpath == path + '/') or (subpath == path + '\\')
        ):
            return False

        # Check for subpath containment.  This should work on either Windows or
        # *nix systems.
        return (
            subpath.startswith(path + '\\') or subpath.startswith(path + '/')
        )

    def getOntFileBase(self):
        """
        Returns the name of the ontology file without the file extension.
        """
        ontfname = os.path.basename(self.getOntologyFilePath())

        return os.path.splitext(ontfname)[0]

    def getDevBaseIRI(self):
        """
        Returns the base IRI for non-released ontology documents and imports
        modules.
        """
        iristr = self.getCustom('IRIs', 'dev_base_IRI')

        if iristr != '':
            # Verify that we have a valid absolute IRI string.
            if rfc3987.match(iristr, rule='absolute_IRI') is None:
                raise ConfigError(
                    'Invalid development base IRI string in the build '
                    'configuration file: {0}.  Please check the value of the '
                    'setting "dev_base_IRI".'.format(iristr)
                )
        else:
            # No development base IRI was provided, so try to generate one from
            # the local file system.  If the IRI path starts with '///', we
            # have a Windows path that starts with a drive letter, and the
            # "localhost" authority should be omitted.
            urlpath = urllib.pathname2url(self.confdir)
            if urlpath.startswith('///'):
                urlstart = 'file:'
            else:
                urlstart = 'file://localhost'

            iristr = urlparse.urljoin(urlstart, urlpath)

        return iristr

    def getReleaseBaseIRI(self):
        """
        Returns the base IRI for released ontology documents and imports
        modules.
        """
        iristr = self.getCustom('IRIs', 'release_base_IRI')

        if iristr != '':
            # Verify that we have a valid absolute IRI string.
            if rfc3987.match(iristr, rule='absolute_IRI') is None:
                raise ConfigError(
                    'Invalid release base IRI string in the build '
                    'configuration file: "{0}".  Please check the value of '
                    'the setting "release_base_IRI".'.format(iristr)
                )
        else:
            # No development base IRI was provided, so use the development base
            # IRI.
            iristr = self.getDevBaseIRI()

        return iristr

    def _generatePathIRI(self, pathstr, baseIRI):
        """
        Generates an IRI for a path to a file or directory in the project.  The
        path must be a subpath of the main project directory.  If pathstr is a
        relative path, it is interpreted relative to the main project
        directory.  No attempt is made to confirm that the path is actually
        valid, so this method works just as well to generate IRIs for paths
        that do not (or do not yet) exist.

        pathstr: The path for which to create a corresponding development IRI.
        basIRI: The base IRI string to use when generating the final IRI.
        """
        # See if the path is inside of the project directory (as determined by
        # the location of the project configuration file).
        if not(self._isSubpathInPath(self.confdir, pathstr)):
            raise ConfigError(
                'The path "{0}" is not a subpath of the main project folder '
                '("{1}"), so no corresponding IRI can be automatically '
                'generated.'.format(pathstr, self.confdir)
            )
        
        if os.path.isabs(pathstr):
            # Convert the path to a path relative to the project directory.
            relpath = os.path.relpath(pathstr, self.confdir)
        else:
            relpath = pathstr

        # Parse the development base IRI and add the relative path.
        parts = rfc3987.parse(baseIRI, rule='absolute_IRI')
        iripath = os.path.join(urllib.url2pathname(parts['path']), relpath)

        parts['path'] = urllib.pathname2url(iripath)

        # If the IRI path starts with '///', then we have a Windows path that
        # starts with a drive letter, and the final IRI should not include any
        # host/authority string.
        if parts['path'].startswith('///'):
            parts['authority'] = None

        iristr = rfc3987.compose(**parts)

        return iristr

    def generateDevIRI(self, pathstr):
        """
        Generates a development IRI for a path to a file or directory in the
        project.  The path must be a subpath of the main project directory.  If
        pathstr is a relative path, it is interpreted relative to the main
        project directory.  No attempt is made to confirm that the path is
        actually valid, so this method works just as well to generate IRIs for
        paths that do not (or do not yet) exist.

        pathstr: The path for which to create a corresponding development IRI.
        """
        return self._generatePathIRI(pathstr, self.getDevBaseIRI())

    def generateReleaseIRI(self, pathstr):
        """
        Generates a release IRI for a path to a file or directory in the
        project.  The path must be a subpath of the main project directory.  If
        pathstr is a relative path, it is interpreted relative to the main
        project directory.  No attempt is made to confirm that the path is
        actually valid, so this method works just as well to generate IRIs for
        paths that do not (or do not yet) exist.

        pathstr: The path for which to create a corresponding release IRI.
        """
        return self._generatePathIRI(pathstr, self.getReleaseBaseIRI())

    def getImportsDevBaseIRI(self):
        """
        Returns the base IRI to use when generating import modules.
        """
        return self.generateDevIRI(self.getImportsDir())

    def getReleaseOntologyIRI(self):
        """
        Returns the IRI for the main released ontology.
        """
        iristr = self.getCustom('IRIs', 'release_ontology_IRI')

        if iristr != '':
            # Verify that we have a valid absolute IRI string.
            if rfc3987.match(iristr, rule='absolute_IRI') is None:
                raise ConfigError(
                    'Invalid release ontology IRI string in the build '
                    'configuration file: "{0}".  Please check the value of '
                    'the setting "release_ontology_IRI".'.format(iristr)
                )
        else:
            # No release ontology IRI was provided, so generate one from the
            # release base IRI.
            ontfname = os.path.basename(self.getOntologyFilePath())
            iristr = self.generateReleaseIRI(ontfname)

        return iristr

    def getOntologyFilePath(self):
        """
        Returns the full path to the base compiled ontology filename.  If an
        ontology build is requested, this setting must be provided.
        """
        ontfname = self.getCustom('Ontology', 'ontology_file', '')

        if ontfname == '':
            raise ConfigError(
                'An ontology file name was not provided.  Please set the '
                'value of the "ontology_file" setting in the "[Ontology]" '
                'section of the project configuration file.'
            )

        ontbasepath = self._getAbsPath(ontfname)

        # See if the ontology file is inside of the project directory (as
        # determined by the location of the project configuration file).
        if not(self._isSubpathInPath(self.confdir, ontbasepath)):
            raise ConfigError(
                'The compiled ontology file path ("{0}") is not a subpath of '
                'the main project folder ("{1}").  Please modify the value of '
                'the ontology_file setting in the project configuration file '
                'to correct this error.'.format(ontbasepath, self.confdir)
            )
        
        return ontbasepath

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

    def getEntitySourceDir(self):
        """
        Returns the absolute path to the directory of the terms/entities source
        files.
        """
        pathstr = self.getCustom('Ontology', 'entity_sourcedir', 'src/entities')
        
        return self._getAbsPath(pathstr)

    def getEntitySourceFilePaths(self):
        """
        Returns a list of full paths to all input terms/entities files.
        """
        tfilesraw = self.getCustom('Ontology', 'entity_sourcefiles', '')

        # Remove any empty terms file names.
        tfileslist = []
        for tfnameraw in tfilesraw.split(','):
            if tfnameraw.strip() != '':
                tfileslist.append(tfnameraw.strip())

        # Generate the locations of all terms files.
        termsfolder = self.getEntitySourceDir()
        pathslist = [os.path.join(termsfolder, fname) for fname in tfileslist]

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

    def getExpandEntityDefs(self):
        """
        Returns True if ontology entity text definitions should be modified by
        adding the IDs of term labels referenced in the definitions.  Returns
        False otherwise.
        """
        expand_str = self.getCustom('Build', 'expand_entity_defs', 'True')

        return expand_str.lower() in TRUE_STRS

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
        Returns the absolute path to the compiled import modules.
        """
        default = 'imports'
        pathstr = self.getCustom('Imports', 'imports_dir', default)
        pathstr = self._getAbsPath(pathstr)

        # See if the imports directory is inside of the project directory (as
        # determined by the location of the project configuration file).
        if not(self._isSubpathInPath(self.confdir, pathstr)):
            raise ConfigError(
                'The compiled imports modules folder ("{0}") is not a subpath '
                'of the main project folder ("{1}").  Please modify the value '
                'of the imports_dir setting in the project configuration file '
                'to correct this error.'.format(pathstr, self.confdir))
        
        return pathstr

    def getTopImportsFilePath(self):
        """
        Returns the path to the top-level imports source file.
        """
        pathstr = self.getCustom('Imports', 'top_importsfile', '')
        if pathstr != '':
            pathstr = self._getAbsPath(pathstr)
        else:
            pattern = os.path.join(
                self.getImportsSrcDir(), 'imported_ontologies.*'
            )
            plist = glob.glob(pattern)
            if len(plist) > 0:
                pathstr = plist[0]
            else:
                pathstr = os.path.join(
                    self.getImportsSrcDir(), 'imported_ontologies.csv'
                )

        return pathstr
    
    def getImportModSuffix(self):
        """
        Returns the suffix string to use for generating import module file
        names.
        """
        default = '_' + self.getOntFileBase() + '_import_module.owl'
        suffix = self.getCustom('Imports', 'import_mod_suffix', default)

        return suffix

    def getReasonerStr(self):
        """
        Returns the string identifying the reasoner to use.  If this option is
        not configured, use "HermiT" as the default.
        """
        reasoner = self.getCustom('Reasoning', 'reasoner', 'HermiT')

        if not(reasoner.lower() in [rstr.lower() for rstr in REASONER_STRS]):
            raise ConfigError(
                'Invalid value for the "reasoner" setting in the build '
                'configuration file: "{0}".  Supported values are: '
                '{1}.'.format(
                    reasoner, '"' + '", "'.join(REASONER_STRS) + '"'
                )
            )

        return reasoner

    def getInferenceTypeStrs(self):
        """
        Returns a list of strings identifying the types of inferred axioms to
        generate when running a reasoner on an ontology.  If this option is not
        configured, the defaults configured at the top of this file
        (DEFAULT_INFERENCE_TYPES) will be used.
        """
        rawval = self.getCustom('Reasoning', 'inferences', '')

        raw_inf_strs = [strval.strip() for strval in rawval.split(',')]

        # Make sure all of the inference types are valid, and ignore empty type
        # strings (this can happen, e.g., if the raw string contains a comma
        # without a value on one side of it).
        inf_strs = []
        for inf_str in raw_inf_strs:
            if inf_str != '':
                if not(inf_str.lower() in INFERENCE_TYPES):
                    raise ConfigError(
                        'Invalid inference type for the "inferences" setting '
                        'in the build configuration file: "{0}".  Supported '
                        'values are: "{1}".'.format(
                            inf_str, '", "'.join(INFERENCE_TYPES)
                        )
                    )
                else:
                    inf_strs.append(inf_str)

        if len(inf_strs) == 0:
            inf_strs = list(DEFAULT_INFERENCE_TYPES)

        return inf_strs

    def getAnnotateInferred(self):
        """
        Returns True if inferred axioms should be annotated as such; returns
        False otherwise.
        """
        annotate_inferred = self.getCustom(
            'Reasoning', 'annotate_inferred', 'False'
        )

        return annotate_inferred.lower() in TRUE_STRS

    def getPreprocessInverses(self):
        """
        Returns True if inverse object property assertions and inverse negative
        object property assertions should be added to the ontology prior to
        generating inferred axioms with a reasoner; returns False otherwise.
        """
        preprocess_inverses = self.getCustom(
            'Reasoning', 'preprocess_inverses', 'False'
        )

        return preprocess_inverses.lower() in TRUE_STRS

    def getExcludedTypesFile(self):
        """
        Returns the path to a file containing excluded types information.  If
        this setting is not defined, returns an empty string.
        """
        etfpath = self.getCustom('Reasoning', 'excluded_types_file', '')
        if etfpath != '':
            etfpath = self._getAbsPath(etfpath)

        return etfpath

    def getAnnotateMerged(self):
        """
        Returns True if entities that are merged into the main ontology from an
        external ontology should be annotated with the 'imported from'
        (IAO:0000412) annotation property to indicate their origin; returns
        False otherwise.  The default is True.
        """
        annotate_merged = self.getCustom(
            'Imports', 'annotate_merged', 'True'
        )

        return annotate_merged.lower() in TRUE_STRS

    def getOutputFormat(self):
        """
        Returns the string identifying the output format to use.  If this
        option is not configured, use "RDF/XML" as the default.
        """
        oformat = self.getCustom('Build', 'output_format', 'RDF/XML')

        if not(oformat.lower() in [ofstr.lower() for ofstr in OUTPUT_FORMATS]):
            raise ConfigError(
                'Invalid value for the "output_format" setting in the build '
                'configuration file: "{0}".  Supported values are: '
                '{1}.'.format(
                    oformat, '"' + '", "'.join(OUTPUT_FORMATS) + '"'
                )
            )

        return oformat

    def getDocSpecificationFile(self):
        """
        Returns the path to a file containing documentation specification.  If
        this setting is not defined, returns "src/doc_specification.txt" as the
        default.
        """
        specpath = self.getCustom(
            'Documentation', 'doc_specification', 'src/doc_specification.txt'
        )
        specpath = self._getAbsPath(specpath)

        return specpath

    def getDocsFilePath(self):
        """
        Returns the absolute path to the base name to use for compiled user
        documentation.  If no such value is explicitly provided in the
        configuration file, a sensible default is used.
        """
        default = 'documentation/' + self.getOntFileBase()
        raw_docsfpath = self.getCustom(
            'Documentation', 'docs_file_path', default
        )
        docsfpath = self._getAbsPath(raw_docsfpath)

        # Make sure we got a base name to use for generating documentation file
        # names.
        if os.path.basename(docsfpath) == '':
            raise ConfigError(
                'Invalid value for the "docs_file_path" setting in the project '
                'configuration file: "{0}".  Please provide a base file name '
                'to use for generating documentation file names.'.format(
                    raw_docsfpath
                )
            )

        return docsfpath

    def getDocFormats(self):
        """
        Returns a list of strings identifying the formats to use when
        generating documentation files.  If this option is not configured,
        ['HTML'] will be returned.
        """
        rawval = self.getCustom('Documentation', 'doc_formats', '')

        raw_format_strs = [strval.strip() for strval in rawval.split(',')]

        LC_DOC_FORMAT_TYPES = [fstr.lower() for fstr in DOC_FORMAT_TYPES]

        # Make sure all of the inference types are valid, and ignore empty
        # format strings (this can happen, e.g., if the raw string contains a
        # comma without a value on one side of it).
        format_strs = []
        for format_str in raw_format_strs:
            if format_str != '':
                if not(format_str.lower() in LC_DOC_FORMAT_TYPES):
                    raise ConfigError(
                        'Invalid documentation format string for the '
                        '"doc_formats" setting in the build configuration '
                        'file: "{0}".  Supported values are: "{1}".'.format(
                            format_str, '", "'.join(DOC_FORMAT_TYPES)
                        )
                    )
                else:
                    format_strs.append(format_str)

        if len(format_strs) == 0:
            format_strs = ['HTML']

        return format_strs

