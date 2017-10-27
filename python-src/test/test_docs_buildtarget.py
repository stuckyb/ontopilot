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
from ontopilot.ontoconfig import OntoConfig
from ontopilot.docs_buildtarget import DocsBuildTarget, DocFileInfo
import unittest
import os.path
from collections import namedtuple

# Java imports.


# Define a simple "struct" type for simulating command-line arguments.
ArgsType = namedtuple('args', 'merge_imports')


class TestDocsBuildTarget(unittest.TestCase):
    """
    Tests the supporting ("private") methods of the DocsBuildTarget class.
    """
    def setUp(self):
        self.oc = OntoConfig('test_data/project.conf')
        self.oc.set('Ontology', 'entity_sourcedir', '.')

        # We need to set the imports source location so that the
        # ImportsBuildTarget dependency will initialize without error.
        self.oc.set('Imports', 'imports_src', 'imports_src/')

        args = ArgsType(merge_imports=True)
        self.dbt = DocsBuildTarget(args, False, self.oc)

        self.td_path = os.path.abspath('test_data/')

    def test_checkFilePaths(self):
        # Test a nonexistent documentation specification file.
        with self.assertRaisesRegexp(
            RuntimeError, 'documentation specification file could not be found'
        ):
            self.dbt._checkFilePaths()

    def test_getOutputFileInfos(self):
        self.oc.set('Build', 'insource_builds', 'True')

        self.oc.set('Documentation', 'doc_formats', 'HTML')
        expinfos = [
            DocFileInfo(
                'html',
                os.path.join(self.td_path, 'documentation/ontname_doc.html')
            )
        ]
        self.assertEqual(expinfos, self.dbt.getOutputFileInfos())

        self.oc.set('Documentation', 'doc_formats', 'HTML, Markdown')
        expinfos = [
            DocFileInfo(
                'html',
                os.path.join(self.td_path, 'documentation/ontname_doc.html')
            ),
            DocFileInfo(
                'markdown',
                os.path.join(self.td_path, 'documentation/ontname_doc.md')
            )
        ]
        self.assertEqual(expinfos, self.dbt.getOutputFileInfos())

        self.oc.set('Build', 'insource_builds', 'False')

        self.oc.set('Documentation', 'doc_formats', 'HTML')
        expinfos = [
            DocFileInfo(
                'html',
                os.path.join(self.td_path, 'build/ontname_doc.html')
            )
        ]
        self.assertEqual(expinfos, self.dbt.getOutputFileInfos())

