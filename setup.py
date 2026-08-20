from setuptools import setup, find_packages

setup(
  name='termocast',
  version="1.0.1",
  packages=find_packages(include=["termocast", "termocast.*", "usr", "usr.*"]),
  long_description=open('README.md').read(),
  long_description_content_type='text/markdown',
  author='Swadhin Biswas',
  author_email='swadhinbiswas.cse@gmail.com',
  url='https://github.com/swadhinbiswas/TermoCast',
  license='MIT',
  description='Advanced terminal dashboard — Weather • News • Stocks • Crypto (Textual TUI + Rich)',
  keywords=['weather cli','weather forecast','weather', 'cli', 'tui', 'textual', 'rich', 'news', 'stocks', 'crypto', 'terminal', 'dashboard'],

  classifiers=[
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Intended Audience :: End Users/Desktop',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
    'Topic :: Software Development :: Libraries :: Python Modules',
    "Operating System :: POSIX :: Linux",
    "Environment :: Console :: Curses",
  ],
  python_requires=">=3.9",
  install_requires=[
    'requests>=2.28',
    'geocoder>=1.38',
    'rich>=13.0',
    'typer>=0.9',
    'textual>=6.0',
    'httpx>=0.24',
  ],
  entry_points={
    'console_scripts': [
      'termocast=termocast.cli:app',
      'weather=termocast.cli:weather_entry',
    ],
  },
  
)

