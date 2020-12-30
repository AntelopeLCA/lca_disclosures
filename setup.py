"""
To create the wheel run - python setup.py bdist_wheel
"""

from setuptools import setup, find_packages


"""
Revision History

0.2.0rc1 - 2020 Dec 29 - Remove bw2 implementation to avoid unnecessary dependencies (unfortunately, the package still
depends on scipy and pandas, neither of which are required by core Antelope)

0.1.0 - 2018 Aug 03 - Original release by PJJ
"""

requirements = [
    'scipy>=1.5.2',
    'pandas>=1.1.2'
]


setup(
    name='lca_disclosures',
    version="0.2.0rc1",
    packages=find_packages(),
    author="Brandon Kuczenski",
    author_email="bkuczenski@ucsb.edu",
    license=open('LICENSE').read(),
    #entry_points = {
    #   'console_scripts': [
    #   ]
    #},
    install_requires=requirements,
    url="https://github.com/AntelopeLCA/lca_disclosures/",
    long_description=open('README.md').read(),
    description='Python based tools for working with LCA foreground model disclosures',
    keywords=['LCA', 'Life Cycle Assessment', 'Foreground system', 'Background system',
              'Foreground model'],
    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Visualization',
    ],
)

# Also consider:
# http://code.activestate.com/recipes/577025-loggingwebmonitor-a-central-logging-server-and-mon/
