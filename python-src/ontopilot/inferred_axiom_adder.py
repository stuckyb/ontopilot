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
# Provides methods for adding inferred axioms to an ontology.
#

# Python imports.
from __future__ import unicode_literals
import os.path
from ontopilot import logger
from basictimer import BasicTimer
from tablereaderfactory import TableReaderFactory
from tablereader import TableRowError
from ontopilot import TRUE_STRS

# Java imports.
from java.util import HashSet
from java.lang import UnsupportedOperationException
from org.semanticweb.owlapi.model import IRI
from org.semanticweb.owlapi.model.parameters import Imports as ImportsEnum
from org.semanticweb.owlapi.util import InferredSubClassAxiomGenerator
from org.semanticweb.owlapi.util import InferredEquivalentClassAxiomGenerator
from org.semanticweb.owlapi.util import InferredSubDataPropertyAxiomGenerator
from org.semanticweb.owlapi.util import InferredSubObjectPropertyAxiomGenerator
from org.semanticweb.owlapi.util import InferredClassAssertionAxiomGenerator
from org.semanticweb.owlapi.util import InferredDisjointClassesAxiomGenerator
from org.semanticweb.owlapi.util import InferredOntologyGenerator
from org.semanticweb.owlapi.util import InferredInverseObjectPropertiesAxiomGenerator
from org.semanticweb.owlapi.util import InferredPropertyAssertionGenerator
from org.semanticweb.owlapi.model import AxiomType
from org.semanticweb.owlapi.model.parameters import Imports


# Strings for identifying supported types of inferences for generating inferred
# ontology axioms.
INFERENCE_TYPES = (
    'subclasses', 'subdata properties', 'subobject properties', 'types',
    'equivalent classes', 'disjoint classes', 'inverse object properties',
    'property values'
)


class ExcludedTypeSpecError(TableRowError):
    """
    An exception class for errors encountered in excluded types files.
    """
    def __init__(self, error_msg, tablerow):
        self.tablerow = tablerow

        new_msg = (
            'Error encountered in excluded type assertion specification in '
            + self._generateContextStr(tablerow) + ':\n' + error_msg
        )

        RuntimeError.__init__(self, new_msg)


