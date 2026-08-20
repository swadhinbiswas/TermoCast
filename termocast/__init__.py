"""
TermoCast — Advanced Terminal Dashboard
Weather • News • Stocks • Crypto • System
"""

__version__ = "1.0.0"
__author__ = "Swadhin Biswas"
__email__ = "swadhinbiswas.cse@gmail.com"
__license__ = "MIT"

from .config import Config, load_config

__all__ = ["__version__", "Config", "load_config"]
