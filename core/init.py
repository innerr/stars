#coding:utf-8
#nature@20100725

import os
import sys

_basePath = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if _basePath not in sys.path:
    sys.path.append(_basePath)

_libPath = os.path.join(_basePath, '_libs')
if _libPath not in sys.path:
    sys.path.append(_libPath)

