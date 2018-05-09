# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Classes modelling OWS Common 1.1.0.  These have been constructed from the
UML using the following principles.

Lightweight classes
===================

Some classes are slight extensions of types provided by python, such
as :class:`cows.model.is19115_subset.LanguageString` that has a lang
attribute but is otherwise just a string.

In these cases a new-style class is provided with a ``__slots__``
attribute to restrict it's size.  Such classes can often be substitued
with a builtin python type as documented in the class.

Attribute sequences
===================

When the OWS UML or schema declares a sequence of objects it may be
modelled as a single attribute by pluralising the attribute name.
E.g. :meth:`cows.model.data_identification.Identification.outputFormats`.
In such cases a python sequence or iterable of the specified object is
desired.  Note: :meth:`ows.data_identification.Identification.metadata`
is pleural :-).

In some cases it is more natural to use dictionaries than sequences of
objects with name attributes.  In this case an attribute will be
appended with the word "Dict",
e.g. :meth:`cows.model.operations_metadata.OperationMetadata.operationDict`.

The abstract model classes are all imported here.  For
service-specific classes import cows.model.w*s

"""

from capabilities import *
from common import *
from contents import *
from data_identification import *
from domain import *
from exception_report import *
from iso19115_subset import *
from operations_metadata import *
from service_identification import *
from service_provider import *
