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
# Provides convenience classes that "wrap" OWL API classes and properties and
# implements a higher-level interface for interacting with OWL ontologies.
# None of these classes should be instantiated directly; rather, instances
# should be obtained from the public methods of the ontology.Ontology class.
#

# Python imports.
from __future__ import unicode_literals
from obohelper import oboIDToIRI
from mshelper import ManchesterSyntaxParserHelper

# Java imports.
from org.semanticweb.owlapi.manchestersyntax.renderer import ParserException


# Constants for defining the types of supported ontology entity objects.
CLASS_ENTITY = 0
DATAPROPERTY_ENTITY = 1
OBJECTPROPERTY_ENTITY = 2
ANNOTATIONPROPERTY_ENTITY = 3
INDIVIDUAL_ENTITY = 4


class _OntologyEntity:
    """
    An "abstract" base class for all concrete ontology entity classes.
    """
    # The IRI for the property for definition annotations.
    DEFINITION_IRI = oboIDToIRI('IAO:0000115')

    def __init__(self, entityIRI, entityobj, ontology):
        """
        Initializes this _OntologyEntity.

          entityIRI: The IRI object of the entity.
          entityobj: The OWL API object of the entity.
          ontology: The ontology to which this class belongs.  This should be
            an instance of the local Ontology class (i.e., not an instance of
            the OWL API ontology object.)
        """
        self.ontology = ontology
        self.df = ontology.df
        self.entityIRI = entityIRI
        self.entityobj = entityobj

    def __hash__(self):
        """
        The hash value for an ontology entity should be derived from its
        underlying OWL API entity object.
        """
        return hash(self.entityobj)

    def __eq__(self, other):
        if isinstance(other, _OntologyEntity):
            return self.entityobj.equals(other.getOWLAPIObj())
        else:
            return False

    def __ne__(self, other):
        return not(self == other)

    def getIRI(self):
        return self.entityIRI
    
    def getOWLAPIObj(self):
        """
        Returns the OWL API object wrapped by this entity object.
        """
        return self.entityobj

    def addDefinition(self, deftxt):
        """
        Adds a definition annotation to this entity (i.e., adds an annotation
        for "definition", IAO:0000115).
        """
        deftxt = deftxt.strip()

        defannot = self.df.getOWLAnnotation(
            self.df.getOWLAnnotationProperty(self.DEFINITION_IRI),
            self.df.getOWLLiteral(deftxt)
        )
        annotaxiom = self.df.getOWLAnnotationAssertionAxiom(self.entityIRI, defannot)

        self.ontology.addEntityAxiom(annotaxiom)

    def getDefinitions(self):
        """
        Returns a list of all IAO:0000115 annotation values for this entity.
        """
        return self.getAnnotationValues(self.DEFINITION_IRI)

    def addLabel(self, labeltxt):
        """
        Adds an rdfs:label for this entity.
        """
        labeltxt = labeltxt.strip()

        if labeltxt[0] == "'" and labeltxt[-1] == "'":
            labeltxt = labeltxt[1:-1]

        labelannot = self.df.getOWLAnnotation(
            self.df.getRDFSLabel(), self.df.getOWLLiteral(labeltxt, 'en')
        )
        annotaxiom = self.df.getOWLAnnotationAssertionAxiom(self.entityIRI, labelannot)

        self.ontology.addEntityAxiom(annotaxiom)

    def getLabels(self):
        """
        Returns a list of all rdfs:label values for this entity.
        """
        return self.getAnnotationValues(self.df.getRDFSLabel().getIRI())

    def addComment(self, commenttxt):
        """
        Adds an rdfs:comment for this entity.
        """
        commenttxt = commenttxt.strip()

        commentannot = self.df.getOWLAnnotation(
            self.df.getRDFSComment(), self.df.getOWLLiteral(commenttxt, 'en')
        )
        annotaxiom = self.df.getOWLAnnotationAssertionAxiom(self.entityIRI, commentannot)

        self.ontology.addEntityAxiom(annotaxiom)

    def getComments(self):
        """
        Returns a list of all rdfs:comment annotation values for this entity.
        """
        return self.getAnnotationValues(self.df.getRDFSComment().getIRI())

    def addAnnotation(self, annotprop_id, annottxt):
        """
        Adds an arbitrary annotation for this entity.

        annotprop_id: The identifier of an annotation property.  Can be either
            an OWL API IRI object or a string containing: a label (with or
            without a prefix), a prefix IRI (i.e., a curie, such as
            "owl:Thing"), a full IRI, or an OBO ID (e.g., a string of the form
            "PO:0000003").  Labels should be enclosed in single quotes (e.g.,
            'label txt' or prefix:'label txt').
        annottxt: The annotation text.
        """
        annotprop = self.ontology.getExistingAnnotationProperty(annotprop_id)
        if annotprop is None:
            raise RuntimeError(
                'The specified annotation property, {0}, could not be found '
                'in the source ontology.'.format(annotprop_id)
            )

        annot = self.df.getOWLAnnotation(
            annotprop.getOWLAPIObj(), self.df.getOWLLiteral(annottxt, 'en')
        )
        annotaxiom = self.df.getOWLAnnotationAssertionAxiom(
            self.entityIRI, annot
        )

        self.ontology.addEntityAxiom(annotaxiom)

    def getAnnotationValues(self, annotpropIRI):
        """
        Returns a list containing the string values of all annotation axioms
        for this entity of the specified annotation type.

        annotpropIRI: An OWL API IRI object.
        """
        annotvals = []

        ontset = self.ontology.getOWLOntology().getImportsClosure()
        for owlont in ontset:
            for annot_ax in owlont.getAnnotationAssertionAxioms(self.entityIRI):
                if annot_ax.getProperty().getIRI().equals(annotpropIRI):
                    annotvals.append(annot_ax.getValue().getLiteral())

        return annotvals

    def _getClassExpression(self, manchester_exp):
        """
        Given a string containing a class expression in Manchester Syntax,
        returns a corresponding OWL API class expression object.

        manchester_exps: A string containing an MS "description" production.
        """
        try:
            #self.ontology.mparser = ManchesterSyntaxTool(self.ontology.ontology)
            #cexp = self.ontology.mparser.parseManchesterExpression(formaldef)
            parser = ManchesterSyntaxParserHelper(self.ontology)
            cexps = parser.parseClassExpression(manchester_exp);
        except ParserException as err:
            print err
            raise RuntimeError(
                'Error parsing "{0}" at line {1}, column {2} of the class '
                'expression (Manchester Syntax expected).'.format(
                    err.getCurrentToken(), err.getLineNumber(),
                    err.getColumnNumber()
                )
            )

        return cexps


