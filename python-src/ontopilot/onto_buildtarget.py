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
# Manages the process of building an ontology from a base ontology file and
# zero or more input terms files.
#

# Python imports.
from __future__ import unicode_literals
import os
import glob
from ontopilot import logger
from basictimer import BasicTimer
from tablereaderfactory import TableReaderFactory
from owlontologybuilder import OWLOntologyBuilder, EntityDescriptionError
from ontopilot import TRUE_STRS
from buildtarget import BuildTargetWithConfig
from imports_buildtarget import ImportsBuildTarget

# Java imports.


# Required columns in terms files.
REQUIRED_COLS = ('Type', 'ID')

# Optional columns in terms files.
OPTIONAL_COLS = (
    'Comments', 'Text definition', 'Parent', 'Subclass of', 'Superclass of',
    'Equivalent to', 'Disjoint with', 'Inverse', 'Characteristics',
    'Relations', 'Data facts', 'Annotations', 'Ignore', 'Subproperty of',
    'Superproperty of', 'Domain', 'Range'
)
        
class OntoBuildTarget(BuildTargetWithConfig):
    def __init__(self, args, cfgfile_required=True, config=None):
        """
        args: A "struct" of configuration options (typically, parsed
            command-line arguments).  The required members are
            'no_def_expand' (boolean) and 'config_file' (string).
        cfgfile_required (optional): Whether a config file is required.
        config (optional): An OntoConfig object.
        """
        BuildTargetWithConfig.__init__(self, args, cfgfile_required, config)

        # Determine whether to add IDs to term references in definitions.
        self.expanddefs = self.config.getExpandEntityDefs()

        # Set the imports modules as a dependency, regardless of whether we're
        # using in-source or out-of-source builds.  Either way, it is probably
        # best for end users to make sure imports modules remain updated.  Of
        # course, for out-of-source builds, it is up to the user to make sure
        # the imports modules get copied to their destination location.
        self.ibt = ImportsBuildTarget(args, False, self.config)
        self.addDependency(self.ibt)

    def _isGlobPattern(self, pstr):
        """
        Returns True if pstr contains any shell-style wildcards.  The results
        are only correct for strings that are syntactically valid, and this
        method does not attempt to detect syntax problems.
        """
        # Check for brackets that contain more than one character.  If the
        # brackets only contain one character, then they do not really define a
        # wildcard.
        in_bracket = False
        bracket_chr_cnt = 0
        for char in pstr:
            if (char == '[') and not(in_bracket):
                in_bracket = True
                bracket_char_cnt = 0
            elif in_bracket:
                if char == ']':
                    in_bracket = False
                    if bracket_chr_cnt > 1:
                        return True
                else:
                    bracket_chr_cnt += 1

        # Check for '*' and '?' wildcards that are not escaped with brackets.
        for i in range(len(pstr)):
            if pstr[i] in ('*', '?'):
                if i == 0:
                    return True
                elif i == (len(pstr) - 1):
                    return True
                elif not((pstr[i-1] == '[') and (pstr[i+1] == ']')):
                    return True

        return False

    def _getExpandedSourceFilesList(self):
        """
        Prepares the list of terms files by expanding any paths with
        shell-style wildcards.  Verifies that each path string resolves to one
        or more valid paths, and eliminates any duplicate paths.
        """
        pathsset = set()

        # Attempt to expand each terms path string and eliminate any duplicate
        # paths by building a set of path strings.
        for fpath in self.config.getEntitySourceFilePaths():
            flist = glob.glob(fpath)
            if (len(flist) == 0) and not(self._isGlobPattern(fpath)):
                raise RuntimeError(
                    'The source terms/entities file(s) could not be found: '
                    '{0}.'.format(fpath)
                )
            for filename in flist:
                pathsset.add(filename)

        return list(pathsset)

    def _retrieveAndCheckFilePaths(self):
        """
        Verifies that all files and directories needed for the build exist.
        Once file paths are retrieved from the OntoConfig instance, expanded,
        and verified, they are cached as instance attributes for later use in
        the build process.
        """
        # Verify that the base ontology file exists.
        fpath = self.config.getBaseOntologyPath()
        if not(os.path.isfile(fpath)):
            raise RuntimeError(
                'The base ontology file could not be found: {0}.'.format(fpath)
            )
        self.base_ont_path = fpath

        # Verify that the terms files exist and are of correct type.  The
        # method _getExpandedSourceFilesList() ensures that all paths are valid
        # in the list it returns.
        pathslist = self._getExpandedSourceFilesList()
        for fpath in pathslist:
            if not(os.path.isfile(fpath)):
                raise RuntimeError(
                    'The source terms/entities path "{0}" exists, but is not '
                    'a valid file.'.format(fpath)
                )
        self.termsfile_paths = pathslist

    def getImportsBuildTarget(self):
        """
        Returns the ImportsBuildTarget instance on which this build target
        depends.
        """
        return self.ibt

    def getOutputFilePath(self, add_suffix=True):
        """
        Returns the path of the compiled ontology file.
        """
        rawpath = self.config.getOntologyFilePath()

        if add_suffix:
            # Change the file name so that it ends with the suffix '-raw'.
            pathparts = os.path.splitext(rawpath)
            rawpath = pathparts[0] + '-raw' + pathparts[1]

        if self.config.getDoInSourceBuilds():
            destpath = rawpath
        else:
            ontfilename = os.path.basename(rawpath)
            destpath = os.path.join(self.config.getBuildDir(), ontfilename)

        return destpath

    def getBuildNotRequiredMsg(self):
        return 'The compiled ontology is already up to date.'

    def _isBuildRequired(self):
        """
        Checks if the compiled ontology already exists, and if so, whether file
        modification times indicate that the compiled ontology is already up to
        date.  Returns True if the compiled ontology needs to be updated.
        """
        foutpath = self.getOutputFilePath()

        self._retrieveAndCheckFilePaths()

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

            # Check the modification time of each source entities file.
            for sourcefile in self._getExpandedSourceFilesList():
                if mtime < os.path.getmtime(sourcefile):
                    return True

            # Check the modification time of the top-level imports file.  If
            # this file was changed, and full ontologies were added as imports,
            # the import modules would not need to be built but we would still
            # need to rebuild the main ontology.
            if mtime < os.path.getmtime(self.config.getTopImportsFilePath()):
                return True

            return False
        else:
            return True

    def _run(self):
        """
        Runs the build process and produces a compiled OWL ontology file.
        """
        # We don't need to run _retrieveAndCheckFilePaths() here because the
        # base class ensures that _isBuildRequired() will always be called
        # prior to this method, so _retrieveAndCheckFilePaths() will have
        # already been run.

        timer = BasicTimer()
        timer.start()

        # Get the imports modules IRIs from the imports build target.
        importsIRIs = [info.iristr for info in self.ibt.getImportsInfo()]

        fileoutpath = self.getOutputFilePath()

        # Create the destination directory, if needed.  We only need to check
        # this for in-source builds, since the BuildDirTarget dependency will
        # take care of this for out-of-source builds.
        if self.config.getDoInSourceBuilds():
            destdir = os.path.dirname(fileoutpath)
            if not(os.path.isdir(destdir)):
                self._makeDirs(destdir)

        ontbuilder = OWLOntologyBuilder(self.base_ont_path)
        # Add an import declaration for each import module.
        for importIRI in importsIRIs:
            ontbuilder.getOntology().addImport(importIRI, True)

        # Process each source file.  In this step, entities and label
        # annotations are defined, but processing of all other axioms (e.g.,
        # text definitions, comments, equivalency axioms, subclass of axioms,
        # etc.) is deferred until after all input files have been read.  This
        # allows forward referencing of labels and term IRIs and means that
        # entity descriptions and source files can be processed in any
        # arbitrary order.
        for termsfile in self.termsfile_paths:
            with TableReaderFactory(termsfile) as reader:
                logger.info('Parsing ' + termsfile + '...')
                for table in reader:
                    table.setRequiredColumns(REQUIRED_COLS)
                    table.setOptionalColumns(OPTIONAL_COLS)
        
                    for t_row in table:
                        if not(t_row['Ignore'].lower() in TRUE_STRS):
                            # Collapse all spaces in the "Type" string so that,
                            # e.g., "DataProperty" and "Data Property" will
                            # both work as expected.
                            typestr = t_row['Type'].lower().replace(' ', '')
            
                            if typestr == 'class':
                                ontbuilder.addOrUpdateClass(t_row)
                            elif typestr == 'dataproperty':
                                ontbuilder.addOrUpdateDataProperty(t_row)
                            elif typestr == 'objectproperty':
                                ontbuilder.addOrUpdateObjectProperty(t_row)
                            elif typestr == 'annotationproperty':
                                ontbuilder.addOrUpdateAnnotationProperty(t_row)
                            elif typestr == 'individual':
                                ontbuilder.addOrUpdateIndividual(t_row)
                            elif typestr == '':
                                raise EntityDescriptionError(
                                    'The entity type (e.g., "class", "data '
                                    'property") was not specified.',
                                    t_row
                                )
                            else:
                                raise EntityDescriptionError(
                                    'The entity type "' + t_row['Type']
                                    + '" is not supported.', t_row
                                )

        # Define all deferred axioms from the source entity descriptions.
        logger.info('Defining all remaining entity axioms...')
        ontbuilder.processDeferredEntityAxioms(self.expanddefs)

        # Set the ontology IRI.
        ontIRI = self.config.generateDevIRI(fileoutpath)
        ontbuilder.getOntology().setOntologyID(ontIRI)

        # Write the ontology to the output file.
        logger.info('Writing compiled ontology to ' + fileoutpath + '...')
        ontbuilder.getOntology().saveOntology(
            fileoutpath, self.config.getOutputFormat()
        )

        logger.info(
            'Main ontology build completed in {0} s.\n'.format(timer.stop())
        )

