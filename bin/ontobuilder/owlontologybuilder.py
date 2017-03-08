#
# Provides a single class, OWLOntologyBuilder, that implements methods for
# parsing descriptions of ontology classes (e.g., from CSV files) and
# converting them into classes in an OWL ontology.
#

# Python imports.
import re
from obohelper import termIRIToOboID, OBOIdentiferError
from ontology import Ontology
from ontology_entities import (
    CLASS_ENTITY, DATAPROPERTY_ENTITY, OBJECTPROPERTY_ENTITY,
    ANNOTATIONPROPERTY_ENTITY, INDIVIDUAL_ENTITY
)
from delimstr_parser import DelimStrParser
from tablereader import TableRowError

# Java imports.


class TermDescriptionError(TableRowError):
    """
    An exception class for errors encountered in term descriptions in rows from
    input files.
    """
    def __init__(self, error_msg, tablerow):
        self.tablerow = tablerow

        new_msg = (
            'Error encountered in term description in '
            + self._generateContextStr(tablerow) + ':\n' + error_msg
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

        # Get a PrefixDocumentFormat/PrefixManager instance so that we can
        # generate prefix IRIs for label expansions in text entity definitions.
        owlont = self.ontology.getOWLOntology()
        ontman = self.ontology.getOntologyManager()
        self.prefix_df = ontman.getOntologyFormat(owlont).asPrefixOWLOntologyFormat()

        # A list (used as a stack) for caching information in _TableRow objects
        # and their associated ontology entity objects.  Each list entry is
        # stored as a tuple, (ontology entity instance, _TableRow instance).
        self.entity_trows = []

        # Create a delimited string parser for parsing multiple values out of
        # input fields.
        self.dsparser = DelimStrParser(delimchars=';', quotechars='"\'')

        # Create a delimited string parser for parsing the components of
        # strings with whitespace-separated components, such as individual
        # property assertions (facts).
        self.ws_dsparser = DelimStrParser(delimchars=' \t', quotechars='"\'')

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

        # Add any additional annotations.
        annottexts = self.dsparser.parseString(entdesc['Annotations'])
        for annottext in annottexts:
            annotparts = self.ws_dsparser.parseString(annottext)
            if len(annotparts) != 2:
                raise TermDescriptionError(
                    'The annotation specification is invalid: {0}.  It must '
                    'be of the form annotation_property_ID "Annotation '
                    'text."'.format(annottext),
                    entdesc
                )

            entobj.addAnnotation(
                annotparts[0], self.dsparser.unquoteStr(annotparts[1])
            )

    def _addClassAxioms(self, classobj, classdesc, expanddef=True):
        """
        Adds axioms from a _TableRow class description to an existing class
        object.  If expanddef is True, then term labels in the text definition
        for the new class will be expanded to include the terms' OBO IDs.
        """
        self._addGenericAxioms(classobj, classdesc, expanddef)

        # Add parent classes (i.e., subclass of axioms) specified in the
        # 'Parent' and 'Subclass of' fields.  Parent classes are specified as
        # class expressions in Manchester Syntax.
        ms_exps = (
            self.dsparser.parseString(classdesc['Parent'])
            + self.dsparser.parseString(classdesc['Subclass of'])
        )
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
        explicit argument).
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
            parentIRI = self.ontology.resolveIdentifier(parentID)
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
            disjIRI = self.ontology.resolveIdentifier(propID)
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
        explicit argument).
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
            parentIRI = self.ontology.resolveIdentifier(parentID)
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
            inverseIRI = self.ontology.resolveIdentifier(propID)
            if inverseIRI != None:
                propobj.addInverse(inverseIRI)

        # Add any disjointness axioms.
        propIDs = self.dsparser.parseString(propdesc['Disjoint with'])
        for propID in propIDs:
            disjIRI = self.ontology.resolveIdentifier(propID)
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
        explicit argument).
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
            parentIRI = self.ontology.resolveIdentifier(parentID)
            if parentIRI != None:
                propobj.addSuperproperty(parentIRI)

    def addIndividual(self, indvdesc):
        """
        Adds a new named individual to the ontology, based on a description
        provided as the table row indvdesc (i.e., the single explicit
        argument).
        """
        try:
            # Create the new named individual
            newindv = self.ontology.createNewIndividual(indvdesc['ID'])
            
            # If we have a label, add it to the individual.
            labeltext = indvdesc['Label']
            if labeltext != '':
                newindv.addLabel(labeltext)
        except RuntimeError as err:
            raise TermDescriptionError(str(err), indvdesc)
        
        # Cache the remainder of the individual description.
        self.entity_trows.append((newindv, indvdesc))

    def _addIndividualAxioms(self, indvobj, indvdesc, expanddef=True):
        """
        Adds axioms from a _TableRow object property description to an existing
        named individual object.  If expanddef is True, then term labels in the
        text definition for the individual will be expanded to include the
        terms' OBO IDs.
        """
        self._addGenericAxioms(indvobj, indvdesc, expanddef)

        # Add all types for the individual.
        for classexp in self.dsparser.parseString(indvdesc['Instance of']):
            indvobj.addType(classexp)

        # Add all object property assertions (object property facts).
        for opfact in self.dsparser.parseString(indvdesc['Relations']):
            fact_parts = self.ws_dsparser.parseString(opfact)
            self._checkFactSyntax(fact_parts, opfact, indvdesc)
            if fact_parts[0].lower() == 'not':
                indvobj.addObjectPropertyFact(
                    fact_parts[1], fact_parts[2], is_negative=True
                )
            else:
                indvobj.addObjectPropertyFact(
                    fact_parts[0], fact_parts[1], is_negative=False
                )

        # Add all data property assertions (data property facts).
        for dpfact in self.dsparser.parseString(indvdesc['Data facts']):
            fact_parts = self.ws_dsparser.parseString(dpfact)
            self._checkFactSyntax(fact_parts, dpfact, indvdesc)
            if fact_parts[0].lower() == 'not':
                indvobj.addDataPropertyFact(
                    fact_parts[1], fact_parts[2], is_negative=True
                )
            else:
                indvobj.addDataPropertyFact(
                    fact_parts[0], fact_parts[1], is_negative=False
                )

    def _checkFactSyntax(self, fact_parts, factstr, desc):
        """
        Performs some simple syntax checking of a parsed individual fact
        statement.  Does not attempt to validate any identifiers in the
        statement.
        """
        if len(fact_parts) not in (2, 3):
            raise TermDescriptionError(
                'The individual object/data property assertion (fact) is '
                'invalid: {0}'.format(factstr),
                desc
            )

        if len(fact_parts) == 3:
            if fact_parts[0].lower() != 'not':
                raise TermDescriptionError(
                    'The individual object/data property assertion (fact) is '
                    'invalid: "not" was expected, but "{0}" was '
                    'encountered.'.format(fact_parts[0]),
                    desc
                )

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
                elif typeconst == INDIVIDUAL_ENTITY:
                    self._addIndividualAxioms(entity, desc, expanddefs)
                else:
                    raise RuntimeError('Unsupported ontology entity type: '
                            + str(typeconst) + '.')
            except RuntimeError as err:
                raise TermDescriptionError(str(err), desc)

            # Putting the pop() operation at the end of the loop ensures that a
            # description is only removed from the list/stack if it was
            # processed without an exception being thrown.
            self.entity_trows.pop()
    
    def _expandDefinition(self, deftext):
        """
        Modifies a text definition for an ontology term by adding OBO IDs for
        all term labels in braces ('{' and '}') in the definition.  For
        example, if the definition contains the text "A {whole plant} that...",
        it will be converted to "A 'whole plant' (PO:0000003) that...".  If
        there is a dollar sign ('$') at the beginning of the label, then output
        of the label will be suppressed (i.e., only the OBO ID will be included
        in the expanded definition).  Labels inside curly braces can be written
        with or without enclosing single quotes, and with or without a prefix.
        If labels are missing one or both quotes, _exandDefinition() will
        attempt to fix them.

        deftext (str): The text definition to process.
        """
        # Define a regular expression for recognizing labels in curly braces
        # for the purpose of parsing them out of a larger containing string.
        # Note that this regular expression cannot include label component
        # subgroups in parentheses; if it did, they would be included in the
        # elements of the split string list.  Note also that in this regular
        # expression, the '?' after the '+' qualifier specifies a non-greedy
        # match; this is required for definitions that contain multiple label
        # elements.
        label_split_re = re.compile(r'(\{.+?\})')

        # Define a regular expression for parsing labels with or without a
        # prefix, with or without enclosing single quotes.  Used named groups
        # to reference the parts of the regular expression match that we need
        # to work with.
        labelre = re.compile(
            r"\{(?P<idonly>\$)?(?P<prefix>[A-Za-z]+(_[A-Za-z]+)?:)?(?P<labeltxt>.+)\}$"
        )
        defparts = label_split_re.split(deftext)

        newdef = ''
        for defpart in defparts:
            res = labelre.match(defpart)
            if res != None:
                id_only = res.group('idonly') != None

                # Handle cases where the label text is not wrapped in single
                # quotes.  IDResolver expects label strings to be quoted, so
                # quotes must be added if they are missing.  To do this, we
                # parse out the label components (prefix, if present, and
                # actual label text) and then reassemble the label, making sure
                # the label text is enclosed in single quotes.
                if res.group('prefix') != None:
                    label = res.group('prefix')
                else:
                    label = ''

                # Add the label text to the reassembled label string,
                # attempting to correct any missing single quotes.
                labeltxt = res.group('labeltxt')
                if labeltxt[0] != "'":
                    label += "'"
                label += labeltxt
                if labeltxt[-1] != "'":
                    label += "'"

                # Get the class IRI and OBO ID associated with this label.  If
                # the OBO ID conversion fails, try to convert it to a prefix
                # IRI, and if that fails, just use the full IRI.
                labelIRI = self.ontology.resolveLabel(label)
                try:
                    labelID = termIRIToOboID(labelIRI)
                except OBOIdentiferError:
                    labelID = ''

                if labelID == '':
                    labelID = self.prefix_df.getPrefixIRI(labelIRI)

                if labelID == None:
                    labelID = str(labelIRI)

                if not(id_only):
                    newdef += label + ' '

                newdef += '(' + labelID + ')'
            else:
                newdef += defpart

        if len(defparts) == 0:
            newdef = deftext

        return newdef

