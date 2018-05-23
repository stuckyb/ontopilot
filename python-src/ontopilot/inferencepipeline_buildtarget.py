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
from inferred_axiom_adder import InferredAxiomAdder

# Java imports.
from java.lang import System as JavaSystem


class InferencePipelineBuildTarget(BuildTargetWithConfig):
    """
    Implements an inferencing pipeline mode for OntoPilot in which an incoming
    ontology/data set is accepted either from a file or stdin, inferred axioms
    are added to the ontology/data set, and the results are written to an
    output file or stdout.
    """
    def __init__(self, args, cfgfile_required=False, config=None):
        """
        args: A "struct" of configuration options (typically, parsed
            command-line arguments).  The only required member is
            'config_file', which should provide the path to a configuration
            file (although this is only used if the config argument is None).
        cfgfile_required (optional): Whether a config file is required.
        config (optional): An OntoConfig object.
        """
        BuildTargetWithConfig.__init__(self, args, cfgfile_required, config)

        # This build target does not have any dependencies, since all input is
        # external and does not depend on other build tasks.

        self.srcpath = args.input_data.strip()
        self.outpath = args.fileout.strip()

        self._checkInputFile()

    def _checkInputFile(self):
        """
        Verifies that the user-specified input file exists.
        """
        if self.srcpath != '':
            if not(os.path.isfile(self.srcpath)):
                raise RuntimeError(
                    'The input ontology/data file could not be found: '
                    '{0}.'.format(self.srcpath)
                )

    def _isBuildRequired(self):
        """
        Because this build target works with external input, a "build" is
        always required.
        """
        return True

    def _run(self):
        """
        Runs the inferencing pipeline.
        """
        #self._retrieveAndCheckFilePaths()

        if self.srcpath != '':
            sourceont = Ontology(self.srcpath)
        else:
            sourceont = Ontology(JavaSystem.in)

        logger.info('Running reasoner and adding inferred axioms...')
        inf_types = self.config.getInferenceTypeStrs()
        annotate_inferred = self.config.getAnnotateInferred()
        preprocess_inverses = self.config.getPreprocessInverses()
        iaa = InferredAxiomAdder(sourceont, self.config.getReasonerStr())
        if self.config.getExcludedTypesFile() != '':
            iaa.loadExcludedTypes(self.config.getExcludedTypesFile())
        iaa.addInferredAxioms(
            inf_types, annotate_inferred, preprocess_inverses
        )

        # Write the ontology to the output file or stdout.
        format_str = self.config.getOutputFormat()
        if self.outpath != '':
            logger.info('Writing compiled ontology to ' + self.outpath + '...')
            sourceont.saveOntology(self.outpath, format_str)
        else:
            sourceont.printOntology(format_str)