class InferredAxiomAdder:
    """
    Provides a high-level interface for generating inferred axioms and adding
    them to an ontology.  Besides just adding inferred axioms, this class also
    does a number of more sophisticated procedures, including de-duplicating
    the final axiom set, removing trivial axioms, etc.
    """
    # The IRI for the "dc:source" annotation property.
    SOURCE_PROP_IRI = IRI.create('http://purl.org/dc/elements/1.1/source')

    # The IRI for inferred axiom annotation.
    INFERRED_ANNOT_IRI = IRI.create(
        'http://www.geneontology.org/formats/oboInOwl#is_inferred'
    )

    # Required fields (i.e., keys) for excluded types files.
    ETF_REQUIRED_COLS = ('ID', 'Exclude superclasses')

    # Excluded types file fields for which no warnings are issued if the field
    # is missing.
    ETF_OPTIONAL_COLS = ('Ignore',)

    # Default values for table columns in excluded types files.
    ETF_DEFAULT_COL_VALS = {}

    def __init__(self, ontology, reasoner_str):
        """
        sourceont: The ontology on which to run the reasoner and for which to
            add inferred axioms.
        reasoner_str: A string indicating the type of reasoner to use.
        """
        self.ont = ontology
        self.setReasoner(reasoner_str)

        # A set of OWL API ontology class objects that correspond with types
        # that should be excluded from inferred type/class assertions.
        self.excluded_types = set()

    def setReasoner(self, reasoner_str):
        """
        Sets the reasoner type to use for generating inferred axioms.

        reasoner_str: A string indicating the type of reasoner to use.
        """
        self.reasoner_str = reasoner_str
        self.reasoner = self.ont.getReasonerManager().getReasoner(reasoner_str)

    def _getGeneratorsList(self, inference_types):
        """
        Returns a list of AxiomGenerators for a reasoner that match the
        capabilities of the reasoner.

        inference_types: A list of strings specifying the kinds of inferred
            axioms to generate.  Valid values are detailed in the sample
            configuration file.
        """
        # Get a string for the reasoner class for error reporting.
        reasoner_name = (
            self.reasoner.__class__.__module__ + '.'
            + self.reasoner.__class__.__name__
        )

        # Examine each inference type string, check if it is supported by the
        # current reasoner, and if so, add an appropriate generator to the list
        # of generators.
        generators = []
        for inference_type in inference_types:
            if inference_type == 'subclasses':
                # Check for class hierarchy inferencing support.
                try:
                    testent = self.ont.df.getOWLClass(IRI.create('test'))
                    self.reasoner.getSuperClasses(testent, True)
                    generators.append(InferredSubClassAxiomGenerator())
                except UnsupportedOperationException as err:
                    logger.warning(
                        'The reasoner "{0}" does not support subclass '
                        'inferences.'.format(reasoner_name)
                    )

            elif inference_type == 'equivalent classes':
                # Check for class equivalency inferencing support.
                try:
                    testent = self.ont.df.getOWLClass(IRI.create('test'))
                    self.reasoner.getEquivalentClasses(testent)
                    generators.append(InferredEquivalentClassAxiomGenerator())
                except UnsupportedOperationException as err:
                    logger.warning(
                        'The reasoner "{0}" does not support class equivalency '
                        'inferences.'.format(reasoner_name)
                    )

            elif inference_type == 'disjoint classes':
                # Check for class disjointness inferencing support.
                try:
                    testent = self.ont.df.getOWLClass(IRI.create('test'))
                    self.reasoner.getDisjointClasses(testent)
                    generators.append(InferredDisjointClassesAxiomGenerator())
                except UnsupportedOperationException as err:
                    logger.warning(
                        'The reasoner "{0}" does not support class '
                        'disjointness inferences.'.format(reasoner_name)
                    )

            elif inference_type == 'subdata properties':
                # Check for data property hierarchy inferencing support.
                try:
                    testent = self.ont.df.getOWLDataProperty(IRI.create('test'))
                    self.reasoner.getSuperDataProperties(testent, True)
                    generators.append(InferredSubDataPropertyAxiomGenerator())
                except UnsupportedOperationException as err:
                    logger.warning(
                        'The reasoner "{0}" does not support data property '
                        'hierarchy inferences.'.format(reasoner_name)
                    )

            elif inference_type == 'subobject properties':
                # Check for object property hierarchy inferencing support.
                try:
                    testent = self.ont.df.getOWLObjectProperty(IRI.create('test'))
                    self.reasoner.getSuperObjectProperties(testent, True)
                    generators.append(InferredSubObjectPropertyAxiomGenerator())
                except UnsupportedOperationException as err:
                    logger.warning(
                        'The reasoner "{0}" does not support object property '
                        'hierarchy inferences.'.format(reasoner_name)
                    )

            elif inference_type == 'inverse object properties':
                # Check for inverse object property inferencing support.
                try:
                    testent = self.ont.df.getOWLObjectProperty(IRI.create('test'))
                    self.reasoner.getInverseObjectProperties(testent)
                    generators.append(InferredInverseObjectPropertiesAxiomGenerator())
                except UnsupportedOperationException as err:
                    logger.warning(
                        'The reasoner "{0}" does not support inverse object '
                        'property inferences.'.format(reasoner_name)
                    )

            elif inference_type == 'types':
                # Check for class assertion inferencing support.
                try:
                    testent = self.ont.df.getOWLNamedIndividual(IRI.create('test'))
                    self.reasoner.getTypes(testent, True)
                    generators.append(InferredClassAssertionAxiomGenerator())
                except UnsupportedOperationException as err:
                    logger.warning(
                        'The reasoner "{0}" does not support class assertion '
                        'inferences.'.format(reasoner_name)
                    )

            elif inference_type == 'property values':
                # Check for individual property value inferencing support.
                try:
                    testent = self.ont.df.getOWLNamedIndividual(IRI.create('test'))
                    dprop = self.ont.df.getOWLDataProperty(IRI.create('dprop'))
                    oprop = self.ont.df.getOWLObjectProperty(IRI.create('oprop'))
                    self.reasoner.getDataPropertyValues(testent, dprop)
                    self.reasoner.getObjectPropertyValues(testent, oprop)
                    generators.append(InferredPropertyAssertionGenerator())
                except UnsupportedOperationException as err:
                    logger.warning(
                        'The reasoner "{0}" does not support property '
                        'assertion inferences.'.format(reasoner_name)
                    )

            else:
                raise RuntimeError(
                    'Unsupported inference type: "{0}".'.format(inference_type)
                )

        return generators

    def _getRedundantSubclassOfAxioms(self, owlont):
        """
        Returns a set of all "subclass of" axioms in an ontology that are
        redundant.  In this context, "redundant" means that a class is asserted
        to have two or more different superclasses that are part of the same
        class hierarchy.  Only the superclass nearest to the subclass is
        retained; all other axioms are considered to be redundant.  This
        situation can easily arise after inferred "subclass of" axioms are
        added to an ontology.

        owlont: An OWL API ontology object.
        """
        redundants = set()

        for classobj in owlont.getClassesInSignature():
            # Get the set of direct superclasses for this class.
            supersset = self.reasoner.getSuperClasses(classobj, True).getFlattened()

            # Examine each "subclass of" axiom for this class.  If the
            # superclass asserted in an axiom is not a direct superclass, then
            # the axiom can be considered redundant.
            axioms = owlont.getSubClassAxiomsForSubClass(classobj)
            for axiom in axioms:
                superclass = axiom.getSuperClass()
                if not(superclass.isAnonymous()):
                    if not(supersset.contains(superclass.asOWLClass())):
                        redundants.add(axiom)

        return redundants

    def _addInversePropAssertions(self):
        """
        Finds inverse property pairs in the ontology (including symmetric
        properties) and all property assertions and negative property
        assertions using those properties, then materializes the inverse
        property assertions.  This is all done without using a reasoner.
        """
        owlont = self.ont.getOWLOntology()

        # Use a pair of dictionaries to create a bi-directional lookup table
        # for inverse property pairs.
        inverses_1 = {}
        inverses_2 = {}

        # Use a set to store symmetric properties.
        symmetrics = set()

        # Retrieve all inverse object property axioms and symmetric property
        # axioms from this ontology and its imports closure.
        inv_axioms = set()
        symm_axioms = set()
        for ont in owlont.getImportsClosure():
            inv_axioms.update(
                ont.getAxioms(AxiomType.INVERSE_OBJECT_PROPERTIES)
            )
            symm_axioms.update(
                ont.getAxioms(AxiomType.SYMMETRIC_OBJECT_PROPERTY)
            )

        for axiom in inv_axioms:
            pexp1 = axiom.getFirstProperty()
            pexp2 = axiom.getSecondProperty()

            inverses_1[pexp1] = pexp2
            inverses_2[pexp2] = pexp1

        for axiom in symm_axioms:
            symmetrics.add(axiom.getProperty())

        # Retrieve all object property assertions and negative object property
        # assertions from this ontology and its imports closure.
        pa_axioms = set()
        npa_axioms = set()
        for ont in owlont.getImportsClosure():
            pa_axioms.update(
                ont.getAxioms(AxiomType.OBJECT_PROPERTY_ASSERTION)
            )
            npa_axioms.update(
                ont.getAxioms(AxiomType.NEGATIVE_OBJECT_PROPERTY_ASSERTION)
            )

        # Materialize all inverse object property assertions.
        new_axioms = set()
        for axiom in pa_axioms:
            pexp = axiom.getProperty()
            inv_pexp = None

            if pexp in inverses_1:
                inv_pexp = inverses_1[pexp]
            elif pexp in inverses_2:
                inv_pexp = inverses_2[pexp]
            elif pexp in symmetrics:
                inv_pexp = pexp

            if inv_pexp is not None:
                new_axioms.add(
                    self.ont.df.getOWLObjectPropertyAssertionAxiom(
                        inv_pexp, axiom.getObject(), axiom.getSubject()
                    )
                )

        self.ont.ontman.addAxioms(owlont, new_axioms)

        # Do the same thing for all negative object property assertions.
        new_axioms.clear()
        for axiom in npa_axioms:
            pexp = axiom.getProperty()
            inv_pexp = None

            if pexp in inverses_1:
                inv_pexp = inverses_1[pexp]
            elif pexp in inverses_2:
                inv_pexp = inverses_2[pexp]
            elif pexp in symmetrics:
                inv_pexp = pexp

            if inv_pexp is not None:
                new_axioms.add(
                    self.ont.df.getOWLNegativeObjectPropertyAssertionAxiom(
                        inv_pexp, axiom.getObject(), axiom.getSubject()
                    )
                )

        self.ont.ontman.addAxioms(owlont, new_axioms)

    def _getExcludedTypesFromFile(self, etfpath):
        """
        Parses a tabular data file containing information about the classes to
        exclude from inferred type/class assertions and returns a set of all
        classes (represented as OWL API class objects) referenced in the file.

        etfpath: The path of a tabular data file.
        """
        exctypes = set()

        with TableReaderFactory(etfpath) as reader:
            # Read the terms to import from each table in the input file, add
            # each term to the signature set for module extraction, and add the
            # descendants of each term, if desired.
            for table in reader:
                table.setRequiredColumns(self.ETF_REQUIRED_COLS)
                table.setOptionalColumns(self.ETF_OPTIONAL_COLS)
                table.setDefaultValues(self.ETF_DEFAULT_COL_VALS)

                for row in table:
                    if row['Ignore'].lower() in TRUE_STRS:
                        continue

                    ontclass = self.ont.getExistingClass(row['ID'])
                    if ontclass is None:
                        raise ExcludedTypeSpecError(
                            'Could not find the class "{0}" in the main '
                            'ontology or its imports '
                            'closure.'.format(row['ID']), row
                        )
    
                    owlclass = ontclass.getOWLAPIObj()

                    if row['Exclude class'].lower() in TRUE_STRS:
                        exctypes.add(owlclass)

                    if row['Exclude superclasses'].lower() in TRUE_STRS:
                        supersset = self.reasoner.getSuperClasses(
                            owlclass, False
                        ).getFlattened()

                        for superclass in supersset:
                            exctypes.add(superclass)

        return exctypes

    def loadExcludedTypes(self, etfpath):
        """
        Parses a tabular data file containing information about the classes to
        exclude from inferred type/class assertions.  All classes referenced in
        the input file will be excluded from the inferred type assertions
        generated after the file is loaded.

        etfpath: The path of a tabular data file.
        """
        # Verify that the excluded types file exists.
        if not(os.path.isfile(etfpath)):
            raise RuntimeError(
                'Could not find the excluded types file "' + etfpath + '".'
            )

        self.excluded_types.clear()
        self.excluded_types.update(self._getExcludedTypesFromFile(etfpath))

    def _getExcludedTypeAssertions(self, owlont):
        """
        Returns the set of type assertion axioms in owlont that reference types
        in self.excluded_types.

        owlont: An OWL API ontology object.
        """
        excluded_axioms = set()

        axioms = owlont.getAxioms(AxiomType.CLASS_ASSERTION, Imports.INCLUDED)
        for axiom in axioms:
            cexp = axiom.getClassExpression()
            if not(cexp.isAnonymous()):
                if cexp.asOWLClass() in self.excluded_types:
                    excluded_axioms.add(axiom)

        return excluded_axioms

    def addInferredAxioms(self, inference_types, annotate=False, add_inverses=False):
        """
        Runs a reasoner on this ontology and adds the inferred axioms.

        inference_types: A list of strings specifying the kinds of inferred
            axioms to generate.  Valid values are detailed in the sample
            configuration file.
        annotate: If True, annotate inferred axioms to mark them as inferred.
        add_inverses: If True, inverse property assertions will be explicitly
            added to the ontology *prior* to running the reasoner.  This is
            useful for cases in which a reasoner that does not support inverses
            must be used (e.g., for runtime considerations) on an ontology with
            inverse property axioms.
        """
        timer = BasicTimer()

        owlont = self.ont.getOWLOntology()
        ontman = self.ont.ontman
        df = self.ont.df
        oldaxioms = owlont.getAxioms(ImportsEnum.INCLUDED)

        if add_inverses:
            logger.info(
                'Generating inverse property assertions...'
            )
            timer.start()
            self._addInversePropAssertions()
            logger.info(
                'Inverse property assertions generated in {0} s.'.format(
                    timer.stop()
                )
            )

        # Make sure that the ontology is consistent; otherwise, all inference
        # attempts will fail.
        logger.info(
            'Checking whether the ontology is logically consistent...'
        )
        timer.start()

        entcheck_res = self.ont.checkEntailmentErrors(self.reasoner_str)
        logger.info('Consistency check completed in {0} s.'.format(timer.stop()))

        if not(entcheck_res['is_consistent']):
            raise RuntimeError(
                'The ontology is inconsistent (that is, it has no models).  '
                'This is often caused by the presence of an individual (that '
                'is, a class instance) that is explicitly or implicitly a '
                'member of two disjoint classes.  It might also indicate an '
                'underlying modeling error.  You must correct this problem '
                'before inferred axioms can be added to the ontology.'
            )

        # The general approach is to first get the set of all axioms in the
        # ontology prior to reasoning so that this set can be used for
        # de-duplication later.  Then, inferred axioms are added to a new
        # ontology.  This makes it easy to compare explicit and inferred
        # axioms and to annotate inferred axioms.  Trivial axioms are removed
        # from the inferred axiom set, and the inferred axioms are merged into
        # the main ontology.

        logger.info(
            'Generating inferred axioms...'
        )
        timer.start()

        generators = self._getGeneratorsList(inference_types)
        iog = InferredOntologyGenerator(self.reasoner, generators)

        inferredont = ontman.createOntology()
        iog.fillOntology(self.ont.df, inferredont)

        logger.info('Inferred axioms generated in {0} s.'.format(timer.stop()))

        logger.info(
            'Cleaning up redundant, trivial, and excluded axioms and merging '
            'with the main ontology...'
        )
        timer.start()

        # Delete axioms in the inferred set that are explicitly stated in the
        # source ontology (or its imports closure).
        delaxioms = HashSet()
        for axiom in inferredont.getAxioms():
            if oldaxioms.contains(axiom):
                delaxioms.add(axiom)
        ontman.removeAxioms(inferredont, delaxioms)

        # Delete trivial axioms (e.g., subclass of owl:Thing, etc.).
        trivial_entities = [
            df.getOWLThing(), df.getOWLNothing(),
            df.getOWLTopDataProperty(), df.getOWLTopObjectProperty(),
            df.getOWLBottomDataProperty(), df.getOWLBottomObjectProperty()
        ]
        delaxioms.clear()
        for axiom in inferredont.getAxioms():
            for trivial_entity in trivial_entities:
                if axiom.containsEntityInSignature(trivial_entity):
                    delaxioms.add(axiom)
                    break
        ontman.removeAxioms(inferredont, delaxioms)

        # Find and remove excluded class/type assertions.  This is only
        # necessary if we added inferred class assertions.
        if 'types' in inference_types:
            excluded = self._getExcludedTypeAssertions(inferredont)
            ontman.removeAxioms(inferredont, excluded)

        if annotate:
            # Annotate all of the inferred axioms.
            annotprop = df.getOWLAnnotationProperty(self.INFERRED_ANNOT_IRI)
            annotval = df.getOWLLiteral('true')
            for axiom in inferredont.getAxioms():
                annot = df.getOWLAnnotation(annotprop, annotval)
                newaxiom = axiom.getAnnotatedAxiom(HashSet([annot]))
                ontman.removeAxiom(inferredont, axiom)
                ontman.addAxiom(inferredont, newaxiom)

        # Merge the inferred axioms into the main ontology.
        ontman.addAxioms(owlont, inferredont.getAxioms())

        # Find and remove redundant "subclass of" axioms.  This is only
        # necessary if we inferred the class hierarchy.
        if 'subclasses' in inference_types:
            redundants = self._getRedundantSubclassOfAxioms(owlont)
            ontman.removeAxioms(owlont, redundants)

        logger.info(
            'Axiom clean up and merge completed in {0} s.'.format(timer.stop())
        )

