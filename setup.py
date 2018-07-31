import os
import sys
import subprocess
from package_settings import NAME, VERSION, PACKAGES, DESCRIPTION
from setuptools import setup

# # TODO is there a better way ? dependencies seem to always require the version
# # Calling only at the egg_info step gives us the wanted depth first behavior
# if 'egg_info' in sys.argv and os.getenv('CAPE_DEPENDENCIES', 'False').lower() == 'true':
#     subprocess.check_call(['pip3', 'install','--no-warn-conflicts','--upgrade', '-r', 'requirements.txt'])

setup(
    name=NAME,
    version=VERSION,
    long_description=DESCRIPTION,
    author='Bloomsbury AI',
    author_email='contact@bloomsbury.ai',
    packages=PACKAGES,
    include_package_data=True,
    install_requires=[
        'pytest==3.2.3',
        'peewee==3.5.2',
        'scout==3.0.2',
        'dataclasses==0.6',
        'cytoolz==0.9.0.1',
        'cape_splitter',
        'cape_api_helpers',
    ],
    dependency_links=[
        'git+https://github.com/bloomsburyai/cape-splitter#egg=cape_splitter',
        'git+https://github.com/bloomsburyai/cape-api-helpers#egg=cape_api_helpers'
    ],
    package_data={
        '': ['*.*'],
    },
)
