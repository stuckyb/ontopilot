#
# Provides a single class, OWLOntologyBuilder, that implements methods for
# parsing descriptions of ontology classes (e.g., from CSV files) and
# converting them into classes in an OWL ontology.
#

# Python imports.
import re
import logging
from obohelper import termIRIToOboID, oboIDToIRI
from ontology import Ontology
from ontology_entities import (
    CLASS_ENTITY, DATAPROPERTY_ENTITY, OBJECTPROPERTY_ENTITY,
    ANNOTATIONPROPERTY_ENTITY
)
from delimstr_parser import DelimStrParser

# Java imports.


class TermDescriptionError(RuntimeError):
    """
    An exception class for errors encountered in term descriptions in rows from
    input files.
    """
    def __init__(self, error_msg, tablerow):
        self.tablerow = tablerow

        new_msg = (
            'Error encountered in term description in row '
            + str(tablerow.getRowNum()) + ' of a table in "'
            + tablerow.getFileName() + '":\n' + error_msg
        )

        RuntimeError.__init__(self, new_msg)


class OWLOntologyBuilder:
    """
    Builds an OWL ontology using _TableRow objects that describe new entities
    to add to an existing "base" ontology.  Typically, the new entity
    descriptions will correspond with rows in an input CSV file or other
    tabular file format.  In order to allow forward references of term labels,
    OWLOntologyBuilder uses a 2-stage process for defining new terms.  First,
    when the various addEntity() methods are called, only the new entity and
    label annotation axioms are created.  The remainder of the definition is
    cached along with a reference to the new entity.  The second step happens
    when the method processDeferredEntityAxioms() is called.  This method adds
    all remaining axioms for each entity (e.g., text definitions, comments,
    equivalency axioms, subclass of axioms, etc.).
    """
    def __init__(self, base_ont_path):
        # Load the base ontology.
        self.ontology = Ontology(base_ont_path)

        # A list (used as a stack) for caching information in _TableRow objects
        # and their associated ontology entity objects.  Each list entry is
        # stored as a tuple, (ontology entity instance, _TableRow instance).
        self.entity_trows = []

        self.dsparser = DelimStrParser(';')

    def getOntology(self):
        """
        Returns the Ontology object contained by this OWLOntologyBuilder.
        """
        return self.ontology

    def addClass(self, classdesc):
        """
        Adds a new class to the ontology, based on a class description provided
        as the table row classdesc (i.e., the single explicit argument).
        """
        try:
            # Create the new class.
            newclass = self.ontology.createNewClass(classdesc['ID'])
            
            # Make sure we have a label and add it to the new class.
            labeltext = classdesc['Label']
            if labeltext != '':
                newclass.addLabel(labeltext)
        except RuntimeError as err:
            raise TermDescriptionError(str(err), classdesc)

        # Cache the remainder of the class description.
        self.entity_trows.append((newclass, classdesc))

    def _addGenericAxioms(self, entobj, entdesc, expanddef=True):
        """
        Adds generic axioms (i.e., axioms that all entities have in common)
        from a _TableRow entity description to an existing entity object.  If
        expanddef is True, then term labels in the text definition(s) for the
        new entity will be expanded to include the terms' OBO IDs.
        """
        # Add any text definitions for the entity.
        textdefs = self.dsparser.parseString(entdesc['Text definition'])
        for textdef in textdefs:
            if expanddef:
                textdef = self._expandDefinition(textdef)
            entobj.addDefinition(textdef)

        # Add any comments for the entity.
        commenttexts = self.dsparser.parseString(entdesc['Comments'])
        for commenttext in commenttexts:
            entobj.addComment(commenttext)

    def _addClassAxioms(self, classobj, classdesc, expanddef=True):
        """
        Adds axioms from a _TableRow class description to an existing class
        object.  If expanddef is True, then term labels in the text definition
        for the new class will be expanded to include the terms' OBO IDs.
        """
        self._addGenericAxioms(classobj, classdesc, expanddef)

        # Get the IRI objects of parent classes and add them as parents.
        for parentID in self.dsparser.parseString(classdesc['Parent']):
            parentIRI = self._getIRIFromDesc(parentID)
            if parentIRI != None:
                classobj.addSuperclass(parentIRI)
    
        # Add any subclass of axioms (specified as class expressions in
        # Manchester Syntax).
        ms_exps = self.dsparser.parseString(classdesc['Subclass of'])
        for ms_exp in ms_exps:
            classobj.addSubclassOf(ms_exp)
 
        # Add any equivalency axioms (specified as class expressions in
        # Manchester Syntax).
        ms_exps = self.dsparser.parseString(classdesc['Equivalent to'])
        for ms_exp in ms_exps:
            classobj.addEquivalentTo(ms_exp)

        # Add any disjoint with axioms (specified as class expressions in
        # Manchester Syntax).
        ms_exps = self.dsparser.parseString(classdesc['Disjoint with'])
        for ms_exp in ms_exps:
            classobj.addDisjointWith(ms_exp)
 
    def addDataProperty(self, propdesc):
        """
        Adds a new data property to the ontology, based on a property
        description provided as the table row propdesc (i.e., the single
        explicit argument).  If expanddef is True, then term labels in the text
        definition for the new property will be expanded to include the terms'
        OBO IDs.
        """
        try:
            # Create the new data property.
            newprop = self.ontology.createNewDataProperty(propdesc['ID'])
            
            # Make sure we have a label and add it to the new class.
            labeltext = propdesc['Label']
            if labeltext != '':
                newprop.addLabel(labeltext)
        except RuntimeError as err:
            raise TermDescriptionError(str(err), propdesc)
        
        # Cache the remainder of the property description.
        self.entity_trows.append((newprop, propdesc))

    def _addDataPropertyAxioms(self, propobj, propdesc, expanddef=True):
        """
        Adds axioms from a _TableRow data property description to an existing
        data property object.  If expanddef is True, then term labels in the
        text definition for the new property will be expanded to include the
        terms' OBO IDs.
        """
        self._addGenericAxioms(propobj, propdesc, expanddef)

        # Get the IRI objects of parent properties and add them as parents.
        for parentID in self.dsparser.parseString(propdesc['Parent']):
            parentIRI = self._getIRIFromDesc(parentID)
            if parentIRI != None:
                propobj.addSuperproperty(parentIRI)

        # Add any domain axioms (specified as class expressions in Manchester
        # Syntax).
        ms_exps = self.dsparser.parseString(propdesc['Domain'])
        for ms_exp in ms_exps:
            propobj.addDomain(ms_exp)

        # Add any range axioms (specified as Manchester Syntax "dataRange"
        # productions).
        range_exps = self.dsparser.parseString(propdesc['Range'])
        for range_exp in range_exps:
            propobj.addRange(range_exp)

        # Add any disjointness axioms.
        propIDs = self.dsparser.parseString(propdesc['Disjoint with'])
        for propID in propIDs:
            disjIRI = self._getIRIFromDesc(propID)
            if disjIRI != None:
                propobj.addDisjointWith(disjIRI)

        # Add the characteristics, if provided.  The only supported
        # characteristic for data properties is "functional".
        chars_str = propdesc['Characteristics']
        if chars_str != '':
            if chars_str.lower() == 'functional':
                propobj.makeFunctional()
            else:
                raise RuntimeError(
                    'Unrecognized characteristic(s) for a data property: "'
                    + chars_str + 
                    '".  For data properties, "functional" is the only supported characteristic.'
                )

    def addObjectProperty(self, propdesc):
        """
        Adds a new object property to the ontology, based on a property
        description provided as the table row propdesc (i.e., the single
        explicit argument).  If expanddef is True, then term labels in the text
        definition for the new property will be expanded to include the terms'
        OBO IDs.
        """
        try:
            # Create the new object property.
            newprop = self.ontology.createNewObjectProperty(propdesc['ID'])
            
            # Make sure we have a label and add it to the new class.
            labeltext = propdesc['Label']
            if labeltext != '':
                newprop.addLabel(labeltext)
        except RuntimeError as err:
            raise TermDescriptionError(str(err), propdesc)
        
        # Cache the remainder of the property description.
        self.entity_trows.append((newprop, propdesc))

    def _addObjectPropertyAxioms(self, propobj, propdesc, expanddef=True):
        """
        Adds axioms from a _TableRow object property description to an existing
        object property object.  If expanddef is True, then term labels in the
        text definition for the new property will be expanded to include the
        terms' OBO IDs.
        """
        self._addGenericAxioms(propobj, propdesc, expanddef)

        # Get the IRI objects of parent properties and add them as parents.
        for parentID in self.dsparser.parseString(propdesc['Parent']):
            parentIRI = self._getIRIFromDesc(parentID)
            if parentIRI != None:
                propobj.addSuperproperty(parentIRI)

        # Add any domain axioms (specified as class expressions in Manchester
        # Syntax).
        ms_exps = self.dsparser.parseString(propdesc['Domain'])
        for ms_exp in ms_exps:
            propobj.addDomain(ms_exp)

        # Add any range axioms (specified as class expressions in Manchester
        # Syntax).
        ms_exps = self.dsparser.parseString(propdesc['Range'])
        for ms_exp in ms_exps:
            propobj.addRange(ms_exp)

        # Add any "inverse of" axioms.
        propIDs = self.dsparser.parseString(propdesc['Inverse'])
        for propID in propIDs:
            inverseIRI = self._getIRIFromDesc(propID)
            if inverseIRI != None:
                propobj.addInverse(inverseIRI)

        # Add any disjointness axioms.
        propIDs = self.dsparser.parseString(propdesc['Disjoint with'])
        for propID in propIDs:
            disjIRI = self._getIRIFromDesc(propID)
            if disjIRI != None:
                propobj.addDisjointWith(disjIRI)

        # Add the characteristics, if provided.
        chars_str = propdesc['Characteristics']
        if chars_str != '':
            self._processObjPropCharacteristics(propobj, chars_str)

    def _processObjPropCharacteristics(self, propobj, chars_str):
        """
        Sets the characteristics of an object property according to a string
        containing a comma-separated list of property characteristics.
        """
        for char_str in chars_str.split(','):
            char_str = char_str.strip().lower()

            if char_str == 'functional':
                propobj.makeFunctional()
            elif char_str == 'inverse functional':
                propobj.makeInverseFunctional()
            elif char_str == 'reflexive':
                propobj.makeReflexive()
            elif char_str == 'irreflexive':
                propobj.makeIrreflexive()
            elif char_str == 'symmetric':
                propobj.makeSymmetric()
            elif char_str == 'asymmetric':
                propobj.makeAsymmetric()
            elif char_str == 'transitive':
                propobj.makeTransitive()
            else:
                raise RuntimeError(
                    'Unrecognized characteristic for an object property: "'
                    + char_str + 
                    '".  Supported characteristics for object properties are "functional", "inverse functional", "reflexive", "irreflexive", "symmetric", "asymmetric", and "transitive".'
                )

    def addAnnotationProperty(self, propdesc):
        """
        Adds a new annotation property to the ontology, based on a property
        description provided as the table row propdesc (i.e., the single
        explicit argument).  If expanddef is True, then term labels in the text
        definition for the new property will be expanded to include the terms'
        OBO IDs.
        """
        try:
            # Create the new annotation property.
            newprop = self.ontology.createNewAnnotationProperty(propdesc['ID'])
            
            # Make sure we have a label and add it to the new class.
            labeltext = propdesc['Label']
            if labeltext != '':
                newprop.addLabel(labeltext)
        except RuntimeError as err:
            raise TermDescriptionError(str(err), propdesc)
        
        # Cache the remainder of the property description.
        self.entity_trows.append((newprop, propdesc))

    def _addAnnotationPropertyAxioms(self, propobj, propdesc, expanddef=True):
        """
        Adds axioms from a _TableRow object property description to an existing
        annotation property object.  If expanddef is True, then term labels in
        the text definition for the new property will be expanded to include
        the terms' OBO IDs.
        """
        self._addGenericAxioms(propobj, propdesc, expanddef)

        # Get the IRI objects of parent properties and add them as parents.
        for parentID in self.dsparser.parseString(propdesc['Parent']):
            parentIRI = self._getIRIFromDesc(parentID)
            if parentIRI != None:
                propobj.addSuperproperty(parentIRI)

    def processDeferredEntityAxioms(self, expanddefs=True):
        """
        Processes all cached _TableRow entity descriptions and entity objects
        by adding all remaining axioms for the entities. (e.g., text
        definitions, comments, subclass of axioms, etc.).  If expanddefs is
        True, then term labels in the text definition for the new property will
        be expanded to include the terms' OBO IDs.
        """
        while len(self.entity_trows) > 0:
            entity, desc = self.entity_trows[-1]

            try:
                typeconst = entity.getTypeConst()
                if typeconst == CLASS_ENTITY:
                    self._addClassAxioms(entity, desc, expanddefs)
                elif typeconst == DATAPROPERTY_ENTITY:
                    self._addDataPropertyAxioms(entity, desc, expanddefs)
                elif typeconst == OBJECTPROPERTY_ENTITY:
                    self._addObjectPropertyAxioms(entity, desc, expanddefs)
                elif typeconst == ANNOTATIONPROPERTY_ENTITY:
                    self._addAnnotationPropertyAxioms(entity, desc, expanddefs)
                else:
                    raise RuntimeError('Unsupported ontology entity type: '
                            + str(typeconst) + '.')
            except RuntimeError as err:
                raise TermDescriptionError(str(err), desc)

            # Putting the pop() operation at the end of the loop ensures that a
            # description is only removed from the list/stack if it was
            # processed without an exception being thrown.
            self.entity_trows.pop()

    def _getIRIFromDesc(self, id_desc):
        """
        Parses an identifier field from a term description dictionary and
        returns the matching IRI.  The identifier description, id_desc, can be
        a term label, OBO ID, prefix IRI, or full IRI.  The general format is:
        "'term label' (TERM_ID)", or "'term label'", or "TERM_ID".
        For example: "'whole plant' (PO:0000003)", "'whole plant'", or
        "PO:0000003".  If both a label and ID are provided, this method will
        verify that they correspond.  Returns an OWL API IRI object.
        """
        tdata = id_desc.strip()
        if tdata == '':
            return None

        labelIRI = None
        tdIRI = None
    
        # Check if we have a term label.
        if tdata.startswith("'"):
            if tdata.find("'") == tdata.rfind("'"):
                raise RuntimeError('Missing closing quote in parent class specification: '
                            + tdata + '".')
            label = tdata.split("'")[1]

            # Get the class IRI associated with the label.
            labelIRI = self.ontology.labelToIRI(label)
    
            # See if we also have an ID.
            if tdata.find('(') > -1:
                tdID = tdata.split('(')[1]
                if tdID.find(')') > -1:
                    tdID = tdID.rstrip(')')
                    tdIRI = self.ontology.expandIdentifier(tdID)
                else:
                    raise RuntimeError('Missing closing parenthesis in parent class specification: '
                            + tdata + '".')
        else:
            # We only have an ID.
            tdIRI = self.ontology.expandIdentifier(tdata)
    
        if labelIRI != None:
            if tdIRI != None:
                if labelIRI.equals(tdIRI):
                    return labelIRI
                else:
                    raise RuntimeError('Class label does not match ID in parent class specification: '
                            + tdata + '".')
            else:
                return labelIRI
        else:
            return tdIRI
    
    def _expandDefinition(self, deftext):
        """
        Modifies a text definition for an ontology term by adding OBO IDs for
        all term labels in braces ('{' and '}') in the definition.  For
        example, if the definition contains the text "A {whole plant} that...",
        it will be converted to "A whole plant (PO:0000003) that...".  It there
        is a dollar sign ('$') at the beginning of the label, then output of
        the label will be suppressed (i.e., only the OBO ID will be included in
        the expanded definition).
        """
        labelre = re.compile(r'(\{[$A-Za-z0-9\- _]+\})')
        defparts = labelre.split(deftext)

        newdef = ''
        for defpart in defparts:
            if labelre.match(defpart) != None:
                label = defpart.strip("{}")

                id_only = False
                if label[0] == '$':
                    label = label[1:]
                    id_only = True

                # Get the class IRI and OBO ID associated with this label.
                labelIRI = self.ontology.labelToIRI(label)
                labelID = termIRIToOboID(labelIRI)

                if not(id_only):
                    newdef += label + ' '

                newdef += '(' + labelID + ')'
            else:
                newdef += defpart

        if len(defparts) == 0:
            newdef = deftext

        return newdef

