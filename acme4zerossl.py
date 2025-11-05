# -*- coding: utf-8 -*-
from pathlib import Path
import json
import logging
import requests
import subprocess
from time import sleep
import datetime

# Uniform Resource Locator
class URL():
    def __init__(self):
        self.Cloudflare = "https://api.cloudflare.com/client/v4/"
        self.Telegram = "https://api.telegram.org/bot"
        self.ZeroSSL = "https://api.zerossl.com/certificates"

# Certificate Signing Request
class CSRConfigSingle():
    def __init__(self, CommonName, Country, State, Loc, Org, OrgUnit):
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
countryName = {Country}
stateOrProvinceName = {State}
localityName = {Loc}
organizationName = {Org}
organizationalUnitName = {OrgUnit}
commonName = {CommonName}
"""

# Certificate Signing Request
class CSRConfigMulti():
    def __init__(self, CommonName, AltName, Country, State, Loc, Org, OrgUnit):
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
countryName = {Country}
stateOrProvinceName = {State}
localityName = {Loc}
organizationName = {Org}
organizationalUnitName = {OrgUnit}
commonName = {CommonName}
"""

# Configuration function, reading json file
class Configuration():
    def __init__(self, ConfigFilePath):
        try:
            ConfigInput = Path(ConfigFilePath)
            with ConfigInput.open("r", encoding = "utf-8") as ConfigFile:
                ConfigData = json.load(ConfigFile)
        # Error
        except Exception as ConfigurationError:
            raise Exception(ConfigurationError)
        self.Load = ConfigData
# TestPass_25J20

# For error handling, logfile config
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
logging.basicConfig(
    level=logging.WARNING, filename="error.acme4zerossl.log", filemode="a", format=FORMAT)
# TestPass_25J08

# Print runtime info
def RuntimeMessage(MessageText):
    EventTime = datetime.datetime.now()
    TextPrintTime = EventTime.strftime("%H:%M:%S")
    print(f"{TextPrintTime} | {MessageText}")
# TestPass_25J26

# Sending Telegram message, set default message for testing
def Telegram2Me(ConfigFilePath, TelegramMessage = ('Here, the world!')):
    # Load config
    TGConfig = Configuration(ConfigFilePath)
    # Connetc URL
    Connect = URL()
    TGMsgURL = (Connect.Telegram + f"{TGConfig.Load['Telegram_BOTs']['Token']}/sendMessage")
    # Text content
    TGMsgText = (f"{TGConfig.Load['Certificate']['Domains'][0]}\n" + TelegramMessage)
    TGMsg = {"chat_id": f"{TGConfig.Load['Telegram_BOTs']['ChatID']}", "text": TGMsgText}
    try:
        TelegramResponse = requests.post(TGMsgURL, json=TGMsg, timeout=30)
        if TelegramResponse.status_code == 200:
            TelegramResponse.close()
            RuntimeMessage(MessageText=TelegramMessage)
        else:
            TelegramResponse.close()
            logging.exception(TelegramResponse.status_code)
    except Exception as TelegramErrorStatus:
        logging.exception(TelegramErrorStatus)
# TestPass_25J20

# Generate Cloudflare API request header
def CFApiHeader(ConfigFilePath):
    # Load config
    CFConfig = Configuration(ConfigFilePath)
    # Generate header including auth token and mail
    CFHeader = {"Authorization": f"Bearer {CFConfig.Load['CloudflareAPI']['Token']}",
                "X-Auth-Email": f"{CFConfig.Load['CloudflareAPI']['Mail']}",
                "Content-Type": "application/json"}
    return CFHeader
# TestPass_25J20

