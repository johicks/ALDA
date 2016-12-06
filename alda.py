#!/usr/bin/env python
'''
ALDA - Amazon Log Delivery Service Automation
ALDA's purpose is to automate LDS enablement for new CPCodes on any
of Amazon's Luna accounts (us/eu/jp)
'''
import argparse
import configparser
import json
import os.path
import requests
from urllib.parse import urljoin
from akamai.netstorage import Netstorage
from akamai.edgegrid import EdgeGridAuth, EdgeRc


def main(args):
    '''Performs main program functions when command line arguments exist'''
    # Perform some basic validation/triage on cpcode arguments
    args.cpcodes = validate_cpcodes(args.cpcodes)

    # Get OPEN API credentials and create connection object
    openapiObj = create_openapi_request('alda.edgerc', args.geo)

    # Get List of LDS Configurations
    print('Retrieving LDS configs', flush=True)
    ldsObj = get_lds_configs(openapiObj)

    # Remove cpcodes with ACTIVE LDS configurations and warn user
    print('Checking cpcode list against active configs', flush=True)
    inactiveCpcodes = check_cpcodes(ldsObj['contents'], args.cpcodes)

    # Continue only if we have at least one CPCode without an ACTIVE config
    if len(inactiveCpcodes) > 0:
        # Connect to NetStorage and create storage locations
        print('', flush=True)
        print('Connecting to NetStorage', flush=True)
        connectionDetails = get_netstorage_credentials('alda.netstorage')
        create_netstorage_paths(args.format, args.geo, inactiveCpcodes, connectionDetails)
        # Create LDS Configurations
        print('', flush=True)
        print('Creating LDS configs', flush=True)
        create_lds_configs(args.format, args.geo, inactiveCpcodes,
                           openapiObj, connectionDetails)
    else:
        return


def validate_cpcodes(cpcodes):
    '''Triages cpcode argument list in the following ways:
    123456,789012,345678 = 123456 789012 345678
    123456, 789012, 345678 = 123456 789012 345678
    qwerty, qwerty, qwerty = ERROR

    returns list
    '''
    # Check if user entered a comma separated list with no spaces
    if len(cpcodes) == 1 and ',' in cpcodes[0]:
        cpcodes = cpcodes[0].split(',')
    else:
        for i in range(len(cpcodes)):
            if ',' in cpcodes[i]:
                # Remove commas from list if user entered comma separated arguments
                cpcodes[i] = cpcodes[i].replace(',', '')

            # Check that each CPCode is a valid integer
            try:
                int(cpcodes[i])
            except ValueError:
                raise ValueError('ERROR - Invalid CPCode: {0}'.format(cpcodes[i]))
    return cpcodes


def create_openapi_request(edgercFile, geo):
    '''Creates http request object and signs it with Akamai EdgeGridAuth

    Keyword Arguments:
    edgercFile -- .edgerc file on disk containing Akamai API credentials
    geo -- command line argument indicating which Luna account to access

    returns dictionary
    '''
    openapiObj = {}
    if not os.path.isfile(edgercFile):
        raise FileNotFoundError(edgercFile)
    edgerc = EdgeRc(edgercFile)
    section = 'C-14QDNW3'
    if geo == 'eu':
        section = '3-11XPV4E'
    elif geo == 'jp':
        section = 'C-XGVIZ2'
    baseurl = 'https://{0}'.format(edgerc.get(section, 'host'))
    s = requests.Session()
    try:
        s.auth = EdgeGridAuth.from_edgerc(edgerc, section)
    except configparser.NoSectionError:
        raise ValueError('EdgeRC file missing section: {0}'.format(section))

    openapiObj.setdefault('baseurl', baseurl)
    openapiObj.setdefault('request', s)

    return openapiObj


def get_lds_configs(openapiObj):
    '''Calls
    https://developer.akamai.com/api/luna/lds/resources.html#listconfigurations
    and lists all LDS configurations on Luna

    Keyword Arguments:
    openapiObj -- dictionary containing baseurl and signed http request object

    returns dictionary
    '''
    result = openapiObj['request'].get(urljoin(openapiObj['baseurl'],
                                               '/lds/v1/configurations'
                                               )
                                       )
    return result.json()


