#
# Provides a single class, OWLOntologyBuilder, that implements methods for
# parsing descriptions of ontology classes (e.g., from CSV files) and
# converting them into classes in an OWL ontology.
#

# Python imports.
import re
from ontology import Ontology, termIRIToOboID, oboIDToIRI

# Java imports.


class OWLOntologyBuilder:
    """
    Builds an OWL ontology using Python dictionaries that describe new classes
    to add to an existing "base" ontology.  Typically, the new class
    descriptions will correspond with rows in an input CSV file.
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
        as the dictionary classdesc (i.e., the single explicit argument).  If
        expanddef is True, then term labels in the text definition for the new
        class will be expanded to include the terms' OBO IDs.
        """
        # Create the new class.
        newclass = self.ontology.createNewClass(oboIDToIRI(classdesc['ID']))
        
        # Make sure we have a label and add it to the new class.
        labeltext = classdesc['Label'].strip()
        if labeltext == '':
            raise RuntimeError('No label was provided for ' + classdesc['ID']
                    + '.')
        newclass.addLabel(labeltext)
        
        # Add the text definition to the class, if we have one.
        textdef = classdesc['Text definition'].strip()
        if textdef != '':
            if expanddef:
                textdef = self._expandDefinition(textdef)

            newclass.addDefinition(textdef)
        
        # Get the OWLClass object of the parent class, making sure that it is
        # actually defined.
        parentIRI = self._getParentIRIFromDesc(classdesc)
        newclass.addSuperclass(parentIRI)
    
        # Add the formal definition (specified as a class expression in
        # Manchester Syntax), if we have one.
        formaldef = classdesc['Formal definition'].strip()
        if formaldef != '':
            newclass.addClassExpression(formaldef)
 
    def _getParentIRIFromDesc(self, classdesc):
        """
        Parses a superclass (parent) IRI from a class description dictionary.
        The parent class information should have the key "Parent class".
        Either a class label, ID, or both can be provided.  The general format
        is: "'class label' (CLASS_ID)".  For example:
        "'whole plant' (PO:0000003)".  If both a label and ID are provided,
        this method will verify that they correspond.
        """
        tdata = classdesc['Parent class'].strip()
        if tdata == '':
            raise RuntimeError('No parent class was provided.')
    
        # Check if we have a class label.
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
                    tdIRI = oboIDToIRI(tdID)
                else:
                    raise RuntimeError('Missing closing parenthesis in parent class specification: '
                            + tdata + '".')
        else:
            # We only have an ID.
            labelIRI = None
            tdIRI = oboIDToIRI(tdata)
    
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

