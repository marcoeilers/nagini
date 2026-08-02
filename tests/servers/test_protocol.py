"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


"""JVM-free unit tests for the structured counterexample serialization and the
ZMQ server request parsing. These need the nagini package importable but do
not start a JVM or verify anything."""


import json

from collections import OrderedDict

import pytest

try:
    from nagini_translation.models.converter import (
        counterexample_to_dict,
        counterexample_to_text,
        Model,
    )
    from nagini_translation.main import _parse_client_request
except Exception as e:  # pragma: no cover - environment dependent
    pytest.skip("nagini could not be imported: {}".format(e),
                allow_module_level=True)


def _full_model():
    return Model(
        input_store=OrderedDict([('a', 0), ('b', 3)]),
        current_store=OrderedDict([('a', 0), ('Result()', 'None')]),
        old_heap=OrderedDict([('A0', OrderedDict([('f', 3), ('g', 'A1')]))]),
        heap=OrderedDict([('A0', OrderedDict([('f', 4)])),
                          ('MustTerminate(_)', OrderedDict())]),
    )


def _pure_model():
    return Model(
        input_store=None,
        current_store=OrderedDict([('a', True)]),
        old_heap=None,
        heap=OrderedDict(),
    )


# -- Model.to_dict ----------------------------------------------------------

def test_full_model_to_dict():
    d = _full_model().to_dict()
    assert d['kind'] == 'model'
    assert d['oldStore'] == [{'name': 'a', 'value': '0'},
                             {'name': 'b', 'value': '3'}]
    assert d['store'] == [{'name': 'a', 'value': '0'},
                          {'name': 'Result()', 'value': 'None'}]
    assert d['oldHeap'] == [{'name': 'A0',
                             'entries': [{'name': 'f', 'value': '3'},
                                         {'name': 'g', 'value': 'A1'}]}]
    # An empty entries list marks a predicate/permission-only heap entry.
    assert d['heap'][1] == {'name': 'MustTerminate(_)', 'entries': []}
    # The dict must be JSON-serializable as-is.
    json.dumps(d)


def test_pure_model_to_dict():
    d = _pure_model().to_dict()
    assert d['oldStore'] is None
    assert d['oldHeap'] is None
    assert d['store'] == [{'name': 'a', 'value': 'True'}]
    assert d['heap'] == []


# -- counterexample_to_dict -------------------------------------------------

def test_counterexample_to_dict_none():
    assert counterexample_to_dict(None) is None


def test_counterexample_to_dict_model():
    assert counterexample_to_dict(_full_model())['kind'] == 'model'


def test_counterexample_to_dict_sif_string():
    # The SIF double-execution case yields an already-rendered string.
    text = 'First execution:\nStore: Empty.\nSecond execution:\nStore: Empty.'
    assert counterexample_to_dict(text) == {'kind': 'text', 'text': text}


# -- counterexample_to_text round-trips -------------------------------------

def test_text_roundtrip_full_model():
    model = _full_model()
    assert counterexample_to_text(model.to_dict()) == str(model)


def test_text_roundtrip_pure_model():
    model = _pure_model()
    assert counterexample_to_text(model.to_dict()) == str(model)


def test_text_of_text_kind_and_none():
    assert counterexample_to_text({'kind': 'text', 'text': 'abc'}) == 'abc'
    assert counterexample_to_text(None) == ''


# -- _parse_client_request --------------------------------------------------

def test_parse_request_legacy_plain_string():
    assert _parse_client_request('/tmp/foo.py') == ('/tmp/foo.py', None, {})


def test_parse_request_old_json():
    file, selected, options = _parse_client_request(
        json.dumps({'file': '/tmp/foo.py', 'select': 'a,b'}))
    assert file == '/tmp/foo.py'
    assert selected == {'a', 'b'}
    assert options == {}


def test_parse_request_json_format_options():
    file, selected, options = _parse_client_request(
        json.dumps({'file': '/tmp/foo.py', 'format': 'json',
                    'counterexample': True}))
    assert file == '/tmp/foo.py'
    assert selected is None
    assert options == {'format': 'json', 'counterexample': True}
