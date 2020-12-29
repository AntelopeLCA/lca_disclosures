"""
To create the wheel run - python setup.py bdist_wheel
"""

from setuptools import setup, find_packages



setup(
    name='lca_disclosures',
    version="0.2.0",
    packages=find_packages(),
    author="Brandon Kuczenski",
    author_email="bkuczenski@ucsb.edu",
    license=open('LICENSE').read(),
    #entry_points = {
    #   'console_scripts': [
    #   ]
    #},
    #install_requires=[
    #],
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
