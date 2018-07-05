# -*- coding: utf-8 -*-
#
# Python jsonparser setup script
#
# Copyright (C) 2018 Sathya Kuppuswamy
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# @Author  : Sathya Kupppuswamy(sathyaosid@gmail.com)
# @History :
#            @v0.0 - Initial update
# @TODO    :
#
#

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(name='jsonparser',
      version='0.1',
      description='Jsonparser with ref resolver, include external json files, and environment variable'
                  'susbstutition support.',
      long_description=readme,
      classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 2.7',
        'Topic :: Text Processing :: Linguistic',
      ],
      keywords='python json jsonschme jsonparser',
      url='https://github.com/knsathya/jsonparser.git',
      author='Kuppuswamy Sathyanarayanan',
      author_email='sathyaosid@gmail.com',
      license='GPLv2',
      packages=['jsonparser'],
      install_requires=[
          'jsonschema',
          'jsonmerge'
      ],
      test_suite='tests',
      tests_require=[
          ''
      ],
      entry_points={
          'console_scripts': [''],
      },
      include_package_data=True,
      zip_safe=False)