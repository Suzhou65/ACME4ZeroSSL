# -*- coding: utf-8 -*-
import logging
import json
import requests
import subprocess
from time import sleep

# For error handling, logfile config
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
# Error logfile name and level config
logging.basicConfig(level = logging.WARNING,
                    filename = "acme4zerossl.error.log",
                    filemode = "a", format = FORMAT)
# TestPass_25J08

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
        return None
# TestPass_25J08

# Sending telegram message via bots
def SendAlertViaTelegram(ConfigPath = (), MessagePayload = ()):
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
            TelegramResponse = requests.post(TelegramBotURL, json = TelegramJsonPayload, timeout = 5)
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
# TestPass_25J12

# Generate Cloudflare API request header
def CloudflareApiRequestHeader(ConfigPath = ()):
    # Read configuration
    ConfigurationDict = Configuration(ConfigPath)
    # Header Payload
    CloudflareAptAuth = ConfigurationDict["CloudflareAPI"]["AuthToken"]
    CloudflareAuthMail = ConfigurationDict["CloudflareAPI"]["AuthMail"]
    # Using API Token as default
    return {"Authorization": f"Bearer {CloudflareAptAuth}", "X-Auth-Email": CloudflareAuthMail, "Content-Type": "application/json"}
# TestPass_25J08

# Verify CloudFlare API
def VerifyCloudflareApi(ConfigPath = (), CloudflareApiResponAll = (None)):
    # Verify URL
    CloudflareVerifyRequest = ("https://api.cloudflare.com/client/v4/user/tokens/verify")
    # Header
    CloudflareTokenVerifyHeader = CloudflareApiRequestHeader(ConfigPath)
    # Send verify request
    try:
        CloudflareVerifyRespon = requests.get(CloudflareVerifyRequest, headers = CloudflareTokenVerifyHeader, timeout = 5)
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
        FullyDnsRecordRespon = requests.get(CloudflareDnsRecordRequest, headers = CloudflareRequestVerifyHeader, timeout = 5)
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
                json.dump(FullyDnsRecordResponDict, DNSRecordJSON, indent = 3)
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
    # Get CNAME records id via list
    RecordsID = UpdateDnsRecordCname[0]
    # CNANE and target config
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
        CnameUpdateRequest = requests.put(CloudflareCnameUpdate, headers = CnameUpdateVerifyHeader, data = UpdateCnameJson, timeout = 5)
        if CnameUpdateRequest.status_code == 200:
            CnameUpdateRespon = json.loads(CnameUpdateRequest.text)
            CnameUpdateRequest.close()
            return CnameUpdateRespon
        else:
            return CnameUpdateRequest.status_code
    except Exception as ErrorStatus:
        logging.exception(ErrorStatus)
        return False
# TestPass_25J13

# Create certificates signing request
def CreateCertSigningRequest(ConfigPath = ()):
    # Read configuration
    ConfigurationDict = Configuration(ConfigPath)
    # Check domain numbers
    DomainList = ConfigurationDict["ZeroSSLDomains"]["Domains"]
    # If multiple domains, ex: www.example.com & example.com
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
    OpensslCommand = ["openssl", "req", "-new",
                      "-keyout", f"{PendingKey}",
                      "-out", f"{CertificateSigningRequest}",
                      "-config", f"{CsrConfigPath}"]
    # Using OpenSSL generate CSR and PK
    try:
        subprocess.Popen(OpensslCommand, stdout = subprocess.PIPE)
        sleep(5)
        return CertificateSigningRequest
    except Exception as ErrorStatus:
        logging.exception(ErrorStatus)
        return False
# TestPass_25J11

# Sending certificate create request
def ZeroSSLCreateCertificate(ConfigPath = ()):
    # Read configuration
    ConfigurationDict = Configuration(ConfigPath)
    ZeroSSLApiAuth = ConfigurationDict["ZeroSSLAPI"]["AccessKey"]
    # Read Certificates signing request 
    CertificateSigningRequest = ConfigurationDict["Certificate"]["CertificateSigningRequestPath"]
    with open(CertificateSigningRequest, "r") as CertificateSigningRequestFile:
        CertificateSigningRequestPayload = CertificateSigningRequestFile.read().replace("\n","")
        CertificateSigningRequestFile.close()
    # Reading domain
    DomainList = ConfigurationDict["ZeroSSLDomains"]["Domains"]
    # Create payload, multiple domains
    if len(DomainList) == 2:
        CreateCertificatePayload = {
            "certificate_domains": f"{DomainList[0]},{DomainList[1]}",
            "certificate_validity_days": 90,
            "certificate_csr": CertificateSigningRequestPayload}
    # Single domain
    else:
        CreateCertificatePayload = {
            "certificate_domains": f"{DomainList[0]}",
            "certificate_validity_days": 90,
            "certificate_csr": CertificateSigningRequestPayload}
    CreateCertificateJson = json.dumps(CreateCertificatePayload)
    # Header disclose JSON
    CreateCertificateHeader = {"Content-Type": "application/json"}
    # Create certificat URL
    CreateCertificateUrl = (f"https://api.zerossl.com/certificates?access_key={ZeroSSLApiAuth}")
    try:
        # Sending create certificat request
        CreateCertificateRequest = requests.post(CreateCertificateUrl, headers = CreateCertificateHeader, data = CreateCertificateJson, timeout = 5)
        # Trun JSON into dict
        CreateCertificateResult = json.loads(CreateCertificateRequest.text)
        CreateCertificateRequest.close()
        # Svae validation cache
        CertificateCacheFile = ConfigurationDict["ZeroSSLAPI"]["VerifyCachePath"]
        with open(CertificateCacheFile,"w+") as CertificateValidationCache:
                json.dump(CreateCertificateResult, CertificateValidationCache, indent = 4)
                CertificateValidationCache.close()
        if len(CreateCertificateResult["additional_domains"]) == 0:
            CertificateValidation = {
                "id": CreateCertificateResult["id"],
                "Cname1": [
                    CreateCertificateResult["validation"]["other_methods"][f"{DomainList[0]}"]["cname_validation_p1"],
                    CreateCertificateResult["validation"]["other_methods"][f"{DomainList[0]}"]["cname_validation_p2"]]}
        else:
            CertificateValidation = {
                "Certificate": CreateCertificateResult["id"],
                "Cname1": [
                    CreateCertificateResult["validation"]["other_methods"][f"{DomainList[0]}"]["cname_validation_p1"],
                    CreateCertificateResult["validation"]["other_methods"][f"{DomainList[0]}"]["cname_validation_p2"]],
                "Cname2": [
                    CreateCertificateResult["validation"]["other_methods"][f"{DomainList[1]}"]["cname_validation_p1"],
                    CreateCertificateResult["validation"]["other_methods"][f"{DomainList[1]}"]["cname_validation_p2"]]}
        return CertificateValidation
    except Exception as ErrorStatus:
        logging.exception(ErrorStatus)
        return False
