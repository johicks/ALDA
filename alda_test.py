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
    with pytest.raises(ValueError):
        alda.validate_cpcodes(cpcodes)


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


def test_get_lds_configs_and_cpcodes_us():
    openapiObj = alda.create_openapi_request('alda.edgerc', 'us')
    ldsConfigs = alda.get_lds_configs(openapiObj)
    assert ldsConfigs['errorMessage'] is None

    # If test is failing, probable that one of these cpcodes status changed
    # Check portal and update accordingly
    cpcodes_active = ['100899', '193213', '153058']
    cpcodes_inactive = ['513803', '482486', '453163']

    empty_cpcode_list = alda.check_cpcodes(ldsConfigs['contents'], cpcodes_active)
    full_cpcode_list = alda.check_cpcodes(ldsConfigs['contents'], cpcodes_inactive)

    assert len(empty_cpcode_list) == 0
    assert len(full_cpcode_list) == 3


def test_get_lds_configs_and_cpcodes_eu():
    openapiObj = alda.create_openapi_request('alda.edgerc', 'eu')
    ldsConfigs = alda.get_lds_configs(openapiObj)
    assert ldsConfigs['errorMessage'] is None

    # If test is failing, probable that one of these cpcodes status changed
    # Check portal and update accordingly
    cpcodes_active = ['175681', '203346', '269263']
    cpcodes_inactive = ['526922', '457310', '411230']

    empty_cpcode_list = alda.check_cpcodes(ldsConfigs['contents'], cpcodes_active)
    full_cpcode_list = alda.check_cpcodes(ldsConfigs['contents'], cpcodes_inactive)

    assert len(empty_cpcode_list) == 0
    assert len(full_cpcode_list) == 3


def test_get_lds_configs_and_cpcodes_jp():
    openapiObj = alda.create_openapi_request('alda.edgerc', 'jp')
    ldsConfigs = alda.get_lds_configs(openapiObj)
    assert ldsConfigs['errorMessage'] is None

    # If test is failing, probable that one of these cpcodes status changed
    # Check portal and update accordingly
    cpcodes_active = ['202369', '272610', '384159']
    cpcodes_inactive = ['515552', '515550', '515551']

    empty_cpcode_list = alda.check_cpcodes(ldsConfigs['contents'], cpcodes_active)
    full_cpcode_list = alda.check_cpcodes(ldsConfigs['contents'], cpcodes_inactive)

    assert len(empty_cpcode_list) == 0
    assert len(full_cpcode_list) == 3
