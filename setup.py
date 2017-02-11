import os
import re

from setuptools import find_packages, setup


def read_version():
    regexp = re.compile(r"^__version__\W*=\W*'([\d.abrc]+)'")
    init_py = os.path.join(os.path.dirname(__file__), 'maplocate', '__init__.py')
    with open(init_py) as f:
        for line in f:
            match = regexp.match(line)
            if match is not None:
                return match.group(1)
        else:
            raise RuntimeError('Cannot find version in maplocate/__init__.py')


install_requires = []


setup(name='maplocate',
      version=read_version(),
      description='Maplocate setup',
      platforms=['POSIX'],
      packages=find_packages(),
      include_package_data=True,
      author='dimetriuss',
      author_email='dimetriuss@gmail.com',
      url='https://github.com/dimetriuss/maplocate',
      install_requires=install_requires,
      entry_points={
          'console_scripts': [
              'maplocate = argsrun:main',
              ],
          'maplocate': [
              'serve-maplocate = maplocate.main:gateway',
              ]},
      zip_safe=False)

