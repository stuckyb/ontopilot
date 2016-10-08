#
# Provides a single class, OWLOntologyBuilder, that implements methods for
# parsing descriptions of ontology classes (e.g., from CSV files) and
# converting them into classes in an OWL ontology.
#

# Python imports.
import re
from obohelper import termIRIToOboID, oboIDToIRI
from ontology import Ontology

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
        
        # Get the IRI object of the parent class and add it as a parent.
        parentIRI = self._getIRIFromDesc(classdesc['Parent'])
        if parentIRI != None:
            newclass.addSuperclass(parentIRI)
    
        # Add the formal definition (specified as a class expression in
        # Manchester Syntax), if we have one.
        formaldef = classdesc['Formal definition'].strip()
        if formaldef != '':
            newclass.addClassExpression(formaldef)
 
    def addDataProperty(self, propdesc, expanddef=True):
        """
        Adds a new data property to the ontology, based on a property
        description provided as the dictionary propdesc (i.e., the single
        explicit argument).  If expanddef is True, then term labels in the text
        definition for the new property will be expanded to include the terms'
        OBO IDs.
        """
        # Create the new data property.
        newprop = self.ontology.createNewDataProperty(oboIDToIRI(propdesc['ID']))
        
        # Make sure we have a label and add it to the new class.
        labeltext = propdesc['Label'].strip()
        if labeltext == '':
            raise RuntimeError('No label was provided for ' + propdesc['ID']
                    + '.')
        newprop.addLabel(labeltext)
        
        # Add the text definition to the class, if we have one.
        textdef = propdesc['Text definition'].strip()
        if textdef != '':
            if expanddef:
                textdef = self._expandDefinition(textdef)

            newprop.addDefinition(textdef)
        
        # Get the IRI object of the parent property and add it as a parent.
        parentIRI = self._getIRIFromDesc(propdesc['Parent'])
        if parentIRI != None:
            newprop.addSuperproperty(parentIRI)

        # Add the domain, if we have one.
        domainIRI = self._getIRIFromDesc(propdesc['Domain'])
        if domainIRI != None:
            newprop.setDomain(domainIRI)
 
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

