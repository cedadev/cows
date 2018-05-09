# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from setuptools import setup, find_packages
from cows import __version__

setup(
    name='cows',
    version=__version__,
    
    description='CEDA OGC Web Services Framework (COWS).  A framework for creatining integrated OGC web services using Pylons',
    author='Ag Stephens',
    author_email='ag.stephens@stfc.ac.uk',
    url='https://github.com/cedadev/cows',

    # We only list dependencies that we are confident will easy_install without
    # a hitch here.
    install_requires=['Pylons>=1.0', 'genshi>=0.6', 'mock>=0.6', 'owslib>=0.3.1'],

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
