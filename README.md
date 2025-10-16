# Acme4ZeroSSL
[![Python](https://github.takahashi65.info/lib_badge/python.svg)](https://www.python.org/)
[![under_development](https://github.takahashi65.info/lib_badge/under_development.svg)](https://github.com/Suzhou65/acme4zerossl)
[![Size](https://img.shields.io/github/repo-size/Suzhou65/acme4zerossl.svg)](https://shields.io/category/size)

Python script to issue and renew TLS certs from ZeroSSL.

## Contents
- [Acme4ZeroSSL](#acme4zerossl)
  * [Contents](#contents)
  * [Development Purpose](#development-purpose)
  * [Usage](#usage)
    + [Configuration file](#configuration-file)
    + [Cloudflare API](#Cloudflare-api)
    + [ZeroSSL REST API](#zerossl-rest-api)
    + [Telegram BOTs](#telegram-bots)
  * [Import module](#import-module)
  * [Script](#script)
    + [Verify Cloudflare Token](verify-cloudflare-token)
    + [Find CNAME Records ID](find-cname-records-id)
    + [Verify via CNAME](verify-via-cname)
    + [Cancel Certificate](cancel-certificate)
    + [Revoke Certificate](revoke-certificate)
  * [Dependencies](#dependencies)
  * [License](#license)
  * [Resources](#resources)

## Development Purpose
I manage sh*tload of servers, including profile page, HomeKit gateway, several Hentai@Home distributed file systems. Also, some headless system based on Apache Tomcat, which don't support authentication via HTTP/HTTPS challenge file.

Even though I can update CNAME record through Cloudflare API, certificate downloading and install has to be done manually. Current certificate validity is 90 days, but as that period gets shorter, those process becomes more annoying and frequent.

Developed to automate renewal certificate with ZeroSSL REST API.
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
  "CloudflareZone":{
      "ZoneID": ""
   },
  "CloudflareCNAME":{
      "CNAMERecordsID": [""]
   },
   "ZeroSSLAPI":{
      "AccessKey": "",
      "Cache": ""
   },
   "Certificate":{
      "Domains": ["www.example.com","example.com"],
      "Config": "",
      "CSR": "",
      "PendingPK": "",
      "PK": "",
      "CA": "",
      "CAB": ""
   }
}
```
Configuration file must include following parameters:  

+ ```Telegram BOT``` token and chat ID for status notifications.
+ ```ZeroSSL API Key```
+ ```Cloudflare API configuration``` include API Key, Account email, Zone ID and Specific DNS records.
+ ```Domains``` list that require certificate renewal.
+ ```File paths``` include Certificate Signing Request sign config, CSR, pending / effective Private Key and Certificates.

For using configuration file, please modify filepath inside script.
```python
ConfigFilePath = "/Users/Documents/script_acme4zerossl/acme4zerossl.config.json"
```
Improper configuration may result in partial or complete system failure. Make sure all required parameters are defined in the configuration file.

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

### Verify Cloudflare Token
### Find CNAME Records ID
### Verify via CNAME
### Cancel Certificate
### Revoke Certificate

## Dependencies
### Python version
* Python 3.7.3 or above
* Testing on the above Python version: 3.12.2
### Python module
* logging
* json
* requests
* subprocess
* time
* sys

## License
General Public License -3.0

## Resources
### ZeroSSL API
- [ZeroSSL REST APIdocumentation](https://zerossl.com/documentation/api/)
### Reference repository
- [ZeroSSL-CertRenew](https://github.com/ajnik/ZeroSSL-CertRenew/tree/master)
