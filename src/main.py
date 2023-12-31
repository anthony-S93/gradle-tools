import sys
from gt.actions import *

try:
    start(sys.argv[1:])
except Exception as e:
    if str(e):
        print(e)
