# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

# Copyright (C) 2007 STFC & NERC (Science and Technology Facilities Council).
# This software may be distributed under the terms of the
# Q Public License, version 1.0 or later.
# http://ndg.nerc.ac.uk/public_docs/QPublic_license.txt
"""
Decorators for annotating OWS server controllers with information used
to populate the cows model.

@author: Stephen Pascoe
"""

from cows.util import make_domain
from cows.exceptions import * 
import inspect

def _wrap_sig(func, requiredArgs, optionalArgs, withVarkw=False, withVarargs=False):
    """
    Wrap a function in a function with a definied signature
    (i.e. args, *args and **kwargs).  This function works around a
    problem PEP-0262 is designed to address.  When wrapping functions using
    decorators you loose the function signature (visible via
    inspect.getargspec()).  This is a problem for Pylons because it uses inspection to
    dispatch controller actions.

    Not all signature information is retained in the wrapper.  Optional arguments are
    supported but their default values are not visible (the wrapped method will handle
    them as usual).

    @param func: A function to be wrapped
    @param requiredArgs: Required argument names
    @param optionalArgs: Optional argument names
    @param withVarargs: If True allow variable arguments
    @param withVarkw: If True allow variable keyword arguments
    @return: A function with the given argument signature which wraps func.

    """

    # Default acts as a singleton to mark optional arguments
    class Default:
        pass
    
    if withVarkw:
        varkw = 'varkw_in'
    else:
        varkw = None
    if withVarargs:
        varargs = 'varargs_in'
    else:
        varargs = None

    args = requiredArgs + optionalArgs
    first_default = len(requiredArgs)

    def formatarg(arg):
        i = args.index(arg)
        if i < first_default:
            return arg
        else:
            return '%s=_wrap_default' % arg

    def process(localVars):
        args = [localVars[x] for x in requiredArgs]
        args += localVars.get('varargs_in', [])
        kwargs = localVars.get('varkw_in', {})
        for arg in optionalArgs:
            if localVars[arg] != Default:
                kwargs[arg] = localVars[arg]
        return args, kwargs

    wrap_vars = dict(_wrap_func=func, _wrap_process=process, _wrap_default=Default)
    wrap_sig = inspect.formatargspec(args, varargs, varkw,
                                     formatarg=formatarg)

    wrap_expr = """
def %s%s:
    args, kwargs = _wrap_process(locals())    
    return _wrap_func(*args, **kwargs)""" % (func.__name__, wrap_sig)

    exec wrap_expr in wrap_vars

    return wrap_vars[func.__name__]


def ows_operation(method):
    """
    A decorator which defines a method as a OWS operation.

    The method is anotated with the attributes of the OWS protocol which are then
    interogated during dispatch by OwsController to enforce OWS operation calling
    behaviour.
    
    """

    method._ows_name = method.__name__

    return method

#-----------------------------------------------------------------------------

from unittest import TestCase

class TestOperationDecorator(TestCase):
    def setUp(self):
        class Foo(object):
            @ows_operation(['Bar'], ['Baz'])
            def MyOp(self, bar, baz=1):
                return bar+baz

        self.foo = Foo()

    def testOwsProtocol(self):
        # Check OWS protocol is adhered to
        assert self.foo.MyOp._ows_name == 'MyOp'
        assert self.foo.MyOp._ows_required_parameters == ['Bar']
        assert self.foo.MyOp._ows_optional_parameters == ['Baz']

    def testCall(self):
        assert self.foo.MyOp(2) == 3
        assert self.foo.MyOp(bar=2) == 3
        assert self.foo.MyOp(bar=2, baz=2) == 4

    def testExtraArgs(self):
        self.assertRaises(TypeError, lambda: self.foo.MyOp(1, 2, 3))
        self.assertRaises(TypeError, lambda: self.foo.MyOp(1, 2, x=3))
        


class TestWrapSignature(TestCase):
    def setUp(self):
        def f(x, y, z='default', z2='default2', *args, **kwargs):
            return dict(x=x, y=y, z=z, z2=z2, args=args, kwargs=kwargs)
        self.wrap = _wrap_sig(f, ['x', 'y'], ['z', 'z2'], True, True)

    def test1(self):
        self.assertRaises(TypeError, lambda: self.wrap(1))

    def test2(self):
        d = self.wrap(1, 2)
        self.assertEquals(d['x'], 1)
        self.assertEquals(d['y'], 2)

    def test3(self):
        d = self.wrap(1,2)
        self.assertEquals(d['z'], 'default')
        self.assertEquals(d['z2'], 'default2')

    def test4(self):
        d = self.wrap(1, 2, 3)
        self.assertEquals(d['z'], 3)
        self.assertEquals(d['z2'], 'default2')

    def test5(self):
        d = self.wrap(1, 2, z2=3)
        self.assertEquals(d['z'], 'default')
        self.assertEquals(d['z2'], 3)

    def test6(self):
        d = self.wrap(*(1,2))
        self.assertEquals(d['x'], 1)
        self.assertEquals(d['y'], 2)

    def test7(self):
        d = self.wrap(1, 2, 3, 4)
        self.assertEquals(d['x'], 1)
        self.assertEquals(d['y'], 2)
        self.assertEquals(d['z'], 3)
        self.assertEquals(d['z2'], 4)

    def test8(self):
        d = self.wrap(1,2, **dict(z=3, w=4))
        self.assertEquals(d['z'], 3)
        self.assertEquals(d['kwargs']['w'],4)

class TestWrapSignature2(TestWrapSignature):
    def setUp(self):
        """
        Make a function that accepts anything but has the same return value as in
        TestWrapSignature.
        """
        def f(*args, **kwargs):
            d = {}

            try:
                d['x'] = args[0]
            except IndexError:
                d['x'] = kwargs['x']

            try:
                d['y'] = args[1]
            except IndexError:
                d['y'] = kwargs['y']

            try:
                d['z'] = args[2]
            except IndexError:
                try:
                    d['z'] = kwargs['z']
                except KeyError:
                    d['z'] = 'default'

            try:
                d['z2'] = args[3]
            except IndexError:
                try:
                    d['z2'] = kwargs['z2']
                except KeyError:
                    d['z2'] = 'default2'

            for k in 'x', 'y', 'z', 'z2':
                if k in kwargs:
                    del kwargs[k]

            d['args'] = args[4:]
            d['kwargs'] = kwargs

            return d

        self.wrap = _wrap_sig(f, ['x', 'y'], ['z', 'z2'], True, True)
