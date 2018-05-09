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
Construct a ServiceMetadata instance with a simplified interface.

"""

import os
import ConfigParser
from cStringIO import StringIO

from cows.model import *

class ServiceMetadataBuilder(object):
    def __init__(self, serviceMetadata=None):
        if serviceMetadata is None:
            self.clear()
        else:
            self.serviceMetadata = serviceMetadata

    def clear(self):
        """
        Clear the serviceMetadata instance.

        """
        self.serviceMetadata = ServiceMetadata()

    def fromConfig(self, config):
        """
        Load ServiceIdentification and ServiceProvider information from a
        config file.

        """

        self.serviceMetadata.serviceIdentification =  self._siFromConfig(config)
        self.serviceMetadata.serviceProvider = self._spFromConfig(config)


    #-------------------------------------------------------------------------

    def _siFromConfig(self, config):

        siConfig = dict(config.items('serviceIdentification'))

        # serviceType and versions are typically populated from the framework
        # They are included here for completeness and because serviceType is
        # required in the data model
        type = siConfig.get('type', 'OWS')
        versions = siConfig.get('versions', '').split()
        
        profiles = siConfig.get('profiles', '').split()
        fees = siConfig.get('fees')
        accessConstraints = siConfig.get('accessConstraints')

        # Only one title & abstract supported
        title = siConfig.get('title')
        abstract = siConfig.get('abstract')

        keywords = siConfig.get('keywords', '').split()

        return ServiceIdentification(serviceType=type,
                                     serviceTypeVersions=versions,
                                     profiles=profiles,
                                     fees=fees,
                                     accessConstraints=accessConstraints,
                                     titles=[title],
                                     abstracts=[abstract],
                                     keywords=keywords)

    def _spFromConfig(self, config):
        spConfig = dict(config.items('serviceProvider'))

        provider = spConfig['provider']
        site = spConfig.get('site')

        # Contact info
        name = spConfig.get('contact.name')
        position = spConfig.get('contact.position')
        role = spConfig.get('contact.role')
        hos = spConfig.get('contact.hoursOfService')
        instr = spConfig.get('contact.instructions')

        # Look for all address fields of name contact.address<n>
        address = []
        for i in range(1, 8):
            k = 'contact.address%d' % i
            try:
                address.append(spConfig[k])
            except KeyError:
                break
        city = spConfig.get('contact.city')
        adminArea = spConfig.get('contact.administrativearea') #NOTE, this has changed from administrativeArea as configparser has an apparent problem with camelcase.
        postalCode = spConfig.get('contact.postalcode')
        country = spConfig.get('contact.country')
        email = spConfig.get('contact.email')
        phone = spConfig.get('contact.phone')
        fax = spConfig.get('contact.facsimile')
        onlineResource = spConfig.get('contact.onlineresource')

        a = Address(deliveryPoints=address, city=city,
                    administrativeArea=adminArea, postalCode=postalCode,
                    country=country, electronicMailAddress=email)
        t = Telephone(voice=phone, facsimile=fax)
        c = Contact(hoursOfService=hos,
                    contactInstructions=instr,
                    address=a,
                    phone=t,
                    onlineResource=onlineResource)
        rp = ResponsibleParty(individualName=name,
                              positionName=position,
                              role=role,
                              contactInfo=c)

        return ServiceProvider(providerName=provider,
                               serviceContact=rp,
                               providerSite=site)
    
    
#
# Simple functional interface
#

def loadConfigFile(filename):
    if not os.path.exists(filename):
        raise ValueError('Configuration %s does not exist' % filename)

    b = ServiceMetadataBuilder()

    config = ConfigParser.SafeConfigParser()
    config.read([filename])

    b.fromConfig(config)

    return b.serviceMetadata

def loadConfig(configString):
    b = ServiceMetadataBuilder()

    config = ConfigParser.SafeConfigParser()
    fp = StringIO(configString)
    config.readfp(fp)

    b.fromConfig(config)

    return b.serviceMetadata


#-------------------------------------------------------------------------------

def test_loadConfig():
    sm = loadConfig("""
[serviceIdentification]
type: WMS
versions: 1.1.1 1.3.0
fees: Loadsamoney
accessConstraints: byebye
title: The quick brown fox jumps
  over the lazy dog
abstract: None
keywords: foo bar baz
  spud

[serviceProvider]
provider: Superman
site: http://example.com
contact.name: Joe Blogs
contact.address1: foo
contact.address2: bar
contact.email: foo@bar.baz

""")

    from genshi.template import TemplateLoader
    from pkg_resources import resource_filename
    loader = TemplateLoader(
               [resource_filename('cows.pylons.templates', '')])
    t = loader.load('wms_capabilities_1_1_1.xml')

    # Mock objects
    class C:
        service_metadata = sm
    c = C()

    class H:
        def url(self): return 'http://example.com/'
    h=H()

    print t.generate(c=c, h=h).render()
