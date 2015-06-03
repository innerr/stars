#coding:utf-8

import os
import sys
import time
import unittest

basePath = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(basePath)
import core.init

keysPath = basePath + '/../../keys/'

ok = 'ok'
