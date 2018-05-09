# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from setuptools import setup, find_packages

setup(
    name='cows',
    version='2.0.0',
    
    description='CEDA OGC Web Services Framework (COWS).  A framework for creatining integrated OGC web services using Pylons',
    author='Stephen Pascoe',
    author_email='S.Pascoe@rl.ac.uk',
    url='http://proj.badc.rl.ac.uk/ndg/wiki/OwsFramework',

    # We only list dependencies that we are confident will easy_install without
    # a hitch here.
    install_requires=['Pylons>=1.0', 'genshi>=0.6', 'numpy>=1.3.0', 'cdat_lite>=5.2', 'csml>=2.7',
                      'pycairo>=1.2', 'Shapely>=1.2.5', 'PIL>=1.1.7', 
                      'matplotlib>=1.0.0', 'basemap>=1.0.0',
                      'mock>=0.6', 'owslib>=0.3.1', 'geoplot>=0.4.0', 'image_utils>=1.0'],
    find_links=['http://ndg.nerc.ac.uk/dist'],

    classifiers=[
    'Development Status :: 4 - Beta',
    'Environment :: Web Environment',
    'Framework :: Pylons',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Operating System :: POSIX :: Linux',
    'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    'Topic :: Scientific/Engineering :: Atmospheric Science',
    'Topic :: Scientific/Engineering :: Visualization',
    ],

    packages=find_packages(exclude=['cows.test', 'cows.test.*']),
    include_package_data=True,
    exclude_package_data={'cows': ['test/*']},

    entry_points = """
        [paste.app_factory]
        testapp = cows.test.testapp.wsgiapp:make_app

        [paste.app_install]
        testapp = pylons.util:PylonsInstaller

        [paste.paster_create_template]
        cows_server=cows.pylons.project_templates:CowsServer

    """,
    test_suite='nose.collector',
    )
