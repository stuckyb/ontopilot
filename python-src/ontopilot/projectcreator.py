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

#
# Manages the process of creating a new ontology project.
#

# Python imports.
from __future__ import unicode_literals
import os, shutil
import re
from ontopilot import logger
from ontoconfig import OntoConfig

# Java imports.


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
            raise RuntimeError(
                'The target directory for the new project, "{0}", could not '
                'be found.'.format(self.targetdir)
            )

    def _copyAndModify(self, srcpath, destpath, replacements):
        """
        Copies a file from srcpath to destpath while searching for and
        replacing target strings in the source.  The search and replace values
        are provided as a list (or tuple) of lists (or tuples), each of which
        is a pair for which the first element is a regular expression search
        pattern and the second element is replacement text.

        srcpath: The source file.
        destpath: The destination file.
        replacements: A list/tuple of lists/tuples containing regex search
            patterns and replacement text.
        """
        if not(os.path.isfile(srcpath)):
            raise RuntimeError(
                'The ontology project template file, "{0}", could not be '
                'found.  Please check that the software was installed '
                'correctly.'.format(srcpath)
            )

        try:
            with file(srcpath) as filein, file(destpath, 'w') as fileout:
                for line in filein:
                    for replacement in replacements:
                        if replacement[0].search(line) is not None:
                            line = replacement[0].sub(replacement[1], line)

                    fileout.write(line)
        except IOError:
            raise RuntimeError(
                'The ontology project file, "{0}", could not be created.  '
                'Please make sure that you have permission to create new '
                'files and directories in the new project '
                'location.'.format(destpath)
            )

    def _initConfig(self):
        """
        Copies the template configuration file and initializes it with a
        variety of project-specific settings.  Returns an initialized
        OntoConfig object.
        """
        configpath = os.path.join(self.templatedir, 'project.conf')
        ontname = os.path.splitext(os.path.basename(self.ontfilename))[0]

        if not(os.path.isfile(configpath)):
            raise RuntimeError(
                'Could not find the template project configuration file: '
                '{0}.'.format(configpath)
            )

        outpath = os.path.join(self.targetdir, 'project.conf')

        if os.path.exists(outpath):
            raise RuntimeError(
                'A project configuration file already exists in the target '
                'directory: {0}.  Please move, delete, or rename the existing '
                'configuration file before initializing a new '
                'project.'.format(outpath)
            )

        rel_ontpath = os.path.join('ontology', self.ontfilename)

        # Define regular expressions for recognizing specific configuration
        # settings and create the customized replacement settings strings.
        replacements = [
            (
                re.compile('^ontology_file =\s*$'),
                'ontology_file = {0}\n'.format(rel_ontpath)
            ),
            (
                re.compile('^entity_sourcefiles =\s*$'),
                (
                    'entity_sourcefiles = {0}_*.csv, {0}_*.ods, {0}_*.xls, '
                    '{0}_*.xlsx\n'.format(ontname)
                )
            ),
            (
                re.compile('^imports_src =\s*$'),
                'imports_src = src/imports/\n'
            ),
            (
                re.compile('^imports_dir =\s*$'),
                'imports_dir = imports/\n'
            ),
            (
                re.compile('^entity_sourcedir =\s*$'),
                'entity_sourcedir = src/entities/\n'
            )
        ]

        # Copy and customize the template.
        self._copyAndModify(configpath, outpath, replacements)
        
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
            config.getEntitySourceDir(), config.getImportsSrcDir(),
            os.path.dirname(config.getOntologyFilePath()),
            config.getImportsDir(), os.path.dirname(config.getDocsFilePath())
        ]

        # Create the project directories.
        for dirname in dirnames:
            dirpath = os.path.join(self.targetdir, dirname)
            if not(os.path.isdir(dirpath)):
                if not(os.path.exists(dirpath)):
                    try:
                        os.makedirs(dirpath)
                    except OSError:
                        raise RuntimeError(
                            'The new project directory, "{0}", could not be '
                            'created.  Please make sure that you have '
                            'permission to create new files and directories '
                            'in the new project location.'.format(dirpath)
                        )
                else:
                    raise RuntimeError(
                        'The path "{0}" already exists, but is not a '
                        'directory.  This file must be moved, renamed, or '
                        'deleted before the new project can be '
                        'created.'.format(dirpath)
                    )

    def _robustCopy(self, sourcepath, destpath):
        """
        A robust file copy that checks for some common error conditions and
        generates error message that try to be helpful to end users.
        """
        if not(os.path.isfile(sourcepath)):
            raise RuntimeError(
                'The ontology project template file, "{0}", could not be '
                'found.  Please check that the software was installed '
                'correctly.'.format(sourcepath)
            )

        try:
            shutil.copyfile(sourcepath, destpath)
        except IOError:
            raise RuntimeError(
                'The ontology project file, "{0}", could not be created.  '
                'Please make sure that you have permission to create new '
                'files and directories in the new project '
                'location.'.format(destpath)
            )

    def _createSourceFiles(self, config):
        """
        Creates the initial source files for a new ontology project.

        config: An OntoConfig object from which to get the project settings.
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
        self._copyAndModify(srcpath, destpath, replacements)

        # Copy and rename the sample import terms file.
        srcpath = os.path.join(self.templatedir, 'bfo_sample_entities.csv')
        destpath = os.path.join(
            config.getImportsSrcDir(), 'bfo_{0}_entities.csv'.format(projname)
        )
        self._robustCopy(srcpath, destpath)

        # Create a list of terms source file / destination pairs.
        copypairs = [
            ('sample_classes.csv', '{0}_classes.csv'.format(projname)),
            ('sample_properties.csv', '{0}_properties.csv'.format(projname)),
            ('sample_individuals.csv', '{0}_individuals.csv'.format(projname))
        ]

        # Copy and rename the sample ontology terms files.
        for copypair in copypairs:
            srcpath = os.path.join(self.templatedir, copypair[0])
            destpath = os.path.join(config.getEntitySourceDir(), copypair[1])
            self._robustCopy(srcpath, destpath)

        # Copy and rename the base ontology file.
        srcpath = os.path.join(self.templatedir, 'sample-base.owl')
        destpath = config.getBaseOntologyPath()
        self._robustCopy(srcpath, destpath)

        # Copy and customize the documentation specification file.
        docspec_fname = 'doc_specification.txt'
        srcpath = os.path.join(self.templatedir, docspec_fname)
        destpath = os.path.join(
            os.path.dirname(config.getDocSpecificationFile()), docspec_fname
        )
        self._copyAndModify(srcpath, destpath, replacements)

    def createProject(self):
        """
        Creates a new ontology project in the target directory.
        """
        # Copy in the template configuration file, customize the template, and
        # load the configuration settings.
        logger.info('Creating custom project configuration file...')
        config = self._initConfig()

        logger.info('Generating project folder structure...')
        self._createProjectDirs(config)

        logger.info('Creating initial source files...')
        self._createSourceFiles(config)