class _OntologyClass(_OntologyEntity):
    """
    Provides a high-level interface to the OWL API's ontology object system
    for OWL classes.  Conceptually, instances of this class represent a single
    OWL class in an OWL ontology.  This class should not be instantiated
    directly; instead, instances should be obtained through Ontology's public
    interface.
    """
    def __init__(self, classIRI, classobj, ontology):
        """
        Initializes this _OntologyClass.

          class_iri: The IRI object of the class.
          classobj: The OWL API class object of the class.
          ontology: The ontology to which this class belongs.  This should be
            an instance of the local Ontology class (i.e., not an instance of
            the OWL API ontology object.)
        """
        _OntologyEntity.__init__(self, classIRI, classobj, ontology)

    def getTypeConst(self):
        return CLASS_ENTITY
        
    def addSuperclass(self, manchester_exp):
        """
        Adds a class expression as a superclass of this class.  The class
        expression should be written in Manchester Syntax (MS).

        manchester_exp: A string containing an MS "description" production.
        """
        if manchester_exp != '':
            cexp = self._getClassExpression(manchester_exp)
            eaxiom = self.df.getOWLSubClassOfAxiom(self.entityobj, cexp)
            self.ontology.addEntityAxiom(eaxiom)

    def addSubclass(self, manchester_exp):
        """
        Adds a class expression as a subclass of this class.  The class
        expression should be written in Manchester Syntax (MS).

        manchester_exp: A string containing an MS "description" production.
        """
        if manchester_exp != '':
            cexp = self._getClassExpression(manchester_exp)
            eaxiom = self.df.getOWLSubClassOfAxiom(cexp, self.entityobj)
            self.ontology.addEntityAxiom(eaxiom)

    def addEquivalentTo(self, manchester_exp):
        """
        Adds a class expression as an equivalency axiom.  The class expressions
        should be written in Manchester Syntax (MS).

        manchester_exp: A string containing an MS "description" production.
        """
        if manchester_exp != '':
            cexp = self._getClassExpression(manchester_exp)
            eaxiom = self.df.getOWLEquivalentClassesAxiom(self.entityobj, cexp)
            self.ontology.addEntityAxiom(eaxiom)

    def addDisjointWith(self, manchester_exp):
        """
        Adds a class expression as a "disjoint with" axioms.  The class
        expressions should be written in Manchester Syntax (MS).

        manchester_exp: A string containing an MS "description" production.
        """
        if manchester_exp != '':
            cexp = self._getClassExpression(manchester_exp)
            axiom = self.df.getOWLDisjointClassesAxiom(self.entityobj, cexp)
            self.ontology.addEntityAxiom(axiom)