# Verify Cloudflare API token
def VerifyCFToken(ConfigFilePath, DisplayVerifyResult = (None)):
    # Load config
    VerifyHeader = CFApiHeader(ConfigFilePath)
    # Connect URL
    Connect = URL()
    TokebVerifyURL = (Connect.Cloudflare + "user/tokens/verify")
    try:
        TokebVerifyResponse = requests.get(TokebVerifyURL, headers=VerifyHeader, timeout=30)
        # Only return verify result
        if TokebVerifyResponse.status_code == 200 and DisplayVerifyResult is None:
            TokebVerifyResponseData = json.loads(TokebVerifyResponse.text)
            TokebVerifyResponse.close()
            return TokebVerifyResponseData['result']['status']
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
# TestPass_25J19

# Download all DNS records from Cloudflare
def GetCFRecords(ConfigFilePath, FileOutput = (None)):
    CFConfig = Configuration(ConfigFilePath)
    Connect = URL()
    GetRecords = (Connect.Cloudflare +
                  f"zones/{CFConfig.Load['CloudflareRecords']['ZoneID']}/dns_records")
    # Auth header
    VerifyHeader = CFApiHeader(ConfigFilePath)
    try:
        GetRecordsRespon = requests.get(GetRecords, headers=VerifyHeader, timeout=30)
        if GetRecordsRespon.status_code == 200 and FileOutput is None:
            GetRecordsData = json.loads(GetRecordsRespon.text)
            GetRecordsRespon.close()
            return GetRecordsData
        elif GetRecordsRespon.status_code == 200 and FileOutput is not None:
            GetRecordsData = json.loads(GetRecordsRespon.text)
            GetRecordsRespon.close()
            OutPath = Path(FileOutput)            
            with OutPath.open("w") as RecordsFile:
                json.dump(GetRecordsData, RecordsFile, indent = 3)
            return FileOutput
        elif GetRecordsRespon.status_code != 200:
            logging.warning(GetRecordsRespon.status_code)
            GetRecordsRespon.close()
            return GetRecordsRespon.status_code
    except Exception as GetCFRecordsError:
        logging.exception(GetCFRecordsError)
        return False
# TestPass_25J19

