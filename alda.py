#!/usr/bin/env python

import sys
# from akamai.netstorage import Netstorage
import requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from urllib.parse import urljoin


def main(argv):
    sformat = argv[1]
    geo = argv[2]
    if not argv[3].endswith(","):
        cpcodes = argv[3].split(',')
    else:
        Help("ERROR: CPCode list ends with ',' please remove spaces in list")
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
    ldsObj = get_lds_configs()
    ldsConfigs = ldsObj['contents']
    # Remove cpcodes with ACTIVE LDS configurations and warn user
    inactiveCpcodes = check_cpcodes(ldsConfigs, cpcodes)
    #


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

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        main(sys.argv)
    else:
        Help("ERROR: Missing argument(s)")
