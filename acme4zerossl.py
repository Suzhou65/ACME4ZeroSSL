# -*- coding: utf-8 -*-
from pathlib import Path
import json
import logging
import requests
import subprocess
from time import sleep
import datetime

# Error handling
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
logging.basicConfig(
    level=logging.WARNING,
    filename="error.acme4zerossl.log", filemode="a", format=FORMAT)
# TESTPASS 25J08

# URL reference
class API():
    def __init__(self):
        self.Cloudflare = "https://api.cloudflare.com/client/v4/"
        self.Telegram   = "https://api.telegram.org/bot"
        self.ZeroSSL    = "https://api.zerossl.com/certificates"

# Configuration function, reading json file
class Configuration():
    def __init__(self, ConfigFilePath):
        try:
            ConfigInput = Path(ConfigFilePath)
            with ConfigInput.open("r", encoding = "utf-8") as ConfigFile:
                ConfigData = json.load(ConfigFile)
                self.Load = ConfigData
        # Error
        except Exception as ConfigurationError:
            raise Exception(ConfigurationError)
    # TESTPASS 25K14

# Runtime package
class Runtime():
    def __init__(self, ConfigFilePath):
        self.RuntimeConfig = Configuration(ConfigFilePath).Load
        # File path
        self.Cache         = self.RuntimeConfig['ZeroSSLAPI']['Cache']
        self.CSRConfigFile = self.RuntimeConfig['Certificate']['Config']
        self.CSROutput     = self.RuntimeConfig['Certificate']['CSR']
        self.PendingPK     = self.RuntimeConfig['Certificate']['PendingPK']
        self.ActivePK      = self.RuntimeConfig['Certificate']['PK']
        self.Certificate   = self.RuntimeConfig['Certificate']['CA']
        self.CertificateBA = self.RuntimeConfig['Certificate']['CAB']
        # CSR distinguished name cong
        self.Country       = self.RuntimeConfig['Certificate']['Counrty']
        self.State         = self.RuntimeConfig['Certificate']['StateOrProvince']
        self.Locality      = self.RuntimeConfig['Certificate']['Locality']
        self.Organization  = self.RuntimeConfig['Certificate']['Organization']
        self.Unit          = self.RuntimeConfig['Certificate']['OrganizationalUnit']
        # Domains list
        self.DomainList    = self.RuntimeConfig['Certificate']['Domains']
        self.CommonName    = self.DomainList[0]
        self.AltName       = self.DomainList[1] if len(self.DomainList) > 1 else ""
    # Print runtime info
    def Message(self, MessageText):
        EventTime = datetime.datetime.now()
        TextPrintTime = EventTime.strftime("%H:%M:%S")
        print(f"{TextPrintTime} | {MessageText}")
    # TESTPASS 25K13

    # Check certificate expires, default minimum is 14 days
    def ExpiresCheck(self, Minimum = (14)):
        # Load config for cache path
        CacheFilePath = Path(self.Cache)
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
    # TESTPASS 25K14

    # Certificate Signing Request
    def CSRConfig(self):
        CSRTextbook = f"""[req]
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
DNS.1 = {self.CommonName}
[req_distinguished_name]
countryName = {self.Country}
stateOrProvinceName = {self.State}
localityName = {self.Locality}
organizationName = {self.Organization}
organizationalUnitName = {self.Unit}
commonName = {self.CommonName}
"""
        return CSRTextbook
    # TESTPASS 25K14

    # Certificate Signing Request
    def CSRConfigMulti(self):
        CSRTextbook = f"""[req]
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
DNS.1 = {self.CommonName}
DNS.2 = {self.AltName}
[req_distinguished_name]
countryName = {self.Country}
stateOrProvinceName = {self.State}
localityName = {self.Locality}
organizationName = {self.Organization}
organizationalUnitName = {self.Unit}
commonName = {self.CommonName}
"""
        return CSRTextbook
    # TESTPASS 25K14

    # Create certificates signing request and PK
    def CreateCSR(self):
        # Multiple domains, ex: www.example.com & example.com
        if len(self.DomainList) > 1 and self.DomainList[1]:
            CSRText = Runtime.CSRConfigMulti(self)
        # Single domains, ex: www.example.com        
        else:
            CSRText = Runtime.CSRConfig(self)
        # CSR Config path
        CSRConfigPath = Path(self.CSRConfigFile)
        with CSRConfigPath.open("w") as CSRSignConfig:
            CSRSignConfig.writelines(CSRText)
        # OpenSSL generate command
        OpensslCommand = ["openssl", "req", "-new",
                          "-keyout", f"{self.PendingPK}", "-out", f"{self.CSROutput}",
                          "-config", f"{self.CSRConfigFile}"]
        # Run command
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
    # TESTPASS 25K15

    # Install certificate to server folder, reload is optional
    def CertificateInstall(self, CertificateContent, ServerCommand = (None)):
        try:
            # Private key
            PKPending = Path(self.PendingPK)
            PKActive = Path(self.ActivePK)
            with PKPending.open("r") as PendingPrivateKey, PKActive.open("w") as ActivePrivateKey:
                ActivePrivateKey.write(PendingPrivateKey.read())
            # Certificate
            Certificate = Path(self.Certificate)
            CAString = CertificateContent['certificate.crt']
            with Certificate.open("w") as ActiveCertificate:
                ActiveCertificate.write(CAString)
            # Save certificate authority bundle
            CertificateBA = Path(self.CertificateBA)
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
    #

