#
# Provides convenience classes that "wrap" OWL API classes and properties and
# implements a higher-level interface for interacting with OWL ontologies.
# None of these classes should be instantiated directly; rather, instances
# should be obtained from the public methods of the ontology.Ontology class.
#

# Python imports.
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

        self.ontology.addTermAxiom(annotaxiom)

    def addLabel(self, labeltxt):
        """
        Adds an rdfs:label for this entity.
        """
        labeltxt = labeltxt.strip()

        labelannot = self.df.getOWLAnnotation(
            self.df.getRDFSLabel(), self.df.getOWLLiteral(labeltxt, 'en')
        )
        annotaxiom = self.df.getOWLAnnotationAssertionAxiom(self.entityIRI, labelannot)

        self.ontology.addTermAxiom(annotaxiom)

    def addComment(self, commenttxt):
        """
        Adds an rdfs:comment for this entity.
        """
        commenttxt = commenttxt.strip()

        commentannot = self.df.getOWLAnnotation(
            self.df.getRDFSComment(), self.df.getOWLLiteral(commenttxt, 'en')
        )
        annotaxiom = self.df.getOWLAnnotationAssertionAxiom(self.entityIRI, commentannot)

        self.ontology.addTermAxiom(annotaxiom)

    def getAnnotationValues(self, annotpropIRI):
        """
        Returns a list containing the string values of all annotation axioms
        for this entity of the specified annotation type.
        """
        annotvals = []

        owlont = self.ontology.getOWLOntology()
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
            raise RuntimeError('Error parsing "' + err.getCurrentToken()
                    + '" at line ' + str(err.getLineNumber()) + ', column '
                    + str(err.getColumnNumber())
                    + ' of the class expression (Manchester Syntax expected).')

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
        
    def addSuperclass(self, parent_id):
        """
        Adds a parent class for this class.

        parent_id: The identifier of the parent class.  Can be either an OWL
            API IRI object or a string containing: a label (with or without a
            prefix), a prefix IRI (i.e., a curie, such as "owl:Thing"), a full
            IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label txt' or
            prefix:'label txt').
        """
        # Get the OWLClass object of the parent class, making sure that it is
        # actually defined.
        parentclass = self.ontology.getExistingClass(parent_id)
        if parentclass == None:
            raise RuntimeError('The designated superclass, ' + str(parent_id)
                    + ', could not be found in the source ontology.')
        parentclass = parentclass.getOWLAPIObj()
        
        # Add the subclass axiom to the ontology.
        newaxiom = self.df.getOWLSubClassOfAxiom(self.entityobj, parentclass)
        self.ontology.addTermAxiom(newaxiom)

    def addSubclassOf(self, manchester_exp):
        """
        Adds a class expression as a "subclass of" axiom.  The class expression
        should be written in Manchester Syntax (MS).

        manchester_exp: A string containing an MS "description" production.
        """
        if manchester_exp != '':
            cexp = self._getClassExpression(manchester_exp)
            eaxiom = self.df.getOWLSubClassOfAxiom(self.entityobj, cexp)
            self.ontology.addTermAxiom(eaxiom)

    def addEquivalentTo(self, manchester_exp):
        """
        Adds a class expression as an equivalency axiom.  The class expressions
        should be written in Manchester Syntax (MS).

        manchester_exp: A string containing an MS "description" production.
        """
        if manchester_exp != '':
            cexp = self._getClassExpression(manchester_exp)
            eaxiom = self.df.getOWLEquivalentClassesAxiom(self.entityobj, cexp)
            self.ontology.addTermAxiom(eaxiom)

    def addDisjointWith(self, manchester_exp):
        """
        Adds a class expression as a "disjoint with" axioms.  The class
        expressions should be written in Manchester Syntax (MS).

        manchester_exp: A string containing an MS "description" production.
        """
        if manchester_exp != '':
            cexp = self._getClassExpression(manchester_exp)
            axiom = self.df.getOWLDisjointClassesAxiom(self.entityobj, cexp)
            self.ontology.addTermAxiom(axiom)


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
        if parentprop == None:
            raise RuntimeError('The designated superproperty, ' + str(parent_id)
                    + ', could not be found in the source ontology.')
        parentprop = parentprop.getOWLAPIObj()

        # Add the subproperty axiom to the ontology.
        newaxiom = self.df.getOWLSubDataPropertyOfAxiom(self.entityobj, parentprop)
        self.ontology.addTermAxiom(newaxiom)

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
            self.ontology.addTermAxiom(daxiom)

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
                raise RuntimeError('Error parsing "' + err.getCurrentToken()
                        + '" at line ' + str(err.getLineNumber()) + ', column '
                        + str(err.getColumnNumber())
                        + ' of the data property range (Manchester Syntax expected).')

            # Add the range axiom.
            raxiom = self.df.getOWLDataPropertyRangeAxiom(self.entityobj, datarange)
            self.ontology.addTermAxiom(raxiom)

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
        self.ontology.addTermAxiom(daxiom)

    def makeFunctional(self):
        """
        Makes this data property a functional property.
        """
        faxiom = self.df.getOWLFunctionalDataPropertyAxiom(self.entityobj)
        self.ontology.addTermAxiom(faxiom)


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
        if parentprop == None:
            raise RuntimeError('The designated superproperty, ' + str(parent_id)
                    + ', could not be found in the source ontology.')
        parentprop = parentprop.getOWLAPIObj()

        # Add the subproperty axiom to the ontology.
        newaxiom = self.df.getOWLSubObjectPropertyOfAxiom(self.entityobj, parentprop)
        self.ontology.addTermAxiom(newaxiom)

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
            self.ontology.addTermAxiom(daxiom)

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
            self.ontology.addTermAxiom(raxiom)

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
        self.ontology.addTermAxiom(iaxiom)

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
        self.ontology.addTermAxiom(daxiom)

    def makeFunctional(self):
        """
        Makes this property a functional property.
        """
        paxiom = self.df.getOWLFunctionalObjectPropertyAxiom(self.entityobj)
        self.ontology.addTermAxiom(paxiom)

    def makeInverseFunctional(self):
        """
        Makes this property an inverse functional property.
        """
        paxiom = self.df.getOWLInverseFunctionalObjectPropertyAxiom(self.entityobj)
        self.ontology.addTermAxiom(paxiom)

    def makeReflexive(self):
        """
        Makes this property a reflexive property.
        """
        paxiom = self.df.getOWLReflexiveObjectPropertyAxiom(self.entityobj)
        self.ontology.addTermAxiom(paxiom)

    def makeIrreflexive(self):
        """
        Makes this property an irreflexive property.
        """
        paxiom = self.df.getOWLIrreflexiveObjectPropertyAxiom(self.entityobj)
        self.ontology.addTermAxiom(paxiom)

    def makeSymmetric(self):
        """
        Makes this property a symmetric property.
        """
        paxiom = self.df.getOWLSymmetricObjectPropertyAxiom(self.entityobj)
        self.ontology.addTermAxiom(paxiom)

    def makeAsymmetric(self):
        """
        Makes this property an asymmetric property.
        """
        paxiom = self.df.getOWLAsymmetricObjectPropertyAxiom(self.entityobj)
        self.ontology.addTermAxiom(paxiom)

    def makeTransitive(self):
        """
        Makes this property a transitive property.
        """
        paxiom = self.df.getOWLTransitiveObjectPropertyAxiom(self.entityobj)
        self.ontology.addTermAxiom(paxiom)


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
        if parentprop == None:
            raise RuntimeError('The designated superproperty, ' + str(parent_id)
                    + ', could not be found in the source ontology.')
        parentprop = parentprop.getOWLAPIObj()

        # Add the subproperty axiom to the ontology.
        newaxiom = self.df.getOWLSubAnnotationPropertyOfAxiom(self.entityobj, parentprop)
        self.ontology.addTermAxiom(newaxiom)


