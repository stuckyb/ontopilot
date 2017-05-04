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
import os
import datetime
from ontopilot import logger
from ontology import Ontology
from buildtarget import BuildTargetWithConfig
from modified_onto_buildtarget import ModifiedOntoBuildTarget
from collections import namedtuple

# Java imports.


class _ArgsType:
    """
    A simple "struct"-type class for copying arguments from another struct-type
    class (such as ArgumentParser objects).
    """
    def __init__(self, structobj):
        """
        The attributes from structobj will be copied to this object.
        """
        for key, value in vars(structobj).iteritems():
            setattr(self, key, value)


# Define a simple "struct" type for gathering file path and IRI information.
FileInfo = namedtuple(
    'FileInfo', ['sourcepath', 'destpath', 'oldIRI', 'destIRI', 'versionIRI']
)


class ReleaseBuildTarget(BuildTargetWithConfig):
    """
    Manages the process of building a complete release version of the compiled
    ontology and imports modules.
    """
    def __init__(self, args, cfgfile_required=True, config=None):
        """
        args: A "struct" of configuration options (typically, parsed
            command-line arguments).  The required members are 'merge_imports'
            (boolean), 'reason' (boolean), 'no_def_expand' (boolean),
            'release_date' (string), and 'config_file' (string).
        cfgfile_required (optional): Whether a config file is required.
        config (optional): An OntoConfig object.
        """
        BuildTargetWithConfig.__init__(self, args, cfgfile_required, config)

        # Each release will include a merged, prereasoned ontology file, a
        # merged, unreasoned ontology file, and an unmerged, unreasoned
        # ontology file.  So we need to set dependencies for each of those
        # build targets.
        newargs = _ArgsType(args)
        newargs.merge_imports = True
        self.mobt_merged = ModifiedOntoBuildTarget(newargs, False, self.config)

        newargs = _ArgsType(args)
        newargs.merge_imports = True
        newargs.reason = True
        self.mobt_merged_reasoned = ModifiedOntoBuildTarget(
            newargs, False, self.config
        )

        self.addDependency(self.mobt_merged)
        self.addDependency(self.mobt_merged_reasoned)

        self.release_dir = self._generateReleaseDirPath(args.release_date)

    def _generateReleaseDirPath(self, datestr):
        """
        Returns the path for the release directory.
        """
        if datestr == '':
            datestr = datetime.date.today().isoformat()
        else:
            # Check that the date string is in the format YYYY-MM-DD.
            try:
                datetime.datetime.strptime(datestr, '%Y-%m-%d')
            except ValueError:
                raise ValueError(
                    'The custom release date string, "{0}", is invalid.  The '
                    'string must be in the format YYYY-MM-DD and must '
                    'represent a valid date.'.format(datestr)
                )

        release_dir = os.path.join(
            self.config.getProjectDir(), 'releases', datestr
        )

        return release_dir

    def _generateImportFileInfo(self, sourcepath, old_iri):
        """
        Generates and returns a FileInfo object for a release import module
        file.

        sourcepath: The location of the source import module file.
        old_iri (str): The old (current) IRI of the import module.
        """
        # Get the path to the module, relative to the main project location.
        mod_relpath = os.path.relpath(sourcepath, self.config.getProjectDir())

        destpath = os.path.join(self.release_dir, mod_relpath)

        destIRI = self.config.generateReleaseIRI(mod_relpath)

        versionIRI = self.config.generateReleaseIRI(destpath)

        finfo = FileInfo(
            sourcepath=sourcepath, destpath=destpath, oldIRI=old_iri,
            destIRI=destIRI, versionIRI=versionIRI
        )

        return finfo

    def _generateOntologyFileInfo(self, sourcepath, suffix, is_main):
        """
        Generates and returns a FileInfo object for a release ontology file.

        sourcepath: The location of the source ontology file.
        suffix (str): The suffix to attach to the base ontology file name.
        is_main (bool): Whether this is the main ontology file.
        """
        # Parse the base ontology file name.
        ofnparts = os.path.splitext(
            os.path.basename(self.config.getOntologyFilePath())
        )

        destpath = os.path.join(
            self.release_dir, ofnparts[0] + suffix + ofnparts[1]
        )

        if is_main:
            destIRI = self.config.getReleaseOntologyIRI()
        else:
            destIRI = self.config.generateReleaseIRI(
                os.path.basename(destpath)
            )

        versionIRI = self.config.generateReleaseIRI(destpath)

        finfo = FileInfo(
            sourcepath=sourcepath, destpath=destpath, oldIRI='',
            destIRI=destIRI, versionIRI=versionIRI
        )

        return finfo

    def _generateBuildInfo(self):
        """
        Generates the paths and IRIs needed to build the release.  Sets two
        class attributes: ont_fileinfos and imports_fileinfos, which are lists
        of FileInfo objects that describe how to build the release components.
        """
        # Gather the ontology file information.  Get the compiled main ontology
        # file path from one of the modified ontology dependencies.
        self.ont_fileinfos = []

        spath = self.mobt_merged.getOntoBuildTarget().getOutputFilePath()
        self.ont_fileinfos.append(
            self._generateOntologyFileInfo(spath, '-raw', False)
        )

        spath = self.mobt_merged.getOutputFilePath()
        self.ont_fileinfos.append(
            self._generateOntologyFileInfo(spath, '-merged', False)
        )

        spath = self.mobt_merged_reasoned.getOutputFilePath()
        self.ont_fileinfos.append(
            self._generateOntologyFileInfo(spath, '', True)
        )

        # Gather the imports file information.
        self.imports_fileinfos = []

        ibt = self.mobt_merged.getOntoBuildTarget().getImportsBuildTarget()
        importsinfos = ibt.getImportsInfo()
        for importsinfo in importsinfos:
            self.imports_fileinfos.append(
                self._generateImportFileInfo(
                    importsinfo.filename, importsinfo.iristr
                )
            )

    def getBuildNotRequiredMsg(self):
        return 'The release files are already up to date.'

    def _isBuildRequired(self):
        """
        Checks if all of the release files already exist.  If not, returns
        True.  Otherwise, checking the build status is deferred to the
        dependencies: if any dependencies require a build, then the release
        will automatically be built, too (this is automatically enforced by the
        base class).
        """
        self._generateBuildInfo()

        for fileinfo in (self.ont_fileinfos + self.imports_fileinfos):
            if not(os.path.isfile(fileinfo.destpath)):
                return True

        return False

    def _run(self):
        """
        Runs the build process to produce a new ontology release.
        """
        # We don't need to run generateBuildInfo() here because the base class
        # ensures that _isBuildRequired() will always be called prior to this
        # method, so generateBuildInfo() will have already been run.

        # Create the main release directory, if needed.
        if not(os.path.isdir(self.release_dir)):
            self._makeDirs(self.release_dir)

        # Get the path to the released imports modules directory and create it,
        # if needed.
        if len(self.imports_fileinfos) > 0:
            dirpath = os.path.dirname(self.imports_fileinfos[0].destpath)
            if not(os.path.exists(dirpath)):
                self._makeDirs(dirpath)

        # Create the release import module files.
        logger.info('Creating release import modules...')
        for fileinfo in self.imports_fileinfos:
            ont = Ontology(fileinfo.sourcepath)
            ont.setOntologyID(fileinfo.destIRI, fileinfo.versionIRI)
            ont.saveOntology(fileinfo.destpath)

        # Create the release ontology files.
        logger.info('Creating release ontology files...')
        for fileinfo in self.ont_fileinfos:
            ont = Ontology(fileinfo.sourcepath)
            ont.setOntologyID(fileinfo.destIRI, fileinfo.versionIRI)

            # Update the IRIs of any released import modules that are
            # explicitly imported by the ontology.
            for ifinfo in self.imports_fileinfos:
                if ont.hasImport(ifinfo.oldIRI):
                    ont.updateImportIRI(ifinfo.oldIRI, ifinfo.versionIRI)

            ont.saveOntology(fileinfo.destpath, self.config.getOutputFormat())