class _OntologyDataProperty(_OntologyEntity):
    """
    Provides a high-level interface to the OWL API's ontology object system
    for OWL data properties.  Conceptually, instances of this class represent a
    single OWL data property in an OWL ontology.  This class should not be
    instantiated directly; instead, instances should be obtained through
    Ontology's public interface.
    """
    def __init__(self, propIRI, propobj, ontology):
        """
        Initializes this _OntologyDataProperty.

          class_iri: The IRI object of the property.
          propobj: The OWL API property object of the property.
          ontology: The ontology to which this class belongs.  This should be
            an instance of the local Ontology class (i.e., not an instance of
            the OWL API ontology object.)
        """
        _OntologyEntity.__init__(self, propIRI, propobj, ontology)
        
    def getTypeConst(self):
        return DATAPROPERTY_ENTITY
        
    def addSuperproperty(self, parent_id):
        """
        Adds a parent property for this property.

        parent_id: The identifier of the parent property.  Can be either an OWL
            API IRI object or a string containing: a label (with or without a
            prefix), a prefix IRI (i.e., a curie, such as "owl:Thing"), a full
            IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label txt' or
            prefix:'label txt').
        """
        # Get the OWL property object of the parent, making sure that it is
        # actually defined.
        parentprop = self.ontology.getExistingDataProperty(parent_id)
        if parentprop is None:
            raise RuntimeError(
                'The designated superproperty, {0}, could not be found in the '
                'source ontology.'.format(parent_id)
            )
        parentprop = parentprop.getOWLAPIObj()

        # Add the subproperty axiom to the ontology.
        newaxiom = self.df.getOWLSubDataPropertyOfAxiom(self.entityobj, parentprop)
        self.ontology.addEntityAxiom(newaxiom)

    def addSubproperty(self, child_id):
        """
        Adds a child property for this property.

        chile_id: The identifier of the child property.  Can be either an OWL
            API IRI object or a string containing: a label (with or without a
            prefix), a prefix IRI (i.e., a curie, such as "owl:Thing"), a full
            IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label txt' or
            prefix:'label txt').
        """
        # Get the OWL property object of the child, making sure that it is
        # actually defined.
        childprop = self.ontology.getExistingDataProperty(child_id)
        if childprop is None:
            raise RuntimeError(
                'The designated subproperty, {0}, could not be found in the '
                'source ontology.'.format(child_id)
            )
        childprop = childprop.getOWLAPIObj()

        # Add the subproperty axiom to the ontology.
        newaxiom = self.df.getOWLSubDataPropertyOfAxiom(childprop, self.entityobj)
        self.ontology.addEntityAxiom(newaxiom)

    def addDomain(self, manchester_exp):
        """
        Adds a class expression as a domain for this data property.  The class
        expression should be written in Manchester Syntax (MS).

        manchester_exp: A string containing an MS "description" production.
        """
        if manchester_exp != '':
            cexp = self._getClassExpression(manchester_exp)

            # Add the domain axiom.
            daxiom = self.df.getOWLDataPropertyDomainAxiom(self.entityobj, cexp)
            self.ontology.addEntityAxiom(daxiom)

    def addRange(self, datarange_exp):
        """
        Creates a range axiom for this data property.

        datarange_exp: A text string containing a valid Manchester Syntax
            "dataRange" production.
        """
        if datarange_exp != '':
            try:
                parser = ManchesterSyntaxParserHelper(self.ontology)

                # Parse the expression to get an OWLDataRange object.
                datarange = parser.parseDataRange(datarange_exp);
            except ParserException as err:
                print err
                raise RuntimeError(
                    'Error parsing "{0}" at line {1}, column {2} of the data '
                    'property range (Manchester Syntax expected).'.format(
                        err.getCurrentToken(), err.getLineNumber(),
                        err.getColumnNumber()
                    )
                )

            # Add the range axiom.
            raxiom = self.df.getOWLDataPropertyRangeAxiom(self.entityobj, datarange)
            self.ontology.addEntityAxiom(raxiom)

    def addEquivalentTo(self, prop_id):
        """
        Sets this property as equivalent to another property.

        prop_id: The identifier of a data property.  Can be either an OWL API
            IRI object or a string containing: a label (with or without a
            prefix), a prefix IRI (i.e., a curie, such as "owl:Thing"), a full
            IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label txt' or
            prefix:'label txt').
        """
        # Get the OWL property object, making sure that it is actually defined.
        prop = self.ontology.getExistingDataProperty(prop_id)
        if prop is None:
            raise RuntimeError(
                'The designated equivalent property, "{0}", could not be '
                'found in the source ontology.'.format(parent_id)
            )
        owlprop = prop.getOWLAPIObj()

        # Add the equivalency axiom.
        daxiom = self.df.getOWLEquivalentDataPropertiesAxiom(
            self.entityobj, owlprop
        )
        self.ontology.addEntityAxiom(daxiom)

    def addDisjointWith(self, prop_id):
        """
        Sets this property as disjoint with another property.

        prop_id: The identifier of a data property.  Can be either an OWL
            API IRI object or a string containing: a label (with or without a
            prefix), a prefix IRI (i.e., a curie, such as "owl:Thing"), a full
            IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label txt' or
            prefix:'label txt').
        """
        propIRI = self.ontology.resolveIdentifier(prop_id)

        # Get the property object.  We do not require that the property is
        # already declared, because a "disjoint with" axiom might have to be
        # defined before both properties in the axiom have been defined.
        dpropobj = self.df.getOWLDataProperty(propIRI)

        # Add the "disjoint with" axiom.
        daxiom = self.df.getOWLDisjointDataPropertiesAxiom(self.entityobj, dpropobj)
        self.ontology.addEntityAxiom(daxiom)

    def makeFunctional(self):
        """
        Makes this data property a functional property.
        """
        faxiom = self.df.getOWLFunctionalDataPropertyAxiom(self.entityobj)
        self.ontology.addEntityAxiom(faxiom)