def check_cpcodes(ldsConfigs, cpcodes):
    '''Loops through log delivery configs and checks list of cpcodes given by
    user to see if they are listed with ACTIVE status, indicating they are
    already being delivered somewhere

    Keyword Arguments:
    ldsConfigs -- deserialized json response from LDS API
    cpcodes -- list of cpcodes provided by user via command line
    '''
    for config in range(len(ldsConfigs)):
        cpcode = ldsConfigs[config]['cpCode']['dictId']
        status = ldsConfigs[config]['status']
        if cpcode in cpcodes and status == 'ACTIVE':
            cpcodes.remove(cpcode)
            cpcode_name = ldsConfigs[config]['cpCode']['dictValue']
            print('CPCode {0} - "{1}" has an active LDS configuration. '
                  'Please manually review.'.format(cpcode, cpcode_name), flush=True)
    return cpcodes


def get_netstorage_credentials(configFile):
    '''Pulls NetStorage connection/credential details from configFile

    Keyword Arguments:
    configFile -- file on disk named alda.netstorage

    returns ConfigParser
    '''
    if not os.path.isfile(configFile):
        raise FileNotFoundError(configFile)
    else:
        config = configparser.ConfigParser()
        config.read(configFile)

    return config


def create_netstorage_paths(sformat, geo, cpcodes, connectionDetails):
    '''Connects to Akamai's NetStorage infrastructure and creates file
    paths to receive log delivery via FTP

    Keyword Arguments:
    sformat -- string provided by user indicating streaming format
    geo -- string provided by user indicating service geo
    cpcodes -- list of cpcodes provided by user
    connectionDetails -- ConfigParser object containing NS auth details
    '''
    for cpcode in cpcodes:
        ns = Netstorage(connectionDetails['DEFAULT']['Hostname'],
                        connectionDetails['DEFAULT']['Key-name'],
                        connectionDetails['DEFAULT']['Key'], ssl=True)
        ns_dir = '/{0}/logdelivery/{1}/{2}/{3}'\
                .format(connectionDetails['DEFAULT']['Cpcode'], sformat, geo, cpcode)
        print('Creating {0}'.format(ns_dir), flush=True)
        ns.mkdir(ns_dir)


def create_lds_configs(sformat, geo, cpcodes, openapiObj, connectionDetails):
    '''Creates new LDS configurations for each cpcode

    Keyword Arguments:
    sformat -- string provided by user indicating streaming format
    geo -- string provided by user indicating service geo
    cpcodes -- list of cpcodes provided by user
    openapiObj -- dictionary containing baseurl and signed http request object
    connectionDetails -- ConfigParser object containing NS auth details
    '''
    for cpcode in cpcodes:
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

        result = openapiObj['request'].post(urljoin(openapiObj['baseurl'], '/lds/v1/configurations'),
                                            data=json.dumps(lds_payload),
                                            headers={'Accept': '*/*', 'Content-Type': 'application/json'})

        if result.status_code == 200:
            print('LDS successfully created for CPCode: {0}'.format(cpcode), flush=True)
        else:
            print('LDS creation FAILED for CPCode: {0}'.format(cpcode), flush=True)
            print(result.text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='ALDA - Amazon Log Delivery Service Automation'
    )
    parser.add_argument('--format', required=True,
                        choices=['assets', 'dash', 'download', 'hls', 'mp4',
                                 'ott', 'smooth', 'videoads'],
                        help='Streaming format (determines NS file path)')
    parser.add_argument('--geo', required=True,
                        choices=['eu', 'in', 'jp', 'row', 'us'],
                        help='Geo (determines NS file path AND\
                        Luna account for LDS enablement)')
    parser.add_argument('--cpcodes', required=True, nargs='*',
                        help='List of CPCodes for LDS enablement.\
                        Takes comma or space separated list.')

    args = parser.parse_args()
    main(args)
