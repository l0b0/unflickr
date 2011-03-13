#!/usr/bin/env python
"""
Setup configuration
"""

from setuptools import setup
from unflickr import unflickr as package

setup(
    name=package.__name__,
    version=package.__version__,
    description='Download your Flickr metadata and media',
    long_description=package.__doc__,
    url=package.__url__,
    keywords='Flickr backup download metadata photo video',
    packages=[package.__package__],
    install_requires=['flickrapi'],
    entry_points={
        'console_scripts': [
            '%(package)s = %(package)s.%(package)s:main' % {
                'package': package.__name__}]},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Topic :: Multimedia :: Graphics',
        'Topic :: System :: Archiving :: Backup',
    ],
    test_suite='tests.tests',
    author=package.__author__,
    author_email=package.__email__,
    maintainer=package.__maintainer__,
    maintainer_email=package.__email__,
    download_url='http://pypi.python.org/pypi/unflickr/',
    platforms=['POSIX', 'Windows'],
    license=package.__license__,
    )
