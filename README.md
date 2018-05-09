# COWS: CEDA OGC Web Services framework

COWS is a set of tools for building OGC Web Services using the Pylons web application framework.  
It's key features are:

 - A data model compatible with OGC Common 1.1.0
 - OWS operation dispatch.  Version negotiation, argument parsing and exception serialisation.
 - Specific OGC Service implementations with plugable data handlers.  Currently WMS is by far the most mature with support for WCS and WPS in development but not yet in the COWS package.

COWS is alpha-quality software and the API is in flux.  Some parts provide quite high-level 
control of services whereas others are little more than a little helping hand.  For instance 
the mechanism for creating creating Capabilities documents involves overriding 2 different methods 
A better way is likely to emerge before a beta release.

Although some parts of theAs it develops COWS is beginning to become more like a framework in it's own right.  

## Overview 

 1. COWS stack
 2. COWS OWS-common data model
 3. COWS and Pylons
 4. WMS interface classes
 
## COWS stack 

COWS is intended to be used with the Pylons web application framework, but it isn't a Pylons 
application in itself.  Instead you create a Pylons application that imports COWS.  You could 
think of the structure of a COWS application as follows.

```
|| Application      ||
|| COWS   Framework ||
|| Pylons Framework ||
|| Python           ||
```

## COWS OWS-common data model

The Data model described in OGC-Common 1.1.0 is a complex beast, reflecting the goal of unifying OGC service standards
that have evolved independently.  COWS reflects the OGC Common data model in the  {{{cows.model}}} package.  This package 
contains classes that shadow the main OGC common UML classes.  COWS also provides Genshi templates for serialising the 
OGC-Common data model into a Capabilities document.  

In principle all OGC services should expose their Capabilities using the OGC-Common model.  However, most OWS standards require 
extensions to OWS-Common and support for well established legacy versions (e.g. WMS-1.1) require a substantially different 
Capabilities XML schema.  Therefore service-specific Genshi templates are provided that take the OGC-Common model as input
where possible.

## COWS and Pylons 

COWS aims to give application developers the full flexibility of Pylons when building OWS services.

### Multiple service endpoints via Routes
 
Different elements of a URL are translated into controller arguments using the Routes module.  This allows you to create 
multiple services e.g. 
 
 - http://www.example.com/dataset1/wms 
 - http://www.example.com/dataset2/wms
 - http://www.example.com/dataset1/wcs
  
could all be served from the same codebase.  
  
  
## COWS Quick Start guide

The core of COWS is the cows.pylons.ows_controller.OwsController class.  If you want to implement a completely new service you would start from here.

 1. Create a pylons application {{{$ paster create -t pylons }}}.  You will be prompted for a project name.
 2. Add COWS as a dependency.  Not essential but good practice.

 ```
 #!python
 def setup(# ...
           install_requires=['Pylons>=1.0', 'COWS'],
           dependency_links=['http://ndg.nerc.ac.uk/dist'],
           # ...
           )
 ``` 
 3. Create a controller for your service {{{$ paster controller wxs }}}
 4. Edit controllers/wxs.py to inherit from {{{cows.pylons.ows_controller.OwsController}}}
  
           
 
 
