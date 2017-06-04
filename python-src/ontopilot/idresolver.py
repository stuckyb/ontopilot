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
from __future__ import unicode_literals
from labelmap import LabelMap, InvalidLabelError, AmbiguousLabelError
from obohelper import isOboID, oboIDToIRI, getIRIForOboPrefix
from rfc3987 import rfc3987
import re

# Java imports.
from org.semanticweb.owlapi.model import IRI
from org.semanticweb.owlapi.model import OWLRuntimeException


# Compile a regular expression for recognizing and parsing entity labels with
# an OBO or IRI prefix.
prefix_label_re = re.compile(
    "(?P<prefix>[A-Za-z]+(_[A-Za-z]+)?):(?P<labeltxt>'.+')$"
)


class IDResolver:
    """
    Provides a high-level interface for ontology identifier resolution.  The
    various methods allow resolving prefix IRIs, relative IRIs, OBO IDs, and
    term labels (with and without prefixes) to full IRIs.
    """
    def __init__(self, ontology):
        """
        ontology: The Ontology instance to link with this IDResolver.
        """
        self.ontology = ontology
        ontman = self.ontology.getOntologyManager()
        owlont = self.ontology.getOWLOntology()
        self.prefix_df = ontman.getOntologyFormat(owlont).asPrefixOWLOntologyFormat()

        # Set up a LabelMap to track the source ontology.
        self.labelmap = LabelMap(self.ontology)

    def expandIRI(self, iri):
        """
        Expands an IRI string into a full IRI and returns a corresponding OWL
        API IRI object.  Also accepts OWL API IRI objects, in which case they
        are returned unaltered.  IRI strings can be either full IRIs, prefix
        IRIs (i.e. curies, such as "owl:Thing"), or relative IRIs (e.g.,
        "term_name").  If the IRI string is a prefix IRI or relative IRI, it
        will be expanded using the prefixes or base defined in the ontology.
        If the string is not a prefix IRI or relative IRI, then it is assumed
        to be a full IRI.

        iri: The IRI to expand.  Can be either a string or an OWL API IRI
            object.  In the latter case, iri is returned as is.
        """
        if isinstance(iri, basestring):
            # Verify that we have a valid IRI string.
            if rfc3987.match(iri, rule='IRI_reference') is None:
                raise RuntimeError('Invalid IRI string: "' + iri + '".')

            try:
                # If iri is not a prefix IRI, the OWL API will throw an
                # OWLRuntimeException.
                fullIRI = self.prefix_df.getIRI(iri)
            except OWLRuntimeException:
                fullIRI = IRI.create(iri)
        elif isinstance(iri, IRI):
            fullIRI = iri
        else:
            raise RuntimeError('Unsupported type for conversion to IRI.')

        return fullIRI

    def _isLabel(self, idstr):
        """
        Tests if a string is a label, either with or without an OBO/IRI prefix.
        """
        if len(idstr) < 3:
            return False

        if (idstr[0] == "'") and (idstr[-1] == "'"):
            return True

        res = prefix_label_re.match(idstr)
        if res is not None:
            return True
        else:
            return False

    def resolveLabel(self, labelstr):
        """
        Resolves a label (either with or without a prefix) to a full IRI.  The
        label text, but not the prefix, must be enclosed in single quotes
        (e.g., 'label txt' or prefix:'label txt').  If the label includes a
        prefix, label lookup will be attempted interpreting the prefix as both
        an OBO prefix and a standard IRI prefix.

        Returns: An OWL API IRI object.
        """
        if not(self._isLabel(labelstr)):
            raise RuntimeError(
                'The string "{0}" is not a valid ontology entity '
                'label.'.format(labelstr)
            )

        if (labelstr[0] == "'") and (labelstr[-1] == "'"):
            # If we have a non-prefixed label, do the lookup directly.
            return self.labelmap.lookupIRI(labelstr[1:-1])
        else:
            # If we have a prefixed label, we need to parse out the prefix and
            # the label text and resolve the prefix to an IRI root first.  The
            # prefix could be either an OBO prefix or a standard IRI prefix, so
            # we need to try to get both.
            res = prefix_label_re.match(labelstr)
            prefix = res.group('prefix')
            labeltxt = res.group('labeltxt')
            obo_root = getIRIForOboPrefix(res.group('prefix'))
            iri_root = self.prefix_df.getPrefix(prefix + ':')

            # Attempt to resolve the label using both prefixes (if we have
            # both).  If both lookups succeed, then the label is ambiguous and
            # cannot be resolved.
            obo_lookup = iri_lookup = None

            try:
                obo_lookup = self.labelmap.lookupIRI(labeltxt[1:-1], obo_root)
            except InvalidLabelError:
                obo_lookup = None

            if iri_root is not None:
                try:
                    iri_lookup = self.labelmap.lookupIRI(
                        labeltxt[1:-1], iri_root
                    )
                except InvalidLabelError:
                    iri_lookup = None

            if (obo_lookup is not None) and (iri_lookup is not None):
                if obo_lookup.equals(iri_lookup):
                    return obo_lookup
                else:
                    raise AmbiguousLabelError(
                        'Attempted to use an ambiguous label: The label "{0}" '
                        'resolved to more than one IRI in the source ontology '
                        'and its imports closure.  This was because the label '
                        'could be resolved with the label prefix, "{1}", '
                        'treated as either an OBO prefix or a standard IRI '
                        'prefix, and the resulting full IRIs were not the '
                        'same.'.format(labelstr, prefix)
                )
            elif obo_lookup is not None:
                return obo_lookup
            elif iri_lookup is not None:
                return iri_lookup
            else:
                raise InvalidLabelError(
                    'The provided label, "{0}", does not match any labels in '
                    'the source ontology or its imports '
                    'closure.'.format(labelstr)
                )

    def resolveIdentifier(self, id_obj):
        """
        Converts an object representing an identifier into a fully expanded
        IRI.  The argument id_obj can be either an OWL API IRI object or a
        string containing: a label (with or without a prefix), a prefix IRI
        (i.e., a curie, such as "owl:Thing"), a relative IRI, a full IRI, a
        label (either with or without an OBO or IRI prefix), or an OBO ID
        (e.g., a string of the form "PO:0000003").  Returns an OWL API IRI
        object.  Labels, except for their prefix, must be enclosed in single
        quotes (e.g., 'some label' or prefix:'some label').

        id_obj: The identifier to resolve to an absolute IRI.
        Returns: An OWL API IRI object.
        """
        if isinstance(id_obj, basestring):
            if self._isLabel(id_obj):
                IRIobj = self.resolveLabel(id_obj)
            elif isOboID(id_obj):
                IRIobj = oboIDToIRI(id_obj)
            else:
                IRIobj = self.expandIRI(id_obj)
        elif isinstance(id_obj, IRI):
            IRIobj = id_obj
        else:
            raise RuntimeError(
                'Unsupported type for conversion to IRI: {0}.'.format(
                    type(id_obj)
                )
            )

        return IRIobj

    def resolveNonlabelIdentifier(self, id_obj):
        """
        The functionality is the same as resolveIdentifier(), except that
        labels are explicitly disallowed and an exception will be thrown if a
        label is encountered.  This provides a useful restriction for cases
        where labels should not be valid identifiers, such as when defining new
        entities in an ontology (if an entity does not yet exist, it cannot
        have a label!).
        """
        if isinstance(id_obj, basestring):
            if self._isLabel(id_obj):
                raise RuntimeError(
                    'The identifier "{0}" appears to be an entity label, but '
                    'labels are not allowed in this context.'.format(id_obj)
                )

        return self.resolveIdentifier(id_obj)

