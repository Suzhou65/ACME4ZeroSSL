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
  * [Import module](#import-module)
  * [Function](#function)
    + [Verify Cloudflare API Token](#verify-cloudflare-api-token)
    + [Asking CNAME Records ID hosing on Cloudflare](#asking-cname-records-id-hosing-on-cloudflare)
    + [Verify with CNAME challenge](#verify-with-cname-challenge)
    + [Verify with HTTPS file challenge](#verify-with-https-file-challenge)
    + [Download certificate](#download-certificate)
    + [Cancel certificate](#cancel-certificate)
    + [Revoke certificate](#revoke-certificate)
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
>
> If you only need ACME certification for a single domain name, simply keep only one DNS records ID inside `CNAMERecordsID` list.<br>
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
"HTMLFilePath": "/var/www/html/"
```

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
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
Tg = acme4zerossl.Telegram(ConfigFilePath)
Tg.GetChatID()
```
Now ChatID will printout:
```
2025-05-14 19:19:18 | You ChatID is: XXXXXXXXX
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
Cf.VerifyCFToken(DisplayVerifyResult = True)
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
import acme4zerossl as acme
from time import sleep
from sys import exit
# Configuration file path
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
ServerCommand  = None
# Script
def main():
    Rt = acme.Runtime(ConfigFilePath)
    Cf = acme.Cloudflare(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Create certificates signing request
    ResultCreateCSR = Rt.CreateCSR()
    if isinstance(ResultCreateCSR, bool):
        raise Exception()
    elif isinstance(ResultCreateCSR, int):
        pass
    # Sending CSR
    VerifyRequest = Zs.ZeroSSLCreateCA()
    # Function error
    if isinstance(VerifyRequest, bool):
        raise Exception()
    # ZeroSSL REST API HTTP error
    elif isinstance(VerifyRequest, int):
        raise Exception()
    # Phrasing ZeroSSL verify
    elif isinstance(VerifyRequest, dict):
        VerifyData = Zs.ZeroSSLVerifyData(VerifyRequest, Mode="CNAME")
    # Check verify data
    if isinstance(VerifyData, bool):
        raise Exception()
    elif isinstance(VerifyData, dict):
        pass
    # Update CNAME via Cloudflare API
    if ("additional_domains") in VerifyData:
        UpdatePayloads = [
            VerifyData.get('common_name'),
            VerifyData.get('additional_domains')]
    elif ("additional_domains") not in VerifyData:
        UpdatePayloads = [
            VerifyData.get('common_name')]
    # Update Cloudflare CNAME records
    for UpdatePayload in UpdatePayloads:
        ResultUpdateCFCNAME = Cf.UpdateCFCNAME(UpdatePayload)
        # Function error
        if isinstance(ResultUpdateCFCNAME, bool):
            raise Exception()
        # Cloudflare API HTTP error
        elif isinstance(ResultUpdateCFCNAME, int):
            raise Exception()
        # Check CNAME update result
        elif isinstance(ResultUpdateCFCNAME, dict):
            ResultUpdateResult = ResultUpdateCFCNAME.get("success")
            if ResultUpdateResult == True:
                sleep(5)
            elif ResultUpdateResult == False:
                raise Exception()
            else:
                raise Exception()
        else:
            raise Exception()
    # Wait DNS records update and active
    sleep(30)
    # Verify CNAME challenge
    CertificateID = VerifyData.get("id","")
    VerifyResult = Zs.ZeroSSLVerification(CertificateID, ValidationMethod="CNAME_CSR_HASH")
    # Function error
    if isinstance(VerifyResult, bool):
        raise Exception()
    # ZeroSSL REST API HTTP error
    elif isinstance(VerifyResult, int):
        raise Exception()
    # Possible errors respon
    elif isinstance(VerifyResult, dict) and ("error") in VerifyResult:
        VerifyErrorStatus = VerifyResult.get("error",{}).get("type","Unknown Error")
        raise Exception (VerifyErrorStatus)
    # Check verify status
    elif isinstance(VerifyResult, dict) and ("status") in VerifyResult:
        VerifyStatus = VerifyResult.get("status")
        # Verify successful, wait issued
        if VerifyStatus == ("draft"):
            raise Exception()
        elif VerifyStatus == ("pending_validation"):
            sleep(30)
        # Verify successful and been issued
        elif VerifyStatus == ("issued"):
            sleep(5)
        # Undefined error
        else:
            raise Exception()
    # Download certificates
    CertificateContent = Zs.ZeroSSLDownloadCA(CertificateID)
    if isinstance(CertificateContent, bool):
        raise Exception()
    elif isinstance(CertificateContent, str):
        raise Exception(CertificateContent)
    elif isinstance(CertificateContent, dict) and ("certificate.crt") in CertificateContent:
        sleep(5)
    # Install certificate to server folder
    ResultCheck = Rt.CertificateInstall(CertificateContent, ServerCommand)
    if isinstance(ResultCheck, bool):
        raise Exception()
    elif isinstance(ResultCheck, int):
        pass
    elif isinstance(ResultCheck, (list,str)):
        pass
    else:
        raise Exception ()
# Runtime, including check validity date of certificate
if __name__ == "__main__":
    try:
        main()
    except Exception:
        exit(0)
```
> **Support webpage server restart (optional)**<br>
> Adding command to `ServerCommand` with list object.<br>
```python
# Apache
ServerCommand  = ['systemctl', 'reload', 'apache2']
# Nginx
ServerCommand  = ['service', 'nginx', 'restart']
```

### Verify with HTTPS file challenge
> **Demonstration script**<br>
> `script_httpsfile.py` including Telegram BOTs notify and check validity date of certificate.<br>
```python
# -*- coding: utf-8 -*-
import acme4zerossl as acme
from time import sleep
from sys import exit

# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
ServerCommand  = None

# Script
def main():
    Rt = acme.Runtime(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Create certificates signing request
    ResultCreateCSR = Rt.CreateCSR()
    if isinstance(ResultCreateCSR, bool):
        raise Exception()
    elif isinstance(ResultCreateCSR, int):
        pass
    # Sending CSR
    VerifyRequest = Zs.ZeroSSLCreateCA()
    # Function error
    if isinstance(VerifyRequest, bool):
        raise Exception()
    # ZeroSSL REST API HTTP error
    elif isinstance(VerifyRequest, int):
        raise Exception()
    # Phrasing ZeroSSL verify
    elif isinstance(VerifyRequest, dict):
        VerifyData = Zs.ZeroSSLVerifyData(VerifyRequest, Mode="FILE")
    # Check verify data
    if isinstance(VerifyData, bool):
        raise Exception()
    elif isinstance(VerifyData, dict):
        pass
    # Validation file path and content
    if ("additional_domains") in VerifyData:
        ValidationFiles = [
            VerifyData.get('common_name'),
            VerifyData.get('additional_domains')]
    elif ("additional_domains") not in VerifyData:
        ValidationFiles = [
            VerifyData.get('common_name')]
    # Create validation file
    for ValidationFile in ValidationFiles:
        Rt.CreateValidationFile(ValidationFile)
    # Wait for web server cahce
    sleep(15)
    # Verify file challenge
    CertificateID = VerifyData.get("id")
    VerifyResult = Zs.ZeroSSLVerification(CertificateID, ValidationMethod="HTTPS_CSR_HASH")
    # Function error
    if isinstance(VerifyResult, bool):
        raise Exception()
    # ZeroSSL REST API HTTP error
    elif isinstance(VerifyResult, int):
        raise Exception()
    # Possible errors respon
    elif isinstance(VerifyResult, dict) and ("error") in VerifyResult:
        VerifyErrorStatus = VerifyResult.get("error",{})
        ErrorType = VerifyErrorStatus.get("type", "Unknown Error")
        raise Exception (ErrorType)
    # Check verify status
    elif isinstance(VerifyResult, dict) and ("status") in VerifyResult:
        VerifyStatus = VerifyResult.get("status")
        # Verify successful, wait issued
        if VerifyStatus == ("draft"):
            raise Exception()
        elif VerifyStatus == ("pending_validation"):
            sleep(30)
        # Verify successful and been issued
        elif VerifyStatus == ("issued"):
            sleep(5)
        # Undefined error
        else:
            raise Exception()
    # Delete validation file
    for ValidationFile in ValidationFiles:
        Rt.CleanValidationFile(ValidationFile)
    # Download certificates
    CertificateContent = Zs.ZeroSSLDownloadCA(CertificateID)
    if isinstance(CertificateContent, bool):
        raise Exception()
    elif isinstance(CertificateContent, str):
        raise Exception(CertificateContent)
    elif isinstance(CertificateContent, dict) and ("certificate.crt") in CertificateContent:
        sleep(5)
    # Install certificate to server folder
    ResultCheck = Rt.CertificateInstall(CertificateContent, ServerCommand)
    ExpiresDate = VerifyResult.get("expires")
    if isinstance(ResultCheck, bool):
        raise Exception()
    elif isinstance(ResultCheck, int):
        pass
    elif isinstance(ResultCheck, (list,str)):
        pss
    else:
        raise Exception ()
# Runtime, including check validity date of certificate
if __name__ == "__main__":
    try:
        Rt = acme.Runtime(ConfigFilePath)
        # Minimum is 14 days
        CertificateMinimum = Rt.ExpiresCheck()
        if isinstance(CertificateMinimum, bool):
            main()
        elif isinstance(CertificateMinimum, int):
            Rt.Message(f"Certificate's validity date has {CertificateMinimum} days left.")
    except Exception:
        exit(0)
```

### Download certificate
> **Demonstration script**<br>
> `script_download.py`.<br>
```python
import acme4zerossl as acme
from sys import exit

# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
# Script
def main():
    Rt = acme.Runtime(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Print prompt
    Rt.Message("Certificate manual download script start. Download certificate hash reference from cache file by default.")
    # Input certificate hash manually
    CertificateID = input("Please input certificate ID (hash), or press ENTER using cache file: ")
    # Download certificate payload
    CertificateContent = Zs.ZeroSSLDownloadCA(CertificateID or None)
    # Check
    if isinstance(CertificateContent, bool):
        Rt.Message("Error occurred during certificates download.")
        raise Exception()
    elif isinstance(CertificateContent, str):
        Rt.Message(f"Error occurred during download certificate. Error status: {CertificateContent}")
        raise Exception()
    # Download certificate and save to folder
    elif isinstance(CertificateContent, dict) and ("certificate.crt") in CertificateContent:
        Rt.Message(f"Downloading certificate...")
    ResultCheck = Rt.CertificateInstall(CertificateContent)
    if isinstance(ResultCheck, bool):
        Rt.Message("Error occurred during certificate saving.")
        raise Exception()
    elif isinstance(ResultCheck, int):
        Rt.Message("Certificate been downloaded to folder. You may need to restart server manually.")
    elif isinstance(ResultCheck, (list,str)):
        Rt.Message(f"Certificate been downloaded and server has reload or restart.")
# Runtime
if __name__ == "__main__":
    try:
        main()
    except Exception:
        exit(1)
```

### Cancel certificate<br>
> Only certificates with status draft or `pending_validation` can be cancelled.<br>
> After verification, the certificates `cannot been cancelled`.<br>

> **Demonstration script**<br>
> Demonstration script named `script_cancel.py`.<br>
```python
import acme4zerossl as acme
from sys import exit

# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
# Script
def main():
    Rt = acme.Runtime(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Input certificate hash manually
    CertificateID = input("Please input certificate ID (hash): ")
    # Cancel certificate
    CancelStatus = Zs.ZeroSSLCancelCA(CertificateID)
    # Status check, Error
    if isinstance(CancelStatus, bool):
        Rt.Message("Error occurred during cancel.")
    # ZeroSSL REST API HTTP error
    elif isinstance(CancelStatus, int):
        Rt.Message(f"Unable connect ZeroSSL API, HTTP error code: {CancelStatus}.")
        raise Exception()
    # Standard response, check status code
    elif isinstance(CancelStatus, dict):
        CancelResult = CancelStatus.get("success",{})
        if CancelResult == 1:
            Rt.Message(f"Certificate ID: {CertificateID} has been cancelled.")
        elif CancelResult == 0:
            Rt.Message("ZeroSSL REST API request successful, however unable cancel certificate.")
        else:
            Rt.Message(f"Undefined status: {CancelResult}")
            raise Exception()
    else:
        Rt.Message("Error occurred during cancel certificate.")
        raise Exception()
# Runtime
if __name__ == "__main__":
    try:
        main()
    except Exception:
        exit(1)
```

### Revoke certificate
> **Note**  
> ZeroSSL REST API require reason for certificate revoke (Optional).
> Only certificates with status `issued` can be revoked. If a certificate has already been successfully revoked you will get a success response nevertheless.

> **Demonstration script**<br>
> Demonstration script named `script_revoke.py`.<br>
```python
import acme4zerossl as acme
from sys import exit

# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
# Script
def main():
    Rt = acme.Runtime(ConfigFilePath)
    Revoke = acme.ZeroSSL(ConfigFilePath)
    # Input certificate hash manually
    CertificateID = input("Please input certificate ID (hash): ")
    # Revoke certificate
    RevokeStatus = Revoke.ZeroSSLRevokeCA(CertificateID)
    # Status check
    if isinstance(RevokeStatus, bool):
        Rt.Message("Error occurred during revoke.")
    elif isinstance(RevokeStatus, int):
        Rt.Message(f"Unable connect ZeroSSL API, HTTP error code: {RevokeStatus}.")
        raise Exception()
    elif isinstance(RevokeStatus, dict) and ("success") in RevokeStatus:
        RevokeResult = RevokeStatus.get("success","")
        if RevokeResult == 1:
            Rt.Message(f"Certificate ID: {CertificateID} has been revoked.")
        elif RevokeResult == 0:
            Rt.Message("ZeroSSL REST API request successful, however unable revoke certificate.")
        else:
            Rt.Message(f"Undefined status: {RevokeResult}")
            raise Exception()
    else:
        Rt.Message("Error occurred during revoke certificate.")
        raise Exception()
# Runtime
if __name__ == "__main__":
    try:
        main()
    except Exception:
        exit(1)
```

## Dependencies
### Python version
Testing passed on above Python version:
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