# Sending Telegram message
class Telegram():
    def __init__(self, ConfigFilePath):
        self.TgConfig     = Configuration(ConfigFilePath).Load
        self.BotToken     = self.TgConfig['Telegram_BOTs']['Token']
        self.ChatID       = self.TgConfig['Telegram_BOTs']['ChatID']
        self.Domainheader = self.TgConfig['Certificate']['Domains'][0]
        self.Com = API()
        # Print message
        self.RtM          = Runtime(ConfigFilePath)
    # Set default message for testing
    def Message2Me(self, TelegramMessage = ('Here, the world!')):
        # Connetc URL
        TgURL = (self.Com.Telegram + f"{self.BotToken}/sendMessage")
        # Text content
        TgText = (f"{self.Domainheader}\n" + TelegramMessage)
        TgMsg = {"chat_id": f"{self.ChatID}", "text": TgText}
        try:
            TgResponse = requests.post(TgURL, json=TgMsg, timeout=30)
            if TgResponse.status_code == 200:
                TgResponse.close()
                self.RtM.Message(TelegramMessage)
            else:
                TgResponse.close()
                logging.exception(TgResponse.status_code)
        except Exception as TelegramErrorStatus:
            logging.exception(TelegramErrorStatus)
    # TESTPASS 25K15

# Cloudflare API package
class Cloudflare():
    def __init__(self, ConfigFilePath):
        self.CfConfig = Configuration(ConfigFilePath).Load
        self.Token    = self.CfConfig['CloudflareAPI']['Token']
        self.Mail     = self.CfConfig['CloudflareAPI']['Mail']
        self.Zone     = self.CfConfig['CloudflareRecords']['ZoneID']
        self.Com = API()
        # Generate Cloudflare API request header
        self.CFHeader = {"Authorization": f"Bearer {self.Token}",
                         "X-Auth-Email": f"{self.Mail}",
                         "Content-Type": "application/json"}
    # Verify Cloudflare API token
    def VerifyCFToken(self, DisplayVerifyResult = (None)):
        CfVerifyURL = (self.Com.Cloudflare + "user/tokens/verify")
        try:
            TokenResponse = requests.get(CfVerifyURL, headers=self.CFHeader, timeout=30)
            # Only return verify result
            if TokenResponse.status_code == 200 and DisplayVerifyResult is None:
                TokenVerifyData = json.loads(TokenResponse.text)
                TokenResponse.close()
                return TokenVerifyData['result']['status']
            # Return all
            elif TokenResponse.status_code == 200 and DisplayVerifyResult is not None:
                TokenVerifyData = json.loads(TokenResponse.text)
                TokenResponse.close()
                return TokenVerifyData
            elif TokenResponse.status_code != 200: 
                logging.warning(TokenResponse.status_code)
                return TokenResponse.status_code
        except Exception as VerifyCFError:
            logging.exception(VerifyCFError)
            return False
    # TESTPASS+25K14

    # Download all DNS records from Cloudflare
    def GetCFRecords(self, FileOutput = (None)):
        GetRecords = (self.Com.Cloudflare + f"zones/{self.Zone}/dns_records")
        try:
            RecordsRespon = requests.get(GetRecords, headers=self.CFHeader, timeout=30)
            # Return records as dict
            if RecordsRespon.status_code == 200 and FileOutput is None:
                RecordsData = json.loads(RecordsRespon.text)
                RecordsRespon.close()
                return RecordsData
            # Enable records file output
            elif RecordsRespon.status_code == 200 and FileOutput is not None:
                RecordsData = json.loads(RecordsRespon.text)
                RecordsRespon.close()
                RecordsOutputPath = Path(FileOutput)            
                with RecordsOutputPath.open("w") as RecordsFile:
                    json.dump(RecordsData, RecordsFile, indent = 3)
                return FileOutput
            elif RecordsRespon.status_code != 200:
                logging.warning(RecordsRespon.status_code)
                RecordsRespon.close()
                return RecordsRespon.status_code
        except Exception as GetCFRecordsError:
            logging.exception(GetCFRecordsError)
            return False
    # TESTPASS+25K14

    # Update CNAME records at Cloudflare
    def UpdateCFCNAME(self, UpdatePayload):
        # Records ID
        RecordID = UpdatePayload[0]
        UpdateCNAME = (self.Com.Cloudflare + f"zones/{self.Zone}/dns_records/{RecordID}")
        # CNAME update payload
        UpdateCNAMEData = {"type": "CNAME",
                           "name": f"{UpdatePayload[1]}", "content": f"{UpdatePayload[2]}",
                           "proxiable": False, "proxied": False, "ttl": 1}
        UpdateJSON = json.dumps(UpdateCNAMEData)
        try:
            UpdateRespon = requests.put(UpdateCNAME, headers=self.CFHeader, data=UpdateJSON, timeout=30)
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
    #