class _OntologyObjectProperty(_OntologyEntity):
    """
    Provides a high-level interface to the OWL API's ontology object system for
    OWL object properties.  Conceptually, instances of this class represent a
    single OWL object property in an OWL ontology.  This class should not be
    instantiated directly; instead, instances should be obtained through
    Ontology's public interface.
    """
    def __init__(self, propIRI, propobj, ontology):
        """
        Initializes this _OntologyObjectProperty.

          class_iri: The IRI object of the property.
          classobj: The OWL API class object of the property.
          ontology: The ontology to which this class belongs.  This should be
            an instance of the local Ontology class (i.e., not an instance of
            the OWL API ontology object.)
        """
        _OntologyEntity.__init__(self, propIRI, propobj, ontology)
        
    def getTypeConst(self):
        return OBJECTPROPERTY_ENTITY
        
    def addSuperproperty(self, parent_id):
        """
        Adds a parent property for this property.

        parent_id: The identifier of the parent property.  Can be either an OWL
            API IRI object or a string containing: a label (with or without a
            prefix), a prefix IRI (i.e., a curie, such as "owl:Thing"), a full
            IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label txt' or
            prefix:'label txt').
        """
        # Get the OWL property object of the parent, making sure that it is
        # actually defined.
        parentprop = self.ontology.getExistingObjectProperty(parent_id)
        if parentprop is None:
            raise RuntimeError(
                'The designated superproperty, {0}, could not be found in the '
                'source ontology.'.format(parent_id)
            )
        parentprop = parentprop.getOWLAPIObj()

        # Add the subproperty axiom to the ontology.
        newaxiom = self.df.getOWLSubObjectPropertyOfAxiom(self.entityobj, parentprop)
        self.ontology.addEntityAxiom(newaxiom)

    def addSubproperty(self, child_id):
        """
        Adds a child property for this property.

        chile_id: The identifier of the child property.  Can be either an OWL
            API IRI object or a string containing: a label (with or without a
            prefix), a prefix IRI (i.e., a curie, such as "owl:Thing"), a full
            IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label txt' or
            prefix:'label txt').
        """
        # Get the OWL property object of the child, making sure that it is
        # actually defined.
        childprop = self.ontology.getExistingObjectProperty(child_id)
        if childprop is None:
            raise RuntimeError(
                'The designated subproperty, {0}, could not be found in the '
                'source ontology.'.format(child_id)
            )
        childprop = childprop.getOWLAPIObj()

        # Add the subproperty axiom to the ontology.
        newaxiom = self.df.getOWLSubObjectPropertyOfAxiom(childprop, self.entityobj)
        self.ontology.addEntityAxiom(newaxiom)

    def addDomain(self, manchester_exp):
        """
        Adds a class expression as a domain for this object property.  The
        class expression should be written in Manchester Syntax (MS).

        manchester_exp: A string containing an MS "description" production.
        """
        if manchester_exp != '':
            cexp = self._getClassExpression(manchester_exp)

            # Add the domain axiom.
            daxiom = self.df.getOWLObjectPropertyDomainAxiom(self.entityobj, cexp)
            self.ontology.addEntityAxiom(daxiom)

    def addRange(self, manchester_exp):
        """
        Adds a class expression as a range for this object property.  The class
        expression should be written in Manchester Syntax (MS).

        manchester_exp: A string containing an MS "description" production.
        """
        if manchester_exp != '':
            cexp = self._getClassExpression(manchester_exp)

            # Add the range axiom.
            raxiom = self.df.getOWLObjectPropertyRangeAxiom(self.entityobj, cexp)
            self.ontology.addEntityAxiom(raxiom)

    def addInverse(self, inverse_id):
        """
        Creates an inverse axiom for this property.

        inverse_id: The identifier of an object property.  Can be either an OWL
            API IRI object or a string containing: a label (with or without a
            prefix), a prefix IRI (i.e., a curie, such as "owl:Thing"), a full
            IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label txt' or
            prefix:'label txt').
        """
        inverseIRI = self.ontology.resolveIdentifier(inverse_id)

        # Get the inverse property object.  We do not require that the property
        # is already declared, because an inverse axiom might have to be
        # defined before both properties in the axiom have been defined.
        inv_propobj = self.df.getOWLObjectProperty(inverseIRI)

        # Add the "inverse of" axiom.
        iaxiom = self.df.getOWLInverseObjectPropertiesAxiom(self.entityobj, inv_propobj)
        self.ontology.addEntityAxiom(iaxiom)

    def addEquivalentTo(self, prop_id):
        """
        Sets this property as equivalent to another property.

        prop_id: The identifier of an object property.  Can be either an OWL
            API IRI object or a string containing: a label (with or without a
            prefix), a prefix IRI (i.e., a curie, such as "owl:Thing"), a full
            IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label txt' or
            prefix:'label txt').
        """
        # Get the OWL property object, making sure that it is actually defined.
        prop = self.ontology.getExistingObjectProperty(prop_id)
        if prop is None:
            raise RuntimeError(
                'The designated equivalent property, "{0}", could not be '
                'found in the source ontology.'.format(parent_id)
            )
        owlprop = prop.getOWLAPIObj()

        # Add the equivalency axiom.
        daxiom = self.df.getOWLEquivalentObjectPropertiesAxiom(
            self.entityobj, owlprop
        )
        self.ontology.addEntityAxiom(daxiom)

    def addDisjointWith(self, prop_id):
        """
        Sets this property as disjoint with another property.

        prop_id: The identifier of an object property.  Can be either an OWL
            API IRI object or a string containing: a label (with or without a
            prefix), a prefix IRI (i.e., a curie, such as "owl:Thing"), a full
            IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label txt' or
            prefix:'label txt').
        """
        propIRI = self.ontology.resolveIdentifier(prop_id)

        # Get the property object.  We do not require that the property is
        # already declared, because a "disjoint with" axiom might have to be
        # defined before both properties in the axiom have been defined.
        dpropobj = self.df.getOWLObjectProperty(propIRI)

        # Add the "disjoint with" axiom.
        daxiom = self.df.getOWLDisjointObjectPropertiesAxiom(self.entityobj, dpropobj)
        self.ontology.addEntityAxiom(daxiom)

    def makeFunctional(self):
        """
        Makes this property a functional property.
        """
        paxiom = self.df.getOWLFunctionalObjectPropertyAxiom(self.entityobj)
        self.ontology.addEntityAxiom(paxiom)

    def makeInverseFunctional(self):
        """
        Makes this property an inverse functional property.
        """
        paxiom = self.df.getOWLInverseFunctionalObjectPropertyAxiom(self.entityobj)
        self.ontology.addEntityAxiom(paxiom)

    def makeReflexive(self):
        """
        Makes this property a reflexive property.
        """
        paxiom = self.df.getOWLReflexiveObjectPropertyAxiom(self.entityobj)
        self.ontology.addEntityAxiom(paxiom)

    def makeIrreflexive(self):
        """
        Makes this property an irreflexive property.
        """
        paxiom = self.df.getOWLIrreflexiveObjectPropertyAxiom(self.entityobj)
        self.ontology.addEntityAxiom(paxiom)

    def makeSymmetric(self):
        """
        Makes this property a symmetric property.
        """
        paxiom = self.df.getOWLSymmetricObjectPropertyAxiom(self.entityobj)
        self.ontology.addEntityAxiom(paxiom)

    def makeAsymmetric(self):
        """
        Makes this property an asymmetric property.
        """
        paxiom = self.df.getOWLAsymmetricObjectPropertyAxiom(self.entityobj)
        self.ontology.addEntityAxiom(paxiom)

    def makeTransitive(self):
        """
        Makes this property a transitive property.
        """
        paxiom = self.df.getOWLTransitiveObjectPropertyAxiom(self.entityobj)
        self.ontology.addEntityAxiom(paxiom)


