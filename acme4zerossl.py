# -*- coding: utf-8 -*-
import logging
from pathlib import Path
import json
import datetime
import textwrap
import requests
import subprocess
from time import sleep

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
            # Script config path
            ConfigPath = Path(ConfigFilePath)
            # Local path
            ConfigFolder = Path(__file__).resolve().parent
            ConfigLocal = ConfigFolder / ConfigPath.name
            try:
                with ConfigPath.open("r", encoding = "utf-8") as ConfigContent:
                    self.Load = json.load(ConfigContent)
            # Try to find configuration file at local folder
            except FileNotFoundError:
                with ConfigLocal.open("r", encoding = "utf-8") as ConfigContent:
                    self.Load = json.load(ConfigContent)
        # Error
        except Exception as ConfigError:
            logging.exception(f"PATH={ConfigPath}| {ConfigLocal}| Error={ConfigError}")
            raise
        # QC 2025L19

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
        # File path, file validation
        self.Fileverify    = self.RuntimeConfig['FileChallenge']['HTMLFilePath']
        # CSR config
        self.Country       = self.RuntimeConfig['Certificate']['Country']
        self.State         = self.RuntimeConfig['Certificate']['StateOrProvince']
        self.Locality      = self.RuntimeConfig['Certificate']['Locality']
        self.Organization  = self.RuntimeConfig['Certificate']['Organization']
        self.Unit          = self.RuntimeConfig['Certificate']['OrganizationalUnit']
        # Domains list
        self.DomainList    = self.RuntimeConfig['Certificate']['Domains']
        self.CommonName    = self.DomainList[0]
        self.AltName       = self.DomainList[1] if len(self.DomainList) > 1 else ""
        # Terminal text width
        self.MessageWidth  = 100

    # Print runtime info
    def Message(self, MessageText):
        EventTime = datetime.datetime.now()
        TextPrintTime = EventTime.strftime("%H:%M:%S")
        TextPrefix = (f"{TextPrintTime} | ")
        UsableWidth = self.MessageWidth - len(TextPrefix)
        SequentIndent = " " * len(TextPrefix)
        Wrapping = textwrap.fill(MessageText, width=UsableWidth, subsequent_indent=SequentIndent)
        print(TextPrefix + Wrapping)
        # QC 2025K21

    # Check certificate expires, default minimum is 14 days
    def ExpiresCheck(self, Minimum = (14)):
        # Load config for cache path
        CacheFilePath = Path(self.Cache)
        # Read cache get certificate expires
        try:
            with CacheFilePath.open("r", encoding = "utf-8") as CacheCheck:
                CacheData = json.load(CacheCheck)
        # Cache file not found, means first time running ACME4SSL
        except FileNotFoundError:
            return False
        # Get expires
        try:
            ExpiresTime = datetime.datetime.strptime(CacheData.get("expires",""), "%Y-%m-%d %H:%M:%S")
            # Calculate
            CurrentTime = datetime.datetime.now()
            TimeDiff = ExpiresTime - CurrentTime
            if TimeDiff.days > Minimum:
                return TimeDiff.days
            # Below minimum
            elif TimeDiff.days <= Minimum:
                return False
        # Calculate error, force renewed
        except Exception as CalculateError:
            logging.exception(CalculateError)
            return False
        # QC 2025L14

    # Certificate Signing Request
    def CSRConfig(self):
        try:
            # Setting empty alt names
            AltNames1 = f"DNS.1 = {self.CommonName}"
            AltNames2 = f"DNS.2 = {self.AltName}" if isinstance(self.AltName,str) and self.AltName.strip() else ""
            DNconfig  = f"commonName = {self.CommonName}"
            # Certificate Signing Request contents
            CSRConfigContents = [
                # Basic Config
                "[req]",
                "default_bits = 2048",
                "prompt = no",
                "encrypt_key = no",
                "default_md = sha256",
                "utf8 = yes",
                "string_mask = utf8only",
                # X509 Basic Constraints
                "req_extensions = x509_v3_req",
                "distinguished_name = req_distinguished_name",
                "[x509_v3_req]",

                "subjectAltName = @alt_names",
                "[alt_names]",
                AltNames1, AltNames2,
                # Distinguished
                "[req_distinguished_name]",
                f"countryName = {self.Country}",
                f"stateOrProvinceName = {self.State}",
                f"localityName = {self.Locality}",
                f"organizationName = {self.Organization}",
                f"organizationalUnitName = {self.Unit}",
                DNconfig]
            return CSRConfigContents
        except Exception as CSRGenError:
            logging.exception(CSRGenError)
            return False
        # QC 2025L15 Mod

    # Create certificates signing request and PK
    def CreateCSR(self):
        CSRConfigContents = self.CSRConfig()
        if not isinstance(CSRConfigContents, list) or not CSRConfigContents:
            return False
        try:
            # Path check
            CSRConfigPath = Path(self.CSRConfigFile)
            CSRConfigPath.parent.mkdir(parents=True, exist_ok=True)
            Path(self.PendingPK).parent.mkdir(parents=True, exist_ok=True)
            Path(self.CSROutput).parent.mkdir(parents=True, exist_ok=True)
            with CSRConfigPath.open("w") as CSRSignConfig:
                # Drop empty alt names
                for CSRConfigLine in filter(None, CSRConfigContents):
                    CSRSignConfig.write(CSRConfigLine + "\n")
            # OpenSSL generate command
            OpensslCommand = ["openssl", "req", "-new", "-nodes", "-newkey", "rsa:2048",
                              "-keyout", f"{self.PendingPK}", "-out", f"{self.CSROutput}",
                              "-config", f"{self.CSRConfigFile}"]
            # Using OpenSSL generate CSR and PK
            CsrStatus = subprocess.Popen(OpensslCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # Discard openssl command output
            stdout, stderr = CsrStatus.communicate()
            # Check openssl command successful
            if CsrStatus.returncode == 0:
                return 200
            elif CsrStatus.returncode != 0:
                logging.error(f"{CsrStatus.returncode}| {stderr}")
                return False
        except Exception as CreateCSRError:
            logging.exception(CreateCSRError)
            return False
        # QC 2025L15 Mod

    # Create and write ACME Challenge file
    def CreateValidationFile(self, VerifyRequestFile):
        try:
            # Part of file path and name
            ValidationFile = VerifyRequestFile.get("file")
            # Empty
            if not ValidationFile:
                logging.warning("Empty Challenge file path.")
                return
            else:
                ValidationFilePath = Path(ValidationFile)
                FolderPath = Path(self.Fileverify)
                FullFilePath = FolderPath / ValidationFilePath
            # Check folder inside webpage folder
            FullFilePath.parent.mkdir(parents=True, exist_ok=True)
            # File content
            ChallengeTexts = VerifyRequestFile.get("content","")
            # Open File
            with FullFilePath.open("w", encoding="utf-8") as ChallengeFile:
                # Write-in ZeroSSL challenge file content
                if isinstance(ChallengeTexts, list):
                    for ChallengeText in ChallengeTexts:
                        ChallengeFile.write(ChallengeText + "\n")
                # If ZeroSSL content became string
                elif isinstance(ChallengeTexts, str):
                    ChallengeFile.write(ChallengeTexts + "\n")
                # Fail-safe, may be empty or blank
                else:
                    ChallengeFile.write(str(ChallengeTexts) + "\n")
            # Challenge file create notice
            self.Message(f"{FullFilePath} has been created.")
        except Exception as CreateValidationFileError:
            logging.exception(CreateValidationFileError)
        # QC 2025L14

    # Delete ACME Challenge file after verify
    def CleanValidationFile(self, VerifyRequestFile):
        try:
            # Part of file path and name
            ValidationFile = VerifyRequestFile.get("file")
            # Empty
            if not ValidationFile:
                return
            else:
                ValidationFilePath = Path(ValidationFile)
                FolderPath = Path(self.Fileverify)
                ChallengeFileRemain = FolderPath / ValidationFilePath
            # Delete file
            if ChallengeFileRemain.exists():
                try:
                    ChallengeFileRemain.unlink()
                # File already delete
                except FileNotFoundError:
                    pass
        except Exception as CleanValidationFileError:
            logging.exception(CleanValidationFileError)
        # QC 2025L14

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
            CAString = CertificateContent.get("certificate.crt","")
            with Certificate.open("w") as ActiveCertificate:
                ActiveCertificate.write(CAString)
            # Save certificate authority bundle
            CertificateBA = Path(self.CertificateBA)
            CABString = CertificateContent.get("ca_bundle.crt","")
            with CertificateBA.open("w") as ActiveCertificateBA:
                ActiveCertificateBA.write(CABString)
            sleep(5)
            # Server reload or restart option
            if ServerCommand is not None:
                ServerStatus = subprocess.Popen(ServerCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                # Discard output
                stdout, stderr = ServerStatus.communicate()
                # Check if reboot command successful
                if ServerStatus.returncode == 0:
                    return ServerCommand
                # Restart or reload fail
                elif ServerStatus.returncode != 0:
                    logging.error(f"{ServerStatus.returncode}| {stderr}")
                    return False
            elif ServerCommand is None:
                return 200
        except Exception as InstallCAError:
            logging.exception(InstallCAError)
            return False
        # QC 2025K21

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
            elif TgResponse.status_code == 400:
                TgResponse.close()
                self.RtM.Message("Telegram ChatID is empty, notifications will not be sent.")
                logging.error(TgResponse.status_code)
            else:
                TgResponse.close()
                logging.warning(TgResponse.status_code)
        except Exception as TelegramErrorStatus:
            logging.exception(TelegramErrorStatus)
        # QC 2025K23

    # Get Telegram ChatID
    def GetChatID(self):
        # Connetc URL
        TgAskURL = (self.Com.Telegram + f"{self.BotToken}/getUpdates")
        try:
            TgAskResponse = requests.post(TgAskURL, timeout=30)
            if TgAskResponse.status_code == 200:
                TgAskData = json.loads(TgAskResponse.text)
                TgAskResponse.close()
                TgAskResult = TgAskData.get("result","")
                # Empty result
                if not TgAskResult:
                    self.RtM.Message("You must send message to bot first.")
                # Select ChatID
                else:
                    CheckChatList = TgAskData.get("result","")
                    CheckChatResult = CheckChatList[0]
                    CheckChatID = CheckChatResult.get("message",{}).get("chat",{}).get("id","")
                    self.RtM.Message(f"You ChatID is: {CheckChatID}")
            else:
                TgAskResponse.close()
                logging.warning(TgAskResponse.status_code)
        except Exception as TelegramErrorStatus:
            logging.exception(TelegramErrorStatus)
        # QC 2025L10 Mod
        
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
                return TokenVerifyData.get("result",{}).get("status","")
            # Return all
            elif TokenResponse.status_code == 200 and DisplayVerifyResult is not None:
                TokenVerifyData = json.loads(TokenResponse.text)
                TokenResponse.close()
                return TokenVerifyData
            elif TokenResponse.status_code != 200:
                TokenResponse.close()
                logging.warning(TokenResponse.status_code)
                return TokenResponse.status_code
        except Exception as VerifyCFError:
            logging.exception(VerifyCFError)
            return False
        # QC 2025L10 Mod

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
        # QC 2025K20

    # Update CNAME records at Cloudflare
    def UpdateCFCNAME(self, UpdatePayload):
        try:
            # Records ID
            RecordID = UpdatePayload.get("cname_id")
            if not RecordID:
                logging.warning("Error during phrasing CNAME update payload, missing record ID.")
                return False
            else:
                UpdateCNAME = (self.Com.Cloudflare + f"zones/{self.Zone}/dns_records/{RecordID}")
            # CNAME update payload
            CNAMEText = UpdatePayload.get("cname")
            CNAMEValue = UpdatePayload.get("value")
            if CNAMEText and CNAMEValue:
                UpdateCNAMEData = {
                    "type":"CNAME", "name":CNAMEText, "content":CNAMEValue,
                    "proxiable":False, "proxied":False, "ttl":1}
                UpdateJSON = json.dumps(UpdateCNAMEData)
            else:
                logging.warning("Error during phrasing CNAME update payload, missing CNAME or Value.")
                return False
            # Update
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
        # UNQC

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
        # ZeroSSL JSON structure
        self.L1            = "validation"
        self.L2            = "other_methods"
        self.CNAME         = "cname_validation_p1"
        self.VALUE         = "cname_validation_p2"
        self.FILE          = "file_validation_url_https"
        self.CONTENT       = "file_validation_content"
        # Cloudflare
        self.CNAMEList     = self.ZeroSSLConfig['CloudflareRecords']['CNAMERecordsID']
        self.CommonNameID  = self.CNAMEList[0] if self.CNAMEList else ""
        self.AltNameID     = self.CNAMEList[1] if len(self.CNAMEList) > 1 else ""
        # REST API and Header
        self.Com = API()
        self.ZeroSSLHeader = {"Content-Type":"application/json"}

    # Sending certificate create request
    def ZeroSSLCreateCA(self):
        # Read Certificates signing request
        CSRFile = Path(self.ZeroSSLCSR)
        with CSRFile.open("r") as CSRFileData:
            CSRPayload = CSRFileData.read()
        # Reading domain
        if len(self.DomainList) > 1 and self.DomainList[1]:
            CertificateDomains = f"{self.DomainList[0]}, {self.DomainList[1]}"
        else:
            CertificateDomains = f"{self.DomainList[0]}"
        # Package as JSON
        CreatePayload = {"certificate_domains":CertificateDomains,
                         "certificate_validity_days":90,
                         "certificate_csr":CSRPayload}
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
                CreateRespon.close()
                logging.warning(CreateRespon.status_code)
                return CreateRespon.status_code
        except Exception as ErrorStatus:
            logging.exception(ErrorStatus)
            return False
        # QC 2025L14

    # Phrasing ZeroSSL verify JSON
    def ZeroSSLVerifyData(self, VerifyRequest, Mode = ('CNAME')):
        try:
            # Additional domain check
            AdditionalDomainCheck = VerifyRequest.get(self.L1,{}).get(self.L2,{}).get(self.AltName)
            AdditionalCheck = bool(AdditionalDomainCheck)
            # Certificate ID
            VerifyCertificateID = VerifyRequest.get("id","")
            # Common Name CNAME
            CommonName_CNAME = VerifyRequest.get(self.L1,{}).get(self.L2,{}).get(self.CommonName,{}).get(self.CNAME,"")
            # Common Name VALUE
            CommonName_VALUE = VerifyRequest.get(self.L1,{}).get(self.L2,{}).get(self.CommonName,{}).get(self.VALUE,"")
            # Additional domain CNAME
            Additional_CNAME = VerifyRequest.get(self.L1,{}).get(self.L2,{}).get(self.AltName,{}).get(self.CNAME,"")
            # Additional domain VALUE
            Additional_VALUE = VerifyRequest.get(self.L1,{}).get(self.L2,{}).get(self.AltName,{}).get(self.VALUE,"")
            # Common_domain, verify file path and file name
            CommonName_FILE = VerifyRequest.get(self.L1,{}).get(self.L2,{}).get(self.CommonName,{}).get(self.FILE,"").replace(f"https://{self.CommonName}/","")
            # Common_domain, file content
            CommonName_CONTENT = VerifyRequest.get(self.L1,{}).get(self.L2,{}).get(self.CommonName,{}).get(self.CONTENT,"")
            # Additional_domains, verify file path and file name
            Additional_FILE = VerifyRequest.get(self.L1,{}).get(self.L2,{}).get(self.AltName,{}).get(self.FILE,"").replace(f"https://{self.AltName}/","")
            # Additional_domains, file content
            Additional_CONTENT = VerifyRequest.get(self.L1,{}).get(self.L2,{}).get(self.AltName,{}).get(self.CONTENT,"")
            # CNAME mode
            if Mode == ("CNAME") and not AdditionalCheck:
                CreateCAVerify = {
                    "id": VerifyCertificateID,
                    "common_name": {"cname_id": self.CommonNameID, "cname": CommonName_CNAME,"value": CommonName_VALUE}}
                # Retutn phrasing dict
                return CreateCAVerify
            # CNAME mode, additional domain
            elif Mode == ("CNAME") and AdditionalCheck:
                CreateCAVerify = {
                    "id": VerifyCertificateID,
                    "common_name": {"cname_id": self.CommonNameID, "cname": CommonName_CNAME, "value": CommonName_VALUE},
                    "additional_domains":{"cname_id": self.AltNameID, "cname": Additional_CNAME, "value": Additional_VALUE}}
                return CreateCAVerify
            # File mode
            elif Mode == ("FILE") and not AdditionalCheck:
                CreateCAVerify = {
                    "id": VerifyCertificateID,
                    "common_name": {"file":CommonName_FILE, "content": CommonName_CONTENT}}
                return CreateCAVerify
            # File mode, additional domain
            elif Mode == ("FILE") and AdditionalCheck:
                CreateCAVerify = {
                    "id": VerifyCertificateID,
                    "common_name": {"file":CommonName_FILE, "content": CommonName_CONTENT},
                    "additional_domains": {"file":Additional_FILE, "content": Additional_CONTENT}}
                return CreateCAVerify
            else:
                logging.warning(f"Unknown ZeroSSL validation mode: {Mode}")
                return False
        # Error
        except Exception as VerifyDataPhrasingError:
            logging.exception(VerifyDataPhrasingError)
            return False
        # UNQC CNAME / QC 2025L14 FILE

    # Verification, when using CNAME and HTTP/HTTPS file verify
    def ZeroSSLVerification(self, CertificateID = (None), ValidationMethod = ('CNAME_CSR_HASH')):
        # Reading certificate hash from cache
        if CertificateID is None:
            CacheInput = Path(self.Validation)
            with CacheInput.open("r", encoding = "utf-8") as CacheFile:
                CacheData = json.load(CacheFile)
            CertificateID = CacheData.get("id")
        # Using input string
        elif CertificateID is not None:
            pass
        # Verification URL and verification method, default is CNAME
        Verification = (self.Com.ZeroSSL + f"/{CertificateID}/challenges?access_key={self.ZeroSSLAuth}")
        VerifyMethodData = {"validation_method":ValidationMethod}
        VerifyJSON = json.dumps(VerifyMethodData)
        try:
            VerificationRespon = requests.post(Verification, headers=self.ZeroSSLHeader, data=VerifyJSON, timeout=30)
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
        # QC 2025K24

    # Download certificate from ZeroSSL
    def ZeroSSLDownloadCA(self, CertificateID = (None)):
        # Reading certificate hash from cache
        if CertificateID is None:
            CacheInput = Path(self.Validation)
            with CacheInput.open("r", encoding = "utf-8") as CacheFile:
                CacheData = json.load(CacheFile)
            CertificateID = CacheData.get("id","")
        # Using input string
        elif CertificateID is not None:
            pass
        # Download
        DownloadCA = (self.Com.ZeroSSL + f"/{CertificateID}/download/return?access_key={self.ZeroSSLAuth}")
        try:
            # ZeroSSL Inline download certificate need JSON header
            DownloadRespon = requests.get(DownloadCA, headers=self.ZeroSSLHeader, timeout=30)
            if DownloadRespon.status_code == 200:
                CertificateJSON = json.loads(DownloadRespon.text)
                DownloadRespon.close()
                # Return certificate payload
                if ("certificate.crt") in CertificateJSON:
                    return CertificateJSON
                # Retrun error status
                elif ("certificate.crt") not in CertificateJSON:
                    DownloadCAError = CertificateJSON.get("error",{}).get("type","")
                    logging.error(DownloadCAError)
                    return False
            elif DownloadRespon.status_code != 200:
                DownloadRespon.close()
                logging.error(f"ZeroSSL REST API ERROR: {DownloadRespon.status_code}")
                return DownloadRespon.status_code
        except Exception as DownloadCAError:
            logging.exception(DownloadCAError)
            return False
        # QC 2025L10 Mod

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
                CancelRespon.close()
                return CancelRespon.status_code
        except Exception as CancelCAError:
            logging.exception(CancelCAError)
            return False
        # QC 2025K22

    # Revoke certificate from ZeroSSL
    def ZeroSSLRevokeCA(self, CertificateID, RevokeReason = (None)):
        RevokeCA = (self.Com.ZeroSSL + f"/{CertificateID}/revoke?access_key={self.ZeroSSLAuth}")
        # Unspecified revoke reason
        if RevokeReason is None:
            RevokeReason = ("Unspecified")
        elif RevokeReason is not None:
            pass
        RevokeReasonData = {"reason":f"{RevokeReason}"}
        RevokeReasonJSON = json.dumps(RevokeReasonData)
        try:
            RevokeRespon = requests.post(RevokeCA, headers=self.ZeroSSLHeader, data=RevokeReasonJSON ,timeout=30)
            if RevokeRespon.status_code == 200:
                RevokeJSON = json.loads(RevokeRespon.text)
                RevokeRespon.close()
                return RevokeJSON
            else:
                RevokeRespon.close()
                return RevokeRespon.status_code
        except Exception as RevokeCAError:
            logging.exception(RevokeCAError)
            return False
        # QC 2025K22
