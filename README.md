# Acme4ZeroSSL
[![Python](https://github.takahashi65.info/lib_badge/python.svg)](https://www.python.org/)
[![UA](https://github.takahashi65.info/lib_badge/active_maintenance.svg)](https://github.com/Suzhou65/acme4zerossl)
[![Size](https://img.shields.io/github/repo-size/Suzhou65/acme4zerossl.svg)](https://shields.io/category/size)

Python script for renew certificate from ZeroSSL.

## Contents
- [Acme4ZeroSSL](#acme4zerossl)
  * [Contents](#contents)
  * [Development Purpose](#development-purpose)
  * [Limitation](#limitation)
  * [Usage](#usage)
    + [Configuration file](#configuration-file)
    + [Cloudflare API](#Cloudflare-api)
    + [ZeroSSL REST API](#zerossl-rest-api)
    + [Telegram BOTs](#telegram-bots)
    + [Webpage Server Reload or Restart](#webpage-server-reload-or-restart)
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
I manage sh*tload of servers, including my profile page, apartment's HomeKit gateway, several Hentai@Home client. Also, some headless system based on Apache Tomcat, which don't support authentication via HTTP/HTTPS challenge file.<br>

Even though I can update CNAME record through Cloudflare API, certificate downloading and install has to be done manually. Current certificate validity is 90 days, but as that period gets shorter, those process becomes more annoying and frequent.<br>

Developed to automate renewal certificate with ZeroSSL REST API, pair with Cloudflare hosting DNS records for CNAME challenge.

## Limitation
> **DNS hosting**<br>
> Currently support Cloudflare only.<br>

> **Domains**<br>
> Single Common Name (CN).<br>
> Or single CN with single Subject Alternative Name (SAN) pairs.<br>
> Doesn't support wildcard certificate.<br>

## Usage
### Configuration file
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
   }
}
```
Configuration file must include following parameters:
> **Telegram BOTS token**<br>
> Storage BOTs `Token` inside `Telegram_BOTs`.<br>
> `Chat channel ID` storage at `ChatID`.<br>

> **Cloudflare API Key**<br>
> Storage `Cloudflare API Token` inside `CloudflareAPI`.<br>
> `API authy email` storage at `Mail`.<br>
>
> **Note:**<br>
> Please remove the `Bearer` string and blank.

> **Cloudflare Zone ID**<br>
> Storage `Cloudflare Zone ID` inside `ZoneID`.<br> 
> `CNAME records ID` storage at `CNAMERecordsID` list.<br>
```json
"CNAMERecordsID": ["XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX","XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"]
```
>
> If you only need ACME certification for a single domain name, simply keep one ID inside `CNAMERecordsID` list.<br>
```json
"CNAMERecordsID": ["XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"]
```
> **ZeroSSL REST API Key**<br>
> Storage `ZeroSSL Access Key` inside `ZeroSSLAPI`.<br>
> Storage ZeroSSL certificate verify data as JSON file at `Cache`.<br>
```json
"AccessKey": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
"Cache": "/Documents/script/cache.domain.json"
```
> **Certificate**<br>
> Storage dertificate's domains `Domains`.<br>
```json
"Domains": ["www.example.com", "example.com"],
```
> **If you only need to renew single domain name:** Simply keep only one domain in `Domains` list inside.<br>
```json
"Domains": ["www.example.com"],
```
> **Certificate signing request (CSR) configuration**<br>
> `Country` following ISO 3166-1 standard.<br>
> `StateOrProvince` for geographical information.<br>
> `Locality` for geographical information.<br>
> `Organization` is recommended to NGO or Personal Business.<br>
> `OrganizationalUnit` is recommended to NGO or Personal Business.<br>
```json
"Country": "JP",
"StateOrProvince": "Tokyo Metropolis",
"Locality": "Shimokitazawa",
"Organization": "STARRY",
"OrganizationalUnit": "Kessoku Bando",
```
> `Config` is CSR configuration file for generate CSR.<br>
> `CSR` is Certificate signing request saving path.<br>
```json
"Config": "/Documents/script/domain.csr.conf",
"CSR": "/Documents/script/domain.csr",
```
> Certificate catalog also include active Private key and Certificates path.<br>
> **Fail-safe:** private key won't update until renewal Certificate was download, will storage as pending key (PendingPK).<br>
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
> **Well-known URIs:** acme-challenge URI will automatically create by ACME script.

### Cloudflare API
For using CNAME challenge function, you need to domain registered with Cloudflare, or choice Cloudflare as DNS hosting service.<br>
> **For safety:**<br>
> Please modify the token’s permissions. `only allowing DNS record edit` is is recommended.<br>
> Also make sure copy the secret to secure place.<br>

### ZeroSSL REST API
Login ZeroSSL, go to [Developer](https://app.zerossl.com/developer) page, you will find your ZeroSSL API Key, make sure to copy the secret to a secure place.<br>

> **If you suspect that your API Key has been compromised:**<br>
> Please click `Reset Key` and check is any unusual, or suspicious certificate been issued.<br>

### Telegram BOTs
Using Telegram Bot, contect [BotFather](https://t.me/botfather) create new Bot accounts.<br>

At this point chat channel wasn't created, so you can't find the `ChatID`. Running `Message2Me` function will receive `400 Bad Request` from Telegram API, following message will printout:
```
2025-05-14 19:19:00 | Telegram ChatID is empty, notifications will not be sent.
```
You need to start the chat channel with that bot, i.e. say `Hello the world` to him. Then running `GetChatID`
```python
import acme4zerossl
ConfigFilePath = "/documents/script/acme4zerossl.config.json"
Tg = acme4zerossl.Telegram(ConfigFilePath)
Tg.GetChatID()
```
Now ChatID will printout:
```
2025-05-14 19:19:18 | You ChatID is: XXXXXXXXX
```
### Webpage Server Reload or Restart
Function `CertificateInstall` support webpage server restart when certificate was downloaded (optional).<br>
> **Command type**<br>
> Adding command to `ServerCommand` with list object.<br>
> Default is `None`, after download certificate will skip webpage server reload or restart.<br>
```python
# Function
Rt.CertificateInstall(CertificateContent, ServerCommand)
# Default is None
ServerCommand = None
# Apache2, using systemd
ServerCommand = ['systemctl','reload','apache2.service']
# Nginx, using systemd
ServerCommand = ['systemctl','reload','nginx']
# Nginx, using init
ServerCommand = ['/etc/init.d/nginx','reload']
```

### Schedule
Recommend using `systemd`.<br>
> **systemd service file**<br>
> Create service file `/etc/systemd/system/acme.service` for systemd.<br>

> WorkingDirectory `/documents/script` prevent absolute/relative path issue.<br>
> ExecStart `/usr/bin/python3` depend on Python environment.<br>
> Path `/documents/script/script_cname.py` is acme script located.<br>
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
WorkingDirectory=/documents/script
# Python environment (interpreter) and script located
ExecStart=/usr/bin/python3 /documents/script/script_cname.py
# Log output
StandardOutput=journal
StandardError=journal
```
> **Timer file**<br>
> Next is timer file `/etc/systemd/system/acme.timer`.<br>
> Following example running everyday 5:00 AM and 10 minutes after boot up.<br>
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
> Enable systemd timer and clean cache.<br>
```shell
# Enable and start the timer
systemctl enable acme.timer
systemctl start acme.timer

# Reload
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

ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
Cf = acme.Cloudflare(ConfigFilePath)
Cf.VerifyCFToken()
```
> **Default Output**<br>
> Show result's value as string only.<br>
> Enable fully result by using `DisplayVerifyResult`<br>
```python
Cf.VerifyCFToken(DisplayVerifyResult=True)
```

### Asking CNAME Records ID hosing on Cloudflare
```python
import acme4zerossl as acme

ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
Cf = acme.Cloudflare(ConfigFilePath)
Cf.GetCFRecords()
```
> **Default Output**<br>
> Output is `dictionary` object contain fully Cloudflare dns records data belong specify Zone ID.<br>
> Adding `FileOutput` for output JSON file.<br>
```python
FileOutput = "/Documents/script/records.cloudflare.json"
Cf.GetCFRecords(FileOutput)
```

### Verify with CNAME challenge
> **Demonstration script**<br>
> `script_cname.py` including Telegram BOTs notify and check validity date of certificate.<br>
```python
# -*- coding: utf-8 -*-
import acme4zerossl as acme
import logging
from time import sleep
from sys import exit
# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
# Server reload or restart command
ServerCommand  = None
# Error handling
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
logging.basicConfig(level=logging.INFO,filename="acme4zerossl.log",filemode="a",format=FORMAT)
# Script
def main(VerifyRetry,Interval):
    # Load object
    Rt = acme.Runtime(ConfigFilePath)
    Cf = acme.Cloudflare(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Create certificates signing request
    ResultCreateCSR = Rt.CreateCSR()
    if not isinstance(ResultCreateCSR,list):
        raise RuntimeError("Error occurred during Create CSR and Private key.")
    # Sending CSR
    VerifyRequest = Zs.ZeroSSLCreateCA()
    if not isinstance(VerifyRequest,dict):
        raise RuntimeError("Error occurred during request new certificate.")
    # Phrasing ZeroSSL verify
    VerifyData = Zs.ZeroSSLVerifyData(VerifyRequest)
    if not isinstance(VerifyData,dict):
        raise RuntimeError("Error occurred during phrasing ZeroSSL verify data.")
    CertificateID = VerifyData.get("id",None)
    if CertificateID is None:
        raise RuntimeError("Certificate hash is empty.")
    # CNAME Update data 
    UpdatePayloads = [VerifyData['common_name']]
    AdditionalDomains = VerifyData.get('additional_domains')
    if AdditionalDomains:
        UpdatePayloads.append(AdditionalDomains)
    # Update Cloudflare hsoting CNAME records
    for UpdatePayload in UpdatePayloads:
        ResultUpdateCFCNAME = Cf.UpdateCFCNAME(UpdatePayload)
        # Check CNAME update result
        if not isinstance(ResultUpdateCFCNAME,dict):
            raise RuntimeError("Error occurred during connect Cloudflare update CNAME.")
        else:
            sleep(5)
    # Wait DNS records update and active
    sleep(60)
    # Verify CNAME challenge
    VerifyResult = Zs.ZeroSSLVerification(CertificateID,ValidationMethod="CNAME_CSR_HASH")
    if not isinstance(VerifyResult,str):
        raise RuntimeError("Error occurred during verification.")
    # Check verify status
    if VerifyResult == "draft":
        raise RuntimeError("Not verified yet.")
    # Verify passed (Under CNAME and file validation, pending_validation means verify successful)
    elif VerifyResult in ("pending_validation","issued"):
        sleep(30)
        # Download certificates, adding retry and interval in case backlog certificate issuance
        for _ in range(VerifyRetry):
            CertificateContent = Zs.ZeroSSLDownloadCA(CertificateID)
            # Successful download certificates
            if isinstance(CertificateContent,dict):
                break
            sleep(Interval)
        else:
            raise RuntimeError(f"Unable download certificate.")
    # Undefined error
    else:
        raise RuntimeError(f"Unable to check verification status, currently verification status: {VerifyResult}")
    # Install certificate to server folder
    ResultCheck = Rt.CertificateInstall(CertificateContent,ServerCommand)
    if ResultCheck is False:
        raise RuntimeError("Error occurred during certificate install. You may need to download and install manually.")
    else:
        return
# Runtime
if __name__ == "__main__":
    try:
        main(10,60)
        logging.info("Certificate has been renewed")
        exit(0)
    # Ctrl+C manually stop
    except KeyboardInterrupt:
        logging.warning("Manually interrupt")
        exit(0)
    except Exception as RenewedError:
        logging.exception(f"Script error| {RenewedError}")
        exit(1)
```

### Verify with HTTPS file challenge
> **Demonstration script**<br>
> `script_httpsfile.py` including Telegram BOTs notify and check validity date of certificate.<br>
```python
# -*- coding: utf-8 -*-
import acme4zerossl as acme
import logging
from time import sleep
from sys import exit
# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
# Server reload or restart command
ServerCommand  = None
# Error handling
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
logging.basicConfig(level=logging.INFO,filename="acme4zerossl.log",filemode="a",format=FORMAT)
# Script
def main(VerifyRetry,Interval):
    Rt = acme.Runtime(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Create certificates signing request
    ResultCreateCSR = Rt.CreateCSR()
    if not isinstance(ResultCreateCSR,list):
        raise RuntimeError("Error occurred during Create CSR and Private key.")
    # Sending CSR
    VerifyRequest = Zs.ZeroSSLCreateCA()
    if not isinstance(VerifyRequest,dict):
        raise RuntimeError("Error occurred during request new certificate.")
    # Phrasing ZeroSSL verify
    VerifyData = Zs.ZeroSSLVerifyData(VerifyRequest,ValidationMethod="HTTPS_CSR_HASH")
    if not isinstance(VerifyData,dict):
        raise RuntimeError("Error occurred during phrasing ZeroSSL verify data.")
    CertificateID = VerifyData.get("id",None)
    if CertificateID is None:
        raise RuntimeError("Certificate hash is empty")
    # Validation file path and content
    ValidationFiles = [VerifyData['common_name']]
    AdditionalDomains = VerifyData.get("additional_domains")
    if AdditionalDomains:
        ValidationFiles.append(AdditionalDomains)
    # Create validation file
    for ValidationFile in ValidationFiles:
        CreateValidationFileStatus = Rt.CreateValidationFile(ValidationFile)
        if CreateValidationFileStatus is not True:
            raise RuntimeError("Error occurred during create validation file")
    # Cahce
    sleep(60)
    # Verify file challenge
    VerifyResult = Zs.ZeroSSLVerification(CertificateID,ValidationMethod="HTTPS_CSR_HASH")
    if not isinstance(VerifyResult,str):
        raise RuntimeError("Error occurred during file verification.")
    # Check verify status
    if VerifyResult == "draft":
        raise RuntimeError("Not verified yet.")
    # Verify passed (Under CNAME and file validation, pending_validation means verify successful)
    elif VerifyResult in ("pending_validation","issued"):
        sleep(30)
        # Download certificates, adding retry and interval in case backlog certificate issuance
        for _ in range(VerifyRetry):
            CertificateContent = Zs.ZeroSSLDownloadCA(CertificateID)
            # Successful download certificates
            if isinstance(CertificateContent,dict):
                break
            sleep(Interval)
        else:
            raise RuntimeError(f"Unable download certificate.")
    # Undefined error
    else:
        raise RuntimeError(f"Unable to check verification status, undefined status: {VerifyResult}")
    # Delete validation file
    for ValidationFile in ValidationFiles:
        Rt.CleanValidationFile(ValidationFile)
    # Install certificate to server folder
    ResultCheck = Rt.CertificateInstall(CertificateContent,ServerCommand)
    if ResultCheck is False:
        raise RuntimeError("Error occurred during certificate install. You may need to download and install manually.")
    else:
        return
# Runtime
if __name__ == "__main__":
    try:
        main(10,60)
        logging.info("Certificate has been renewed")
        exit(0)
    # Ctrl+C manually stop
    except KeyboardInterrupt:
        logging.warning("Manually interrupt")
        exit(0)
    except Exception as RenewedError:
        logging.exception(f"Script error| {RenewedError}")
        exit(1)
```

### Download certificate
```python
# -*- coding: utf-8 -*-
import acme4zerossl as acme
from sys import exit
# Config
ConfigFilePath = "/documents/script/acme4zerossl.config.json"
# Script
def DownloadScript(CertificateID):
    Rt = acme.Runtime(ConfigFilePath)
    Download = acme.ZeroSSL(ConfigFilePath)
    # Download certificate payload
    CertificateContent = Download.ZeroSSLDownloadCA(CertificateID or None)
    # Check
    if not isinstance(CertificateContent, dict):
        raise Exception()
    # Download certificate and save to folder
    elif isinstance(CertificateContent, dict) and ("certificate.crt") in CertificateContent:
        pass
    ResultCheck = Rt.CertificateInstall(CertificateContent)
    if isinstance is False:
        raise Exception()
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
ConfigFilePath = "/documents/script/acme4zerossl.config.json"
# Script
def CancelScript(CertificateID):
    Rt = acme.Runtime(ConfigFilePath)
    Cancel = acme.ZeroSSL(ConfigFilePath)
    # Cancel certificate
    CancelStatus = Cancel.ZeroSSLCancelCA(CertificateID)
    # Status check, Error
    if not isinstance(CancelStatus, dict):
    # Standard response, check status code
    elif isinstance(CancelStatus, dict):
        CancelResult = CancelStatus.get("success",{})
        if CancelResult == 1:
            Rt.Message(f"Certificate ID: {CertificateID} has been cancelled.")
        elif CancelResult == 0:
            Rt.Message("ZeroSSL REST API request successful, however unable cancel certificate.")
        else:
            raise Exception()
    else:
        raise Exception()
# Runtime
try:
    # Input certificate hash manually
    CertificateID = input("Please input certificate ID (hash): ")
    CancelScript(CertificateID)
    exit(0)
except Exception:
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
ConfigFilePath = "/documents/script/acme4zerossl.config.json"
# Script
def RevokeScript(CertificateID):
    Rt = acme.Runtime(ConfigFilePath)
    Revoke = acme.ZeroSSL(ConfigFilePath)
    # Revoke certificate
    RevokeStatus = Revoke.ZeroSSLRevokeCA(CertificateID)
    # Status check
    if not isinstance(RevokeStatus, dict):
        raise Exception()
    elif isinstance(RevokeStatus, dict) and ("success") in RevokeStatus:
        RevokeResult = RevokeStatus.get("success","")
        if RevokeResult == 1:
            Rt.Message(f"Certificate ID: {CertificateID} has been revoked.")
        elif RevokeResult == 0:
            Rt.Message("ZeroSSL REST API request successful, however unable revoke certificate.")
        else:
            raise Exception()
    else:
        raise Exception()
# Runtime
try:
    # Input certificate hash manually
    CertificateID = input("Please input certificate ID (hash): ")
    RevokeScript(CertificateID)
    exit(0)
except Exception:
    exit(1)
```
## Self-signed certificate
Using self-signed certificate prevent IP connecting leak domain certificate.<br>
> **Demonstration script**<br>
> stand alone, functionable `script_selfsigned.py`.

> **CSR config:** authority configuration at line 18 to 24.<br>
> **Certificate name and folder path:** configuration at line 27 to 31.<br>
> **Server command:** at line 33, same as ACME script.
```python
# Configuration
def __init__(self):
    self.IpIfy4 = "https://api.ipify.org?format=json"
    self.IpIfy6 = "https://api64.ipify.org/?format=json"
    # CSR config
    self.Days         = 47
    self.Country      = "JP"
    self.State        = "Tokyo Metropolis"
    self.Locality     = "Toshima"
    self.Organization = "Tsukinomori Girls' Academy"
    self.Unit         = "Concert Band Club"
    self.CSRConfig    = "selfsigned_certificate.conf"
    # CSR config path
    self.ConfigFolder = Path.cwd()
    # Certificate folder path, None as default path
    self.CertFolder   = None
    # Certificate and private key name
    self.PrivateKey   = "selfsigned_certificate.key"
    self.Certificate  = "selfsigned_certificate.crt"
    # Server command
    self.WebServer    = None
```

## Dependencies
### Python version
Testing passed on above Python version:<br>
+ 3.12.11
+ 3.9.6
+ 3.9.2
+ 3.7.3

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
- [ZeroSSL REST APIdocumentation](https://zerossl.com/documentation/api/) the official documentation.

### Reference repository
- [ZeroSSL-CertRenew](https://github.com/ajnik/ZeroSSL-CertRenew/tree/master) for HTTP/HTTPS challenge file.
