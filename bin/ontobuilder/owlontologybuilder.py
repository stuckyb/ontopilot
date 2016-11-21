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

# Java imports.


class OWLOntologyBuilder:
    """
    Builds an OWL ontology using _TableRow objects that describe new entities
    to add to an existing "base" ontology.  Typically, the new entity
    descriptions will correspond with rows in an input CSV file or other
    tabular file format.
    """
    def __init__(self, base_ont_path):
        # Load the base ontology.
        self.ontology = Ontology(base_ont_path)

    def getOntology(self):
        """
        Returns the Ontology object contained by this OWLOntologyBuilder.
        """
        return self.ontology

    def addClass(self, classdesc, expanddef=True):
        """
        Adds a new class to the ontology, based on a class description provided
        as the table row classdesc (i.e., the single explicit argument).  If
        expanddef is True, then term labels in the text definition for the new
        class will be expanded to include the terms' OBO IDs.
        """
        # Create the new class.
        newclass = self.ontology.createNewClass(
            oboIDToIRI(classdesc['ID'])
        )
        
        # Make sure we have a label and add it to the new class.
        labeltext = classdesc['Label']
        if labeltext != '':
            newclass.addLabel(labeltext)

        # Add the text definition to the class, if we have one.
        textdef = classdesc['Text definition']
        if textdef != '':
            if expanddef:
                textdef = self._expandDefinition(textdef)

            newclass.addDefinition(textdef)

        # Add any comments for the class.
        commenttext = classdesc['Comments']
        if commenttext != '':
            newclass.addComment(commenttext)

        # Get the IRI object of the parent class and add it as a parent.
        parentIRI = self._getIRIFromDesc(
            classdesc['Parent']
        )
        if parentIRI != None:
            newclass.addSuperclass(parentIRI)
    
        # Add any subclass of axioms (specified as class expressions in
        # Manchester Syntax).
        ms_exp = classdesc['Subclass of']
        if ms_exp != '':
            newclass.addClassExpression(ms_exp, False)
 
        # Add any equivalency axioms (specified as class expressions in
        # Manchester Syntax).
        ms_exp = classdesc['Equivalent to']
        if ms_exp != '':
            newclass.addClassExpression(ms_exp, True)
 
    def addDataProperty(self, propdesc, expanddef=True):
        """
        Adds a new data property to the ontology, based on a property
        description provided as the table row propdesc (i.e., the single
        explicit argument).  If expanddef is True, then term labels in the text
        definition for the new property will be expanded to include the terms'
        OBO IDs.
        """
        # Create the new data property.
        newprop = self.ontology.createNewDataProperty(
            oboIDToIRI(propdesc['ID'])
        )
        
        # Make sure we have a label and add it to the new class.
        labeltext = propdesc['Label']
        if labeltext != '':
            newprop.addLabel(labeltext)
        
        # Add the text definition to the class, if we have one.
        textdef = propdesc['Text definition']
        if textdef != '':
            if expanddef:
                textdef = self._expandDefinition(textdef)

            newprop.addDefinition(textdef)
        
        # Add any comments for the property.
        commenttext = propdesc['Comments']
        if commenttext != '':
            newprop.addComment(commenttext)

        # Get the IRI object of the parent property and add it as a parent.
        parentIRI = self._getIRIFromDesc(
            propdesc['Parent']
        )
        if parentIRI != None:
            newprop.addSuperproperty(parentIRI)

        # Add the domain, if we have one.
        domainIRI = self._getIRIFromDesc(
            propdesc['Domain']
        )
        if domainIRI != None:
            newprop.setDomain(domainIRI)

        # Add the range, if we have one.
        range_exp = propdesc['Range']
        if range_exp != '':
            newprop.setRange(range_exp)

        # Add the disjoint with axiom, if we have a disjoint property.
        disjIRI = self._getIRIFromDesc(
            propdesc['Disjoint with']
        )
        if disjIRI != None:
            newprop.setDisjointWith(disjIRI)

        # Add the characteristics, if provided.  The only supported
        # characteristic for data properties is "functional".
        chars_str = propdesc['Characteristics']
        if chars_str != '':
            if chars_str.lower() == 'functional':
                newprop.makeFunctional()
            else:
                raise RuntimeError(
                    'Unrecognized characteristic(s) for a data property: "'
                    + chars_str + 
                    '".  For data properties, "functional" is the only supported characteristic.'
                )

    def addObjectProperty(self, propdesc, expanddef=True):
        """
        Adds a new object property to the ontology, based on a property
        description provided as the table row propdesc (i.e., the single
        explicit argument).  If expanddef is True, then term labels in the text
        definition for the new property will be expanded to include the terms'
        OBO IDs.
        """
        # Create the new object property.
        newprop = self.ontology.createNewObjectProperty(
            oboIDToIRI(propdesc['ID'])
        )
        
        # Make sure we have a label and add it to the new class.
        labeltext = propdesc['Label']
        if labeltext != '':
            newprop.addLabel(labeltext)
        
        # Add the text definition to the class, if we have one.
        textdef = propdesc['Text definition']
        if textdef != '':
            if expanddef:
                textdef = self._expandDefinition(textdef)

            newprop.addDefinition(textdef)
        
        # Add any comments for the property.
        commenttext = propdesc['Comments']
        if commenttext != '':
            newprop.addComment(commenttext)

        # Get the IRI object of the parent property and add it as a parent.
        parentIRI = self._getIRIFromDesc(
            propdesc['Parent']
        )
        if parentIRI != None:
            newprop.addSuperproperty(parentIRI)

        # Add the domain, if we have one.
        domainIRI = self._getIRIFromDesc(
            propdesc['Domain']
        )
        if domainIRI != None:
            newprop.setDomain(domainIRI)

        # Add the range, if we have one.
        rangeIRI = self._getIRIFromDesc(
            propdesc['Range']
        )
        if rangeIRI != None:
            newprop.setRange(rangeIRI)

        # Add the inverse axiom, if we have an inverse property.
        inverseIRI = self._getIRIFromDesc(
            propdesc['Inverse']
        )
        if inverseIRI != None:
            newprop.setInverse(inverseIRI)

        # Add the disjoint with axiom, if we have a disjoint property.
        disjIRI = self._getIRIFromDesc(
            propdesc['Disjoint with']
        )
        if disjIRI != None:
            newprop.setDisjointWith(disjIRI)

        # Add the characteristics, if provided.  The only supported
        # characteristic for data properties is "functional".
        chars_str = propdesc['Characteristics']
        if chars_str != '':
            self._processObjPropCharacteristics(newprop, chars_str)

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
        it will be converted to "A whole plant (PO:0000003) that...".
        """
        labelre = re.compile(r'(\{[A-Za-z _]+\})')
        defparts = labelre.split(deftext)

        newdef = ''
        for defpart in defparts:
            if labelre.match(defpart) != None:
                label = defpart.strip("{}")

                # Get the class IRI associated with this label.
                labelIRI = self.ontology.labelToIRI(label)

                labelID = termIRIToOboID(labelIRI)
                newdef += label + ' (' + labelID + ')'
            else:
                newdef += defpart

        if len(defparts) == 0:
            newdef = deftext

        return newdef