# TestPass_25J13, Single domain only

# Verification, when using CNAME and HTTP/HTTPS file verify
def ZeroSSLVerification(ConfigPath = (), ValidationMethod = (), CertificateValidation = ()):
    # Read configuration
    ConfigurationDict = Configuration(ConfigPath)
    ZeroSSLApiAuth = ConfigurationDict["ZeroSSLAPI"]["AccessKey"]
    # Certificates id
    CertificatesID = CertificateValidation["id"]
    # Verification method, choice CNAME
    VerificationMethod = {"validation_method": ValidationMethod}
    # Verification URL
    CertificateVerificationUrl = (f"https://api.zerossl.com/certificates/{CertificatesID}/challenges?access_key={ZeroSSLApiAuth}")
    try:
        # Sending verification request
        VerificationRequest = requests.post(CertificateVerificationUrl, data = VerificationMethod, timeout = 5)
        # Trun JSON into dict
        VerificationResult = json.loads(VerificationRequest.text)
        VerificationRequest.close()
        return VerificationResult
    except Exception as ErrorStatus:
        logging.exception(ErrorStatus)
        return False
# TestPass_25J13

# Download certificate from ZeroSSL
def ZeroSSLDownloadCertificate(ConfigPath = (), CertificateValidation = ()):
    # Read configuration
    ConfigurationDict = Configuration(ConfigPath)
    ZeroSSLApiAuth = ConfigurationDict["ZeroSSLAPI"]["AccessKey"]
    # Certificates id
    CertificatesID = CertificateValidation["id"]
    # Header disclose JSON
    CertificateDownloadHeader = {"Content-Type": "application/json"}
    CertificateDownloadUrl = (f"https://api.zerossl.com/certificates/{CertificatesID}/download/return?access_key={ZeroSSLApiAuth}")
    try:
        # Sending download request
        CertificateDownloadRespon = requests.get(CertificateDownloadUrl, headers = CertificateDownloadHeader, timeout = 5)
        # Trun JSON into dict
        CertificateDownloadResult = json.loads(CertificateDownloadRespon.text)
        CertificateDownloadRespon.close()
        if "certificate.crt" in CertificateDownloadResult:
            return CertificateDownloadResult
        else:
            ErrorStatus = CertificateDownloadResult["error"]["type"]
            logging.exception(ErrorStatus)
            return False
    except Exception as ErrorStatus:
        logging.exception(ErrorStatus)
        return False
# UNTESTED

# Install certificate to server folder
def CertificateInstallation(ConfigPath = (), CertificatePayload = (), ServerReloadCommand = ()):
    # Read configuration, get file path
    ConfigurationDict = Configuration(ConfigPath)
    PrivateKeyCache = ConfigurationDict["Certificate"]["PendingPrivateKeyPath"]
    PrivateKey = ConfigurationDict["Certificate"]["PrivateKeyPenPath"]
    Certificate = ConfigurationDict["Certificate"]["CertificatePath"]
    CertificateBA = ConfigurationDict["Certificate"]["CertificateAuthorityBundlePath"]
    try:
        # Save private key
        with open(PrivateKeyCache, "r") as PendingPrivateKey:
            with open(PrivateKey, "w+") as ActivePrivateKey:
                for PrivateKeyLine in PendingPrivateKey:
                    ActivePrivateKey.write(PrivateKeyLine)
                ActivePrivateKey.close()
            PendingPrivateKey.close()
        # Save certificate
        CertificateContent = CertificatePayload["certificate.crt"]
        with open(Certificate, "w+") as ActiveCertificate:
            ActiveCertificate.write(CertificateContent)
            ActiveCertificate.close()
        # Save certificate authority bundle
        CertificateAuthorityBundleContent = CertificatePayload["ca_bundle.crt"]
        with open(CertificateBA, "w+") as ActiveCertificateBA:
            ActiveCertificateBA.write(CertificateAuthorityBundleContent)
            ActiveCertificateBA.close()
            sleep(5)
            # Reload server
            subprocess.Popen(ServerReloadCommand, stdout = subprocess.PIPE)
        return 200
    except Exception as ErrorStatus:
        logging.exception(ErrorStatus)
        return False
# UNTESTED
