import os
import sys
import pytest

if not os.getenv('CI'):
    pytest.skip('Please run with ./shlaxfile.py test', allow_module_level=True)
