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
from basictimer import BasicTimer
from ontology import Ontology
from buildtarget import BuildTargetWithConfig
from onto_buildtarget import OntoBuildTarget
from inferred_axiom_adder import InferredAxiomAdder

# Java imports.


class ModifiedOntoBuildTarget(BuildTargetWithConfig):
    """
    Manages the process of building a "modified" ontology from the standard
    compiled ontology.  In this case, "modified" means either with imports
    merged into the main ontology, with inferred axioms added, or both.
    """
    def __init__(self, args, cfgfile_required=True, config=None):
        """
        args: A "struct" of configuration options (typically, parsed
            command-line arguments).  The required members are 'merge_imports'
            (boolean), 'reason' (boolean), 'no_def_expand' (boolean), and
            'config_file' (string).
        cfgfile_required (optional): Whether a config file is required.
        config (optional): An OntoConfig object.
        """
        BuildTargetWithConfig.__init__(self, args, cfgfile_required, config)

        self.mergeimports = args.merge_imports
        self.prereason = args.reason

        self.obt = OntoBuildTarget(args, False, self.config)

        # If we have nothing to do, then there are no dependencies.
        if self.mergeimports or self.prereason:
            self.addDependency(self.obt)

    def _retrieveAndCheckFilePaths(self):
        """
        Verifies that all files and directories needed for the build exist.
        """
        # Verify that the main ontology file exists.
        fpath = self.obt.getOutputFilePath()
        if not(os.path.isfile(fpath)):
            raise RuntimeError(
                'The main compiled ontology file could not be found: '
                '{0}.'.format(fpath)
            )

        # Verify that the build directory exists.
        destdir = os.path.dirname(self.getOutputFilePath())
        if not(os.path.isdir(destdir)):
            raise RuntimeError(
                'The destination directory for the ontology does not '
                'exist: {0}.'.format(destdir)
            )

    def getOntoBuildTarget(self):
        """
        Returns the instance of OntoBuildTarget on which this build target
        depends.
        """
        return self.obt

    def getOutputFilePath(self):
        """
        Returns the path of the enhanced ontology file.
        """
        main_ontpath = self.obt.getOutputFilePath(add_suffix=False)
        destpath = main_ontpath

        # If we are merging the imports into the ontology, modify the file name
        # accordingly.
        if self.mergeimports:
            parts = os.path.splitext(destpath)
            destpath = parts[0] + '-merged' + parts[1]

        # If we are adding inferred axioms to the ontology, modify the file
        # name accordingly.
        if self.prereason:
            parts = os.path.splitext(destpath)
            destpath = parts[0] + '-reasoned' + parts[1]

        return destpath

    def getBuildNotRequiredMsg(self):
        return 'The compiled ontology files are already up to date.'

    def _isBuildRequired(self):
        """
        Checks if the modified ontology already exists, and if so, whether file
        modification times indicate that the modified ontology is already up to
        date.  Returns True if the modified ontology needs to be updated.
        """
        # If neither modification is requested, then no build is required.
        if not(self.mergeimports) and not(self.prereason):
            return False

        foutpath = self.getOutputFilePath()
        main_ontpath = self.obt.getOutputFilePath()

        if os.path.isfile(foutpath):
            # If the main ontology file is newer than the compiled ontology, a
            # new build is needed.
            if os.path.isfile(main_ontpath):
                mtime = os.path.getmtime(foutpath)

                return mtime < os.path.getmtime(main_ontpath)
            else:
                # If the main ontology file does not exist, a build is
                # required.
                return True
        else:
            # If the modified ontology file does not exist, a build is
            # obviously required.
            return True

    def _run(self):
        """
        Runs the build process and produces a new, modified version of the main
        OWL ontology file.
        """
        timer = BasicTimer()
        timer.start()

        self._retrieveAndCheckFilePaths()

        mainont = Ontology(self.obt.getOutputFilePath())

        if self.mergeimports:
            # Merge the axioms from each imported ontology directly into this
            # ontology (that is, do not use import statements).
            logger.info(
                'Merging all imported ontologies into the main ontology...'
            )
            for importIRI in mainont.getImports():
                mainont.mergeOntology(
                    importIRI, self.config.getAnnotateMerged()
                )

        if self.prereason:
            logger.info('Running reasoner and adding inferred axioms...')
            inf_types = self.config.getInferenceTypeStrs()
            annotate_inferred = self.config.getAnnotateInferred()
            preprocess_inverses = self.config.getPreprocessInverses()
            iaa = InferredAxiomAdder(mainont, self.config.getReasonerStr())
            if self.config.getExcludedTypesFile() != '':
                iaa.loadExcludedTypes(self.config.getExcludedTypesFile())
            iaa.addInferredAxioms(
                inf_types, annotate_inferred, preprocess_inverses
            )

        fileoutpath = self.getOutputFilePath()

        # Set the ontology IRI.
        ontIRI = self.config.generateDevIRI(fileoutpath)
        mainont.setOntologyID(ontIRI)

        # Write the ontology to the output file.
        logger.info('Writing compiled ontology to ' + fileoutpath + '...')
        mainont.saveOntology(fileoutpath, self.config.getOutputFormat())

        if self.mergeimports and self.prereason:
            msgtxt = 'Merged and reasoned '
        elif self.mergeimports:
            msgtxt = 'Merged '
        else:
            msgtxt = 'Reasoned '

        logger.info(
            (msgtxt + 'ontology build completed in {0} s.\n').format(
                timer.stop()
            )
        )

