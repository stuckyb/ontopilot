
#
# Manages the process of building an ontology from a base ontology file and
# zero or more input terms files.
#

# Python imports.
import os, glob, shutil
import re
import urllib, urlparse
from tablereaderfactory import TableReaderFactory
from owlontologybuilder import OWLOntologyBuilder, TermDescriptionError
from ontobuilder import TRUE_STRS
from imports_buildmanager import ImportsBuildManager
from ontoconfig import OntoConfig

# Java imports.
from org.semanticweb.owlapi.model import IRI


# Required columns in terms files.
REQUIRED_COLS = ('Type', 'ID')

# Optional columns in terms files.
OPTIONAL_COLS = (
    'Comments', 'Parent', 'Subclass of', 'Equivalent to', 'Disjoint with',
    'Ignore'
)
        
class ProjectCreator:
    """
    Contains methods for initializing the folder structure and starting files
    for a new ontology development project.
    """
    def __init__(self, targetdir, ontfilename, templatedir):
        """
        targetdir: The target project directory.
        ontfilename: A name to use for the new OWL ontology file
        templatedir: A directory containing project template files.
        """
        self.targetdir = os.path.abspath(targetdir)
        self.ontfilename = ontfilename
        self.templatedir = os.path.abspath(templatedir)

        if not(os.path.isdir(self.targetdir)):
            raise RuntimeError('The target directory for the new project, "{0}", could not be found.'.format(self.targetdir))

    def _copyAndModify(self, srcpath, destpath, replacements):
        """
        Copies a file from srcpath to destpath while searching for and
        replacing target strings in the source.

        srcpath: The source file.
        destpath: The destination file.
        replacements: A list/tuple of lists/tuples containing regex search
            patterns and replacement text.
        """
        with file(srcpath) as filein, file(destpath, 'w') as fileout:
            for line in filein:
                for replacement in replacements:
                    if replacement[0].search(line) != None:
                        line = replacement[0].sub(replacement[1], line)

                fileout.write(line)

    def _initConfig(self):
        """
        Copies the template configuration file and initializes it with the
        ontology file path and IRI.  Returns an initialized OntoConfig object.
        """
        configpath = os.path.join(self.templatedir, 'ontology.conf')
        ontname = os.path.splitext(os.path.basename(self.ontfilename))[0]

        if not(os.path.isfile(configpath)):
            raise RuntimeError(
                'Could not find the template ontology configuration file: {0}.'.format(configpath)
            )

        outpath = os.path.join(self.targetdir, 'ontology.conf')

        if os.path.exists(outpath):
            raise RuntimeError(
                'A project configuration file already exists in the target directory: {0}.  Please move, delete, or rename the existing configuration file before initializing a new project.'.format(outpath)
            )

        rel_ontpath = os.path.join('ontology', self.ontfilename)
        abs_ontpath = os.path.abspath(rel_ontpath)
        ontIRIstr = urlparse.urljoin(
            'file://localhost', urllib.pathname2url(abs_ontpath)
        )

        # Define regular expressions for recognizing specific configuration
        # settings and create the customized replacement settings strings.
        replacements = [
            (
                re.compile('^ontology_file =\s*$'),
                'ontology_file = {0}\n'.format(rel_ontpath)
            ),
            (
                re.compile('^ontologyIRI =\s*$'),
                'ontologyIRI = {0}\n'.format(ontIRIstr)
            ),
            (
                re.compile('^termsfiles =\s*$'),
                'termsfiles = {0}_classes.csv, {0}_properties.csv\n'.format(ontname)
            )
        ]

        # Copy and customize the template.
        try:
            self._copyAndModify(configpath, outpath, replacements)
        except IOError:
            raise RuntimeError(
                'The new project configuration file, "{0}", could not be created.  Please make sure that you have permission to create new files and directories in the new project location.'.format(outpath)
            )

        return OntoConfig(outpath)

    def _createProjectDirs(self, config):
        """
        Creates the folder structure for a new ontology project.

        config: An OntoConfig object from which to get the project folder
            structure.
        """
        # Get all project directory paths from the new project's configuration
        # file.
        dirnames = [
            config.getTermsDir(), config.getImportsSrcDir(),
            os.path.dirname(config.getOntologyFilePath()),
            config.getImportsDir()
        ]

        # Create the project directories.
        for dirname in dirnames:
            dirpath = os.path.join(self.targetdir, dirname)
            if not(os.path.isdir(dirpath)):
                if not(os.path.exists(dirpath)):
                    try:
                        os.makedirs(dirpath)
                    except OSError:
                        raise RuntimeError('The new project directory, "{0}", could not be created.  Please make sure that you have permission to create new files and directories in the new project location.'.format(dirpath))
                else:
                    raise RuntimeError('The path "{0}" already exists, but is not a directory.  This file must be moved, renamed, or deleted before the new project can be created.'.format(dirpath))

    def _createSourceFiles(self, config):
        """
        Creates the initial source files for a new ontology project.

        config: An OntoConfig object from which to get the project folder
            structure.
        """
        projname = config.getOntFileBase()

        # Define a regular expression/replacement pair for customizing sample
        # files with the new project's name.
        replacements = [
            (
                re.compile('ontname'),
                projname
            )
        ]

        # Copy and customize the top-level import file.
        srcpath = os.path.join(self.templatedir, 'imported_ontologies.csv')
        destpath = config.getTopImportsFilePath()
        try:
            self._copyAndModify(srcpath, destpath, replacements)
        except IOError:
            raise RuntimeError(
                'The new top-level imports file, "{0}", could not be created.  Please make sure that you have permission to create new files and directories in the new project location.'.format(destpath)
            )

        # Copy and rename the sample import terms file.
        srcpath = os.path.join(self.templatedir, 'bfo_sample_terms.csv')
        destpath = os.path.join(
            config.getImportsSrcDir(), 'bfo_{0}_terms.csv'.format(projname)
        )
        try:
            shutil.copyfile(srcpath, destpath)
        except IOError:
            raise RuntimeError(
                'The sample import terms file, "{0}", could not be created.  Please make sure that you have permission to create new files and directories in the new project location.'.format(destpath)
            )

        # Create a list of terms source file / destination pairs.
        copypairs = [
            (
                os.path.join(self.templatedir, 'sample_classes.csv'),
                '{0}_classes.csv'.format(projname)
            ),
            (
                os.path.join(self.templatedir, 'sample_properties.csv'),
                '{0}_properties.csv'.format(projname)
            )
        ]

        # Copy and rename the sample ontology terms files.
        for copypair in copypairs:
            destpath = os.path.join(
                config.getTermsDir(), copypair[1]
            )
            try:
                shutil.copyfile(copypair[0], destpath)
            except IOError:
                raise RuntimeError(
                    'The sample terms file, "{0}", could not be created.  Please make sure that you have permission to create new files and directories in the new project location.'.format(destpath)
                )

    def createProject(self):
        """
        Creates a new ontology project in the target directory.
        """
        # Copy in the template configuration file, customize the template, and
        # load the configuration settings.
        print 'Creating custom project configuration file...'
        config = self._initConfig()

        print 'Generating project folder structure...'
        self._createProjectDirs(config)

        print 'Creating initial source files...'
        self._createSourceFiles(config)

