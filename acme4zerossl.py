# -*- coding: utf-8 -*-
import logging
import datetime
import json
import requests
import subprocess
import time

# For error handling, logfile config
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
# Error logfile name and level config
logging.basicConfig(level = logging.WARNING,
                    filename = "acme4zerossl.error.log",
                    filemode = "a", format = FORMAT)
# TestPass_25J08

# Generate timestamp
def GetTime():
    CurrentTime = datetime.datetime.now()
    return CurrentTime.strftime("%Y-%m-%d %H:%M:%S")
# TestPass_25J10

# Configuration function
def Configuration(ConfigPath = ()):
    # Reading configuration file only
    try:
        with open(ConfigPath,"r") as ConfigurationJSON:
            # Return dictionary
            ConfigurationDict = json.load(ConfigurationJSON)
            ConfigurationJSON.close()
            return ConfigurationDict
        # If configuration file not found
    except FileNotFoundError:
        logging.exception(f"No such configuration file or directory: {ConfigPath}")
        return False
# TestPass_25J08

# Sending telegram message via bots
def SendAlert(ConfigPath = (), MessagePayload = ()):
    # Load configuration
    MessageConfig = Configuration(ConfigPath)
    TelegramBotToken = MessageConfig["Telegram_BOTs"]["TelegramToken"]
    TelegramReceiver = MessageConfig["Telegram_BOTs"]["TelegramChatID"]
    # Check telegram BOTs configuration
    if len(TelegramBotToken) == 0 or len(TelegramReceiver) == 0:
        return ("Telegram configuration not found, please initialize.")
    # Find configuration
    else:
        # Make telegram url
        TelegramBotURL = (f"https://api.telegram.org/bot{TelegramBotToken}/sendMessage")
        TelegramJsonPayload = {"chat_id": TelegramReceiver, "text": MessagePayload}
        # Sending telegram 
        try:
            TelegramResponse = requests.post(TelegramBotURL,json=TelegramJsonPayload)
            if TelegramResponse.status_code == 200:
                TelegramResponse.close()
                return 200
            # Chat channel wasn't create
            elif TelegramResponse.status_code == 400:
                TelegramResponse.close()
                return ("Chat channel wasn't create.")
            # Other error
            elif TelegramResponse.status_code != 200 or 400:
                TelegramResponse.close()
                return (f"Telegram API respons: {TelegramResponse.status_code}")
        except Exception as ErrorStatus:
            logging.exception(ErrorStatus)
            return False
#

# Generate Cloudflare API request header
def CloudflareApiRequestHeader(ConfigPath = ()):
    # Read configuration
    ConfigurationDict = Configuration(ConfigPath)
    # Header Payload
    CloudflareAptAuth = ConfigurationDict["CloudflareAPI"]["AuthToken"]
    CloudflareAuthMail = ConfigurationDict["CloudflareAPI"]["AuthMail"]
    # Using API Token as default
    return {"Authorization":f"Bearer {CloudflareAptAuth}", "X-Auth-Email":CloudflareAuthMail, "Content-Type":"application/json"}
# TestPass_25J08

# Verify CloudFlare API
def VerifyCloudflareApi(ConfigPath = (), CloudflareApiResponAll = (None)):
    # Verify URL
    CloudflareVerifyRequest = ("https://api.cloudflare.com/client/v4/user/tokens/verify")
    # Header
    CloudflareTokenVerifyHeader = CloudflareApiRequestHeader(ConfigPath)
    # Send verify request
    try:
        CloudflareVerifyRespon = requests.get(CloudflareVerifyRequest, headers=CloudflareTokenVerifyHeader, timeout=5)
        # Success, only retrun verify status
        if CloudflareVerifyRespon.status_code == 200 and CloudflareApiResponAll is None:
            CloudflareVerifyResponDict = json.loads(CloudflareVerifyRespon.text)
            CloudflareVerifyRespon.close()
            return CloudflareVerifyResponDict["result"]["status"]
        # Success, return full payload
        elif CloudflareVerifyRespon.status_code == 200 and CloudflareApiResponAll is not None:
            VerifyResponDict = json.loads(CloudflareVerifyRespon.text)
            CloudflareVerifyRespon.close()
            return VerifyResponDict
        # Unsuccess
        elif CloudflareVerifyRespon.status_code != 200: 
            logging.warning(CloudflareVerifyRespon.status_code)
            return CloudflareVerifyRespon.status_code
    except Exception as ErrorStatus:
        logging.exception(ErrorStatus)
        return False
