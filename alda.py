#!/usr/bin/env python

import sys
from akamai.netstorage import Netstorage
import requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from urllib.parse import urljoin
import json


def main(argv):
    sformat = argv[1]
    geo = argv[2]
    if not argv[3].endswith(","):
        cpcodes = argv[3].split(',')
    else:
        Help("ERROR: CPCode list format invalid")
        return
    # Check if format is valid
    if not check_format(sformat):
        Help("ERROR: Invalid Format specified. Valid values: assets, dash, "
             "download, hls, mp4, ott, smooth, videoads")
        return
    # Check if geo is valid
    if not check_geo(geo):
        Help("ERROR: Invalid geo specified. Valid values: eu, in, jp, row, us")
        return
    # Get List of LDS Configurations
    print("Retreiving LDS configs", flush=True)
    ldsObj = get_lds_configs()
    ldsConfigs = ldsObj['contents']
    # Remove cpcodes with ACTIVE LDS configurations and warn user
    print("Checking cpcode list against active configs", flush=True)
    inactiveCpcodes = check_cpcodes(ldsConfigs, cpcodes)
    # We now have a valid list of cpcodes to provision.
    # Connect to NetStorage and create storage locations
    print("Connecting to NetStorage", flush=True)
    connectionDetails = get_netstorage_credentials("alda.netstorage")
    create_netstorage_paths(sformat, geo, inactiveCpcodes, connectionDetails)
    # Create LDS Configurations
    print("Creating LDS configs")
    create_lds_configs(sformat, geo, inactiveCpcodes, connectionDetails)


def Help(errorHelp):
    print(errorHelp)
    print("Usage: alda.py format geo cpcode1,cpcode2,cpcode3")


def check_format(sformat):
    return sformat.lower() in ("assets", "dash", "download", "hls", "mp4",
                               "ott", "smooth", "videoads")


def check_geo(geo):
    return geo.lower() in ("eu", "in", "jp", "row", "us")


def get_lds_configs():
    edgerc = EdgeRc('alda.edgerc')
    section = 'C-14QDNW3'
    baseurl = 'https://{0}'.format(edgerc.get(section, 'host'))
    s = requests.Session()
    s.auth = EdgeGridAuth.from_edgerc(edgerc, section)
    result = s.get(urljoin(baseurl, '/lds/v1/configurations'))
    return result.json()


def check_cpcodes(ldsConfigs, cpcodes):
    for config in range(len(ldsConfigs)):
        cpcode = ldsConfigs[config]['cpCode']['dictId']
        cpcode_name = ldsConfigs[config]['cpCode']['dictValue']
        status = ldsConfigs[config]['status']
        if cpcode in cpcodes and status == 'ACTIVE':
            cpcodes.remove(cpcode)
            print("CPCode '{0} - {1}' has an active LDS configuration. "
                  "Please manually review.".format(cpcode, cpcode_name))
    return cpcodes


def create_netstorage_paths(sformat, geo, cpcodes, connectionDetails):
    for cpcode in cpcodes:
        file_path = "logdelivery/{0}/{1}/{2}".format(sformat, geo, cpcode)
        ns = Netstorage(connectionDetails['hostname'],
                        connectionDetails['kname'],
                        connectionDetails['key'], ssl=True)
        ns_dir = '/' + connectionDetails['cpcode'] + '/' + file_path
        print("Creating {0}".format(ns_dir))
        ns.mkdir(ns_dir)


def get_netstorage_credentials(configFile):
    credentials = {}
    with open(configFile, 'r') as f:
        while True:
            read_data = f.readline()
            if "Key-name" in read_data:
                credentials.setdefault('kname', read_data.split(':')[1].rstrip())
            elif "Key" in read_data:
                credentials.setdefault('key', read_data.split(':')[1].rstrip())
            elif "Hostname" in read_data:
                credentials.setdefault('hostname', read_data.split(':')[1].rstrip())
            elif "Cpcode" in read_data:
                credentials.setdefault('cpcode', read_data.split(':')[1].rstrip())
            elif "Password" in read_data:
                credentials.setdefault('password', read_data.split(':')[1].rstrip())
            elif read_data == "":
                break
    f.closed
    return credentials


def create_lds_configs(sformat, geo, cpcodes, connectionDetails):
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
                "contactEmail": ["nibenson@amazon.com"],
                "dictId": "B-C-PNOHOD"
            }
        }''')
        lds_payload['acgObject']['id'] = cpcode
        lds_payload['logIdentifier'] = cpcode
        lds_payload['ftpConfiguration']['directory'] =\
            "/{0}/logdelivery/{1}/{2}/{3}".format(
            connectionDetails['cpcode'], sformat, geo, cpcode)
        lds_payload['ftpConfiguration']['password'] = connectionDetails['password']
        edgerc = EdgeRc('alda.edgerc')
        section = 'C-14QDNW3'
        baseurl = 'https://{0}'.format(edgerc.get(section, 'host'))
        s = requests.Session()
        s.auth = EdgeGridAuth.from_edgerc(edgerc, section)
        result = s.post(urljoin(baseurl, '/lds/v1/configurations'), data=json.dumps(lds_payload), headers={'Accept': '*/*', 'Content-Type': 'application/json'})
        print(result.text)


if __name__ == "__main__":
    if len(sys.argv) >= 4:
        main(sys.argv)
    else:
        Help("ERROR: Missing argument(s)")