class _OntologyAnnotationProperty(_OntologyEntity):
    """
    Provides a high-level interface to the OWL API's ontology object system for
    OWL annotation properties.  Conceptually, instances of this class represent
    a single OWL annotation property in an OWL ontology.  This class should not
    be instantiated directly; instead, instances should be obtained through
    Ontology's public interface.
    """
    def __init__(self, propIRI, propobj, ontology):
        """
        Initializes this _OntologyAnnotationProperty.

          class_iri: The IRI object of the property.
          propobj: The OWL API property object of the property.
          ontology: The ontology to which this class belongs.  This should be
            an instance of the local Ontology class (i.e., not an instance of
            the OWL API ontology object.)
        """
        _OntologyEntity.__init__(self, propIRI, propobj, ontology)
        
    def getTypeConst(self):
        return ANNOTATIONPROPERTY_ENTITY
        
    def addSuperproperty(self, parent_id):
        """
        Adds a parent property for this property.

        parent_id: The identifier of the parent property.  Can be either an OWL
            API IRI object or a string containing: a label (with or without a
            prefix), a prefix IRI (i.e., a curie, such as "owl:Thing"), a full
            IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label txt' or
            prefix:'label txt').
        """
        # Get the OWL property object of the parent, making sure that it is
        # actually defined.
        parentprop = self.ontology.getExistingAnnotationProperty(parent_id)
        if parentprop is None:
            raise RuntimeError(
                'The designated superproperty, {0}, could not be found in the '
                'source ontology.'.format(parent_id)
            )
        parentprop = parentprop.getOWLAPIObj()

        # Add the subproperty axiom to the ontology.
        newaxiom = self.df.getOWLSubAnnotationPropertyOfAxiom(self.entityobj, parentprop)
        self.ontology.addEntityAxiom(newaxiom)

    def addSubproperty(self, child_id):
        """
        Adds a child property for this property.

        chile_id: The identifier of the child property.  Can be either an OWL
            API IRI object or a string containing: a label (with or without a
            prefix), a prefix IRI (i.e., a curie, such as "owl:Thing"), a full
            IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label txt' or
            prefix:'label txt').
        """
        # Get the OWL property object of the child, making sure that it is
        # actually defined.
        childprop = self.ontology.getExistingAnnotationProperty(child_id)
        if childprop is None:
            raise RuntimeError(
                'The designated subproperty, {0}, could not be found in the '
                'source ontology.'.format(child_id)
            )
        childprop = childprop.getOWLAPIObj()

        # Add the subproperty axiom to the ontology.
        newaxiom = self.df.getOWLSubAnnotationPropertyOfAxiom(childprop, self.entityobj)
        self.ontology.addEntityAxiom(newaxiom)