# TestPass_25J08

# Get All DNS records, RunnableCheckPass
def CloudflareRequestDnsRecordAll(ConfigPath = (), OutputJsonFile = (None)):
    # Load configuration
    ZoneDict = Configuration(ConfigPath)
    # Get Zone IDs
    ZoneID = ZoneDict["CloudflareZone"]["ZoneID"]
    # URL
    CloudflareDnsRecordRequest = (f"https://api.cloudflare.com/client/v4/zones/{ZoneID}/dns_records")
    # Header
    CloudflareRequestVerifyHeader = CloudflareApiRequestHeader(ConfigPath)
    # Send DNS record request
    try:
        FullyDnsRecordRespon = requests.get(CloudflareDnsRecordRequest, headers=CloudflareRequestVerifyHeader, timeout=5)
        if FullyDnsRecordRespon.status_code != 200:
            logging.warning(FullyDnsRecordRespon.status_code)
            FullyDnsRecordRespon.close()
            return FullyDnsRecordRespon.status_code
        # Success, retrun dictionary
        elif FullyDnsRecordRespon.status_code == 200 and OutputJsonFile is None:
            FullyDnsRecordResponDict = json.loads(FullyDnsRecordRespon.text)
            FullyDnsRecordRespon.close()
            return FullyDnsRecordResponDict
        # Success, save JSON file
        elif FullyDnsRecordRespon.status_code == 200 and OutputJsonFile is not None:
            FullyDnsRecordResponDict = json.loads(FullyDnsRecordRespon.text)
            FullyDnsRecordRespon.close()
            with open(OutputJsonFile,"w") as DNSRecordJSON:
                json.dump(FullyDnsRecordResponDict, DNSRecordJSON, indent=3)
                DNSRecordJSON.close()
                return [FullyDnsRecordResponDict, OutputJsonFile]
    except Exception as ErrorStatus:
        logging.exception(ErrorStatus)
        return False
# TestPass_25J08

# Update DNS CNAME records
def CloudflareUpdateSpecifyCname(ConfigPath = (), UpdateDnsRecordCname =()):
    # Load configuration
    RecordDict = Configuration(ConfigPath)
    # Zone and RecordsID configuration
    ZoneID = RecordDict["CloudflareZone"]["ZoneID"]
    RecordsID = UpdateDnsRecordCname[0]
    RecordNAME = UpdateDnsRecordCname[1]
    RecordTarget = UpdateDnsRecordCname[2]
    # Cloudflare API URL
    CloudflareCnameUpdate = (f"https://api.cloudflare.com/client/v4/zones/{ZoneID}/dns_records/{RecordsID}")
    # Payload dictionary
    UpdateSpecifyCnameDict = {
        "type": "CNAME",
        "name": RecordNAME,
        "content": RecordTarget,
        "proxiable": False,
        "proxied": False,
        "ttl": 1}
    # Turn into JSON payload
    UpdateCnameJson = json.dumps(UpdateSpecifyCnameDict)
    # Header
    CnameUpdateVerifyHeader = CloudflareApiRequestHeader(ConfigPath)
    # HTTP PUT
    try:
        CnameUpdateRequest = requests.put(CloudflareCnameUpdate, headers=CnameUpdateVerifyHeader, data=UpdateCnameJson, timeout=5)
        CnameUpdateRespon = json.loads(CnameUpdateRequest.text)
        CnameUpdateRequest.close()
        return CnameUpdateRespon
    except Exception as ErrorStatus:
        logging.exception(ErrorStatus)
        return False
