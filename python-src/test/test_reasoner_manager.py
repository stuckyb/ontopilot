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
from ontopilot.ontology import Ontology
from ontopilot.reasoner_manager import ReasonerManager
import unittest
#from testfixtures import LogCapture

# Java imports.
from org.semanticweb.elk.owlapi import ElkReasoner
from org.semanticweb.HermiT import Reasoner as HermitReasoner
from com.clarkparsia.pellet.owlapiv3 import PelletReasoner
from uk.ac.manchester.cs.jfact import JFactReasoner


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
        correct type of reasoner, that reasoner instances are functionally
        singletons, and that all reasoners run in non-buffered mode.  Also
        verifies that reasoner name strings are not case sensitive.
        """
        reasoner = self.rman.getReasoner('ELK')
        self.assertIsInstance(reasoner, ElkReasoner)
        self.assertIs(reasoner, self.rman.getReasoner('elk'))

        reasoner = self.rman.getReasoner('HermiT')
        self.assertIsInstance(reasoner, HermitReasoner)
        self.assertIs(reasoner, self.rman.getReasoner('hermit'))

        reasoner = self.rman.getReasoner('Pellet')
        self.assertIsInstance(reasoner, PelletReasoner)
        self.assertIs(reasoner, self.rman.getReasoner('pellet'))

        reasoner = self.rman.getReasoner('JFact')
        self.assertIsInstance(reasoner, JFactReasoner)
        self.assertIs(reasoner, self.rman.getReasoner('jfact'))

