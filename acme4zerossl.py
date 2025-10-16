# -*- coding: utf-8 -*-
import logging
import json
import requests
import subprocess
from time import sleep

# Uniform Resource Locator
class URL():
    def __init__(self):
        self.Cloudflare = "https://api.cloudflare.com/client/v4/"
        self.Telegram = "https://api.telegram.org/bot"
        self.ZeroSSL = "https://api.zerossl.com/certificates"
# Certificate Signing Request
class CSRConfigSingle():
    def __init__(self, CommonName):
        self.CSRconfig = f"""[req]
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
DNS.1 = {CommonName}
[req_distinguished_name]
countryName = TW
stateOrProvinceName = Taiwan
localityName = Taipei City
organizationName = NonProfit
organizationalUnitName = PersonalUse
commonName = {CommonName}
"""
# Certificate Signing Request
class CSRConfigMulti():
    def __init__(self, CommonName, AltName):
        self.CSRconfig = f"""[req]
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
DNS.1 = {CommonName}
DNS.2 = {AltName}
[req_distinguished_name]
countryName = TW
stateOrProvinceName = Taiwan
localityName = Taipei City
organizationName = NonProfit
organizationalUnitName = PersonalUse
commonName = {CommonName}
"""
# Configuration function, reading json file
class Configuration():
    def __init__(self, ConfigFilePath):
        try:
            with open(ConfigFilePath, "r", encoding = "utf-8") as ConfigFile:
                ConfigData = json.load(ConfigFile)
                ConfigFile.close()
        # If configuration file not found
        except FileNotFoundError:
            raise(f"No such configuration file or directory: {ConfigFilePath}")
        # Format error 
        except Exception as ConfigurationError:
            raise ConfigurationError
        self.Load = ConfigData
# TestPass_25J16

# For error handling, logfile config
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
# Error logfile name and level config
logging.basicConfig(
    level = logging.WARNING, filename = "acme4zerossl.error.log", filemode = "a", format = FORMAT)
# TestPass_25J08

# Generate Cloudflare API request header
def CFApiHeader(ConfigFilePath):
    CFConfig = Configuration(ConfigFilePath)
    CFHeader = {"Authorization": f"Bearer {CFConfig.Load["CloudflareAPI"]["Token"]}",
                "X-Auth-Email": f"{CFConfig.Load["CloudflareAPI"]["Mail"]}",
                "Content-Type": "application/json"}
    return CFHeader
# TestPass_25J16

# Sending telegram message via bots
def Telegram2Me(ConfigFilePath, TelegramMessage = ("Here, the world!")):
    TGConfig = Configuration(ConfigFilePath)
    Connect = URL()
    TelegramMsgURL = (Connect.Telegram + f"{TGConfig.Load["Telegram_BOTs"]["Token"]}/sendMessage")
    TelegramMsg = {"chat_id": f"{TGConfig.Load["Telegram_BOTs"]["ChatID"]}", "text": TelegramMessage}
    # Sending 
    try:
        TelegramResponse = requests.post(TelegramMsgURL, json=TelegramMsg, timeout=10)
        if TelegramResponse.status_code == 200:
            TelegramResponse.close()
            return 200
        # Chat channel wasn't create
        elif TelegramResponse.status_code == 400:
            TelegramResponse.close()
            return ("Chat channel wasn't create.")
        else:
            TelegramResponse.close()
            return (f"Telegram API respons: {TelegramResponse.status_code}")
    except Exception as TelegramErrorStatus:
        logging.exception(TelegramErrorStatus)
        return False
# TestPass_25J16

# Verify Cloudflare API token
def VerifyCFToken(ConfigFilePath, DisplayVerifyResult = (None)):
    VerifyHeader = CFApiHeader(ConfigFilePath)
    Connect = URL()
    TokebVerifyURL = (Connect.Cloudflare + "user/tokens/verify")
    try:
        TokebVerifyResponse = requests.get(TokebVerifyURL, headers=VerifyHeader, timeout=10)
        # Only return verify result
        if TokebVerifyResponse.status_code == 200 and DisplayVerifyResult is None:
            TokebVerifyResponseData = json.loads(TokebVerifyResponse.text)
            TokebVerifyResponse.close()
            return TokebVerifyResponseData["result"]["status"]
        # Return all
        elif TokebVerifyResponse.status_code == 200 and DisplayVerifyResult is not None:
            TokebVerifyResponseData = json.loads(TokebVerifyResponse.text)
            TokebVerifyResponse.close()
            return TokebVerifyResponseData
        elif TokebVerifyResponse.status_code != 200: 
            logging.warning(TokebVerifyResponse.status_code)
            return TokebVerifyResponse.status_code
    except Exception as VerifyCFError:
        logging.exception(VerifyCFError)
        return False
