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
a4zlog = logging.getLogger(__name__)

class API():
    def __init__(self):
        self.Cloudflare = "https://api.cloudflare.com/client/v4/"
        self.Telegram   = "https://api.telegram.org/bot"
        self.ZeroSSL    = "https://api.zerossl.com/certificates"

# Configuration function, reading json file
class Configuration():
    def __init__(self,ConfigFilePath):
        try:
            # Script config path
            ConfigPathInput = Path(ConfigFilePath)
            # Local path
            LocFolderPath = Path(__file__).resolve().parent
            # Local path with config name input
            LocConfig = LocFolderPath / ConfigPathInput.name
            # Read configuration
            with ConfigPathInput.open("r",encoding="utf-8") as ConfigContent:
                    self.Load = json.load(ConfigContent)
        # Try to find configuration file at local folder
        except FileNotFoundError:
            with LocConfig.open("r",encoding="utf-8") as ConfigContent:
                self.Load = json.load(ConfigContent)
        # Error
        except Exception as ReadConfigError:
            a4zlog.exception(f"Unable reading configuration |Error: {ReadConfigError}")
            raise
        # QC 2026A16

# Runtime package
class Runtime():
    def __init__(self,ConfigFilePath):
        try:
            self.RuntimeConfig = Configuration(ConfigFilePath).Load
            # File path
            self.Cache         = self.RuntimeConfig['ZeroSSLAPI']['Cache']
            self.CSRConfigFile = self.RuntimeConfig['Certificate']['Config']
            self.CSROutput     = self.RuntimeConfig['Certificate']['CSR']
            self.PendingPK     = self.RuntimeConfig['Certificate']['PendingPK']
            self.ActivePK      = self.RuntimeConfig['Certificate']['PK']
            self.Certificate   = self.RuntimeConfig['Certificate']['CA']
            self.CertificateBA = self.RuntimeConfig['Certificate']['CAB']
            # File path for HTTP/HTTPS file validation
            self.Fileverify    = self.RuntimeConfig['FileChallenge']['HTMLFilePath']
            # CSR config
            self.Country       = self.RuntimeConfig['Certificate']['Country']
            self.State         = self.RuntimeConfig['Certificate']['StateOrProvince']
            self.Locality      = self.RuntimeConfig['Certificate']['Locality']
            self.Organization  = self.RuntimeConfig['Certificate']['Organization']
            self.Unit          = self.RuntimeConfig['Certificate']['OrganizationalUnit']
            # Domains list
            self.DomainList    = self.RuntimeConfig['Certificate']['Domains']
            self.CommonName    = self.DomainList[0] if len(self.DomainList) > 0 else ""
            self.AltName       = self.DomainList[1] if len(self.DomainList) > 1 else ""
            # Terminal text width
            self.MessageWidth  = 100
        # Class initial error
        except Exception as RuntimeInitialError:
            a4zlog.exception(f"Runtime_Initialization_Error |{RuntimeInitialError}")
            raise

    # Print runtime info
    def Message(self,MessageText):
        try:
            # Time prompt
            EventTime = datetime.datetime.now()
            TextPrintTime = EventTime.strftime("%H:%M:%S")
            TextPrefix = (f"{TextPrintTime} |")
            # Time prompt length
            UsableWidth = self.MessageWidth - len(TextPrefix)
            SequentIndent = " " * len(TextPrefix)
            Wrapping = textwrap.fill(MessageText, width=UsableWidth, subsequent_indent=SequentIndent)
            print(TextPrefix + Wrapping)
        # Error, unable printout runtime message
        except Exception as RuntimeMessagePrintError:
            a4zlog.warning(f"Unable printout runtime |{RuntimeMessagePrintError}")
        # QC 2025K21

    # Check certificate expires, default minimum is 14 days
    def ExpiresCheck(self,Minimum=(14)):
        # Load config for cache path
        CacheFilePath = Path(self.Cache)
        # Read cache get certificate expires
        try:
            with CacheFilePath.open("r",encoding="utf-8") as CacheCheck:
                CacheData = json.load(CacheCheck)
        # Cache file not found, means first time running ACME4SSL
        except FileNotFoundError:
            a4zlog.info("ZeroSSL cache file not found, assume an initialization situation")
            return None
        # Get expires
        try:
            # Translate cache file certificate expires string into time format
            ExpiresTime = datetime.datetime.strptime(CacheData.get("expires"),"%Y-%m-%d %H:%M:%S")
            # Currently time
            CurrentTime = datetime.datetime.now()
            # Calculate
            TimeDifference = ExpiresTime - CurrentTime
            # No need renewed
            if TimeDifference.days > Minimum:
                return TimeDifference.days
            # Below minimum, renewed
            elif TimeDifference.days <= Minimum:
                return None
        # Calculate error, force renewed
        except Exception as ExpiresCheckError:
            a4zlog.warning(f"Unable check certificate expires, force renewed |Error: {ExpiresCheckError}")
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
                AltNames1,AltNames2,
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
            a4zlog.exception(f"Error occurred during phrasing CSR config |Error: {CSRConfigError}")
            return False
        # QC 2026A19

    # Create certificates signing request and PK
    def CreateCSR(self):
        try:
            CSRConfigContents = self.CSRConfig()
            if not isinstance(CSRConfigContents,list):
                a4zlog.error(f"Unable create CSR file due to wrong CSR config")
                return False
            # Path check
            CSRConfigPath = Path(self.CSRConfigFile)
            CSRConfigPath.parent.mkdir(parents=True,exist_ok=True)
            Path(self.PendingPK).parent.mkdir(parents=True,exist_ok=True)
            Path(self.CSROutput).parent.mkdir(parents=True,exist_ok=True)
            with CSRConfigPath.open("w",encoding="utf-8") as CSRSignConfig:
                # Drop empty alt names
                for CSRConfigLine in filter(None,CSRConfigContents):
                    CSRSignConfig.write(CSRConfigLine+"\n")
            # OpenSSL generate command
            OpensslCommand = ["openssl","req","-new","-nodes","-newkey","rsa:2048",
                              "-keyout",f"{self.PendingPK}","-out",f"{self.CSROutput}","-config",f"{self.CSRConfigFile}"]
            # Using OpenSSL generate CSR and PK
            CsrStatus = subprocess.Popen(OpensslCommand,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            # Discard openssl command output
            stdout, stderr = CsrStatus.communicate()
            # Check openssl command successful
            if CsrStatus.returncode == 0:
                return OpensslCommand
            else:
                # Logging stderr for debug
                a4zlog.warning(f"Unable running OpenSSL command | Output:{stdout} |Error:{stderr}")
                return False
        except Exception as CreateCSRError:
            a4zlog.exception(f"Error occurred during create CSR file |Error: {CreateCSRError}")
            return False
        # QC 2026A19

    # Create and write ACME Challenge file
    def CreateValidationFile(self,VerifyRequestFile):
        try:
            # Part of file path and name
            ValidationFile = VerifyRequestFile.get("file")
            # Empty
            if not ValidationFile:
                a4zlog.warning("Unable create challenge file with empty path")
                return False
            else:
                ValidationFilePath = Path(ValidationFile)
                FolderPath = Path(self.Fileverify)
                FullFilePath = FolderPath / ValidationFilePath
            # Check folder inside webpage folder
            FullFilePath.parent.mkdir(parents=True,exist_ok=True)
            # File content, empty string as fail-safe
            ChallengeTexts = VerifyRequestFile.get("content","")
            # Open File
            with FullFilePath.open("w",encoding="utf-8") as ChallengeFile:
                # Write-in ZeroSSL challenge file content
                if isinstance(ChallengeTexts,list):
                    for ChallengeText in ChallengeTexts:
                        ChallengeFile.write(ChallengeText + "\n")
                # If ZeroSSL content became string
                elif isinstance(ChallengeTexts,str):
                    ChallengeFile.write(ChallengeTexts + "\n")
                # Fail-safe, may be empty or blank
                else:
                    ChallengeFile.write(str(ChallengeTexts) + "\n")
            # Challenge file create notice
            self.Message(f"Challenge has been created at: {FullFilePath}")
            return True
        except Exception as CreateValidationFileError:
            a4zlog.exception(f"Error occurred during create challenge file |Error: {CreateValidationFileError}")
            return False
        # QC 2025A19

    # Delete ACME Challenge file after verify
    def CleanValidationFile(self,VerifyRequestFile):
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
            a4zlog.exception(f"Error occurred during delete challenge file |Error: {CleanValidationFileError}")
        # QC 2026A19

    # Install certificate to server folder, reload is optional
    def CertificateInstall(self,CertificateContent,ServerCommand=None):
        try:
            # Move private key from pending to folder
            PKPending = Path(self.PendingPK)
            PKActive = Path(self.ActivePK)
            PKActive.parent.mkdir(parents=True,exist_ok=True)
            with PKPending.open("r") as PendingPrivateKey,PKActive.open("w") as ActivePrivateKey:
                ActivePrivateKey.write(PendingPrivateKey.read())
            # Certificate
            Certificate = Path(self.Certificate)
            Certificate.parent.mkdir(parents=True,exist_ok=True)
            CAString = CertificateContent.get("certificate.crt","")
            with Certificate.open("w") as ActiveCertificate:
                ActiveCertificate.write(CAString)
            # Save certificate authority bundle
            CertificateBA = Path(self.CertificateBA)
            CertificateBA.parent.mkdir(parents=True,exist_ok=True)
            CABString = CertificateContent.get("ca_bundle.crt","")
            with CertificateBA.open("w") as ActiveCertificateBA:
                ActiveCertificateBA.write(CABString)
            sleep(5)
            # Server reload or restart option
            if ServerCommand is not None:
                ServerStatus = subprocess.Popen(ServerCommand,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                # Discard output
                stdout, stderr = ServerStatus.communicate()
                # Check if reboot command successful
                if ServerStatus.returncode == 0:
                    return ServerCommand
                # Restart or reload fail
                else:
                    a4zlog.error(f"Unable running server reload/restart command |Output:{stdout} |Error:{stderr}")
                    return False
            else:
                return 200
        except Exception as CertificateInstallError:
            a4zlog.exception(f"Error occurred during install certificate or reload/restart server |Error: {CertificateInstallError}")
            return False
        # QC 2025K21

# Sending Telegram message
class Telegram():
    def __init__(self,ConfigFilePath):
        try:
            self.TgConfig     = Configuration(ConfigFilePath).Load
            self.BotToken     = self.TgConfig['Telegram_BOTs']['Token']
            self.ChatID       = self.TgConfig['Telegram_BOTs']['ChatID']
            self.Domainheader = self.TgConfig['Certificate']['Domains'][0]
            self.Com = API()
            # Print message
            self.RtM          = Runtime(ConfigFilePath)
        except Exception as TelegramInitialError:
            a4zlog.exception(f"Telegram__init__ |{TelegramInitialError}")
            raise

    # Set default message for testing
    def Message2Me(self,TelegramMessage="Here, the world!"):
        try:
            # Disable message sending
            if not str(self.BotToken).strip():
                return
            # Text content with domain name
            MessageHeader = (f"{self.Domainheader}\n" + TelegramMessage)
            MessageText = {"chat_id":f"{self.ChatID}","text":MessageHeader}
            # Connetc URL
            TelegramSendURL = (self.Com.Telegram + f"{self.BotToken}/sendMessage")
            with requests.Session() as MessageSender:
                PostResponse = MessageSender.post(TelegramSendURL,json=MessageText,timeout=30)
            if PostResponse.status_code == 200:
                # Runtime printout
                self.RtM.Message(TelegramMessage)
            elif PostResponse.status_code == 400:
                a4zlog.warning(f"Telegram ChatID is empty, notifications will not be sent")
            else:
                a4zlog.warning(f"Unable sending notifications |HTTP Error: {PostResponse.status_code}")
        except Exception as Message2MeError:
            a4zlog.exception(f"Error occurred during sending notifications |Error: {Message2MeError}")
        # QC 2026A29

    # Get Telegram ChatID
    def GetChatID(self):
        try:
            # Disable ChatID checker
            if not str(self.BotToken).strip():
                return
            # Connetc URL
            AskChatIDURL = (self.Com.Telegram + f"{self.BotToken}/getUpdates")
            with requests.Session() as AskChatID:
                ChatIDResponse = AskChatID.post(AskChatIDURL,timeout=30)
            if ChatIDResponse.status_code == 200:
                TelegramData = ChatIDResponse.json()
            else:
                a4zlog.warning(f"Unable get ChatID |HTTP Error: {ChatIDResponse.status_code}")
                return
            # Check JSON
            AskChatIDResult = TelegramData.get("result")
            # Empty result
            if not AskChatIDResult:
                self.RtM.Message("You must send message to bot at first")
                return
            else:
                # Select ChatID
                CheckChatList = AskChatIDResult.get("result")
                CheckChatResult = CheckChatList[0]
                CheckChatID = CheckChatResult.get("message",{}).get("chat",{}).get("id")
                self.RtM.Message(f"You ChatID is: {CheckChatID}")
        except Exception as GetChatIDError:
            a4zlog.exception(f"Error occurred during get ChatID |Error: {GetChatIDError}")
        # QC 2026A29

# Cloudflare API package
class Cloudflare():
    def __init__(self,ConfigFilePath):
        try:
            self.CfConfig = Configuration(ConfigFilePath).Load
            self.Token    = self.CfConfig['CloudflareAPI']['Token']
            self.Zone     = self.CfConfig['CloudflareRecords']['ZoneID']
            self.Com = API()
            # Generate Cloudflare API request header
            self.CFHeader = {"Authorization":f"Bearer {self.Token}","Content-Type":"application/json"}
        except Exception as CloudflareInitialError:
            a4zlog.exception(f"Cloudflare__init__ |{CloudflareInitialError}")

    # Verify Cloudflare API token
    def VerifyCFToken(self,DisplayVerifyResult=None):
        try:
            VerifTokenAPI = (self.Com.Cloudflare + "user/tokens/verify")
            with requests.Session() as TokenVerify:
                TokenVerifyResponse = TokenVerify.get(VerifTokenAPI,headers=self.CFHeader,timeout=30)
                if TokenVerifyResponse.status_code == 200:
                    TokenVerifyData = TokenVerifyResponse.json()
                else:
                    a4zlog.warning(f"Unable connect Cloudflare API |HTTP Error: {TokenVerifyResponse.status_code}")
                    return False
            # Check respon status
            VerifyCheckStatus = TokenVerifyData.get("success")
            # Error
            if VerifyCheckStatus == False:
                TokenVerifyError = TokenVerifyData.get("errors")
                a4zlog.warning(f"Error occurred during update verify token |API error: {TokenVerifyError}")
                return False
            # Success
            if DisplayVerifyResult is None:
                return TokenVerifyData.get("result",{}).get("status")
            else:
                return TokenVerifyData
        except Exception as VerifyCFTokenError:
            a4zlog.exception(f"Error occurred during verify Cloudflare API token |Error: {VerifyCFTokenError}")
            return False
        # QC 2026A29

    # Download all DNS records from Cloudflare
    def GetCFRecords(self,FileOutput=None):
        try:
            GetZoneDNSRecordsAPI = (self.Com.Cloudflare + f"zones/{self.Zone}/dns_records")
            with requests.Session() as GetCloudflareRecords:
                RecordsRespon = GetCloudflareRecords.get(GetZoneDNSRecordsAPI,headers=self.CFHeader,timeout=30)
                # Check HTTP status
                if RecordsRespon.status_code == 200:
                    RecordsResponData = RecordsRespon.json()
                else:
                    a4zlog.warning(f"Unable connect Cloudflare API |HTTP Error: {RecordsRespon.status_code}")
                    return False
            # Return records as dict
            GetRecordsStatus = RecordsResponData.get("success")
            if GetRecordsStatus == False:
                GetRecordsError = RecordsResponData.get("errors")
                a4zlog.warning(f"Error occurred during download DNS records |API error: {GetRecordsError}")
                return False
            # Enable records file output
            if FileOutput is not None:
                RecordsOutputPath = Path(FileOutput)
                with RecordsOutputPath.open("w",encoding="utf-8") as RecordsFile:
                    json.dump(RecordsResponData,RecordsFile,indent=3)
                return FileOutput
            else:
                return RecordsResponData
        except Exception as GetCFRecordsError:
            a4zlog.exception(f"Error occurred during download DNS records |Error: {GetCFRecordsError}")
            return False
        # QC 2026A29

    # Update CNAME records at Cloudflare
    def UpdateCFCNAME(self,UpdatePayload):
        try:
            # Records ID check
            RecordID = UpdatePayload.get("cname_id")
            if not RecordID:
                a4zlog.warning(f"Error occurred during phrasing CNAME update payload |Record ID: {RecordID}")
                return False
            # CNAME update payload
            CNAMEText = UpdatePayload.get("cname")
            CNAMEValue = UpdatePayload.get("value")
            if not (CNAMEText and CNAMEValue):
                a4zlog.warning(f"Error occurred during phrasing CNAME update payload |CNAME: {CNAMEText} |Value: {CNAMEValue}")
                return False
            # Payload
            UpdateCNAMEContent = {"type":"CNAME","name":CNAMEText,"content":CNAMEValue,"proxiable":False,"proxied":False,"ttl":1}
            UpdateCNAMEJSON = json.dumps(UpdateCNAMEContent)
            # Update
            UpdateCNAMEAPI = (self.Com.Cloudflare + f"zones/{self.Zone}/dns_records/{RecordID}")
            with requests.Session() as RequestCNAMEUpdate:
                UpdateRespon = RequestCNAMEUpdate.put(UpdateCNAMEAPI,headers=self.CFHeader,data=UpdateCNAMEJSON,timeout=30)
                if UpdateRespon.status_code == 200:
                    UpdateResponData = UpdateRespon.json()
                else:
                    a4zlog.warning(f"Unable connect Cloudflare API |HTTP Error: {UpdateRespon.status_code}")
                    return False
            # Check
            UpdateResponCheck = UpdateResponData.get("success")
            if UpdateResponCheck == False:
                UpdateCNAMEError = UpdateResponData.get("errors")
                a4zlog.warning(f"Error occurred during update CNAME record |API error: {UpdateCNAMEError}")
                return False
            else:
                return UpdateResponData
        except Exception as UpdateCNAMEError:
            a4zlog.exception(f"Error occurred during update CNAME record |Error: {UpdateCNAMEError}")
            return False
        # QC 2026A20

# ZeroSSL REST API package
class ZeroSSL():
    def __init__(self,ConfigFilePath):
        try:
            self.ZeroSSLConfig = Configuration(ConfigFilePath).Load
            self.ZeroSSLAuth   = self.ZeroSSLConfig['ZeroSSLAPI']['AccessKey']
            self.ZeroSSLCSR    = self.ZeroSSLConfig['Certificate']['CSR']
            self.Validation    = self.ZeroSSLConfig['ZeroSSLAPI']['Cache']
            self.DomainList    = self.ZeroSSLConfig['Certificate']['Domains']
            self.CommonName    = self.DomainList[0]
            self.AltName       = self.DomainList[1] if len(self.DomainList) > 1 else ""
            # Please dynamic modify following ZeroSSL roadmap based on Ballot SC-081v3
            self.ValidityDays  = self.ZeroSSLConfig['Certificate']['ValidityDays']
            # ZeroSSL JSON structure
            self.L1            = "validation"
            self.L2            = "other_methods"
            self.CNAME         = "cname_validation_p1"
            self.VALUE         = "cname_validation_p2"
            self.FILE          = "file_validation_url_https"
            self.CONTENT       = "file_validation_content"
            # Check ZeroSSL certificate payload when downloading inline
            self.Certificate   = "certificate.crt"
            # Cloudflare
            self.CNAMEList     = self.ZeroSSLConfig['CloudflareRecords']['CNAMERecordsID']
            self.CommonNameID  = self.CNAMEList[0] if self.CNAMEList else ""
            self.AltNameID     = self.CNAMEList[1] if len(self.CNAMEList) > 1 else ""
            # REST API and Header
            self.Com = API()
            self.ZeroSSLHeader = {"Content-Type":"application/json"}
        except Exception as ZeroSSLInitialError:
            a4zlog.exception(f"ZeroSSL__init__ |{ZeroSSLInitialError}")

    # Sending certificate create request
    def ZeroSSLCreateCA(self):
        try:
            # Read Certificates signing request
            CSRFile = Path(self.ZeroSSLCSR)
            with CSRFile.open("r") as CSRFileData:
                CSRPayload = CSRFileData.read()
            # Reading domain
            if len(self.DomainList) > 1 and self.DomainList[1]:
                CertificateDomains = f"{self.DomainList[0]},{self.DomainList[1]}"
            else:
                CertificateDomains = f"{self.DomainList[0]}"
            # Package as JSON
            CertificateCreateContent = {"certificate_domains":CertificateDomains,"certificate_validity_days":self.ValidityDays,"certificate_csr":CSRPayload}
            CertificateCreateJSON = json.dumps(CertificateCreateContent)
            # URL
            CertificateCreateREST = (self.Com.ZeroSSL + f"?access_key={self.ZeroSSLAuth}")
            with requests.Session() as RequestCreate:
                CreateRespon = RequestCreate.post(CertificateCreateREST,headers=self.ZeroSSLHeader,data=CertificateCreateJSON,timeout=30)
                if CreateRespon.status_code == 200:
                    CreateResponData = CreateRespon.json()
                else:
                    a4zlog.warning(f"Unable connect ZeroSSL API |HTTP Error: {CreateRespon.status_code}")
                    return False
             # Possible errors respon
            CreateCAError = CreateResponData.get("success")
            if CreateCAError == False:
                CreateCAErrorStatus = CreateResponData.get("error",{}).get("type","Unknown error")
                a4zlog.warning(f"Error occurred during request new certificate |API error: {CreateCAErrorStatus}")
                return False
            # Check certificate status
            VerifyStatus = CreateResponData.get("status",None)
            if VerifyStatus is not None:
                # Saving validation data
                ValidationCacheFile = Path(self.Validation)
                with ValidationCacheFile.open("w",encoding="utf-8") as ValidationData:
                    json.dump(CreateResponData,ValidationData,indent=4)
                return CreateResponData
            # Catch exception
            else:
                a4zlog.warning(f"Unknown error occurred during request new certificate")
                return False
        except Exception as ErrorStatus:
            a4zlog.exception(f"Error occurred during request new certificate |Error: {ErrorStatus}")
            return False
        # QC 2026A20

    # Phrasing ZeroSSL verify JSON
    def ZeroSSLVerifyData(self,VerifyRequest,ValidationMethod="CNAME_CSR_HASH"):
        try:
            # Additional domain check
            AdditionalDomainCheck = VerifyRequest.get(self.L1,{}).get(self.L2,{}).get(self.AltName)
            AdditionalCheck = bool(AdditionalDomainCheck)
            # Certificate ID
            VerifyCertificateID = VerifyRequest.get("id",None)
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
            # CNAME_CSR_HASH
            if ValidationMethod == "CNAME_CSR_HASH" and not AdditionalCheck:
                CreateCAVerify = {"id":VerifyCertificateID,
                                  "common_name":{"cname_id":self.CommonNameID,"cname":CommonName_CNAME,"value":CommonName_VALUE}}
                # Retutn phrasing dict
                return CreateCAVerify
            # CNAME_CSR_HASH, additional domain
            elif ValidationMethod == "CNAME_CSR_HASH" and AdditionalCheck:
                CreateCAVerify = {"id":VerifyCertificateID,
                                  "common_name":{"cname_id":self.CommonNameID,"cname":CommonName_CNAME,"value":CommonName_VALUE},
                                  "additional_domains":{"cname_id":self.AltNameID,"cname":Additional_CNAME,"value":Additional_VALUE}}
                return CreateCAVerify
            # HTTPS_CSR_HASH
            elif ValidationMethod == "HTTPS_CSR_HASH" and not AdditionalCheck:
                CreateCAVerify = {"id":VerifyCertificateID,
                                  "common_name":{"file":CommonName_FILE,"content":CommonName_CONTENT}}
                return CreateCAVerify
            # HTTPS_CSR_HASH, additional domain
            elif ValidationMethod == "HTTPS_CSR_HASH" and AdditionalCheck:
                CreateCAVerify = {"id":VerifyCertificateID,
                                  "common_name":{"file":CommonName_FILE,"content":CommonName_CONTENT},
                                  "additional_domains":{"file":Additional_FILE,"content":Additional_CONTENT}}
                return CreateCAVerify
            else:
                a4zlog.warning(f"Unable phrasing ZeroSSL verify data |Validation mode: {ValidationMethod}")
                return False
        # Error
        except Exception as VerifyDataPhrasingError:
            a4zlog.exception(f"Error occurred during phrasing ZeroSSL verify data |Error: {VerifyDataPhrasingError}")
            return False
        # QC 2026A19, CNAME und HTTPS_FILE

    # Verification, when using CNAME and HTTP/HTTPS file verify
    def ZeroSSLVerification(self,CertificateID=None,ValidationMethod="CNAME_CSR_HASH"):
        try:
            # Reading certificate hash from cache
            if CertificateID is None or not str(CertificateID).strip():
                CacheInput = Path(self.Validation)
                with CacheInput.open("r",encoding="utf-8") as CacheFile:
                    CacheData = json.load(CacheFile)
                CertificateID = CacheData.get("id")
            if not CertificateID:
                a4zlog.warning("Certificate ID is empty after cache fallback")
                return False
            # Verification URL and verification method, default is CNAME
            VerificationREST = (self.Com.ZeroSSL + f"/{CertificateID}/challenges?access_key={self.ZeroSSLAuth}")
            VerifyMethodData = {"validation_method":ValidationMethod}
            VerifyMethodJSON = json.dumps(VerifyMethodData)
            with requests.Session() as RequestVerification:
                VerificationRespon = RequestVerification.post(VerificationREST,headers=self.ZeroSSLHeader,data=VerifyMethodJSON,timeout=30)
                if VerificationRespon.status_code == 200:
                    VerificationResponData = VerificationRespon.json()
                else:
                    a4zlog.warning(f"Unable connect ZeroSSL API |HTTP Error: {VerificationRespon.status_code}")
                    return False
            # Possible errors respon
            VerifyCheck = VerificationResponData.get("success")
            if VerifyCheck == False:
                VerifyErrorStatus = VerificationResponData.get("error",{}).get("type","Unknown error")
                a4zlog.warning(f"Error occurred during verification |API error: {VerifyErrorStatus}")
                return False
            # Get certificate status
            VerifyStatus = VerificationResponData.get("status",False)
            return VerifyStatus                
        except Exception as CAVerificationError:
            a4zlog.exception(f"Error occurred during verification |Error: {CAVerificationError}")
            return False
        # QC 2026A19

    # Download certificate from ZeroSSL
    def ZeroSSLDownloadCA(self,CertificateID=None):
        try:
            # Reading certificate hash from cache
            if CertificateID is None or not str(CertificateID).strip():
                CacheInput = Path(self.Validation)
                with CacheInput.open("r",encoding="utf-8") as CacheFile:
                    CacheData = json.load(CacheFile)
                CertificateID = CacheData.get("id")
            if not CertificateID:
                a4zlog.warning("Certificate ID is empty after cache fallback")
                return False
            # Download
            CertificateDownloadREST = (self.Com.ZeroSSL + f"/{CertificateID}/download/return?access_key={self.ZeroSSLAuth}")
            # ZeroSSL Inline download certificate need JSON header
            with requests.Session() as RequestDownload:
                DownloadRespon = RequestDownload.get(CertificateDownloadREST,headers=self.ZeroSSLHeader,timeout=30)
                if DownloadRespon.status_code == 200:
                    DownloadResponData = DownloadRespon.json()
                else:
                    a4zlog.error(f"Unable connect ZeroSSL API |HTTP Error: {DownloadRespon.status_code}")
                    return False
            # Possible errors respon
            DownloadCheck = DownloadResponData.get("success")
            if DownloadCheck == False:
                DownloadErrorStatus = DownloadResponData.get("error",{}).get("type","Unknown error")
                a4zlog.warning(f"Error occurred during download certificate |API error: {DownloadErrorStatus}")
                return False
            # Return certificate payload, inline mode check
            if not DownloadResponData.get(self.Certificate,"").strip():
                a4zlog.warning(f"Certificate payload is empty during download certificate")
                return False
            return DownloadResponData
        except Exception as DownloadCAError:
            a4zlog.exception(f"Error occurred during downloading |Error: {DownloadCAError}")
            return False
        # QC 2026A20

    # Cancel certificate from ZeroSSL
    def ZeroSSLCancelCA(self,CertificateID):
        try:
            CertificateCancelREST = (self.Com.ZeroSSL + f"/{CertificateID}/cancel?access_key={self.ZeroSSLAuth}")
            with requests.Session() as RequestCancel:
                CancelRespon = RequestCancel.post(CertificateCancelREST,headers=self.ZeroSSLHeader,timeout=30)
                if CancelRespon.status_code == 200:
                    CancelResponData = CancelRespon.json()
                else:
                    a4zlog.error(f"Unable connect ZeroSSL API |HTTP Error: {CancelRespon.status_code}")
                    return False
            # Check status
            CancelStatus = CancelResponData.get("success")
            if CancelStatus == False:
                CancelErrorStatus = CancelResponData.get("error",{}).get("type","Unknown error")
                a4zlog.warning(f"Error occurred during cancel certificate |API error: {CancelErrorStatus}")
                return False
            return CancelResponData
        except Exception as CancelCAError:
            a4zlog.exception(f"Error occurred during cancel certificate |Error:{CancelCAError}")
            return False
        # QC 2026A20

    # Revoke certificate from ZeroSSL
    def ZeroSSLRevokeCA(self,CertificateID,RevokeReason=None):
        try:
            # Unspecified revoke reason
            if RevokeReason is None:
                RevokeReason = "Unspecified"
            RevokeReasonData = {"reason":f"{RevokeReason}"}
            RevokeReasonJSON = json.dumps(RevokeReasonData)
            CertificateRevokeREST = (self.Com.ZeroSSL + f"/{CertificateID}/revoke?access_key={self.ZeroSSLAuth}")
            with requests.Session() as RequestRevoke:
                RevokeRespon = RequestRevoke.post(CertificateRevokeREST,headers=self.ZeroSSLHeader,data=RevokeReasonJSON,timeout=30)
                if RevokeRespon.status_code == 200:
                    RevokeResponData = RevokeRespon.json()
                else:
                    a4zlog.error(f"Unable connect ZeroSSL API |HTTP Error: {RevokeRespon.status_code}")
                    return False
            # Check status
            RevokeStatus = RevokeResponData.get("success")
            if RevokeStatus == False:
                RevokeErrorStatus = RevokeResponData.get("error",{}).get("type","Unknown error")
                a4zlog.warning(f"Error occurred during revoke certificate |API error: {RevokeErrorStatus}")
                return False
            return RevokeResponData
        except Exception as RevokeCAError:
            a4zlog.exception(f"Error occurred during revoke certificate |Error:{RevokeCAError}")
            return False
        # UNQC
