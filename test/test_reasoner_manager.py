# Copyright (C) 2016 Brian J. Stucky
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
from ontobuilder.ontology import Ontology
from ontobuilder.reasoner_manager import ReasonerManager
import unittest
#from testfixtures import LogCapture

# Java imports.
from org.semanticweb.elk.owlapi import ElkReasoner
from org.semanticweb.HermiT import Reasoner as HermitReasoner


class Test_ReasonerManager(unittest.TestCase):
    """
    Tests the ReasonerManager class.
    """
    def setUp(self):
        ont = Ontology('test_data/ontology.owl')
        self.rman = ReasonerManager(ont)

    def test_getReasoner(self):
        """
        For each supported reasoner type, make sure ReasonerManager returns the
        correct type of reasoner and that reasoner instances are functionally
        singletons.  Also verifies that reasoner name strings are not case
        sensitive.
        """
        reasoner = self.rman.getReasoner('ELK')
        self.assertIsInstance(reasoner, ElkReasoner)
        self.assertIs(reasoner, self.rman.getReasoner('elk'))

        reasoner = self.rman.getReasoner('HermiT')
        self.assertIsInstance(reasoner, HermitReasoner)
        self.assertIs(reasoner, self.rman.getReasoner('hermit'))
