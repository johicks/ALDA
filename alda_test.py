#!/usr/bin/env python
import alda
import pytest
import requests


def test_validate_cpcodes():
    cpcodes = ['123456,', '123456,', '789123', '123456']
    cpcodes = alda.validate_cpcodes(cpcodes)
    assert cpcodes == ['123456', '123456', '789123', '123456']

    cpcodes = ['123456,789123,456789']
    cpcodes = alda.validate_cpcodes(cpcodes)
    assert cpcodes == ['123456', '789123', '456789']

    cpcodes = ['qwerty', 'qwerty', 'qwerty']
    # validate_cpcodes returns None if int() conversion fails
    assert alda.validate_cpcodes(cpcodes) is None


def test_create_openapi_request():
    edgercFile = 'null'
    geo = 'null'
    with pytest.raises(FileNotFoundError):
        alda.create_openapi_request(edgercFile, geo)

    edgercFile = 'alda.edgerc'
    geo = 'null'
    openapiObj = alda.create_openapi_request(edgercFile, geo)
    assert 'v2.luna.akamaiapis.net' in openapiObj['baseurl']
    assert isinstance(openapiObj['request'], requests.sessions.Session)

    edgercFile = 'alda.edgerc'
    geo = 'eu'
    openapiObj = alda.create_openapi_request(edgercFile, geo)
    assert 'gb.luna.akamaiapis.net' in openapiObj['baseurl']
    assert isinstance(openapiObj['request'], requests.sessions.Session)

    edgercFile = 'alda.edgerc'
    geo = 'jp'
    openapiObj = alda.create_openapi_request(edgercFile, geo)
    assert 'jg.luna.akamaiapis.net' in openapiObj['baseurl']
    assert isinstance(openapiObj['request'], requests.sessions.Session)
