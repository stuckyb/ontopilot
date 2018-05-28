# Copyright (C) 2018 Brian J. Stucky
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
import sys
import csv
from ontopilot import logger
from ontology import Ontology
from buildtarget import BuildTarget
from entityfinder import MATCH_FULL, MATCH_SUBPHRASE, EntityFinder

# Java imports.
from java.lang import System as JavaSystem


class FindEntitiesBuildTarget(BuildTarget):
    """
    Implements an inferencing pipeline mode for OntoPilot in which an incoming
    ontology/data set is accepted either from a file or stdin, inferred axioms
    are added to the ontology/data set, and the results are written to an
    output file or stdout.
    """
    def __init__(self, args):
        """
        args: A "struct" of configuration options (typically, parsed
            command-line arguments).  The only required members are
            'search_ont', which is a list of paths to one or more ontology
            files; 'input_data', which is the path to a set of search terms
            (can be empty); and 'fileout', which is the path to an output file
            (can be empty).
        """
        BuildTarget.__init__(self)

        # This build target does not have any dependencies, since all input is
        # external and does not depend on other build tasks.

        self.search_onts = args.search_ont
        self.tfpath = args.input_data.strip()
        self.outpath = args.fileout.strip()

        self._checkInputFiles()

    def _checkInputFiles(self):
        """
        Verifies that the user-specified input file(s) exists.
        """
        if self.tfpath != '':
            if not(os.path.isfile(self.tfpath)):
                raise RuntimeError(
                    'The input file of search terms could not be found: '
                    '{0}.'.format(self.fpath)
                )

        if len(self.search_onts) == 0:
            raise RuntimeError(
                'You must specify at least one ontology to search.'
            )

        for search_ont in self.search_onts:
            if not(os.path.isfile(search_ont)):
                raise RuntimeError(
                    'The search ontology could not be found: {0}.'.format(
                        search_ont
                    )
                )

    def _isBuildRequired(self):
        """
        Because this build target works with external input, a "build" is
        always required.
        """
        return True

    def _run(self):
        """
        Reads the source ontologies and looks for the search terms.
        """
        ef = EntityFinder()

        for search_ont in self.search_onts:
            logger.info('Reading source ontology {0}...'.format(search_ont))
            ontology = Ontology(search_ont)
            logger.info('Processing ontology entities...')
            ef.addOntologyEntities(ontology)

        if self.tfpath != '':
            termsin = open(self.tfpath)
        else:
            termsin = sys.stdin

        if self.outpath != '':
            logger.info('Writing search results to ' + self.outpath + '...')
            fout = open(self.outpath, 'w')
        else:
            fout = sys.stdout

        writer = csv.DictWriter(
            fout,
            fieldnames=[
                'Search term', 'Matching entity', 'Label(s)', 'Annotation', 'Value', 'Match type',
                'Definition(s)'
            ]
        )
        writer.writeheader()

        row = {}
        for searchterm in termsin:
            searchterm = searchterm.strip()
            results = ef.findEntities(searchterm)

            for result in results:
                entity = result[0]

                row['Search term'] = searchterm
                row['Matching entity'] = str(entity.getIRI())
                row['Label(s)'] = ','.join(entity.getLabels())
                row['Annotation'] = result[1]
                row['Value'] = result[2]
                row['Definition(s)'] = ','.join(entity.getDefinitions())

                if result[3] == MATCH_FULL:
                    row['Match type'] = 'Full'
                else:
                    row['Match type'] = 'Partial'

                writer.writerow(row)

