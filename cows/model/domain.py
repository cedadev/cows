# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

# Copyright (C) 2007 STFC & NERC (Science and Technology Facilities Council).
# This software may be distributed under the terms of the
# Q Public License, version 1.0 or later.
# http://ndg.nerc.ac.uk/public_docs/QPublic_license.txt
"""
Classes modelling the OWS Domain package v1.1.0.

:author: Stephen Pascoe
"""

class Domain(object):
    """
    :note: It seems unnecessary to model Domain and UnNamedDomain seperately.
        This class models both.

    :ivar defaultValue:
    :type defaultValue: None or str
    :ivar metadata:
    :type metadata: iterable of Metadata
    :ivar meaning:
    :type meaning: None, DomainMetadata or str
    :ivar dataType:
    :type dataType: None, DomainMetadata or str
    :ivar valuesUnit: The units of measure or reverence System.  This is a
        simplification of the schema that defines valuesUnit to be a union
        of either referenceSystems or UOM.  It's not clear how this should
        be implemented yet.
    :type valuesUnit: None or DomainMetadata
    :ivar possibleValues:
    :type possibleValues: PossibleValues

    """
    def __init__(self,  defaultValue=None, possibleValues=None, metadata=[],
                 meaning=None, dataType=None, valuesUnit=None):
        if possibleValues is None:
            possibleValues = PossibleValues.fromAnyValue()
        self.possibleValues = possibleValues
        self.defaultValue = defaultValue
        self.metadata = metadata
        self.meaning = meaning
        self.dataType = dataType
        self.valuesUnit = valuesUnit

    def isValidValue(self, value):
        return self.possibleValues.isValidValue(value)

class PossibleValues(object):
    """
    :note: All members of the OWS PossibleValues Union are modelled in this
        class.

    :cvar ANY_VALUE: Flag selecting anyValue union attribute.
    :cvar NO_VALUES: Flag selecting noValues union attribute.
    :cvar ALLOWED_VALUES: Flag selecting AllowedValues union attribute.
    :cvar VALUES_REFERENCE: Flag selecting valuesListReference union attribute
    :ivar type: set to one of the above flags to select union attribute.

    :ivar allowedValues: A collection of either values or ranges
    :type allowedValues: Iterable of str or Range objects
    :ivar valuesRefName :
    :type valuesRefName: None or str
    :ivar valuesRefURI:
    :type valuesRefURI: None or str

    :todo: Range checking
    :todo: Converting into numeric types
    
    """
    ANY_VALUE = 1
    NO_VALUES = 2
    ALLOWED_VALUES = 3
    VALUES_REFERENCE = 4
    
    def __init__(self, type, allowedValues=[], valuesRefName=None,
                 valuesRefURI=None):
        self.type = type
        self.allowedValues = allowedValues
        self.valuesRefName = valuesRefName
        self.valuesRefURI = valuesRefURI

    # The union is implemented by providing a class method for each member.
    @classmethod
    def fromAnyValue(klass):
        k = klass(klass.ANY_VALUE)
        return k

    @classmethod
    def fromNoValues(klass):
        k = klass(klass.NO_VALUES)
        return k

    @classmethod
    def fromAllowedValues(klass, valueOrRanges):
        k = klass(klass.ALLOWED_VALUES, allowedValues=valueOrRanges)
        return k

    @classmethod
    def fromValuesReference(klass, name, uri):
        k = klass(klass.VALUES_REFERENCE, valuesRefName=name, valuesRefURI=uri)
        return k

    def isValidValue(self, value):
        """
        Check that value is valid within domain.

        """
        if self.type == self.ANY_VALUE:
            return True

        if self.type == self.NO_VALUES:
            return not value

        if self.type == self.ALLOWED_VALUES:
            for vr in self.allowedValues:
                if isinstance(vr, Range) and vr.isInRange(value):
                    return True
                if value == vr:
                    return True
            return False
                
        if self.type == self.VALUES_REFERENCE:
            raise NotImplementedError
        

class Range(object):
    """
    :ivar minimumValue:
    :type minimumValue: None or str
    :ivar maximumValue:
    :type maximumValue: None or str
    :ivar spacing:
    :type spacing: None or str
    :ivar rangeClosure:
    :type rangeClosure: One of Range._rangeClosureValues

    """
    _rangeClosureValues = [None, 'open', 'closed', 'open-closed',
                           'closed-open']
    
    def __init__(self, minumumValue=None, maximumValue=None, spacing=None,
                 rangeClosure=None):
        if rangeClosure not in Range._rangeClosureValues:
            raise ValueError, 'Incorrect rangeClosure value'

        self.minimumValue = minimumValue
        self.maximumValue = maximumValue
        self.spacing = spacing
        self.rangeClosure = rangeClosure

    def isInRange(self, value):
        raise NotImplementedError

class DomainMetadata(str):
    """
    If you wish to attach a URI to DomainMetadata use this class, otherwise
    you can substitute it with str.
    
    :ivar reference: A URI
    :type reference: None or str

    """

    def __init__(self, name, reference=None):
        super(DomainMetadata, self).__init__(name)
        self.reference = reference
