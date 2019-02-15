#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_utils
----------------------------------

Tests for the various utility operations employed by magpie.
"""

from magpie.api import api_requests as ar, api_except as ax
from magpie.definitions.pyramid_definitions import (    # noqa: F401
    asbool,
    Request,
    HTTPInternalServerError,
    HTTPNotAcceptable,
    HTTPBadRequest,
    HTTPOk,
)
from magpie.definitions.typedefs import Str     # noqa: F401
from pyramid.testing import DummyRequest
from tests import utils, runner
import unittest


@runner.MAGPIE_TEST_UTILS
class TestUtils(unittest.TestCase):
    @staticmethod
    def make_request(request_path_query):
        # type: (Str) -> Request
        parts = request_path_query.split('?')
        path = parts[0]
        query = dict()
        if len(parts) > 1:
            for q in parts[1:]:
                k, v = q.split('=')
                query[k] = v
        # noinspection PyTypeChecker
        return DummyRequest(path=path, params=query)

    @classmethod
    def setUpClass(cls):
        pass

    def test_get_query_param(self):
        r = self.make_request('/some/path')
        v = ar.get_query_param(r, 'value')
        utils.check_val_equal(v, None)

        r = self.make_request('/some/path?other=test')
        v = ar.get_query_param(r, 'value')
        utils.check_val_equal(v, None)

        r = self.make_request('/some/path?other=test')
        v = ar.get_query_param(r, 'value', True)
        utils.check_val_equal(v, True)

        r = self.make_request('/some/path?value=test')
        v = ar.get_query_param(r, 'value', True)
        utils.check_val_equal(v, 'test')

        r = self.make_request('/some/path?query=value')
        v = ar.get_query_param(r, 'query')
        utils.check_val_equal(v, 'value')

        r = self.make_request('/some/path?QUERY=VALUE')
        v = ar.get_query_param(r, 'query')
        utils.check_val_equal(v, 'VALUE')

        r = self.make_request('/some/path?QUERY=VALUE')
        v = asbool(ar.get_query_param(r, 'query'))
        utils.check_val_equal(v, False)

        r = self.make_request('/some/path?Query=TRUE')
        v = asbool(ar.get_query_param(r, 'query'))
        utils.check_val_equal(v, True)

    def test_verify_param_proper_verifications(self):
        # with default error
        utils.check_raises(lambda: ax.verify_param('b', paramCompare=['a', 'b'], notIn=True), HTTPNotAcceptable)
        utils.check_raises(lambda: ax.verify_param('x', paramCompare=['a', 'b'], isIn=True), HTTPNotAcceptable)
        utils.check_raises(lambda: ax.verify_param('1', paramCompare=int, ofType=True), HTTPNotAcceptable)
        utils.check_raises(lambda: ax.verify_param('x', paramCompare='x', notEqual=True), HTTPNotAcceptable)
        utils.check_raises(lambda: ax.verify_param('x', paramCompare='y', isEqual=True), HTTPNotAcceptable)
        utils.check_raises(lambda: ax.verify_param(False, isTrue=True), HTTPNotAcceptable)
        utils.check_raises(lambda: ax.verify_param(True, isFalse=True), HTTPNotAcceptable)
        utils.check_raises(lambda: ax.verify_param(None, notNone=True), HTTPNotAcceptable)
        utils.check_raises(lambda: ax.verify_param(1, isNone=True), HTTPNotAcceptable)
        utils.check_raises(lambda: ax.verify_param('', notEmpty=True), HTTPNotAcceptable)
        utils.check_raises(lambda: ax.verify_param('abc', isEmpty=True), HTTPNotAcceptable)

        # with requested error
        utils.check_raises(lambda: ax.verify_param('b', paramCompare=['a', 'b'], notIn=True,
                                                   httpError=HTTPBadRequest), HTTPBadRequest)
        utils.check_raises(lambda: ax.verify_param('x', paramCompare=['a', 'b'], isIn=True,
                                                   httpError=HTTPBadRequest), HTTPBadRequest)
        utils.check_raises(lambda: ax.verify_param('1', paramCompare=int, ofType=True,
                                                   httpError=HTTPBadRequest), HTTPBadRequest)
        utils.check_raises(lambda: ax.verify_param('x', paramCompare='x', notEqual=True,
                                                   httpError=HTTPBadRequest), HTTPBadRequest)
        utils.check_raises(lambda: ax.verify_param('x', paramCompare='y', isEqual=True,
                                                   httpError=HTTPBadRequest), HTTPBadRequest)
        utils.check_raises(lambda: ax.verify_param(False, isTrue=True,
                                                   httpError=HTTPBadRequest), HTTPBadRequest)
        utils.check_raises(lambda: ax.verify_param(True, isFalse=True,
                                                   httpError=HTTPBadRequest), HTTPBadRequest)
        utils.check_raises(lambda: ax.verify_param(None, notNone=True,
                                                   httpError=HTTPBadRequest), HTTPBadRequest)
        utils.check_raises(lambda: ax.verify_param(1, isNone=True,
                                                   httpError=HTTPBadRequest), HTTPBadRequest)
        utils.check_raises(lambda: ax.verify_param('', notEmpty=True,
                                                   httpError=HTTPBadRequest), HTTPBadRequest)
        utils.check_raises(lambda: ax.verify_param('abc', isEmpty=True,
                                                   httpError=HTTPBadRequest), HTTPBadRequest)

    def test_verify_param_incorrect_usage(self):
        utils.check_raises(lambda: ax.verify_param('b', paramCompare=['a', 'b']), HTTPInternalServerError)
        utils.check_raises(lambda: ax.verify_param('b', paramCompare=['a', 'b'], notIn=None), HTTPInternalServerError)
        utils.check_raises(lambda: ax.verify_param('b', notIn=True), HTTPInternalServerError)
        utils.check_raises(lambda: ax.verify_param('b', paramCompare=['a', 'b'], notIn=True,
                                                   httpError=HTTPOk), HTTPInternalServerError)

    def test_verify_param_compare_types(self):
        """param and paramCompare must be of same type"""
        utils.check_raises(lambda: ax.verify_param('1', paramCompare=1, isEqual=True), HTTPInternalServerError)
        utils.check_raises(lambda: ax.verify_param('1', paramCompare=True, isEqual=True), HTTPInternalServerError)
        utils.check_raises(lambda: ax.verify_param(1, paramCompare='1', isEqual=True), HTTPInternalServerError)
        utils.check_raises(lambda: ax.verify_param(1, paramCompare=True, isEqual=True), HTTPInternalServerError)

        # strings cases handled correctly (no raise)
        utils.check_no_raise(lambda: ax.verify_param('1', paramCompare=u'1', isEqual=True))