# TestPass_25J16

# Download all DNS records from Cloudflare
def GetCFRecords(ConfigFilePath, FileOutput = (None)):
    CFConfig = Configuration(ConfigFilePath)
    # Verify URL and Header
    Connect = URL()
    GetRecords = (Connect.Cloudflare +
                  f"zones/{CFConfig.Load["CloudflareZone"]["ZoneID"]}/dns_records")
    VerifyHeader = CFApiHeader(ConfigFilePath)
    try:
        GetRecordsRespon = requests.get(GetRecords, headers=VerifyHeader, timeout=10)
        if GetRecordsRespon.status_code == 200 and FileOutput is None:
            GetRecordsData = json.loads(GetRecordsRespon.text)
            GetRecordsRespon.close()
            return GetRecordsData
        elif GetRecordsRespon.status_code == 200 and FileOutput is not None:
            GetRecordsData = json.loads(GetRecordsRespon.text)
            GetRecordsRespon.close()
            with open(FileOutput, "w+") as RecordsFile:
                json.dump(GetRecordsData, RecordsFile, indent = 3)
                GetRecordsRespon.close()
                return FileOutput
        elif GetRecordsRespon.status_code != 200:
            logging.warning(GetRecordsRespon.status_code)
            GetRecordsRespon.close()
            return GetRecordsRespon.status_code
    except Exception as GetCFRecordsError:
        logging.exception(GetCFRecordsError)
        return False
# TestPass_25J16

# Update CNAME records at Cloudflare
def UpdateCFCNAME(ConfigFilePath, UpdatePayload):
    CFConfig = Configuration(ConfigFilePath)
    # Records ID
    RecordsID = UpdatePayload[0]
    # Verify URL and Header
    Connect = URL()
    UpdateCNAME = (Connect.Cloudflare +
                   f"zones/{CFConfig.Load["CloudflareZone"]["ZoneID"]}/dns_records/{RecordsID}")
    VerifyHeader = CFApiHeader(ConfigFilePath)
    # CNAME
    RecordsUpdateData = {"type": "CNAME",
                         "name": f"{UpdatePayload[1]}", "content": f"{UpdatePayload[2]}",
                         "proxiable": False, "proxied": False, "ttl": 1}
    RecordsJSON = json.dumps(RecordsUpdateData)
    # Update CNAME
    try:
        UpdateRespon = requests.put(UpdateCNAME, headers=VerifyHeader, data=RecordsJSON, timeout=10)
        if UpdateRespon.status_code == 200:
            UpdateResponData = json.loads(UpdateRespon.text)
            UpdateRespon.close()
            return UpdateResponData
        elif UpdateRespon.status_code != 200:
            logging.warning(UpdateRespon.status_code)
            UpdateRespon.close()
            return UpdateRespon.status_code
    except Exception as UpdateCNAMEError:
        logging.exception(UpdateCNAMEError)
        return False
# TestPass_25J16

