from __future__ import print_function
import os
import sys
import platform
from setuptools import setup, find_packages
from distutils.version import StrictVersion

if StrictVersion(platform.python_version()) <= StrictVersion("3.10.0"):
    print("pysystemtrade requires Python 3.10.0 or later. Exiting.", file=sys.stderr)
    sys.exit(1)


def read(fname):
    """Utility function to read the README file."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="pysystemtrade",
    version="1.80",
    author="Robert Carver",
    description=(
        "Python framework for running systems as in Robert Carver's book Systematic Trading"
        " (https://www.systematicmoney.org/systematic-trading)"
    ),
    license="GNU GPL v3",
    keywords="systematic trading interactive brokers",
    url="https://qoppac.blogspot.com/p/pysystemtrade.html",
    packages=find_packages(),
    long_description=read("README.md"),
    install_requires=[
        "pandas==2.1.3",
        "matplotlib>=3.0.0",
        "ib-insync==0.9.86",
        "PyYAML>=5.3",
        "numpy>=1.24.0",
        "scipy>=1.0.0",
        "pymongo==3.11.3",
        "psutil==5.6.6",
        "pytest>6.2",
        "Flask>=2.0.1",
        "Werkzeug>=2.0.1",
        "statsmodels==0.14.0",
        "PyPDF2>=2.5.0",
        "pyarrow>=14.0.1",
        "scikit-learn>1.3.0",
    ],
    tests_require=["nose", "flake8"],
    extras_require=dict(),
    test_suite="nose.collector",
    include_package_data=True,
)
