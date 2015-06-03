#coding:utf-8
#nature@20100725

import sys
import os
import types

class ApiCube:
    class ApiLoadFileFailed(Exception):
        pass
    class ApiNotExists(Exception):
        pass
    class ApiBadParams(Exception):
        pass

    def __init__(self, path, filterPaths, corePath=None):
        self._cube = {}
        self._public = {}
        self._module = []
        #TODO 需要解除这个固定core路径耦合
        if isinstance(path, list):
            for it in path:
                self._loadPath(it, filterPaths, corePath)
        else:
            self._loadPath(path, filterPaths, corePath)

    def apiList(self):
        return list(self._cube)

    def apiPublic(self):
        return list(self._public)

    def apiInfo(self, api):
        callable = self._cube.get(api)
        if callable == None:
            return None
        return {'name': callable.__name__, 'params': self._getFunctionArgs(callable), 'doc': str(callable.__doc__)}

    def call(self, function, params, env):
        callable = self._cube.get(function)
        if not callable:
            raise self.ApiNotExists(function)
        args = self._getFunctionArgs(callable)
        if not self._checkArgsEq(args, params):
            raise self.ApiBadParams('Call:' + str(params) + ', Need:' + str(args))
        params['env'] = env
        return callable(**params)

    def loadFunction(self, function, name=None, coreApi=False):
        if name == None:
            name = function.__name__
        self._cube[name] = function
        if not coreApi:
            self._public[name] = function

    def loadModule(self, mod, core=None):
        self._module.append(mod)
        for k in dir(mod):
            v = getattr(mod, k)
            if isinstance(v, types.FunctionType) and self._isApiFunction(v):
                self._cube[k] = v
                if core and mod.__file__.startswith(core):
                    continue
                self._public[k] = v

    def initModule(self, params):
        for mod in self._module:
            initHandler = getattr(mod, '__initialize__', None)
            if initHandler is None:
                continue
            initHandler(params)

    def finalizeModule(self, params):
        for mod in self._module:
            finalizeHandler = getattr(mod, '__finalize__', None)
            if finalizeHandler is None:
                continue
            finalizeHandler(params)

    def _getActiveFiles(self, files):
        activeFiles = []
        for item in files:
            pyfile = item.lower()
            if not pyfile.startswith('api'):
                continue
            if not(pyfile.endswith('.py') or pyfile.endswith('.pyc') or pyfile.endswith('.pyo')):
                continue
            name, ext = os.path.splitext(pyfile)    
            if name in map(lambda x:os.path.splitext(x)[0], activeFiles):
                continue

            tempName = ('%s.%s' % (name, 'py'))
            if ext != 'py' and (tempName in files):
                activeFiles.append(tempName)
            else:
                activeFiles.append(pyfile)
        return activeFiles


    def _loadPath(self, path, filterPaths, core=None):
        if path not in sys.path:
            sys.path.append(path)
        for root, dirs, files in os.walk(path):
            filtered = False
            for it in filterPaths:
                if root.startswith(it):
                    filtered = True
                    break
            if filtered:
                continue
            files = self._getActiveFiles(files)    
            for file in files:
                short = os.path.splitext(file)[0]
                file = os.path.join(root, short)
                name = file[len(path) + 1:].replace('/', '.').replace('\\', '.')
                mod = self._import(name)
                self.loadModule(mod, core)

    @staticmethod
    def _import(name):
        mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod

    @staticmethod
    def _isApiFunction(function):
        if function.__name__.startswith('_'):
            return False
        try:
            ApiCube._getFunctionArgs(function)
        except:
            print 'Can not load api "%s" in module "%s"' % (function.__name__, function.__module__)
            return False
        return True

    @staticmethod
    def _getFunctionArgs(function):
        args = function.func_code.co_varnames[:function.func_code.co_argcount]
        method = 0
        if len(args) > 0 and args[0] == 'self':
            method = 1
        assert(len(args) > 0 + method)
        assert(args[0 + method] == 'env')
        return args[1:]

    @staticmethod
    def _checkArgsEq(args1, args2):
        args1 = list(args1)
        args2 = list(args2)
        args1.sort()
        args2.sort()
        return args1 == args2