# Create certificates signing request
def CreateCSR(ConfigFilePath):
    CSRFileConfig = Configuration(ConfigFilePath)
    # load domains and check
    DomainList = CSRFileConfig.Load["Certificate"]["Domains"]
    CommonName = DomainList[0]
    # Single domains, ex: www.example.com
    if len(DomainList) == 1:
        CreateCSRConfig = CSRConfigSingle(CommonName)
        CSRConfigText = CreateCSRConfig.CSRconfig
    # Multiple domains, ex: www.example.com & example.com
    elif len(DomainList) == 2:
        AltName = DomainList[1]
        CreateCSRConfig = CSRConfigMulti(CommonName, AltName)
        CSRConfigText = CreateCSRConfig.CSRconfig
    # CSR Config path
    CSRConfigPath = CSRFileConfig.Load["Certificate"]["Config"]
    with open(CSRConfigPath, "w") as CSRSignConfig:
        CSRSignConfig.writelines(CSRConfigText)
        CSRSignConfig.close()
    # CSR and pending PK path
    CSRFile = CSRFileConfig.Load["Certificate"]["CSR"]
    PendingPK = CSRFileConfig.Load["Certificate"]["PendingPK"]
    # OpenSSL generate command
    OpensslCommand = ["openssl", "req", "-new",
                      "-keyout", f"{PendingPK}", "-out", f"{CSRFile}",
                      "-config", f"{CSRConfigPath}"]
    try:
        # Using OpenSSL generate CSR and PK
        subprocess.Popen(OpensslCommand, stdout = subprocess.PIPE)
        sleep(5)
        return 200
    except Exception as CreateCSRError:
        logging.exception(CreateCSRError)
        return False
# TestPass_25J16

# Sending certificate create request
def ZeroSSLCreateCA(ConfigFilePath):
    CreateCAConfig = Configuration(ConfigFilePath)
    ZeroSSLAuth = CreateCAConfig["ZeroSSLAPI"]["AccessKey"]
    # Read Certificates signing request
    CSRFile = CreateCAConfig.Load["Certificate"]["CSR"]
    with open(CSRFile, "r") as CSRFileData:
        CSRPayload = CSRFileData.read().replace("\n","")
        CSRFileData.close()
    # Reading domain
    DList = CreateCAConfig.Load["Certificate"]["Domains"]
    if len(DList) == 2:
        CreatePayload = {
            "certificate_domains": f"{DList[0]},{DList[1]}", "certificate_validity_days": 90,
            "certificate_csr": CSRPayload}
    else:
        CreatePayload = {
            "certificate_domains": f"{DList[0]}", "certificate_validity_days": 90,
            "certificate_csr": CSRPayload}
    CreateJSON = json.dumps(CreatePayload)
    # Create CA URL and Header
    Connect = URL()
    CreateCA = (Connect.ZeroSSL + f"?access_key={ZeroSSLAuth}")
    CreateHeader = {"Content-Type": "application/json"}
    # Sending create CA request to ZeroSSL
    try:
        CreateCARespon = requests.post(CreateCA, headers=CreateHeader, data=CreateJSON, timeout=10)
        if CreateCARespon.status_code == 200:
            ResultData = json.loads(CreateCARespon.text)
            CreateCARespon.close()
            # Saving validation data
            ValidationCacheFile = CreateCAConfig.Load["ZeroSSLAPI"]["Cache"]
            with open(ValidationCacheFile, "w+") as ValidationData:
                json.dump(ResultData, ValidationData, indent = 4)
                ValidationData.close()
            return ResultData
        elif CreateCARespon.status_code != 200:
            logging.warning(CreateCARespon.status_code)
            CreateCARespon.close()
            return CreateCARespon.status_code
    except Exception as ErrorStatus:
        logging.exception(ErrorStatus)
        return False
# UNTESTED

# Phrasing ZeroSSL verify JSON
def ZeroSSLVerifyData(VerifyRequest, Mode = ("CNAME")):
    VerifyCN = VerifyRequest["common_name"]
    # CNAME mode
    if Mode == "CNAME" and len(VerifyRequest["additional_domains"]) == 0:
        CAVerify = {
            "id": f"{VerifyRequest["id"]}",
            "common_name_cname": [
                VerifyRequest["validation"]["other_methods"][VerifyCN]["cname_validation_p1"],
                VerifyRequest["validation"]["other_methods"][VerifyCN]["cname_validation_p2"]]}
    elif Mode == "CNAME" and len(VerifyRequest["additional_domains"]) != 0:
        VerifyAD = VerifyRequest["additional_domains"]
        CAVerify = {
            "id": f"{VerifyRequest["id"]}",
            "common_name_cname": [
                VerifyRequest["validation"]["other_methods"][VerifyCN]["cname_validation_p1"],
                VerifyRequest["validation"]["other_methods"][VerifyCN]["cname_validation_p2"]],
            "additional_domains_cname": [
                VerifyRequest["validation"]["other_methods"][VerifyAD]["cname_validation_p1"],
                VerifyRequest["validation"]["other_methods"][VerifyAD]["cname_validation_p2"]]}
    return CAVerify
