#!/usr/bin/env python

try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension


setup(
    name='akane',
    version='0.1.0',
    description='An asynchronous Redis client for Tornado.',
    long_description=open('README.rst').read(),
    author='Frank Smit',
    author_email='frank@61924.nl',
    packages=['akane'],
    license='MIT',
    install_requires=[
        'tornado',
        'hiredis'
    ],
    ext_modules=[Extension('akane.utils', [
        'akane/utils.c',
        'akane/buffer.c'
    ])],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: C',
        'Programming Language :: Python :: 2.7',
        'Topic :: Database',
        'Topic :: Database :: Front-Ends'
    ]
)
