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
# Manages the process of updating the base ontology file with import statements
# for local import modules.  This is primarily useful if the base ontology will
# be used in some way for active development.
#

# Python imports.
from __future__ import unicode_literals
import os
from ontopilot import logger
from ontology import Ontology
from buildtarget import BuildTargetWithConfig
from imports_buildtarget import ImportsBuildTarget

# Java imports.


class UpdateBaseImportsBuildTarget(BuildTargetWithConfig):
    def __init__(self, args, cfgfile_required=True, config=None):
        """
        args: A "struct" of configuration options (typically, parsed
            command-line arguments).  The required members are
            'no_def_expand' (boolean) and 'config_file' (string).
        cfgfile_required (optional): Whether a config file is required.
        config (optional): An OntoConfig object.
        """
        BuildTargetWithConfig.__init__(self, args, cfgfile_required, config)

        # Set the imports modules as a dependency.  This is not strictly
        # required just to update the imports set in the base ontology.
        # However, setting this dependency has the advantage of ensuring that
        # all imports specifications are correct and that the imports modules
        # compile before we try to update the base ontology.  This should help
        # eliminate "silent" errors in the import modules specifications.
        self.ibt = ImportsBuildTarget(args, False, self.config)
        self.addDependency(self.ibt)

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

        # Verify that the build directory exists.
        destdir = os.path.dirname(self.getOutputFilePath())
        if not(os.path.isdir(destdir)):
            raise RuntimeError(
                'The destination directory for the updated base ontology file '
                'does not exist: {0}.'.format(destdir)
            )

    def getOutputFilePath(self):
        """
        Returns the path of the updated base ontology file.
        """
        if self.config.getDoInSourceBuilds():
            destpath = self.config.getBaseOntologyPath()
        else:
            ontfilename = os.path.basename(self.config.getBaseOntologyPath())
            destpath = os.path.join(self.config.getBuildDir(), ontfilename)

        return destpath

    def getBuildNotRequiredMsg(self):
        return 'The base ontology is already up to date.'

    def _isBuildRequired(self):
        """
        If we're doing in-source builds, always returns True because there is
        no way to determine whether a build is required without actually
        reading the contents of the base ontology.  If we're doing
        out-of-source builds, the return value depends on the modification
        times of the base ontology file and the imports specification files.
        """
        if self.config.getDoInSourceBuilds():
            return True

        foutpath = self.getOutputFilePath()

        if os.path.isfile(foutpath):
            mtime = os.path.getmtime(foutpath)

            # If the configuration file is newer than the output base ontology,
            # a new build might be needed if any imports changes were made.
            if mtime < os.path.getmtime(self.config.getConfigFilePath()):
                return True

            # Check the modification time of the base ontology.
            if mtime < os.path.getmtime(self.config.getBaseOntologyPath()):
                return True

            # Check the modification time of the top-level imports file.  If
            # this file was changed, and full ontologies were added as imports,
            # the import modules would not need to be built but we would still
            # need to update the base ontology.
            if mtime < os.path.getmtime(self.config.getTopImportsFilePath()):
                return True

            return False
        else:
            return True

    def _run(self):
        """
        Runs the build process and produces a compiled OWL ontology file.
        """
        # Get the imports modules IRIs from the imports build target.
        importinfos = self.ibt.getImportsInfo()

        self._retrieveAndCheckFilePaths()

        baseont = Ontology(self.base_ont_path)
        # Add an import declaration for each import module.
        for importinfo in importinfos:
            baseont.addImport(importinfo.iristr, True)

        # Write the base ontology to the output file.
        fileoutpath = self.getOutputFilePath()
        logger.info('Writing updated base ontology to ' + fileoutpath + '...')
        baseont.saveOntology(fileoutpath)