# Update CNAME records at Cloudflare
def UpdateCFCNAME(ConfigFilePath, UpdatePayload):
    CFConfig = Configuration(ConfigFilePath)
    RecordsID = UpdatePayload[0]
    # Connect URL
    Connect = URL()
    UpdateCNAME = (Connect.Cloudflare +
                   f"zones/{CFConfig.Load['CloudflareRecords']['ZoneID']}/dns_records/{RecordsID}")
    # Auth header
    VerifyHeader = CFApiHeader(ConfigFilePath)
    # CNAME update payload
    RecordsUpdateData = {"type": "CNAME",
                         "name": f"{UpdatePayload[1]}", "content": f"{UpdatePayload[2]}",
                         "proxiable": False, "proxied": False, "ttl": 1}
    RecordsJSON = json.dumps(RecordsUpdateData)
    try:
        UpdateRespon = requests.put(UpdateCNAME, headers=VerifyHeader, data=RecordsJSON, timeout=30)
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
    # CSR distinguished name cong
    Country = CSRFileConfig.Load['Certificate']['Counrty']
    State = CSRFileConfig.Load['Certificate']['StateOrProvince']
    Loc = CSRFileConfig.Load['Certificate']['Locality']
    Org = CSRFileConfig.Load['Certificate']['Organization']
    OrgUnit = CSRFileConfig.Load['Certificate']['OrganizationalUnit']
    # Load domains list and check
    DomainList = CSRFileConfig.Load['Certificate']['Domains']
    CommonName = DomainList[0]
    # Single domains, ex: www.example.com
    if len(DomainList[1]) == 0:
        CreateCSRConfig = CSRConfigSingle(CommonName,Country,State,Loc,Org,OrgUnit)
        CSRConfigText = CreateCSRConfig.CSRconfig
    # Multiple domains, ex: www.example.com & example.com
    elif len(DomainList[1]) != 0:
        AltName = DomainList[1]
        CreateCSRConfig = CSRConfigMulti(CommonName,AltName,Country,State,Loc,Org,OrgUnit)
        CSRConfigText = CreateCSRConfig.CSRconfig
    # CSR Config path
    CSRConfigPath = Path(CSRFileConfig.Load['Certificate']['Config'])
    with CSRConfigPath.open("w") as CSRSignConfig:
        CSRSignConfig.writelines(CSRConfigText)
    # CSR and pending PK path
    CSRFile = CSRFileConfig.Load['Certificate']['CSR']
    PendingPK = CSRFileConfig.Load['Certificate']['PendingPK']
    # OpenSSL generate command
    OpensslCommand = ["openssl", "req", "-new",
                      "-keyout", f"{PendingPK}", "-out", f"{CSRFile}",
                      "-config", f"{CSRConfigPath}"]
    try:
        # Using OpenSSL generate CSR and PK
        CsrStatus = subprocess.Popen(
            OpensslCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # Discard openssl command output
        stdout, stderr = CsrStatus.communicate()
        # Check openssl command successful
        if CsrStatus.returncode == 0:
            return 200
        elif CsrStatus.returncode != 0:
            return False
    except Exception as CreateCSRError:
        logging.exception(CreateCSRError)
        return False
# TestPass_25J19

# Sending certificate create request
def ZeroSSLCreateCA(ConfigFilePath):
    CreateCAConfig = Configuration(ConfigFilePath)
    ZeroSSLAuth = CreateCAConfig.Load['ZeroSSLAPI']['AccessKey']
    # Read Certificates signing request
    CSRFile = Path(CreateCAConfig.Load['Certificate']['CSR'])
    with CSRFile.open("r") as CSRFileData:
        CSRPayload = CSRFileData.read().replace("\n","")
    # Reading domain
    DList = CreateCAConfig.Load['Certificate']['Domains']
    if len(DList[1]) != 0:
        CreatePayload = {
            "certificate_domains": f"{DList[0]},{DList[1]}", "certificate_validity_days": 90,
            "certificate_csr": CSRPayload}
    elif len(DList[1]) == 0:
        CreatePayload = {
            "certificate_domains": f"{DList[0]}", "certificate_validity_days": 90,
            "certificate_csr": CSRPayload}
    CreateJSON = json.dumps(CreatePayload)
    # Create CA URL and Header
    Connect = URL()
    CreateCA = (Connect.ZeroSSL + f"?access_key={ZeroSSLAuth}")
    CreateHeader = {"Content-Type": "application/json"}
    try:
        CreateCARespon = requests.post(CreateCA, headers=CreateHeader, data=CreateJSON, timeout=30)
        if CreateCARespon.status_code == 200:
            ResultData = json.loads(CreateCARespon.text)
            CreateCARespon.close()
            # Saving validation data
            ValidationCacheFile = Path(CreateCAConfig.Load['ZeroSSLAPI']['Cache'])
            with ValidationCacheFile.open("w") as ValidationData:
                json.dump(ResultData, ValidationData, indent = 4)
            return ResultData
        elif CreateCARespon.status_code != 200:
            logging.warning(CreateCARespon.status_code)
            CreateCARespon.close()
            return CreateCARespon.status_code
    except Exception as ErrorStatus:
        logging.exception(ErrorStatus)
        return False
# TestPass_25J19

# Phrasing ZeroSSL verify JSON, currently CNAME only.
def ZeroSSLVerifyData(ConfigFilePath, VerifyRequest, Mode = ('CNAME')):
    # Get records id
    VerifyCNAME = Configuration(ConfigFilePath)
    VerifyID = VerifyCNAME.Load['CloudflareRecords']['CNAMERecordsID']
    VerifyCN = VerifyRequest['common_name']
    # CNAME mode
    if Mode == ("CNAME") and len(VerifyRequest['additional_domains']) == 0:
        CreateCAVerify = {
            "id": f"{VerifyRequest['id']}",
            "common_name_cname": [
                VerifyID[0],
                VerifyRequest['validation']['other_methods'][VerifyCN]['cname_validation_p1'],
                VerifyRequest['validation']['other_methods'][VerifyCN]['cname_validation_p2']]}
    elif Mode == ("CNAME") and len(VerifyRequest["additional_domains"]) != 0:
        VerifyAD = VerifyRequest['additional_domains']
        CreateCAVerify = {
            "id": f"{VerifyRequest['id']}",
            "common_name_cname": [
                VerifyID[0],
                VerifyRequest['validation']['other_methods'][VerifyCN]['cname_validation_p1'],
                VerifyRequest['validation']['other_methods'][VerifyCN]['cname_validation_p2']],
            "additional_domains_cname": [
                VerifyID[1],
                VerifyRequest['validation']['other_methods'][VerifyAD]['cname_validation_p1'],
                VerifyRequest['validation']['other_methods'][VerifyAD]['cname_validation_p2']]}
    return CreateCAVerify
# TestPass_25J19

# Verification, when using CNAME and HTTP/HTTPS file verify
def ZeroSSLVerification(ConfigFilePath, CertificateID, ValidationMethod = ('CNAME_CSR_HASH')):
    VerifyConfig = Configuration(ConfigFilePath)
    ZZeroSSLAuth = VerifyConfig.Load['ZeroSSLAPI']['AccessKey']
    # Verification URL and verification method, default is CNAME
    Connect = URL()
    CAVerification = (Connect.ZeroSSL + f"/{CertificateID}/challenges?access_key={ZZeroSSLAuth}")
    VerifyMethod = {"validation_method": ValidationMethod}
    try:
        CAVerificationRespon = requests.post(CAVerification, data=VerifyMethod, timeout=30)
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
# TestPass_25J19

# Download certificate from ZeroSSL
def ZeroSSLDownloadCA(ConfigFilePath, CertificateID):
    DownloadCAConfig = Configuration(ConfigFilePath)
    ZeroSSLAuth = DownloadCAConfig.Load['ZeroSSLAPI']['AccessKey']
    Connect = URL()
    DownloadCA = (Connect.ZeroSSL + f"/{CertificateID}/download/return?access_key={ZeroSSLAuth}")
    DownloadCAHeader = {"Content-Type": "application/json"}
    try:
        DownloadCARespon = requests.get(DownloadCA, headers=DownloadCAHeader, timeout=30)
        if DownloadCARespon.status_code == 200:
            CertificateJSON = json.loads(DownloadCARespon.text)
            DownloadCARespon.close()
            # Return certificate payload
            if ("certificate.crt") in CertificateJSON:
                return CertificateJSON
            # Retrun error status
            elif ("certificate.crt") not in CertificateJSON:
                DownloadCAError = CertificateJSON['error']['type']
                logging.exception(DownloadCAError)
                return DownloadCAError
        elif DownloadCARespon.status_code != 200:
            return (f"ZeroSSL REST API ERROR: {DownloadCARespon.status_code}")
    except Exception as DownloadCAError:
        logging.exception(DownloadCAError)
        return False
# TestPass_25J19

# Install certificate to server folder, reload is optional
def CertificateInstall(ConfigFilePath, CertificateContent, ServerCommand = (None)):
    InstallConfig = Configuration(ConfigFilePath)
    try:
        # Private key
        PKPending = Path(InstallConfig.Load['Certificate']['PendingPK'])
        PKActive = Path(InstallConfig.Load['Certificate']['PK'])
        with PKPending.open("r") as PendingPrivateKey, PKActive.open("w") as ActivePrivateKey:
            ActivePrivateKey.write(PendingPrivateKey.read())
        # Certificate
        Certificate = Path(InstallConfig.Load['Certificate']['CA'])
        CAString = CertificateContent['certificate.crt']
        with Certificate.open("w") as ActiveCertificate:
            ActiveCertificate.write(CAString)
        # Save certificate authority bundle
        CertificateBA = Path(InstallConfig.Load['Certificate']['CAB'])
        CABString = CertificateContent['ca_bundle.crt']
        with CertificateBA.open("w") as ActiveCertificateBA:
            ActiveCertificateBA.write(CABString)
        sleep(5)
        # Server reload or restart option
        if ServerCommand is not None:
            ServerStatus = subprocess.Popen(
                ServerCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # Discard output
            stdout, stderr = ServerStatus.communicate()
            # Check if reboot command successful
            if ServerStatus.returncode == 0:
                return ServerCommand
            # Restart or reload fail
            elif ServerStatus.returncode != 0:
                return False
        elif ServerCommand is None:
            return 200
    except Exception as InstallCAError:
        logging.exception(InstallCAError)
        return False
# UNTEST_25J27

# Cancel certificate from ZeroSSL
def ZeroSSLCancelCA(ConfigFilePath, CertificateID):
    CancelCAConfig = Configuration(ConfigFilePath)
    ZeroSSLAuth = CancelCAConfig.Load['ZeroSSLAPI']['AccessKey']
    Connect = URL()
    CancelCA = (Connect.ZeroSSL + f"/{CertificateID}/cancel?access_key={ZeroSSLAuth}")
    CancelCAHeader = {"Content-Type": "application/json"}
    try:
        CancelCARespon = requests.post(CancelCA, headers=CancelCAHeader, timeout=30)
        if CancelCARespon.status_code == 200:
            CancelJSON = json.loads(CancelCARespon.text)
            CancelCARespon.close()
            return CancelJSON
        else:
            return CancelCARespon.status_code
    except Exception as CancelCAError:
        logging.exception(CancelCAError)
        return CancelCAError
# TestPass_25J20

# Revoke certificate from ZeroSSL
def ZeroSSLRevokeCA(ConfigFilePath, CertificateID, RevokeReason = (None)):
    RevokeCAConfig = Configuration(ConfigFilePath)
    ZeroSSLAuth = RevokeCAConfig.Load['ZeroSSLAPI']['AccessKey']
    Connect = URL()
    RevokeCA = (Connect.ZeroSSL + f"/{CertificateID}/revoke?access_key={ZeroSSLAuth}")
    # Unspecified revoke reason
    if RevokeReason is None:
        RevokeReason = ("Unspecified")
    elif RevokeReason is not None:
        pass    
    RevokeCAHeader = {"Content-Type": "application/json", "reason": f"{RevokeReason}"}
    try:
        RevokeCARespon = requests.post(RevokeCA, headers=RevokeCAHeader, timeout=30)
        if RevokeCARespon.status_code == 200:
            RevokeJSON = json.loads(RevokeCARespon.text)
            RevokeCARespon.close()
            return RevokeJSON
        else:
            return RevokeCARespon.status_code
    except Exception as RevokeCAError:
        logging.exception(RevokeCAError)
        return False
# TestPass_25J20

# Check certificate expires, default minimum is 14 days
def ExpiresCheck(ConfigFilePath, Minimum = (14)):
    # Load config for cache path
    CacheConfig = Configuration(ConfigFilePath)
    CacheFilePath = Path(CacheConfig.Load['ZeroSSLAPI']['Cache'])
    # Read cache get certificate expires
    try:
        with CacheFilePath.open("r", encoding = "utf-8") as CacheCheck:
            CacheData = json.load(CacheCheck)
    # Cache file not found, means first time running ACME4SSL
    except Exception:
        return False
    # Get expires
    ExpiresTime = datetime.datetime.strptime(CacheData['expires'], "%Y-%m-%d %H:%M:%S")
    # Calculate
    CurrentTime = datetime.datetime.now()
    TimeDiff = ExpiresTime - CurrentTime
    if TimeDiff.days > Minimum:
        return TimeDiff.days
    # Below minimum
    elif TimeDiff.days <= Minimum:
        return False
# TestPass_25J25
