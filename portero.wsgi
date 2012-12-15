import os
import sys

cwd = os.getcwd()
sys.path.append('/var/www/portero')

from portero import app as application
