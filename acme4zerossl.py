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
logging.basicConfig(level=logging.WARNING, filename="error.acme4zerossl.log", filemode="a", format=FORMAT)

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
            ConfigPathInput = Path(ConfigFilePath)
            # Local path
            LocFolderPath = Path(__file__).resolve().parent
            LocConfig = LocFolderPath / ConfigPathInput.name
            try:
                with ConfigPathInput.open("r", encoding = "utf-8") as ConfigContent:
                    self.Load = json.load(ConfigContent)
            # Try to find configuration file at local folder
            except FileNotFoundError:
                with LocConfig.open("r", encoding = "utf-8") as ConfigContent:
                    self.Load = json.load(ConfigContent)
        # Error
        except Exception as ReadConfigError:
            logging.exception(f"Unable reading configuration |Error: {ReadConfigError} |{ConfigPathInput} |{LocConfig}")
            raise
        # QC 2026A16

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
        try:
            EventTime = datetime.datetime.now()
            TextPrintTime = EventTime.strftime("%H:%M:%S")
            TextPrefix = (f"{TextPrintTime} | ")
            UsableWidth = self.MessageWidth - len(TextPrefix)
            SequentIndent = " " * len(TextPrefix)
            Wrapping = textwrap.fill(MessageText, width=UsableWidth, subsequent_indent=SequentIndent)
            print(TextPrefix + Wrapping)
        except Exception as RuntimeMessagePrintError:
            logging.exception(f"Unable printout runtime |{RuntimeMessagePrintError}")
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
            return None
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
                return None
        # Calculate error, force renewed
        except Exception as ExpiresCheckError:
            logging.exception(f"Unable check certificate expires, force renewed |Error: {ExpiresCheckError}")
            return None
        # QC 2026A16
    # Certificate Signing Request
    def CSRConfig(self):
        try:
            # Get main alternative names
            AltNames1 = f"DNS.1 = {self.CommonName}"
            # Setting second alternative names
            AltNames2 = f"DNS.2 = {self.AltName}" if isinstance(self.AltName,str) and self.AltName.strip() else ""
            # Certificate common name, same as main alternative names
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
        except Exception as CSRConfigError:
            logging.exception(f"Error occurred during phrasing CSR config |Error: {CSRConfigError}")
            return False
        # UNQC
    # Create certificates signing request and PK
    def CreateCSR(self):
        try:
            CSRConfigContents = self.CSRConfig()
            if not isinstance(CSRConfigContents, list):
                logging.error(f"Unable create CSR file due to wrong CSR config")
                return False
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
                return OpensslCommand
            else:
                # Logging stderr for debug
                logging.error(f"Unable running OpenSSL command | Error: {CsrStatus.returncode} |{stdout} |{stderr}")
                return False
        except Exception as CreateCSRError:
            logging.exception(f"Error occurred during create CSR file |Error: {CreateCSRError}")
            return False
        # UNQC
    # Create and write ACME Challenge file
    def CreateValidationFile(self, VerifyRequestFile):
        try:
            # Part of file path and name
            ValidationFile = VerifyRequestFile.get("file")
            # Empty
            if not ValidationFile:
                logging.warning("Unable create HTTP/HTTPS challenge file with empty path")
                return False
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
            self.Message(f"HTTP/HTTPS challenge has been created at: {FullFilePath}")
            return True
        except Exception as CreateValidationFileError:
            logging.exception(f"Error occurred during create challenge file |Error: {CreateValidationFileError}")
            return False
        # UNQC
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
            logging.exception(f"Error occurred during delete challenge file |Error: {CleanValidationFileError}")
        # QC 2025L14
    # Install certificate to server folder, reload is optional
    def CertificateInstall(self, CertificateContent, ServerCommand = None):
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
                else:
                    logging.error(f"Unable running server reload/restart command |Error: {ServerStatus.returncode} |{stdout} |{stderr}")
                    return False
            else:
                return 200
        except Exception as CertificateInstallError:
            logging.exception(f"Error occurred during install certificate or reload/restart server |Error: {CertificateInstallError}")
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
        try:
            # Text content with domain name
            TgText = (f"{self.Domainheader}\n" + TelegramMessage)
            TgMsg = {"chat_id": f"{self.ChatID}", "text": TgText}
            # Connetc URL
            TgURL = (self.Com.Telegram + f"{self.BotToken}/sendMessage")
            with requests.post(TgURL, json=TgMsg, timeout=30) as TgResponse:
                if TgResponse.status_code == 200:
                    self.RtM.Message(TelegramMessage)
                elif TgResponse.status_code == 400:
                    logging.warning(f"Telegram ChatID is empty, notifications will not be sent |{TgResponse.status_code}")
                else:
                    logging.warning(f"Unable sending notifications |HTTP Error: {TgResponse.status_code}")
        except Exception as Message2MeError:
            logging.exception(f"Error occurred during sending notifications |Error: {Message2MeError}")
        # QC 2025K23
    # Get Telegram ChatID
    def GetChatID(self):
        try:
            TgAskURL = (self.Com.Telegram + f"{self.BotToken}/getUpdates")
            with requests.post(TgAskURL, timeout=30) as TgAskResponse:
                if TgAskResponse.status_code == 200:
                    TgAskData = TgAskResponse.json()
                    TgAskResult = TgAskData.get("result")
                    # Empty result
                    if not TgAskResult:
                        self.RtM.Message("You must send message to bot first")
                        return
                    # Select ChatID
                    CheckChatList = TgAskData.get("result")
                    CheckChatResult = CheckChatList[0]
                    CheckChatID = CheckChatResult.get("message",{}).get("chat",{}).get("id")
                    self.RtM.Message(f"You ChatID is: {CheckChatID}")
                elif TgAskResponse.status_code != 200:
                    logging.warning(f"Unable get ChatID |HTTP Error: {TgAskResponse.status_code}")
        except Exception as GetChatIDError:
            logging.exception(f"Error occurred during get ChatID |Error: {GetChatIDError}")
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
        self.CFHeader = {"Authorization": f"Bearer {self.Token}", "X-Auth-Email": f"{self.Mail}", "Content-Type": "application/json"}

    # Verify Cloudflare API token
    def VerifyCFToken(self, DisplayVerifyResult = None):
        try:
            VerifyCFTokenURL = (self.Com.Cloudflare + "user/tokens/verify")
            with requests.get(VerifyCFTokenURL, headers=self.CFHeader, timeout=30) as TokenVerifyResponse:
                if TokenVerifyResponse.status_code == 200:
                    TokenVerifyData = TokenVerifyResponse.json()
                    # Check respon status
                    VerifyCheckStatus = TokenVerifyData.get("success")
                    # Error
                    if VerifyCheckStatus == False:
                        TokenVerifyError = TokenVerifyData.get("errors")
                        logging.warning(f"Error occurred during update verify token |API error: {TokenVerifyError}")
                        return False
                    # Success
                    if DisplayVerifyResult is None:
                        return TokenVerifyData.get("result",{}).get("status")
                    else:
                        return TokenVerifyData
                elif TokenVerifyResponse.status_code != 200:
                    logging.warning(f"Unable connect Cloudflare API |HTTP Error: {TokenVerifyResponse.status_code}")
                    return TokenVerifyResponse.status_code
        except Exception as VerifyCFTokenError:
            logging.exception(f"Error occurred during verify Cloudflare API token |Error: {VerifyCFTokenError}")
            return False
        # QC 2026A16
    # Download all DNS records from Cloudflare
    def GetCFRecords(self, FileOutput = None):
        try:
            GetCFRecordsURL = (self.Com.Cloudflare + f"zones/{self.Zone}/dns_records")
            with requests.get(GetCFRecordsURL, headers=self.CFHeader, timeout=30) as RecordsRespon:
                # Return records as dict
                if RecordsRespon.status_code == 200:
                    RecordsData = RecordsRespon.json()
                    GetRecordsStatus = RecordsData.get("success")
                    if GetRecordsStatus == False:
                        GetRecordsError = RecordsData.get("errors")
                        logging.warning(f"Error occurred during download DNS records |API error: {GetRecordsError}")
                        return False
                    # Enable records file output
                    if FileOutput is not None:
                        RecordsOutputPath = Path(FileOutput)
                        with RecordsOutputPath.open("w") as RecordsFile:
                            json.dump(RecordsData, RecordsFile, indent = 3)
                        return FileOutput
                    else:
                        return RecordsData
                elif RecordsRespon.status_code != 200:
                    logging.warning(f"Unable connect Cloudflare API |HTTP Error: {RecordsRespon.status_code}")
                    return RecordsRespon.status_code
        except Exception as GetCFRecordsError:
            logging.exception(f"Error occurred during download DNS records |Error: {GetCFRecordsError}")
            return False
        # UNQC
    # Update CNAME records at Cloudflare
    def UpdateCFCNAME(self, UpdatePayload):
        try:
            # Records ID
            RecordID = UpdatePayload.get("cname_id")
            if not RecordID:
                logging.warning(f"Error occurred during phrasing CNAME update payload |Record ID: {RecordID}")
                return False
            UpdateCNAMEURL = (self.Com.Cloudflare + f"zones/{self.Zone}/dns_records/{RecordID}")
            # CNAME update payload
            CNAMEText = UpdatePayload.get("cname")
            CNAMEValue = UpdatePayload.get("value")
            if not (CNAMEText and CNAMEValue):
                logging.warning(f"Error occurred during phrasing CNAME update payload |CNAME: {CNAMEText} |Value: {CNAMEValue}")
                return False
            UpdateCNAMEData = {"type":"CNAME", "name":CNAMEText, "content":CNAMEValue, "proxiable":False, "proxied":False, "ttl":1}
            UpdateJSON = json.dumps(UpdateCNAMEData)
            # Update
            with requests.put(UpdateCNAMEURL, headers=self.CFHeader, data=UpdateJSON, timeout=30) as UpdateRespon:
                if UpdateRespon.status_code == 200:
                    UpdateResponData = UpdateRespon.json()
                    UpdateResponCheck = UpdateResponData.get("success")
                    if UpdateResponCheck == False:
                        UpdateCNAMEError = UpdateResponData.get("errors")
                        logging.warning(f"Error occurred during update CNAME record |API error: {UpdateCNAMEError}")
                        return False
                    return UpdateResponData
                elif UpdateRespon.status_code != 200:
                    logging.warning(f"Unable connect Cloudflare API |HTTP Error: {UpdateRespon.status_code}")
                    return UpdateRespon.status_code
        except Exception as UpdateCNAMEError:
            logging.exception(f"Error occurred during update CNAME record |Error: {UpdateCNAMEError}")
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
        self.Certificate   = "certificate.crt"
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
        CreatePayload = {"certificate_domains":CertificateDomains, "certificate_validity_days":90, "certificate_csr":CSRPayload}
        CreateJSON = json.dumps(CreatePayload)
        try:
            CreateCA = (self.Com.ZeroSSL + f"?access_key={self.ZeroSSLAuth}")
            with requests.post(CreateCA, headers=self.ZeroSSLHeader, data=CreateJSON, timeout=30) as CreateCARespon:
                if CreateCARespon.status_code == 200:
                    CreateCAData = CreateCARespon.json()
                    # Possible errors respon
                    CreateCAError = CreateCAData.get("success")
                    if CreateCAError == False:
                        CreateCAErrorStatus = CreateCAData.get("error",{}).get("type","Unknown error")
                        logging.warning(f"Error occurred during request new certificate |API error: {CreateCAErrorStatus}")
                        return False
                    # Check certificate status
                    VerifyStatus = CreateCAData.get("status", None)
                    if VerifyStatus is not None:
                        # Saving validation data
                        ValidationCacheFile = Path(self.Validation)
                        with ValidationCacheFile.open("w") as ValidationData:
                            json.dump(CreateCAData, ValidationData, indent=4)
                        return CreateCAData
                    # Catch exception
                    else:
                        logging.warning(f"Unknown error occurred during request new certificate")
                        return False
                elif CreateCARespon.status_code != 200:
                    logging.warning(f"Unable connect ZeroSSL API |HTTP Error: {CreateCARespon.status_code}")
                    return CreateCARespon.status_code
        except Exception as ErrorStatus:
            logging.exception(f"Error occurred during request new certificate |Error: {ErrorStatus}")
            return False
        # UNQC
    # Phrasing ZeroSSL verify JSON
    def ZeroSSLVerifyData(self, VerifyRequest, ValidationMethod = ('CNAME_CSR_HASH')):
        try:
            # Additional domain check
            AdditionalDomainCheck = VerifyRequest.get(self.L1,{}).get(self.L2,{}).get(self.AltName)
            AdditionalCheck = bool(AdditionalDomainCheck)
            # Certificate ID
            VerifyCertificateID = VerifyRequest.get("id", None)
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
            if ValidationMethod == ("CNAME_CSR_HASH") and not AdditionalCheck:
                CreateCAVerify = {
                    "id": VerifyCertificateID,
                    "common_name": {"cname_id": self.CommonNameID, "cname": CommonName_CNAME,"value": CommonName_VALUE}}
                # Retutn phrasing dict
                return CreateCAVerify
            # CNAME mode, additional domain
            elif ValidationMethod == ("CNAME_CSR_HASH") and AdditionalCheck:
                CreateCAVerify = {
                    "id": VerifyCertificateID,
                    "common_name": {"cname_id": self.CommonNameID, "cname": CommonName_CNAME, "value": CommonName_VALUE},
                    "additional_domains":{"cname_id": self.AltNameID, "cname": Additional_CNAME, "value": Additional_VALUE}}
                return CreateCAVerify
            # File mode
            elif ValidationMethod == ("HTTPS_CSR_HASH") and not AdditionalCheck:
                CreateCAVerify = {
                    "id": VerifyCertificateID,
                    "common_name": {"file":CommonName_FILE, "content": CommonName_CONTENT}}
                return CreateCAVerify
            # File mode, additional domain
            elif ValidationMethod == ("HTTPS_CSR_HASH") and AdditionalCheck:
                CreateCAVerify = {
                    "id": VerifyCertificateID,
                    "common_name": {"file":CommonName_FILE, "content": CommonName_CONTENT},
                    "additional_domains": {"file":Additional_FILE, "content": Additional_CONTENT}}
                return CreateCAVerify
            else:
                logging.warning(f"Unable phrasing ZeroSSL verify data |Unknown validation mode: {ValidationMethod}")
                return False
        # Error
        except Exception as VerifyDataPhrasingError:
            logging.exception(f"Error occurred during phrasing ZeroSSL verify data |Error: {VerifyDataPhrasingError}")
            return False
        # UNQC
    # Verification, when using CNAME and HTTP/HTTPS file verify
    def ZeroSSLVerification(self, CertificateID = None, ValidationMethod = ('CNAME_CSR_HASH')):
        try:
            # Reading certificate hash from cache
            if CertificateID is None or not str(CertificateID).strip():
                CacheInput = Path(self.Validation)
                with CacheInput.open("r", encoding = "utf-8") as CacheFile:
                    CacheData = json.load(CacheFile)
                CertificateID = CacheData.get("id")
            if not CertificateID:
                logging.warning("Certificate ID is empty after cache fallback")
                return False
            # Verification URL and verification method, default is CNAME
            VerificationURL = (self.Com.ZeroSSL + f"/{CertificateID}/challenges?access_key={self.ZeroSSLAuth}")
            VerifyMethodData = {"validation_method": ValidationMethod}
            VerifyJSON = json.dumps(VerifyMethodData)
            with requests.post(VerificationURL, headers=self.ZeroSSLHeader, data=VerifyJSON, timeout=30) as VerificationRespon:
                if VerificationRespon.status_code == 200:
                    VerificationData = VerificationRespon.json()
                    # Possible errors respon
                    VerifyCheck = VerificationData.get("success")
                    if VerifyCheck == False:
                        VerifyErrorStatus = VerificationData.get("error",{}).get("type","Unknown error")
                        logging.warning(f"Error occurred during verification |API error: {VerifyErrorStatus}")
                        return False
                    # Get certificate status
                    VerifyStatus = VerificationData.get("status", False)
                    return VerifyStatus
                elif VerificationRespon.status_code != 200:
                    logging.warning(f"Unable connect ZeroSSL API |HTTP Error: {VerificationRespon.status_code}")
                    return VerificationRespon.status_code
        except Exception as CAVerificationError:
            logging.exception(f"Error occurred during verification |Error: {CAVerificationError}")
            return False
        # UNQC
    # Download certificate from ZeroSSL
    def ZeroSSLDownloadCA(self, CertificateID = None):
        try:
            # Reading certificate hash from cache
            if CertificateID is None or not str(CertificateID).strip():
                CacheInput = Path(self.Validation)
                with CacheInput.open("r", encoding = "utf-8") as CacheFile:
                    CacheData = json.load(CacheFile)
                CertificateID = CacheData.get("id")
            if not CertificateID:
                logging.warning("Certificate ID is empty after cache fallback")
                return False
            # Download
            DownloadCertificateURL = (self.Com.ZeroSSL + f"/{CertificateID}/download/return?access_key={self.ZeroSSLAuth}")
            # ZeroSSL Inline download certificate need JSON header
            with requests.get(DownloadCertificateURL, headers=self.ZeroSSLHeader, timeout=30) as DownloadRespon:
                if DownloadRespon.status_code == 200:
                    CertificatePayload = DownloadRespon.json()
                    # Possible errors respon
                    DownloadCheck = CertificatePayload.get("success")
                    if DownloadCheck == False:
                        DownloadErrorStatus = CertificatePayload.get("error",{}).get("type","Unknown error")
                        logging.warning(f"Error occurred during download certificate |API error: {DownloadErrorStatus}")
                        return False
                    # Return certificate payload, inline mode check
                    CertificateString = CertificatePayload.get(self.Certificate, None)
                    if CertificateString is None:
                        logging.warning(f"Certificate payload is empty during download certificate")
                        return False
                    return CertificatePayload
                elif DownloadRespon.status_code != 200:
                    logging.error(f"Unable connect ZeroSSL API |HTTP Error: {DownloadRespon.status_code}")
                    return DownloadRespon.status_code
        except Exception as DownloadCAError:
            logging.exception(f"Error occurred during downloading |Error: {DownloadCAError}")
            return False
        # UNQC
    # Cancel certificate from ZeroSSL
    def ZeroSSLCancelCA(self, CertificateID):
        try:
            CancelCAURL = (self.Com.ZeroSSL + f"/{CertificateID}/cancel?access_key={self.ZeroSSLAuth}")
            with requests.post(CancelCAURL, headers=self.ZeroSSLHeader, timeout=30) as CancelRespon:
                if CancelRespon.status_code == 200:
                    CancelResponData = CancelRespon.json()
                    CancelStatus = CancelResponData.get("success")
                    if CancelStatus == False:
                        CancelErrorStatus = CancelResponData.get("error",{}).get("type","Unknown error")
                        logging.warning(f"Error occurred during cancel certificate |API error: {CancelErrorStatus}")
                        return False
                    return CancelResponData
                elif CancelRespon.status_code != 200:
                    logging.error(f"Unable connect ZeroSSL API |HTTP Error: {CancelRespon.status_code}")
                    return CancelRespon.status_code
        except Exception as CancelCAError:
            logging.exception(f"Error occurred during cancel certificate |Error:{CancelCAError}")
            return False
        # UNQC
    # Revoke certificate from ZeroSSL
    def ZeroSSLRevokeCA(self, CertificateID, RevokeReason = None):
        try:
            # Unspecified revoke reason
            if RevokeReason is None:
                RevokeReason = ("Unspecified")
            RevokeReasonData = {"reason":f"{RevokeReason}"}
            RevokeReasonJSON = json.dumps(RevokeReasonData)
            RevokeCAURL = (self.Com.ZeroSSL + f"/{CertificateID}/revoke?access_key={self.ZeroSSLAuth}")
            with requests.post(RevokeCAURL, headers=self.ZeroSSLHeader, data=RevokeReasonJSON ,timeout=30) as RevokeRespon:
                if RevokeRespon.status_code == 200:
                    RevokeResponData = RevokeRespon.json()
                    RevokeStatus = RevokeResponData.get("success")
                    if RevokeStatus == False:
                        RevokeErrorStatus = RevokeResponData.get("error",{}).get("type","Unknown error")
                        logging.warning(f"Error occurred during revoke certificate |API error: {RevokeErrorStatus}")
                        return False
                    return RevokeResponData
                elif RevokeRespon.status_code != 200:
                    logging.error(f"Unable connect ZeroSSL API |HTTP Error: {RevokeRespon.status_code}")
                    return RevokeRespon.status_code
        except Exception as RevokeCAError:
            logging.exception(f"Error occurred during revoke certificate |Error:{RevokeCAError}")
            return False
        # UNQC
