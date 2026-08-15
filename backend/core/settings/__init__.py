# init settings 
from .base import *  # Jika menggunakan base configuration

try:
    from .development import *
except ImportError:
    pass