#!/bin/bash

set -o errexit -o nounset

# Go to script directory
cd -- "$(dirname -- "$(readlink -fn -- "$0")")"

# Test
python setup.py test

# Build & upload to PyPI
python setup.py ${1:-} bdist_egg bdist_rpm sdist upload

# Cleanup
python setup.py clean
rm -fr *.pyc build dist *.egg-info

# Add release tag
git tag -a -m 'PyPI release' "$(PYTHONPATH=. python -c 'from offlickr-py.offlickr-py import __version__; print __version__')"
