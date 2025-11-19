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
```diff
- Single Common Name (CN), or single CN & single Subject Alternative Name (SAN) pairs.
- Currently support CNAME challenge only, HTTP/HTTPS challenge file support TBD. 
```
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

+ ```Telegram BOT``` token and chat ID for status notifications.
+ ```ZeroSSL API Key```
+ ```Cloudflare configuration``` include API Key, auth email, Zone ID and Specific DNS records.
+ ```Domains``` list that require certificate renewal.
+ ```Certificate``` include CSR signing configure, CSR, Pending/Active Private key and Certificates path.
+ ```FileChallenge``` files path for HTTP/HTTPS file challenge, usually your Apache/Nginx webpage folder.

```diff
- CNAMERecordsID & Domains list object are structured to match ZeroSSL REST API response structure. Even when single Common Name, leave empty ("") string as placeholder maintain compatibility.
```

### Cloudflare API
For using CNAME challenge function, you need to domain registered with Cloudflare, or choice Cloudflare as DNS hosting service.

Then, login ```Cloudflare Dashboard```, select the domain you hosting, find the ```Get your API token banner```, click ```API Tokens options```.

Modify the token’s permissions. ```only allowing DNS record edit```, then generate API Token. The token secret is only shown once, make sure to copy the secret to a secure place.

Please remove the ```Bearer``` string and blank.

### ZeroSSL REST API
Login ZeroSSL, go to [Developer](https://app.zerossl.com/developer) page, you will find your ZeroSSL API Key, make sure to copy the secret to a secure place.

If you suspect that your API Key has been compromised, please click ```Reset Key``` and check is any unusual, or suspicious certificate been issued.

### Telegram BOTs
Using Telegram Bot, contect [BotFather](https://t.me/botfather) create new Bot accounts.

If the chat channel wasn't created, the Telegram API will return ```HTTP 400 Bad Request```. You need to start the chat channel with that bot, i.e. say ```Hello the world``` to him.

## Import module
```python
# Import as module
import acme4zerossl
# Import the function independently
from acme4zerossl import CreateCSR
```

## Script
### Verify Cloudflare token
```python
from acme4zerossl import VerifyCFToken
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
# Output result's value as string only, not fully result.
VerifyCFToken(ConfigFilePath)
```
The demonstration script is named ```script_verify.py```
### Find CNAME records ID
```python
from acme4zerossl import GetCFRecords
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
FileOutput = None
# Output result's value as dictionary object.
# Adding File Output for output JSON file.
GetCFRecords(ConfigFilePath, FileOutput)
```
Output is dictionary object contain fully cloudflare dns records belong specify Zone id.

### Verify via CNAME challenge
```diff
+ Support webpage server reload or restart (optional).
+ acme.CertificateInstall(CertificateContent, CertificateContent, ServerReloadCommand)
```
```python
import acme4zerossl as acme
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
ServerCommand = None
# ["sudo", "service", "apache2", "reload"]
# ServerCommand must be list object.

# Create certificates signing request
acme.CreateCSR(ConfigFilePath)
# Sending certificate create request to ZeroSSl
VerifyRequest = acme.ZeroSSLCreateCA(ConfigFilePath)
# Phrasing ZeroSSL verify, select CNAME challenge
VerifyData = acme.ZeroSSLVerifyData(VerifyRequest)
# Update CNAME via Cloudflare API
if ("additional_domains_cname") not in VerifyData:
   UpdatePayloads = [
      VerifyData['common_name_cname']]
   acme.UpdateCFCNAME(ConfigFilePath, UpdatePayload)
elif ("additional_domains_cname") in VerifyData:
   UpdatePayloads = [
      VerifyData['common_name_cname'],
      VerifyData['additional_domains_cname']]
for UpdatePayload in UpdatePayloads:
   acme.UpdateCFCNAME(ConfigFilePath, UpdatePayload)
# Verify CNAME challenge
CertificateID = VerifyData['id']
acme.ZeroSSLVerification(ConfigFilePath, CertificateID)
# Download certificates
CertificateContent = acme.ZeroSSLDownloadCA(ConfigFilePath, CertificateID)
# Install certificates
acme.CertificateInstall(ConfigFilePath, CertificateContent, ServerCommand)
```
Demonstration script named ```script_cname.py```, which including Telegram BOTs notify and check validity date of certificate.
### Download certificate

```python

```
### Cancel certificate
``` diff
- Please note that only certificates with status draft or pending_validation can be cancelled.
- After verification, the certificates cannot been cancelled.
```
```python
from acme4zerossl import ZeroSSLCancelCA
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"

# Input certificate hash manually
CertificateID = input("Please input certificate ID (hash): ")
ZeroSSLCancelCA(ConfigFilePath, CertificateID)
```
Demonstration script named ```script_cancel.py```
### Revoke certificate
``` diff
- ZeroSSL REST API require reason for certificate revoke (Optional).
- Only certificates with status issued can be revoked.
- If a certificate has already been successfully revoked you will get a success response nevertheless.
```
```python
from acme4zerossl import ZeroSSLRevokeCA
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
# ZeroSSL REST API need reason for certificate revoke
# Optional RevokeReason string: keyCompromise, affiliationChanged, Superseded, cessationOfOperation
# Default is "Unspecified" as None.
RevokeReason = None
# Input certificate hash manually
CertificateID = input("Please input certificate ID (hash): ")
ZeroSSLRevokeCA(ConfigFilePath, CertificateID, RevokeReason)
```
Demonstration script named ```script_revoke.py```

## Dependencies
### Python version
* Testing passed on above Python version: ```3.11.2```, ```3.12.2```.
* Version ```3.9.2``` and ```3.9.6``` workable.
### Python module
* logging
* json
* requests
* subprocess
* time
* pathlib
* sys

## License
General Public License -3.0

## Resources
### ZeroSSL API
- [ZeroSSL REST APIdocumentation](https://zerossl.com/documentation/api/) the official documentation.
### Reference repository
- [ZeroSSL-CertRenew](https://github.com/ajnik/ZeroSSL-CertRenew/tree/master) for HTTP/HTTPS challenge file.