class _OntologyIndividual(_OntologyEntity):
    """
    Provides a high-level interface to the OWL API's object system for OWL
    individuals.  Conceptually, instances of this class represent a single
    individual in an OWL ontology.  This class should not be instantiated
    directly; instead, instances should be obtained through Ontology's public
    interface.
    """
    def __init__(self, indvIRI, individual_obj, ontology):
        """
        Initializes this _OntologyIndividual.

        indvIRI: The IRI object of the individual.
        individual_obj: An OWL API OWLNamedIndividual instance.
        ontology: The ontology to which this individual belongs.  This should
            be an instance of the local Ontology class (i.e., not an instance
            of the OWL API ontology object.)
        """
        _OntologyEntity.__init__(self, indvIRI, individual_obj, ontology)

    def getTypeConst(self):
        return INDIVIDUAL_ENTITY
        
    def addType(self, manchester_exp):
        """
        Adds a class expression as a type for this individual.  The class
        expression should be written in Manchester Syntax (MS).

        manchester_exp: A string containing an MS "description" production.
        """
        if manchester_exp != '':
            cexp = self._getClassExpression(manchester_exp)
            eaxiom = self.df.getOWLClassAssertionAxiom(cexp, self.entityobj)
            self.ontology.addEntityAxiom(eaxiom)

    def addObjectPropertyFact(self, objprop_id, indv_id, is_negative=False):
        """
        Adds an object property assertion (fact) for this individual.

        objprop_id: The identifier of an object property.  Can be either an OWL
            API IRI object or a string containing: a label (with or without a
            prefix), a prefix IRI (i.e., a curie, such as "owl:Thing"), a full
            IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label txt' or
            prefix:'label txt').
        indv_id: The identifier of the named individual to link to this
            individual with the provided object property.  Can be either an OWL
            API IRI object or a string containing: a label (with or without a
            prefix), a prefix IRI (i.e., a curie, such as "owl:Thing"), a full
            IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label txt' or
            prefix:'label txt').
        is_negative: Whether to create a negative object property assertion.
        """
        # Get the object property, making sure that it is actually defined.
        objprop = self.ontology.getExistingObjectProperty(objprop_id)
        if objprop is None:
            raise RuntimeError(
                'Unable to create a new object property assertion (fact) for '
                'the individual <{0}>.  The object property "{1}" could not '
                'be found in the source ontology.'.format(
                    self.entityIRI, objprop_id
                )
            )
        objprop = objprop.getOWLAPIObj()

        # Get the named individual, making sure that it is actually defined.
        indv = self.ontology.getExistingIndividual(indv_id)
        if indv is None:
            raise RuntimeError(
                'Unable to create a new object property assertion (fact) for '
                'the individual <{0}>.  The named individual "{1}" could not '
                'be found in the source ontology.'.format(
                    self.entityIRI, indv_id
                )
            )
        indv = indv.getOWLAPIObj()

        # Add the object property assertion axiom to the ontology.
        if is_negative:
            newaxiom = self.df.getOWLNegativeObjectPropertyAssertionAxiom(
                objprop, self.entityobj, indv
            )
        else:
            newaxiom = self.df.getOWLObjectPropertyAssertionAxiom(
                objprop, self.entityobj, indv
            )

        self.ontology.addEntityAxiom(newaxiom)

    def addDataPropertyFact(self, dataprop_id, literal_exp, is_negative=False):
        """
        Adds a data property assertion (fact) for this individual.

        dataprop_id: The identifier of a data property.  Can be either an OWL
            API IRI object or a string containing: a label (with or without a
            prefix), a prefix IRI (i.e., a curie, such as "owl:Thing"), a full
            IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label txt' or
            prefix:'label txt').
        literal_exp: A string that represents a literal value.  The string
            should follow the "literal" production of Manchester Syntax.
        is_negative: Whether to create a negative data property assertion.
        """
        # Get the data property, making sure that it is actually defined.
        dataprop = self.ontology.getExistingDataProperty(dataprop_id)
        if dataprop is None:
            raise RuntimeError(
                'Unable to create a new data property assertion (fact) for '
                'the individual <{0}>.  The data property "{1}" could not be '
                'found in the source ontology.'.format(
                    self.entityIRI, dataprop_id
                )
            )
        dataprop = dataprop.getOWLAPIObj()

        # Parse the literal value.
        try:
            parser = ManchesterSyntaxParserHelper(self.ontology)
            litval = parser.parseLiteral(literal_exp);
        except ParserException as err:
            raise RuntimeError(
                'Unable to create a new data property assertion (fact) for '
                'the individual <{0}>.  Error parsing "{1}" at line {2}, '
                'column {3} of the literal expression (Manchester Syntax '
                'expected): {4}.'.format(
                    self.entityIRI, err.getCurrentToken(), err.getLineNumber(),
                    err.getColumnNumber(), literal_exp
                )
            )

        # Add the data property assertion axiom to the ontology.
        if is_negative:
            newaxiom = self.df.getOWLNegativeDataPropertyAssertionAxiom(
                dataprop, self.entityobj, litval
            )
        else:
            newaxiom = self.df.getOWLDataPropertyAssertionAxiom(
                dataprop, self.entityobj, litval
            )
        self.ontology.addEntityAxiom(newaxiom)

