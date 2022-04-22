# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name = 'prog_server',
    version = '1.0.0', #pkg_resources.require("prog_models")[0].version,
    description = 'The NASA Prognostics As-A-Service (PaaS) Sandbox (a.k.a. prog_server) is a simplified Software Oriented Architecture (SOA) for performing prognostics of engineering systems. The PaaS Sandbox is a wrapper around the Prognostics Algorithms and Models Packages, allowing 1+ users to access these packages features through a REST API. The package is intended to be used as a research tool to prototype and benchmark Prognostics As-A-Service (PaaS) architectures and work on the challenges facing such architectures',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url = 'https://github.com/nasa/prog_server',
    author = 'Christopher Teubert',
    author_email = 'christopher.a.teubert@nasa.gov',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Intended Audience :: Manufacturing', 
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Physics',
        'License :: Other/Proprietary License ',   
        'Programming Language :: Python :: 3',     
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3 :: Only'
    ],
    keywords = ['prognostics', 'diagnostics', 'fault detection', 'fdir', 'physics modeling', 'prognostics and health management', 'PHM', 'health management', 'prognostics as a service'],
    package_dir = {"":"src"},
    packages = find_packages(where = 'src'),
    python_requires='>=3.7, <3.11',
    install_requires = [
        'prog_algs',
        'requests',
        'urllib3',
        'flask'
    ],
    license = 'NOSA',
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/nasa/prog_server/issues',
        'Organization': 'https://prognostics.nasa.gov/',
        'Source': 'https://github.com/nasa/prog_server',
    },
)
