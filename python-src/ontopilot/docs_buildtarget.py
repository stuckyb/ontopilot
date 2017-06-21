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
from ontopilot import logger
from ontology import Ontology
from buildtarget import BuildTargetWithConfig
from modified_onto_buildtarget import ModifiedOntoBuildTarget
from documenter import Documenter
from documentation_writers import getDocumentationWriter
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


# Define a simple "struct" type for gathering file format and path information.
DocFileInfo = namedtuple('DocFileInfo', ['formatstr', 'destpath'])


class DocsBuildTarget(BuildTargetWithConfig):
    """
    Manages the process of building documentation files from a compiled,
    reasoned ontology document.
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

        # Use the reasoned version of the ontology to generate the
        # documentation.
        newargs = _ArgsType(args)
        newargs.reason = True
        self.mobt_reasoned = ModifiedOntoBuildTarget(
            newargs, False, self.config
        )

        self.addDependency(self.mobt_reasoned)

    def _checkFilePaths(self):
        """
        Verifies that all files needed for the build exist.
        """
        # Verify that the documentation specification file exists.
        fpath = self.config.getDocSpecificationFile()
        if not(os.path.isfile(fpath)):
            raise RuntimeError(
                'The documentation specification file could not be '
                'found: {0}.'.format(fpath)
            )

    def getBuildNotRequiredMsg(self):
        return 'The documentation files are already up to date.'

    def getOutputFileInfos(self):
        """
        Returns the formats and paths of the compiled ontology documentation
        files as a list of DocFileInfo objects.
        """
        docsbasepath = self.config.getDocsFilePath()

        fileinfos = []

        for formatstr in self.config.getDocFormats():
            lc_formatstr = formatstr.lower()

            if lc_formatstr == 'html':
                rawpath = docsbasepath + '.html'
            elif lc_formatstr == 'markdown':
                rawpath = docsbasepath + '.md'
            else:
                raise RuntimeError(
                    'Unrecognized output documentation format string: '
                    '"{0}".'.format(formatstr)
                )

            if self.config.getDoInSourceBuilds():
                destpath = rawpath
            else:
                docfilename = os.path.basename(rawpath)
                destpath = os.path.join(self.config.getBuildDir(), docfilename)

            fileinfos.append(DocFileInfo(lc_formatstr, destpath))

        return fileinfos

    def _isBuildRequired(self):
        """
        Checks if the documentation files already exist, and if so, whether
        file modification times indicate that the documentation is already up
        to date.  Also, if the compiled ontology dependency needs to be
        (re)built, then the base class ensures that the documentation will also
        be (re)built.  Returns True if the documentation needs to be updated.
        """
        foutinfos = self.getOutputFileInfos()

        self._checkFilePaths()

        for foutinfo in foutinfos:
            foutpath = foutinfo.destpath

            if os.path.isfile(foutpath):
                mtime = os.path.getmtime(foutpath)
    
                # If the configuration file is newer than the compiled
                # documentation, a new build might be needed if any
                # documentation-related changes were made.
                if mtime < os.path.getmtime(self.config.getConfigFilePath()):
                    return True
    
                # Check the modification time of the documentation specification
                # file.
                if mtime < os.path.getmtime(self.config.getDocSpecificationFile()):
                    return True
    
                return False
            else:
                return True

    def _run(self):
        """
        Runs the build process to produce the ontology documentation.
        """
        fileoutinfos = self.getOutputFileInfos()

        # Create the destination directory, if needed.  We only need to check
        # this for in-source builds, since the BuildDirTarget dependency will
        # take care of this for out-of-source builds.
        if self.config.getDoInSourceBuilds():
            destdir = os.path.dirname(fileoutinfos[0].destpath)
            if not(os.path.isdir(destdir)):
                self._makeDirs(destdir)

        logger.info('Creating ontology documentation files...')

        ont = Ontology(self.mobt_reasoned.getOutputFilePath())

        # Create the documentation files.
        for foutinfo in fileoutinfos:
            writer = getDocumentationWriter(foutinfo.formatstr)
            documenter = Documenter(ont, writer)

            with open(self.config.getDocSpecificationFile()) as docspec:
                with open(foutinfo.destpath, 'w') as fout:
                    documenter.document(docspec, fout)

