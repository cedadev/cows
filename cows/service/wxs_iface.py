# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
The classes in this module define the base interface between the OWS
Pylons server and components that provide Web X Server layers.  The
intention is that a WXS can be created for a given datatype and
rendering engine by creating classes that implement these base
interfaces and implement service specific interface modules
:mod:`cows.service.wms_iface`, :mod:`cows.service.wfs_iface` and
:mod:`cows.service.wcs_iface`.  There is no need to mess around with
Pylons controllers or the cows metadata model.

The main entry point for the OWS Pylons server is the ILayerMapper
interface.  This provides a mechanism for serving multiple WxS
endpoints through a single server.  Keywords deduced from the pylons
routes mapper are passed to the ILayerMapper instance to return a
dictionary of ILayer instances.  These are the layers available to the
WxS on this route.

It is expected that implementing classes will inherit from these
interface classes, using them as abstract base classes.  However, in
the future zope.Interface might be used to associate interfaces with
implementations.


"""

class ILayerMapper(object):
    """
    Maps keyword arguments to a collection of layers.

    ILayerMapper supports the retrieval of sets of layers according to arbitary
    keyword/value pairs.

    """
    def map(self, **kwargs):
        """
        Given arbitary keywords/value pairs list the names of
        all layers available.

        :return: A mapping of layer names to ILayer implementations.
        :raise ValueError: If no layers are available for these keywords.

        """
        raise NotImplementedError

class ILayer(object):
    """
    An base interface representing a WxS contents "layer" (e.g. coverage, layer, feature).

    :ivar title: The layer title.  As seen in the Capabilities document.
    :ivar abstract:  Abstract as seen in the Capabilities document.

    """
    title = abstract = NotImplemented
    featureInfoFormats = NotImplemented

    def getBBox(self, crs):
        """
        :return: the bounding box (llx, lly, urx, ury) of the data in the given
            coordinate reference system.

        """
        raise NotImplementedError