#

# Get ZeroSSL REST API Key
def ZeroSSLAPIKey(ConfigPath = ()):
    # Read configuration
    ConfigurationDict = Configuration(ConfigPath)
    # Using API Token as default
    return ConfigurationDict["ZeroSSLAPI"]["AccessKey"]
# TestPass_25J08

# Create certificates signing request
def CreateCertSigningRequest(ConfigPath = ()):
    # Read configuration
    ConfigurationDict = Configuration(ConfigPath)
    # Check domain numbers
    DomainList = ConfigurationDict["ZeroSSLDomains"]["Domains"]
    # If dual domains, ex: www.example.com & example.com
    if len(DomainList) == 2:
        CsrConfig = f"""[req]
default_bits = 2048
prompt = no
encrypt_key = no
default_md = sha256
utf8 = yes
string_mask = utf8only
x509_extensions = x509_v3_req
distinguished_name = req_distinguished_name
[x509_v3_req]
subjectAltName = @alt_names
[alt_names]
DNS.1 = {DomainList[0]}
DNS.2 = {DomainList[1]}
[req_distinguished_name]
countryName = TW
stateOrProvinceName = Taiwan
localityName = Taipei City
organizationName = NonProfit
organizationalUnitName = PersonalUse
commonName = {DomainList[0]}
"""
    # Single domain
    else:
        CsrConfig = f"""[req]
default_bits = 2048
prompt = no
encrypt_key = no
default_md = sha256
utf8 = yes
string_mask = utf8only
x509_extensions = x509_v3_req
distinguished_name = req_distinguished_name
[x509_v3_req]
subjectAltName = @alt_names
[alt_names]
DNS.1 = {DomainList[0]}
[req_distinguished_name]
countryName = TW
stateOrProvinceName = Taiwan
localityName = Taipei City
organizationName = NonProfit
organizationalUnitName = PersonalUse
commonName = {DomainList[0]}
"""
    # Read config saving path
    CsrConfigPath = ConfigurationDict["Certificate"]["CertificateSigningRequestConfigPath"]
    # Certificates signing request config save
    with open(CsrConfigPath,"w+") as CsrConfigWrite:
        CsrConfigWrite.write(CsrConfig)
        CsrConfigWrite.close()
    # Certificates signing request saving
    CertificateSigningRequest = ConfigurationDict["Certificate"]["CertificateSigningRequestPath"]
    # Pending active private key
    PendingKey = ConfigurationDict["Certificate"]["PendingPrivateKeyPath"]
    # Openssl command
    Opensslcommand = ["openssl", "req", "-new",
                      "-keyout", f"{PendingKey}",
                      "-out", f"{CertificateSigningRequest}",
                      "-config", f"{CsrConfigPath}"]
    # Using OpenSSL generate CSR and PK
    try:
        subprocess.Popen(Opensslcommand, stdout=subprocess.PIPE)
        time.sleep(5)
        return CertificateSigningRequest
    except Exception as ErrorStatus:
        logging.exception(ErrorStatus)
# TestPass_25J11

#def ZeroSSLAPI(ConfigPath=(), CertificateUUID):
#    ZeroSSLConfigPath = Configuration(ConfigPath)
#    ZeroSSLAPIKey = ZeroSSLConfigPath["ZeroSSLAPI"]["AccessKey"]
#    # API URL
#    VerificationURL = (f"https://api.zerossl.com/certificates/{CertificateUUID}/status?access_key={ZeroSSLAPIKey}")  
#    # HTTP
#    HeaderSet = {"Content-Type":"application/json"}
#    try:
#        RESTStatusRequest = requests.get(VerificationURL,headers=HeaderSet,timeout=5)
#        RESTStatusRespon = json.loads(RESTStatusRequest.text)
#        RESTStatusRequest.close()
#        return RESTStatusRespon
#    # Error
#    except Exception as ErrorStatus:
#        logging.exception(ErrorStatus)
#        print(ErrorStatus)