# TestPass_25J16, CNAME olny

# Verification, when using CNAME and HTTP/HTTPS file verify
def ZeroSSLVerification(ConfigFilePath, CertificateID, ValidationMethod = ("CNAME_CSR_HASH")):
    VerifyConfig = Configuration(ConfigFilePath)
    ZZeroSSLAuth = VerifyConfig["ZeroSSLAPI"]["AccessKey"]
    # Certificates id
    CertificatesID = CertificateID["id"]
    # Verification URL and verification method, default is CNAME
    Connect = URL()
    CAVerification = (Connect.ZeroSSL + f"/{CertificatesID}/challenges?access_key={ZZeroSSLAuth}")
    VerifyMethod = {"validation_method": ValidationMethod}
    try:
        # Sending verification request
        CAVerificationRespon = requests.post(CAVerification, data=VerifyMethod, timeout=10)
        if CAVerificationRespon.status_code == 200:
            CAVerificationData = json.loads(CAVerificationRespon.text)
            CAVerificationRespon.close()
            return CAVerificationData
        elif CAVerificationRespon.status_code != 200:
            logging.warning(CAVerificationRespon.status_code)
            CAVerificationRespon.close()
            return CAVerificationRespon.status_code
    except Exception as CAVerificationError:
        logging.exception(CAVerificationError)
        return False
# UNTESTED

# Download certificate from ZeroSSL
def ZeroSSLDownloadCA(ConfigFilePath, CertificateID):
    DownloadCAConfig = Configuration(ConfigFilePath)
    ZeroSSLAuth = DownloadCAConfig["ZeroSSLAPI"]["AccessKey"]
    # Create CA URL and Header
    Connect = URL()
    DownloadCA = (Connect.ZeroSSL + f"/{CertificateID}/download/return?access_key={ZeroSSLAuth}")
    DownloadCAHeader = {"Content-Type": "application/json"}
    try:
        # Sending download request
        DownloadCARespon = requests.get(DownloadCA, headers=DownloadCAHeader, timeout=10)
        if DownloadCARespon.status_code == 200:
            CertificateJSON = json.loads(DownloadCARespon.text)
            DownloadCARespon.close()
            if "certificate.crt" in CertificateJSON:
                return CertificateJSON
            elif "certificate.crt" not in CertificateJSON:
                DownloadCAError = CertificateJSON["error"]["type"]
            logging.exception(DownloadCAError)
            return False
    except Exception as DownloadCAError:
        logging.exception(DownloadCAError)
        return False
# UNTESTED

# Install certificate to server folder, reload is optional
def CertificateInstall(ConfigFilePath, CertificateContent, ServerCommand = (None)):
    InstallConfig = Configuration(ConfigFilePath)
    try:
        # Private key
        PKPending = InstallConfig["Certificate"]["PendingPK"]
        PKActive = InstallConfig["Certificate"]["PK"]
        with open(PKPending, "r") as PendingPrivateKey:
            with open(PKActive, "w+") as ActivePrivateKey:
                for PrivateKeyLine in PendingPrivateKey:
                    ActivePrivateKey.write(PrivateKeyLine)
                ActivePrivateKey.close()
            PendingPrivateKey.close()
        # Certificate
        Certificate = InstallConfig["Certificate"]["CA"]
        CAString = CertificateContent["certificate.crt"]
        with open(Certificate, "w+") as ActiveCertificate:
            ActiveCertificate.write(CAString)
            ActiveCertificate.close()
        # Save certificate authority bundle
        CertificateBA = InstallConfig["Certificate"]["CAB"]
        CABString = CertificateContent["ca_bundle.crt"]
        with open(CertificateBA, "w+") as ActiveCertificateBA:
            ActiveCertificateBA.write(CABString)
            ActiveCertificateBA.close()
        if ServerCommand is None:
            pass
        # Server reload or restart
        elif ServerCommand is not None:
            sleep(5)
            subprocess.Popen(ServerCommand, stdout = subprocess.PIPE)
            return 200
    except Exception as InstallError:
        logging.exception(InstallError)
        return False
# UNTESTED
