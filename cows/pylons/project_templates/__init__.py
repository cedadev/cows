# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from paste.script.templates import BasicPackage, var

class CowsServer(BasicPackage):
    _template_dir = 'cows_server'
    summary = "A Pylons template to create CSML-enabled COWS server"
    egg_plugins = ['PasteScript', 'Pylons']
    vars = [
        var('csmlstore', 'The path to your CSML files',
            default='%(here)s/csml'),
        ]
    
