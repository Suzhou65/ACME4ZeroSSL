# Acme4ZeroSSL
[![Python](https://github.takahashi65.info/lib_badge/python.svg)](https://www.python.org/)
[![Version](https://github.takahashi65.info/lib_badge/python-3.12.svg)](https://www.python.org/)
[![under_development](https://github.takahashi65.info/lib_badge/under_development.svg)](https://github.com/Suzhou65/acme4zerossl)
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
  * [Script](#script)
    + [Verify Cloudflare token](#verify-cloudflare-token)
    + [Find CNAME records ID](#find-cname-records-id)
    + [Verify via CNAME](#verify-via-cname)
    + [Download certificate](#download-certificate)
    + [Cancel certificate](#cancel-certificate)
    + [Revoke certificate](#revoke-certificate)
  * [Dependencies](#dependencies)
  * [License](#license)
  * [Resources](#resources)

## Development Purpose
I manage sh*tload of servers, including my profile page, apartment's HomeKit gateway, several Hentai@Home client. Also, some headless system based on Apache Tomcat, which don't support authentication via HTTP/HTTPS challenge file.

Even though I can update CNAME record through Cloudflare API, certificate downloading and install has to be done manually. Current certificate validity is 90 days, but as that period gets shorter, those process becomes more annoying and frequent.

Developed to automate renewal certificate with ZeroSSL REST API, pair with Cloudflare hosting DNS records for CNAME challenge.

## Limitation
> **Note**  
> Single Common Name (CN), or single CN & single Subject Alternative Name (SAN) pairs.  
> Currently support CNAME challenge only, HTTP/HTTPS challenge file support TBD. 

## Usage
### Configuration file
Using JSON format file storage configuration.
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
      "Cache": "/Documents/script/cache.json"
   },
   "Certificate":{
      "Domains": ["www.example.com", "example.com"],
      "Counrty": "",
      "StateOrProvince": "",
      "Locality": "",
      "Organization": "",
      "OrganizationalUnit": "",
      "Config": "/Documents/script/csr.conf",
      "CSR": "/Documents/script/certificate.csr",
      "PendingPK": "/Documents/script/cache.key",
      "PK": "/var/certificate/private.key",
      "CA": "/var/certificate/certificate.crt",
      "CAB": "/var/certificate/ca_bundle.crt"
   },
   "FileChallenge":{
      "HTMLFilePath": ""
   }
}
```

Configuration file must include following parameters:
+ **Telegram BOTS token** storage at `Token` inside `Telegram_BOTs`, **Chat ID** storage at `ChatID`.
+ **Cloudflare API Key** storage at `Token` inside `CloudflareAPI`, **auth email** storage at `Mail`.
> **Note**  
> If you only need ACME certification for a **single domain name**, simply keep only that one domain in both the `CNAMERecordsID` list inside `CloudflareRecords`.

+ **Domains Cloudflare Zone id** storage at `ZoneID`, **CNAME records ID** storage at `CNAMERecordsID` list.
+ **ZeroSSL REST API Key** storage at `AccessKey` inside `ZeroSSLAPI`.
+ ```Domains``` list indise ```Certificate``` is the domain require renewal certificate.
> **Note**  
> If you only need ACME certification for a **single domain name**, simply keep only that one domain in `Domains` list inside `Certificate`.
+ `Certificate` also include CSR signing configure, CSR, Pending/Active Private key and Certificates path.
> **Note**  
> For fail-safe, private key won't update until renewal Certificate was download, will storage as pending key. 
+ `FileChallenge` files path for HTTP/HTTPS file challenge, usually your Apache/Nginx webpage folder.

### Cloudflare API
For using CNAME challenge function, you need to domain registered with Cloudflare, or choice Cloudflare as DNS hosting service.

Then, login `Cloudflare Dashboard`, select the domain you hosting, find the `Get your API token banner`, click `API Tokens options`.

Modify the token’s permissions. `only allowing DNS record edit`, then generate API Token. The token secret is only shown once, make sure to copy the secret to a secure place.

> **Note**  
> Please remove the `Bearer` string and blank.

### ZeroSSL REST API
Login ZeroSSL, go to [Developer](https://app.zerossl.com/developer) page, you will find your ZeroSSL API Key, make sure to copy the secret to a secure place.

If you suspect that your API Key has been compromised, please click ```Reset Key``` and check is any unusual, or suspicious certificate been issued.

### Telegram BOTs
Using Telegram Bot, contect [BotFather](https://t.me/botfather) create new Bot accounts.

If the chat channel wasn't created, the Telegram API will return ```HTTP 400 Bad Request```. You need to start the chat channel with that bot, i.e. say ```Hello the world``` to him.

## Import module
```python
# Import as module
import acme4zerossl as acme
```

## Script
### Verify Cloudflare token
```python
import acme4zerossl as acme

ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
Cf = acme.Cloudflare(ConfigFilePath)
# Output result's value as string only, not fully result.
Cf.VerifyCFToken()
```
The demonstration script is named ```script_verify.py```

### Find CNAME records ID
```python
import acme4zerossl as acme

ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
Cf = acme.Cloudflare(ConfigFilePath)
# Output result's value as dictionary object.
# Adding File Output for output JSON file.
Cf.GetCFRecords(FileOutput = None)
```
Output is `dictionary object` contain fully Cloudflare dns records belong specify Zone id.

### Verify via CNAME challenge
> **Note**  
> Support webpage server reload or restart (optional).

```python
import acme4zerossl as acme
from time import sleep
from sys import exit

ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
# Apache2       ['systemctl', 'reload', 'apache2']
# Nginx         ['service', 'nginx', 'restart']
ServerCommand  = None

# Script
def main():
    Rt = acme.Runtime(ConfigFilePath)
    Cf = acme.Cloudflare(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Create certificates signing request
    ResultCreateCSR = Rt.CreateCSR()
    # Sending CSR
    VerifyRequest = Zs.ZeroSSLCreateCA()
    # Phrasing ZeroSSL verify
    VerifyData = Zs.ZeroSSLVerifyData(VerifyRequest, Mode="CNAME")
    # Update CNAME via Cloudflare API
    if ("additional_domains_cname") not in VerifyData:
        UpdatePayloads = [VerifyData['common_name_cname']]
    elif ("additional_domains_cname") in VerifyData:
        UpdatePayloads = [VerifyData['common_name_cname'],
                          VerifyData['additional_domains_cname']]
    for UpdatePayload in UpdatePayloads:
        ResultUpdateCFCNAME = Cf.UpdateCFCNAME(UpdatePayload)
    # Wait DNS records update and active
    sleep(30)
    # Verify CNAME challenge
    CertificateID = VerifyData['id']
    VerifyResult = Zs.ZeroSSLVerification(CertificateID)
    if type(VerifyResult) is dict and VerifyResult['status'] == ("pending_validation"):
        Rt.Message("CNAME verify successful, wait certificate issued.")
        sleep(30)
    # Verify successful and been issued
    elif type(VerifyResult) is dict and VerifyResult['status'] == ("issued"):
        Rt.Message("CNAME verify successful, certificate been issued.")
        sleep(5)
    # Download certificates
    CertificateContent = Zs.ZeroSSLDownloadCA(CertificateID)
    # Install certificate to server folder
    ResultCheck = Rt.CertificateInstall(CertificateContent, ServerCommand)
# Runtime
try:
   main()
except Exception:
   exit(0)
```
Demonstration script named ```script_cname.py```, which including Telegram BOTs notify and check validity date of certificate.

### Download certificate

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
    if len(CertificateID) == 0:
        CertificateContent = Zs.ZeroSSLDownloadCA()
    else:
        CertificateContent = Zs.ZeroSSLDownloadCA(CertificateID)
    # Download certificate and save to folder
    ResultCheck = Rt.CertificateInstall(CertificateContent)
# Runtime
try:
   main()
except Exception:
   exit(0)
```

### Cancel certificate
> **Note**  
> Please note that only certificates with status draft or `pending_validation` can be cancelled. After verification, the certificates cannot been cancelled.

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
    CancelCAResult = Zs.ZeroSSLCancelCA(CertificateID)
    # Status check
    if type(CancelCAResult) is dict and CancelCAResult['success'] == 1:
        Rt.Message(f"Certificate ID: {CertificateID} has been cancelled.")
    elif type(CancelCAResult) is dict and CancelCAResult['success'] == 0:
        Rt.Message("ZeroSSL REST API request successful, however unable cancel certificate.")
    elif type(CancelCAResult) is int:
        Rt.Message(f"Unable connect ZeroSSL API, HTTP error code: {CancelCAResult}.")
    else:
        Rt.Message("Error occurred during cancel certificate.")
# Runtime
try:
   main()
except Exception:
   exit(0)
```
Demonstration script named ```script_cancel.py```

### Revoke certificate
> **Note**  
> ZeroSSL REST API require reason for certificate revoke (Optional).
> Only certificates with status `issued` can be revoked. If a certificate has already been successfully revoked you will get a success response nevertheless.

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
    if type(RevokeStatus) is dict and RevokeStatus['success'] == 1:
        Rt.Message(f"Certificate ID: {CertificateID} has been revoked.")
    elif type(RevokeStatus) is dict and RevokeStatus['success'] == 0:
        Rt.Message("ZeroSSL REST API request successful, however unable revoke certificate.")
        raise Exception()
    elif type(RevokeStatus) is int:
        Rt.Message(f"Unable connect ZeroSSL API, HTTP error code: {RevokeStatus}.")
        raise Exception()
    else:
        Rt.Message("Error occurred during revoke certificate.")
        raise Exception()
# Runtime
try:
   main()
except Exception:
   exit(0)
```
Demonstration script named ```script_revoke.py```

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
* sys

## License
General Public License -3.0

## Resources
### ZeroSSL API
- [ZeroSSL REST APIdocumentation](https://zerossl.com/documentation/api/) the official documentation.
### Reference repository
- [ZeroSSL-CertRenew](https://github.com/ajnik/ZeroSSL-CertRenew/tree/master) for HTTP/HTTPS challenge file.
