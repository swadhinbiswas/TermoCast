from setuptools import setup, find_packages

setup(
  name='TermoCast',
  version='0.1',
  packages=find_packages(),
  install_requires=[
    'requests',
    'geocoder',
    'rich',
    'typer'
  ],
  entry_points={
    'console_scripts': [
      'weather=usr.bin.weather:weather'
    ]
  }
)

