# ALDA - Amazon Log Delivery Automation
ALDA is a tool built for an Akamai Integrated Account Team (IAT) to manage delivery of logs from Akamai's HTTP/S networks to Akamai's NetStorage platform for later customer ingest.

## 3rd Party Library Installation
`pip install netstorageapi`  
`pip install edgegrid-python`  

## Configuration
ALDA looks for the following files in its working directory:
* alda.edgerc
* alda.netstorage

alda.edgerc follows Akamai's .edgerc format:

>[SECTION1]  
host = foo.luna.akamaiapis.net/  
client_token = foo  
client_secret = foo  
access_token = foo  
max_body = 131072  
[SECTION2]  
host = foo.luna.akamaiapis.net/  
client_token = foo  
client_secret = foo  
access_token = foo  
max_body = 131072  
[SECTION3]  
host = foo.luna.akamaiapis.net/  
client_token = foo  
client_secret = foo  
access_token = foo  
max_body = 131072  

alda.netstorage follows the following convention:

>[DEFAULT]  
Key-name = foo  
Key = foo  
Hostname = foo-nsu.akamaihd.net  
Cpcode = 123456  
Password = foo  

#Usage
`./alda.py --format dash --geo us --cpcodes 123456 123456`

#Tests
alda_test.py can be used in conjunction with pytest for regression testing after code extension/refactoring
