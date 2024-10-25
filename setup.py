from setuptools import setup, find_packages

setup(
  name='termocast',
  version=0.1,
  packages=find_packages(),
  long_description=open('README.md').read(),
  long_description_content_type='text/markdown',
  author='Swadhin Biswas',
  author_email='swadhinbiswas.cse@gmail.com',
  url='https://github.com/swadhinbiswas/TermoCast',
  license='MIT',
  description='A simple weather cli',
  keywords=['weather cli','weather forecast','weather', 'cli', 'command line interface', 'terminal', 'command line', 'forecast'],

  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Topic :: Software Development :: Libraries :: Python Modules',
    "Operating System :: POSIX :: Linux",
  ],
  install_requires=[
    'requests',
    'geocoder',
    'rich',
    'typer'
  ],
  entry_points={
    'console_scripts': [
      'weather=usr.bin.weather:weather'
    ],
    
  },
  
)