class _OntologyIndividual(_OntologyEntity):
    """
    Provides a high-level interface to the OWL API's object system for OWL
    individuals.  Conceptually, instances of this class represent a single
    individual in an OWL ontology.  This class should not be instantiated
    directly; instead, instances should be obtained through Ontology's public
    interface.
    """
    def __init__(self, individualIRI, individual_obj, ontology):
        """
        Initializes this _OntologyIndividual.

        individualIRI: The IRI object of the individual.
        individual_obj: The OWL API class object of the individual.
        ontology: The ontology to which this individual belongs.  This should
            be an instance of the local Ontology class (i.e., not an instance
            of the OWL API ontology object.)
        """
        _OntologyEntity.__init__(self, individualIRI, individual_obj, ontology)

    def getTypeConst(self):
        return INDIVIDUAL_ENTITY
        
    def addType(self, manchester_exp):
        """
        Adds a class expression as a "subclass of" axiom.  The class expression
        should be written in Manchester Syntax (MS).

        manchester_exp: A string containing an MS "description" production.
        """
        if manchester_exp != '':
            cexp = self._getClassExpression(manchester_exp)
            eaxiom = self.df.getOWLClassAssertionAxiom(cexp, self.entityobj)
            self.ontology.addTermAxiom(eaxiom)

