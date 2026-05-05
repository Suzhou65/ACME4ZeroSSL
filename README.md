# Acme4ZeroSSL
![WbH](https://github.takahashi65.info/lib_badge/written-by-human.svg)
![Python](https://github.takahashi65.info/lib_badge/python.svg)
![UM](https://github.takahashi65.info/lib_badge/active_maintenance.svg)
[![Size](https://img.shields.io/github/repo-size/Suzhou65/acme4zerossl.svg)](https://shields.io/category/size)

Python script for renew certificate from ZeroSSL.

## Contents
- [Acme4ZeroSSL](#acme4zerossl)
  * [Contents](#contents)
  * [Development Purpose](#development-purpose)
  * [Limitation](#limitation)
  * [Usage](#usage)
    + [Configuration file](#configuration-file)
    + [Cloudflare API](#cloudflare-api)
    + [ZeroSSL REST API](#zerossl-rest-api)
    + [Telegram BOTs](#telegram-bots)
    + [Webpage Server Reload or Restart](#webpage-server-reload-or-restart)
    + [cPanel Install SSL Certificate](#cpanel-install-ssl-certificate)
    + [Schedule](#schedule)
  * [Import module](#import-module)
  * [Function](#function)
    + [Verify Cloudflare API Token](#verify-cloudflare-api-token)
    + [Asking CNAME Records ID hosing on Cloudflare](#asking-cname-records-id-hosing-on-cloudflare)
    + [Verify with CNAME challenge](#verify-with-cname-challenge)
    + [Verify with HTTPS file challenge](#verify-with-https-file-challenge)
    + [Download certificate](#download-certificate)
    + [Cancel certificate](#cancel-certificate)
    + [Revoke certificate](#revoke-certificate)
  * [Self-signed certificate](#self-signed-certificate)
  * [Dependencies](#dependencies)
  * [License](#license)
  * [Resources](#resources)

## Development Purpose
I manage sh*tload of servers, including my profile page, apartment's HomeKit gateway, several Hentai@Home client. Also, some headless system based on Apache Tomcat, or cPanel hosting webserver, which don't support authentication via HTTP/HTTPS challenge file.<br>

Even though I can update CNAME record through Cloudflare API, certificate downloading and install has to be done manually. Current certificate validity is 90 days, but as that period gets shorter, those processes become more annoying and frequent.<br>

Developed to automate certificate renewal via the ZeroSSL REST API, paired with Cloudflare-hosted DNS records for CNAME challenge.

## Limitation
> **DNS hosting**<br>
> Currently support Cloudflare only.<br>

> **Domains**<br>
> Single Common Name (CN).<br>
> Or single CN with single Subject Alternative Name (SAN) pairs.<br>
> Doesn't support wildcard certificate.<br>

> **cPanel**<br>
> cPanel UAPI accessibility (URL/Username/Token).<br>
> Certificate already installed (doesn't supported initialization).<br>

## Usage
### Configuration file
Supported configuration input as `dictionary` object or `json` file.<br>
Using JSON format file storage configuration. Configuration file must include following parameters:
```json
{
   "Telegram_BOTs":{
      "Token": "",
      "ChatID": ""
   },
   "CloudflareAPI":{
      "Token": "",
      "Mail": ""
   },
  "CloudflareRecords":{
      "ZoneID": "",
      "CNAMERecordsID": ["", ""]
   },
   "ZeroSSLAPI":{
      "AccessKey": "",
      "Cache": ""
   },
   "Certificate":{
      "Domains": ["www.example.com", "example.com"],
      "ValidityDays": 90,
      "Country": "",
      "StateOrProvince": "",
      "Locality": "",
      "Organization": "",
      "OrganizationalUnit": "",
      "Config": "",
      "CSR": "",
      "PendingPK": "",
      "PK": "",
      "CA": "",
      "CAB": ""
   },
   "FileChallenge":{
      "HTMLFilePath": ""
   },
   "Cpanel":{
      "ServerUAPI": "",
      "Username": "",
      "Token": ""
   }
}
```

Configuration file must include following parameters:
> **Telegram BOTS token**<br>
> Store the  BOTs `Token` inside `Telegram_BOTs`.<br>
> `Chat channel ID` store the `ChatID`.<br>

> **Cloudflare API Key**<br>
> Store the  `Cloudflare API Token` inside `CloudflareAPI`.<br>
> `API auth email` store the `Mail`.<br>
>
> **Note:**<br>
> Please remove the `Bearer ` prefix and any whitespace.

> **Cloudflare Zone ID**<br>
> Store the  `Cloudflare Zone ID` inside `ZoneID`.<br> 
> `CNAME records ID` store the `CNAMERecordsID` list.<br>
```json
"CNAMERecordsID": ["XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX","XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"]
```
>
> If you only need ACME certification for a single domain name, simply keep one ID inside `CNAMERecordsID` list.<br>
```json
"CNAMERecordsID": ["XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"]
```
> **ZeroSSL REST API Key**<br>
> Store the  `ZeroSSL Access Key` inside `ZeroSSLAPI`.<br>
> Store the  ZeroSSL certificate verify data as JSON file at `Cache`.<br>
```json
"AccessKey": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
"Cache": "/Documents/script/cache.domain.json"
```
> **Certificate**<br>
> Store the  auth certificate's domains `Domains`.<br>
```json
"Domains": ["www.example.com", "example.com"],
```
> **If you only need to renew single domain name:** Simply keep only one domain in `Domains` list inside.<br>
```json
"Domains": ["www.example.com"],
```
> **certificate validity period**<br>
> Default is 90 days.
> Please adjust this dynamically according to ZeroSSL's roadmap based on Ballot SC-081v3
```json
"ValidityDays": 90,
```
> **Certificate signing request (CSR) configuration**<br>
> `Country` following ISO 3166-1 standard.<br>
> `StateOrProvince` for geographical information.<br>
> `Locality` for geographical information.<br>
> `Organization` is recommended for NGOs or personal businesse.<br>
> `OrganizationalUnit` is recommended for NGOs or personal businesse.<br>
```json
"Country": "JP",
"StateOrProvince": "Tokyo Metropolis",
"Locality": "Shimokitazawa",
"Organization": "STARRY",
"OrganizationalUnit": "Kessoku Bando",
```
> `Config` is is the CSR configuration file used to generate the CSR.<br>
> `CSR` is Certificate signing request saving path.<br>
```json
"Config": "/Documents/script/domain.csr.conf",
"CSR": "/Documents/script/domain.csr",
```
> Certificate section also includes paths for the active private key and certificates.<br>
> **Fail-safe:** private key won't be updated until the renewed certificate is downloaded; it's stored as a pending key in the meantime (PendingPK).<br>
```json
"PendingPK": "/Documents/script/cache.domain.key",
"PK": "/var/certificate/private.key",
"CA": "/var/certificate/certificate.crt",
"CAB": "/var/certificate/ca_bundle.crt"
```
> **FileChallenge**<br>
> Files path for HTTP/HTTPS file challenge.<br>
> Usually is your Apache/Nginx webpage folder.<br>
```json
"HTMLFilePath": "/var/www/html"
```
> **Well-known URIs:** acme-challenge URL will be automatically created by the ACME script.

### Cloudflare API
For using CNAME challenge function, you need to domain registered with Cloudflare, or choice Cloudflare as DNS hosting service.<br>
> **For safety:**<br>
> Please modify the token’s permissions. `only allowing DNS record edit` is recommended.<br>
> Also make sure to copy the secret to secure place.<br>

### ZeroSSL REST API
Log in to ZeroSSL, go to [Developer](https://app.zerossl.com/developer) page, you will find your ZeroSSL API Key, make sure to copy the secret to a secure place.<br>

> **If you suspect that your API Key has been compromised:**<br>
> Please click `Reset Key` and check is any unusual, or suspicious certificate been issued.<br>

### Telegram BOTs
Using Telegram Bot, contact [BotFather](https://t.me/botfather) create new Bot accounts.<br>

At this point the chat channel hasn't been created yet, so you can't find the `ChatID`. Running `Message` function will receive `400 Bad Request` from Telegram API, following message will printout:
```
2025-05-14 19:19:00 | Telegram ChatID is empty, notifications will not be sent.
```
You need to start the chat channel with that bot, i.e. say `Hello world` to him. Then running `GetChatID`
```python
import acme4zerossl
ConfigFile = "/documents/script/acme4zerossl.config.json"
Tg = acme4zerossl.Telegram(ConfigFile)
Tg.GetChatID()
```
Now ChatID will printout:
```
2025-05-14 19:19:18 | You ChatID is: XXXXXXXXX
```
### Webpage Server Reload or Restart
Function `Runtime.Install` supports restarting the webpage server after the certificate is downloaded (optional).<br>
> **Command type**<br>
> Adding command to `ServerCommand` with list object.<br>
> Default is `None`, after download certificate will skip webpage server reload or restart.<br>
```python
# Function
Rt.Install(CertificateContent, ServerCommand)
# Default is None
ServerCommand = None
# Apache2, using systemd
ServerCommand = ['systemctl','reload','apache2.service']
# Nginx, using systemd
ServerCommand = ['systemctl','reload','nginx']
# Nginx, using init
ServerCommand = ['/etc/init.d/nginx','reload']
```

### cPanel Install SSL Certificate
Supported cPanel UAPI operations, including:
> cPanel UAPI token verification<br>
> Certificate, private key and CA bundle upload<br>
> Certificate installing<br>
> Certificate expires date check<br>

> `script_cpanel.py` includes Telegram Bot notifications.<br>
```py
import acme4zerossl as acme

ConfigFile = "/Documents/script/acme4zerossl.config.json"
Cp = acme.Cpanel(ConfigFile)
# UAPI token verification
Cp.Verify()
# Certificate upload
Cp.UploadCertificate()
# Private key and upload
Cp.UploadPrivateKey()
# Upload CA bundle and installing
Cp.Install()
# Expires date check
Cp.CertificateCheck()
```

### Schedule
Recommend using `systemd`.<br>
> **systemd service file**<br>
> Create service file `/etc/systemd/system/acme.service` for systemd.<br>

> WorkingDirectory `/documents/script` prevent absolute/relative path issue.<br>
> ExecStart `/usr/bin/python3` depend on Python environment.<br>
> Path `/documents/script/script_cname.py` is where the ACME script is located.<br>
```conf
[Unit]
Description=ACME script
# Wait till network available
After=network-online.target
Wants=network-online.target

[Service]
# Run once every call
Type=oneshot
# Root
User=root
# Script folder absolute path
WorkingDirectory=/var/acme
# Python environment (interpreter) and script located
ExecStart=/usr/bin/python3 script_cname.py
# Log output
StandardOutput=journal
StandardError=journal
```
> **Timer file**<br>
> Next is timer file `/etc/systemd/system/acme.timer`.<br>
> The following example runs daily at 5:00 AM, plus 10 minutes after boot once the network is available.<br>
```conf
[Unit]
Description=Run ACME script everyday

[Timer]
OnCalendar=*-*-* 05:00:00
# Avoid skip cause by poweroff 
Persistent=true
# Service name
Unit=acme.service
# Adding randomized delay
RandomizedDelaySec=10m
# Avoid inaccuracy
AccuracySec=1m

[Install]
WantedBy=timers.target
```
> **Enable service**<br>
> Enable systemd timer.<br>
```shell
# Enable and start the timer
systemctl enable acme.timer
systemctl start acme.timer

# Reload systemd
systemctl daemon-reload
```


## Import module
```python
# Import as module
import acme4zerossl
# Alternative
import acme4zerossl as acme
```

## Function
### Verify Cloudflare API Token
```python
import acme4zerossl as acme

ConfigFile = "/Documents/script/acme4zerossl.config.json"
Cf = acme.Cloudflare(ConfigFile)
Cf.Verify()
```
> **Default Output**<br>
> Show result's value as string only.<br>
> Enable fully result by using `DisplayVerifyResult`<br>
```python
Cf.Verify(DisplayVerifyResult=True)
```

### Asking CNAME Records ID hosing on Cloudflare
```python
import acme4zerossl as acme

ConfigFile = "/Documents/script/acme4zerossl.config.json"
Cf = acme.Cloudflare(ConfigFile)
Cf.GetDNSRecords()
```
> **Default Output**<br>
> Output is `dictionary` containing all Cloudflare DNS records belonging to the specified Zone ID.<br>
> Adding `FileOutput` for output JSON file.<br>
```python
FileOutput = "/Documents/script/records.cloudflare.json"
Cf.GetDNSRecords(FileOutput)
```

### Verify with CNAME challenge
> **Demonstration script**<br>
> `script_cname.py` includes Telegram Bot notifications.<br>
```python
# -*- coding: utf-8 -*-
import acme4zerossl as acme
import logging
from time import sleep
from sys import exit

# Config load, dictionary or filepath
ConfigFile = "/Documents/script/acme4zerossl.config.json"
# Server reload or restart command
ServerCommand  = None

# Error handling
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
logging.basicConfig(level=logging.WARNING,filename="acme4zerossl.log",filemode="a",format=FORMAT)
# Script
def main(VerifyRetry,Interval):
    # Load object
    Rt = acme.Runtime(ConfigFile)
    Cf = acme.Cloudflare(ConfigFile)
    Zs = acme.ZeroSSL(ConfigFile)
    # Create certificates signing request
    CSRCreateCheck = Rt.CreateCSR()
    if not isinstance(CSRCreateCheck,list):
        raise RuntimeError("Error occurred during Create CSR and Private key.")
    Rt.Message("Successful create CSR and Private key.")
    # Sending CSR to ZeroSSL
    CertCreate = Zs.Create()
    if not isinstance(CertCreate,dict):
        raise RuntimeError("Error occurred during request new certificate.")
    # Parsing ZeroSSL verify
    VerifyData = Zs.PhrasingVerifyJSON(CertCreate,ValidationMethod="CNAME_CSR_HASH")
    if not isinstance(VerifyData,dict):
        raise RuntimeError("Error occurred during parsing ZeroSSL verify data.")
    # Check pending certificate ID
    CertID = VerifyData.get("id",None)
    if CertID is None:
        raise RuntimeError("Certificate hash is empty.")
    Rt.Message(f"Request success, pending certificate hash: {CertID}")
    # Check CNAME domain and payload
    UpdatePayloads = [VerifyData['common_name']]
    AdditionalDomains = VerifyData.get('additional_domains')
    if AdditionalDomains:
        UpdatePayloads.append(AdditionalDomains)
    # Update CNAME via Cloudflare API
    for UpdatePayload in UpdatePayloads:
        CNAMEUpdateCheck = Cf.UpdateCNAME(UpdatePayload)
        # Check CNAME update result
        if not isinstance(CNAMEUpdateCheck,dict):
            raise RuntimeError("Error occurred during connect to Cloudflare API update CNAME.")
        else:
            Rt.Message("Successful update CNAME from Cloudflare.")
            sleep(5)
    # Wait DNS records update and active
    sleep(60)
    # Verify CNAME challenge
    CertVerifyCheck = Zs.Verification(CertID,ValidationMethod="CNAME_CSR_HASH")
    if not isinstance(CertVerifyCheck,str):
        raise RuntimeError("Error occurred during verification.")
    # Check verify status
    if CertVerifyCheck == "draft":
        raise RuntimeError("Not verified yet.")
    # Verify passed (Under CNAME and file validation, pending_validation means verify successful)
    elif CertVerifyCheck in ("pending_validation","issued"):
        Rt.Message(f"Verify successful, now downloading certificate.")
        sleep(30)
        # Download certificates, adding retry and interval in case backlog certificate issuance
        for _ in range(VerifyRetry):
            CertContent = Zs.Download(CertID)
            # Successful download certificates
            if isinstance(CertContent,dict):
                Rt.Message("Certificate has been downloaded.")
                break
            sleep(Interval)
        else:
            raise RuntimeError(f"Unable download certificate.")
    # Undefined error
    else:
        raise RuntimeError(f"Unable to check verification status, currently verification status: {CertVerifyCheck}")
    # Install certificate to server folder
    InstallCheck = Rt.Install(CertContent,ServerCommand)
    if InstallCheck is False:
        raise RuntimeError("Error occurred during certificate install. You may need to download and install manually.")
    # Get certificate expires date
    CertExpiresDate = CertCreate.get("expires","Unknown")
    if isinstance(InstallCheck,int):
        Rt.Message(f"Certificate been renewed, will expires in {CertExpiresDate}. You may need to restart server manually.")
        return
    elif isinstance(InstallCheck,list):
        Rt.Message(f"Certificate been renewed and installed, will expires in {CertExpiresDate}.")
        return

# Runtime, including check validity date of certificate
if __name__ == "__main__":
    try:
        Rt = acme.Runtime(ConfigFile)
        # Default minimum is 14 days
        CertExpiresDays = Rt.ExpiresCheck()
        # Renew determination
        if CertExpiresDays is None:
            main(5,60)
            logging.info("Certificate has been renewed.")
            exit(0)
        # No need to renew
        else:
            Rt.Message(f"Certificate's validity date has {CertExpiresDays} days left.")
            logging.info(f"Certificate check complete |{CertExpiresDays} days left.")
            exit(0)
    except KeyboardInterrupt:
        logging.warning("Manually interrupt.")
        exit(0)
    except Exception as RenewedError:
        logging.exception(f"Script error |{RenewedError}")
        # Notify
        RenewedErrorMessage = str(RenewedError)
        Rt.Message(RenewedErrorMessage)
        exit(1)
```

### Verify with HTTPS file challenge
> **Demonstration script**<br>
> `script_httpsfile.py` includes Telegram Bot notifications.<br>
```python
# -*- coding: utf-8 -*-
import acme4zerossl as acme
import logging
from time import sleep
from sys import exit

# Config load, dictionary or filepath
ConfigFile = "/Documents/script/acme4zerossl.config.json"
# Server reload or restart command
ServerCommand  = None

# Error handling
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
logging.basicConfig(level=logging.WARNING,filename="acme4zerossl.log",filemode="a",format=FORMAT)
# Script
def main(VerifyRetry,Interval):
    Rt = acme.Runtime(ConfigFile)
    Zs = acme.ZeroSSL(ConfigFile)
    # Create certificates signing request
    CSRCreateCheck = Rt.CreateCSR()
    if not isinstance(CSRCreateCheck,list):
        raise RuntimeError("Error occurred during Create CSR and Private key.")
    Rt.Message("Successful create CSR and Private key.")
    # Sending CSR to ZeroSSL
    CertCreate = Zs.Create()
    if not isinstance(CertCreate,dict):
        raise RuntimeError("Error occurred during request new certificate.")
    # Parsing ZeroSSL verify
    VerifyData =  Zs.PhrasingVerifyJSON(CertCreate,ValidationMethod="HTTPS_CSR_HASH")
    if not isinstance(VerifyData,dict):
        raise RuntimeError("Error occurred during parsing ZeroSSL verify data.")
    # Check pending certificate ID
    CertID = VerifyData.get("id",None)
    if CertID is None:
        raise RuntimeError("Certificate hash is empty")
    Rt.Message(f"Request success, pending certificate hash: {CertID}")
    # Validation file path and content
    ValidationFiles = [VerifyData['common_name']]
    AdditionalDomains = VerifyData.get("additional_domains")
    if AdditionalDomains:
        ValidationFiles.append(AdditionalDomains)
    # Create validation file
    for ValidationFile in ValidationFiles:
        CreateValidationFileStatus = Rt.CreateValidationFile(ValidationFile)
        if CreateValidationFileStatus is not True:
            raise RuntimeError("Error occurred during create validation file.")
    # Wait server cache
    sleep(60)
    # Verify file challenge
    CertVerifyCheck = Zs.Verification(CertID,ValidationMethod="HTTPS_CSR_HASH")
    if not isinstance(CertVerifyCheck,str):
        raise RuntimeError("Error occurred during file verification.")
    # Check verify status
    if CertVerifyCheck == "draft":
        raise RuntimeError("Not verified yet.")
    # Verify passed (Under CNAME and file validation, pending_validation means verify successful)
    elif CertVerifyCheck in ("pending_validation","issued"):
        Rt.Message(f"Verify successful, now downloading certificate.")
        sleep(30)
        # Download certificates, adding retry and interval in case backlog certificate issuance
        for _ in range(VerifyRetry):
            CertContent = Zs.Download(CertID)
            # Successful download certificates
            if isinstance(CertContent,dict):
                Rt.Message("Certificate has been downloaded.")
                break
            sleep(Interval)
        else:
            raise RuntimeError(f"Unable download certificate.")
    # Undefined error
    else:
        raise RuntimeError(f"Unable to check verification status, undefined status: {CertVerifyCheck}")
    # Delete validation file
    for ValidationFile in ValidationFiles:
        Rt.DeleteValidationFile(ValidationFile)
    # Install certificate to server folder
    InstallCheck = Rt.Install(CertContent,ServerCommand)
    if InstallCheck is False:
        raise RuntimeError("Error occurred during certificate install. You may need to download and install manually.")
    # Get certificate expires date
    CertExpiresDate = CertCreate.get("expires","Unknown")
    if isinstance(InstallCheck,int):
        Rt.Message(f"Certificate been renewed, will expires in {CertExpiresDate}. You may need to restart server manually.")
        return
    elif isinstance(InstallCheck,list):
        Rt.Message(f"Certificate been renewed and installed, will expires in {CertExpiresDate}.")
        return
# Runtime, including check validity date of certificate
if __name__ == "__main__":
    try:
        Rt = acme.Runtime(ConfigFile)
        # Default minimum is 14 days
        CertExpiresDays = Rt.ExpiresCheck()
        # Renew determination
        if CertExpiresDays is None:
            main(5,60)
            logging.info("Certificate has been renewed.")
            exit(0)
        # No need to renew
        else:
            Rt.Message(f"Certificate's validity date has {CertExpiresDays} days left.")
            logging.info(f"Certificate check complete |{CertExpiresDays} days left.")
            exit(0)
    except KeyboardInterrupt:
        logging.warning("Manually interrupt.")
        exit(0)
    except Exception as RenewedError:
        logging.exception(f"Script error |{RenewedError}")
        # Notify
        RenewedErrorMessage = str(RenewedError)
        Rt.Message(RenewedErrorMessage)
        exit(1)
```

### Download certificate
```python
# -*- coding: utf-8 -*-
import acme4zerossl as acme
from sys import exit
# Config
ConfigFile = "/documents/script/acme4zerossl.config.json"
# Script
def DownloadScript(CertificateID):
    Rt = acme.Runtime(ConfigFile)
    Zs = acme.ZeroSSL(ConfigFile)
    # Download certificate payload
    CertificateContent = Zs.Download(CertificateID or None)
    # Check
    if not isinstance(CertificateContent, dict):
        raise RuntimeError("Unable download certificate")
    # Download certificate and save to folder
    elif isinstance(CertificateContent, dict) and ("certificate.crt") in CertificateContent:
        pass
    ResultCheck = Rt.Install(CertificateContent)
    if ResultCheck is False:
        raise RuntimeError("Error occurred during certificate install")
    elif isinstance(ResultCheck, int):
        Rt.Message("Certificate been downloaded to folder. You may need to restart server manually.")
    elif isinstance(ResultCheck, (list,str)):
        Rt.Message(f"Certificate been downloaded and server has reload or restart.")
# Runtime
try:
    # Input certificate hash manually
    CertificateID = input("Please input certificate ID (hash), or press ENTER using cache file: ")
    DownloadScript(CertificateID)
    exit(0)
except Exception:
    exit(1)
```

### Cancel certificate<br>
> Only certificates with status `draft` or `pending_validation` can be cancelled.<br>
> After verification, the certificates `cannot been cancelled`.<br>
```python
# -*- coding: utf-8 -*-
import acme4zerossl as acme
from sys import exit
# Config
ConfigFile = "/documents/script/acme4zerossl.config.json"
# Script
def CancelScript(CertificateID):
    Rt = acme.Runtime(ConfigFile)
    Zs = acme.ZeroSSL(ConfigFile)
    # Cancel certificate
    CancelStatus = Zs.Cancel(CertificateID)
    # Status check, Error
    if not isinstance(CancelStatus,dict):
        raise RuntimeError("Error occurred during cancel certificate")
    # Standard response, check status code
    elif isinstance(CancelStatus,dict):
        CancelResult = CancelStatus.get("success")
        if CancelResult == 1:
            Rt.Message(f"Certificate ID: {CertificateID} has been cancelled.")
        else:
            raise RuntimeError("Unable cancel certificate")
    else:
        raise RuntimeError("Error occurred during cancel certificate")
# Runtime
try:
    # Input certificate hash manually
    CertificateID = input("Please input certificate ID (hash): ")
    CancelScript(CertificateID)
    exit(0)
except Exception as ScriptError:
    print(ScriptError)
    exit(1)
```

### Revoke certificate
> **Note**<br>
> ZeroSSL REST API require reason for certificate revoke (Optional).<br>
> Only certificates with status `issued` can be revoked. If a certificate has already been successfully revoked you will get a success response nevertheless.<br>
```python
# -*- coding: utf-8 -*-
import acme4zerossl as acme
from sys import exit
# Config
ConfigFile = "/documents/script/acme4zerossl.config.json"
# Script
def RevokeScript(CertificateID):
    Rt = acme.Runtime(ConfigFile)
    Zs = acme.ZeroSSL(ConfigFile)
    # Revoke certificate
    RevokeStatus = Zs.Revoke(CertificateID)
    # Status check
    if not isinstance(RevokeStatus,dict):
        raise Exception()
    elif isinstance(RevokeStatus,dict):
        RevokeResult = RevokeStatus.get("success")
        if RevokeResult == 1:
            Rt.Message(f"Certificate ID: {CertificateID} has been revoked.")
        else:
            raise RuntimeError("Unable revoke certificate")
    else:
        raise RuntimeError("Error occurred during revoke certificate")
# Runtime
try:
    # Input certificate hash manually
    CertificateID = input("Please input certificate ID (hash): ")
    RevokeScript(CertificateID)
    exit(0)
except Exception as ScriptError:
    print(ScriptError)
    exit(1)
```

## Self-signed certificate
Use a self-signed certificate to prevent direct IP connections from leaking the domain certificate.<br>
> **Demonstration script**<br>
> standalone, functional `script_selfsigned.py`.<br>

> **Backup IP Address** configuration at lines 17-18.<br>
> **CSR config:** authority configuration at lines 20-25.<br>
> **Certificate filename and folder path:** configuration at lines 27, 29-30.<br>
> **Server command:** configuration at line 32, the same format as [CertificateInstall](#webpage-server-reload-or-restart).<br>
```python
# Backup IP address, if you really want
self.Address4Backup = ""
self.Address6Backup = None
# CSR config
self.Days         = 365
self.Country      = "JP"
self.State        = "Tokyo Metropolis"
self.Locality     = "Toshima"
self.Organization = "Tsukinomori Girl's Academy"
self.Unit         = "Concert Band Club"
# Certificate folder path, None as default path
self.CertFolder   = None
# Certificate and private key name
self.Certificate  = "selfsigned_certificate.crt"
self.PrivateKey   = "selfsigned_certificate.key"
# Server command
self.WebServer    = None
```

## Dependencies
### Python version
Tested on the following Python versions:<br>
+ 3.14.2
+ 3.12.11
+ 3.11.9
+ 3.9.6
+ 3.9.2

### Python module
+ logging
+ pathlib
+ json
+ datetime
+ textwrap
+ requests
+ subprocess
+ time
+ sys

## License
General Public License -3.0

## Resources
### ZeroSSL API
- [ZeroSSL REST API documentation](https://zerossl.com/documentation/api/) the official documentation.

### Reference repository
- [ZeroSSL-CertRenew](https://github.com/ajnik/ZeroSSL-CertRenew/tree/master) for HTTP/HTTPS challenge file.