# ZeroSSL REST API package
class ZeroSSL():
    def __init__(self, ConfigFilePath):
        self.ZeroSSLConfig = Configuration(ConfigFilePath).Load
        self.ZeroSSLAuth   = self.ZeroSSLConfig['ZeroSSLAPI']['AccessKey']
        self.ZeroSSLCSR    = self.ZeroSSLConfig['Certificate']['CSR']
        self.Validation    = self.ZeroSSLConfig['ZeroSSLAPI']['Cache']
        self.DomainList    = self.ZeroSSLConfig['Certificate']['Domains']
        self.CommonName    = self.DomainList[0]
        self.AltName       = self.DomainList[1] if len(self.DomainList) > 1 else ""
        # Cloudflare
        self.CNAMEList     = self.ZeroSSLConfig['CloudflareRecords']['CNAMERecordsID']
        self.CommonNameID  = self.CNAMEList[0]
        self.AltNameID     = self.CNAMEList[1] if len(self.CNAMEList) > 1 else ""
        # REST API and Header
        self.Com = API()
        self.ZeroSSLHeader = {"Content-Type": "application/json"}
    # Sending certificate create request
    def ZeroSSLCreateCA(self):
        # Read Certificates signing request
        CSRFile = Path(self.ZeroSSLCSR)
        with CSRFile.open("r") as CSRFileData:
            CSRPayload = CSRFileData.read().replace("\n","")
        # Reading domain
        if len(self.DomainList) > 1 and self.DomainList[1]:
            CertificateDomains = f"{self.DomainList[0]}, {self.DomainList[1]}"
        else:
            CertificateDomains = f"{self.DomainList[0]}"
        # Package as JSON
        CreatePayload = {"certificate_domains": CertificateDomains,
                         "certificate_validity_days": 90,
                         "certificate_csr": CSRPayload}
        CreateJSON = json.dumps(CreatePayload)
        # Create URL
        CreateCA = (self.Com.ZeroSSL + f"?access_key={self.ZeroSSLAuth}")
        try:
            CreateRespon = requests.post(CreateCA, headers=self.ZeroSSLHeader, data=CreateJSON, timeout=30)
            if CreateRespon.status_code == 200:
                ResultData = json.loads(CreateRespon.text)
                CreateRespon.close()
                # Saving validation data
                ValidationCacheFile = Path(self.Validation)
                with ValidationCacheFile.open("w") as ValidationData:
                    json.dump(ResultData, ValidationData, indent=4)
                return ResultData
            elif CreateRespon.status_code != 200:
                logging.warning(CreateRespon.status_code)
                CreateRespon.close()
                return CreateRespon.status_code
        except Exception as ErrorStatus:
            logging.exception(ErrorStatus)
            return False
    #

    # Phrasing ZeroSSL verify JSON, currently CNAME only.
    def ZeroSSLVerifyData(self, VerifyRequest, Mode = ('CNAME')):
        try:
            # CNAME mode
            if Mode == ("CNAME") and len(VerifyRequest['additional_domains']) == 0:
                CreateCAVerify = {
                    "id": f"{VerifyRequest['id']}",
                    "common_name_cname": [
                        self.CommonNameID,
                        VerifyRequest['validation']['other_methods'][self.CommonName]['cname_validation_p1'],
                        VerifyRequest['validation']['other_methods'][self.CommonName]['cname_validation_p2']]}
                return CreateCAVerify
            elif Mode == ("CNAME") and len(VerifyRequest["additional_domains"]) != 0:
                CreateCAVerify = {
                    "id": f"{VerifyRequest['id']}",
                    "common_name_cname": [
                        self.CommonNameID,
                        VerifyRequest['validation']['other_methods'][self.CommonName]['cname_validation_p1'],
                        VerifyRequest['validation']['other_methods'][self.CommonName]['cname_validation_p2']],
                    "additional_domains_cname": [
                        self.AltNameID,
                        VerifyRequest['validation']['other_methods'][self.AltName]['cname_validation_p1'],
                        VerifyRequest['validation']['other_methods'][self.AltName]['cname_validation_p2']]}
                return CreateCAVerify
        except:
            pass
    #

    # Verification, when using CNAME and HTTP/HTTPS file verify
    def ZeroSSLVerification(self, CertificateID, ValidationMethod = ('CNAME_CSR_HASH')):
        # Verification URL and verification method, default is CNAME
        Verification = (self.Com.ZeroSSL + f"/{CertificateID}/challenges?access_key={self.ZeroSSLAuth}")
        VerifyMethod = {"validation_method": ValidationMethod}
        try:
            VerificationRespon = requests.post(Verification, data=VerifyMethod, timeout=30)
            if VerificationRespon.status_code == 200:
                VerificationData = json.loads(VerificationRespon.text)
                VerificationRespon.close()
                return VerificationData
            elif VerificationRespon.status_code != 200:
                logging.warning(VerificationRespon.status_code)
                VerificationRespon.close()
                return VerificationRespon.status_code
        except Exception as CAVerificationError:
            logging.exception(CAVerificationError)
            return False
    #

    # Download certificate from ZeroSSL
    def ZeroSSLDownloadCA(self, CertificateID = (None)):
        # Reading certificate hash from cache
        if CertificateID is None:
            CacheInput = Path(self.Validation)
            with CacheInput.open("r", encoding = "utf-8") as CacheFile:
                CacheData = json.load(CacheFile)
            CertificateID = CacheData['id']
        # Using input string
        elif CertificateID is not None:
            pass
        # Download
        DownloadCA = (self.Com.ZeroSSL + f"/{CertificateID}/download/return?access_key={self.ZeroSSLAuth}")
        try:
            DownloadRespon = requests.get(DownloadCA, headers=self.ZeroSSLHeader, timeout=30)
            if DownloadRespon.status_code == 200:
                CertificateJSON = json.loads(DownloadRespon.text)
                DownloadRespon.close()
                # Return certificate payload
                if ("certificate.crt") in CertificateJSON:
                    return CertificateJSON
                # Retrun error status
                elif ("certificate.crt") not in CertificateJSON:
                    DownloadCAError = CertificateJSON['error']['type']
                    logging.exception(DownloadCAError)
                    return DownloadCAError
            elif DownloadRespon.status_code != 200:
                return (f"ZeroSSL REST API ERROR: {DownloadRespon.status_code}")
        except Exception as DownloadCAError:
            logging.exception(DownloadCAError)
            return False
    #

    # Cancel certificate from ZeroSSL
    def ZeroSSLCancelCA(self, CertificateID):
        CancelCA = (self.Com.ZeroSSL + f"/{CertificateID}/cancel?access_key={self.ZeroSSLAuth}")
        try:
            CancelRespon = requests.post(CancelCA, headers=self.ZeroSSLHeader, timeout=30)
            if CancelRespon.status_code == 200:
                CancelJSON = json.loads(CancelRespon.text)
                CancelRespon.close()
                return CancelJSON
            else:
                return CancelRespon.status_code
        except Exception as CancelCAError:
            logging.exception(CancelCAError)
            return CancelCAError
    #

    # Revoke certificate from ZeroSSL
    def ZeroSSLRevokeCA(self, CertificateID, RevokeReason = (None)):
        RevokeCA = (self.Com.ZeroSSL + f"/{CertificateID}/revoke?access_key={self.ZeroSSLAuth}")
        # Unspecified revoke reason
        if RevokeReason is None:
            RevokeReason = ("Unspecified")
        elif RevokeReason is not None:
            pass    
        RevokeHeader = {"Content-Type": "application/json", "reason": f"{RevokeReason}"}
        try:
            RevokeRespon = requests.post(RevokeCA, headers=RevokeHeader, timeout=30)
            if RevokeRespon.status_code == 200:
                RevokeJSON = json.loads(RevokeRespon.text)
                RevokeRespon.close()
                return RevokeJSON
            else:
                return RevokeRespon.status_code
        except Exception as RevokeCAError:
            logging.exception(RevokeCAError)
            return False
    #