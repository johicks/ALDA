#!/usr/bin/env python
import alda
import json
import pytest
import requests
from urllib.parse import urljoin
from akamai.netstorage import Netstorage


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


def test_get_ns_credentials():
    with pytest.raises(FileNotFoundError):
        config = alda.get_netstorage_credentials('null')

    config = alda.get_netstorage_credentials('alda.netstorage')
    assert config['DEFAULT']['Hostname'] is not False
    assert config['DEFAULT']['Key-name'] is not False
    assert config['DEFAULT']['Key'] is not False
    assert config['DEFAULT']['Cpcode'] is not False
    assert config['DEFAULT']['Password'] is not False


def test_create_netstorage_paths():
    sformat = 'smooth'
    geo = 'us'
    cpcodes = ['123456', '789012']
    connectionDetails = alda.get_netstorage_credentials('alda.netstorage')
    ns = Netstorage(connectionDetails['DEFAULT']['Hostname'],
                    connectionDetails['DEFAULT']['Key-name'],
                    connectionDetails['DEFAULT']['Key'], ssl=True)
    for cpcode in cpcodes:
        ns_dir = '/{0}/logdelivery/{1}/{2}/{3}'\
                .format(connectionDetails['DEFAULT']['Cpcode'], sformat, geo, cpcode)
        ok, response = ns.mkdir(ns_dir)  # Test we can make directories
        assert ok is True
        assert response.status_code == 200
        ok, response = ns.rmdir(ns_dir)  # Remove test directories
        print(ok)
        print(response.text)
        assert ok is True
        assert response.status_code == 200


def test_create_lds_configs():
    sformat = 'smooth'
    geo = 'us'
    cpcode = '525828'
    openapiObj = alda.create_openapi_request('alda.edgerc', geo)
    connectionDetails = alda.get_netstorage_credentials('alda.netstorage')

    lds_payload = json.loads('''
    {
        "configurationType": "PRIMARY",
        "acgObject": {
            "id": "000000",
            "type": "CP_CODE"
        },
        "productGroupId": 1,
        "startDate": 1401840000000,
        "logFormat": { "dictId": "2" },
        "logIdentifier": "000000",
        "aggregationType": "COLLECTION",
        "deliveryType": "FTP",
        "deliveryFrequency": {"dictId": "7"},
        "ftpConfiguration": {
            "directory": "",
            "machine": "adsiuslogs.download.akamai.com",
            "login": "amazonlogs",
            "password": ""
        },
        "messageSize": { "dictId": "1" },
        "encoding": { "dictId": "3" },
        "contact": {
            "contactEmail": ["amazon-dm-us-api-support@akamai.com"],
            "dictId": "B-C-PNOHOD"
        }
    }''')
    lds_payload['acgObject']['id'] = cpcode
    lds_payload['logIdentifier'] = cpcode
    lds_payload['ftpConfiguration']['directory'] =\
        '/{0}/logdelivery/{1}/{2}/{3}'.format(
        connectionDetails['DEFAULT']['Cpcode'], sformat, geo, cpcode)
    lds_payload['ftpConfiguration']['password'] = connectionDetails['DEFAULT']['Password']

    # Test that we can create a configuration
    result = openapiObj['request'].post(urljoin(openapiObj['baseurl'], '/lds/v1/configurations'),
                                        data=json.dumps(lds_payload),
                                        headers={'Accept': '*/*', 'Content-Type': 'application/json'})
    assert result.status_code == 200

    resultObject = result.json()
    serviceID = resultObject['contents']
    # Delete the configuration we just created
    result = openapiObj['request'].delete(urljoin(openapiObj['baseurl'], '/lds/v1/configurations/{0}'.format(serviceID)),
                                          data=json.dumps(lds_payload),
                                          headers={'Accept': '*/*', 'Content-Type': 'application/json'})
    assert result.status_code == 200
