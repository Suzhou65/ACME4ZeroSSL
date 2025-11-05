# -*- coding: utf-8 -*-
import acme4zerossl as acme
from time import sleep
from sys import exit

# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
# Apache2       ['systemctl', 'reload', 'apache2']
# Nginx         ['service', 'nginx', 'restart']
ServerCommand = None

# Script
def AcmeScript(ConfigFilePath, ServerCommand):
    # Create certificates signing request
    ResultCreateCSR = acme.CreateCSR(ConfigFilePath)
    if type(ResultCreateCSR) is bool:
        TelegramMessage = ("Error occurred during Create CSR and Private key.")
        acme.Telegram2Me(ConfigFilePath, TelegramMessage)
        raise Exception(TelegramMessage)
    elif type(ResultCreateCSR) is int:
        MessageText = ("Successful create CSR and Private key.")
        acme.RuntimeMessage(MessageText)
    # Sending CSR
    VerifyRequest = acme.ZeroSSLCreateCA(ConfigFilePath)
    if type(VerifyRequest) is int:
        TelegramMessage = (f"Unable connect ZeroSSL API, HTTP Error: {VerifyRequest}.")
        acme.Telegram2Me(ConfigFilePath,TelegramMessage)
        raise Exception(TelegramMessage)
    elif type(VerifyRequest) is bool:
        TelegramMessage = ("Error occurred during request new certificate.")
        acme.Telegram2Me(ConfigFilePath,TelegramMessage)
        raise Exception(TelegramMessage)
    # Phrasing ZeroSSL verify
    elif type(VerifyRequest) is dict:
        VerifyData = acme.ZeroSSLVerifyData(ConfigFilePath, VerifyRequest, Mode="CNAME")
        MessageText = (f"ZeroSSL API request successful, certificate hash: {VerifyData['id']}")
        acme.RuntimeMessage(MessageText)
    # Update CNAME via Cloudflare API
    if ("additional_domains_cname") not in VerifyData:
        UpdatePayloads = [VerifyData['common_name_cname']]
    elif ("additional_domains_cname") in VerifyData:
        UpdatePayloads = [VerifyData['common_name_cname'],
                          VerifyData['additional_domains_cname']]
    for UpdatePayload in UpdatePayloads:
        ResultUpdateCFCNAME = acme.UpdateCFCNAME(ConfigFilePath, UpdatePayload)
        if type(ResultUpdateCFCNAME) is dict and ResultUpdateCFCNAME['success'] == True:
            MessageText = ("Successful update CNAME record from Cloudflare.")
            acme.RuntimeMessage(MessageText)
            sleep(5)
        else:
            TelegramMessage = (f"Cloudflare Update Failed, {ResultUpdateCFCNAME['errors']}")
            acme.Telegram2Me(ConfigFilePath,TelegramMessage)
            raise Exception (ResultUpdateCFCNAME['errors'])
    # Wait DNS records update and active
    sleep(30)
    # Verify CNAME challenge
    CertificateID = VerifyData['id']
    VerifyResult = acme.ZeroSSLVerification(ConfigFilePath, CertificateID)
    if type(VerifyResult) is bool:
        TelegramMessage = ("Error occurred during CNAME verification.")
        acme.Telegram2Me(ConfigFilePath, TelegramMessage)
        raise Exception(TelegramMessage)
    elif type(VerifyResult) is dict and ("error") in VerifyResult:
        acme.Telegram2Me(ConfigFilePath, TelegramMessage = VerifyResult['error']['type'])
        raise Exception (VerifyResult['error']['type'])
    # Verify successful, wait issued
    elif type(VerifyResult) is dict and VerifyResult['status'] == ("pending_validation"):
        MessageText = ("CNAME verify successful, wait certificate issued.")
        acme.RuntimeMessage(MessageText)
        sleep(30)
    # Verify successful and been issued
    elif type(VerifyResult) is dict and VerifyResult['status'] == ("issued"):
        MessageText = ("CNAME verify successful, certificate been issued.")
        acme.RuntimeMessage(MessageText)
        sleep(5)
    # Download certificates
    CertificateContent = acme.ZeroSSLDownloadCA(ConfigFilePath, CertificateID)
    if type(CertificateContent) is bool:
        TelegramMessage = ("Error occurred during certificates download.")
        acme.Telegram2Me(ConfigFilePath, TelegramMessage)
        raise Exception(TelegramMessage)
    elif type(CertificateContent) is str:
        TelegramMessage = (f"Error occurred during download certificate. {CertificateContent}")
        acme.Telegram2Me(ConfigFilePath, TelegramMessage)
        raise Exception(CertificateContent)
    elif type(CertificateContent) is dict and ("certificate.crt") in CertificateContent:
        MessageText = ("Certificate has been downloaded.")
        acme.RuntimeMessage(MessageText)
        sleep(5)
    # Install certificate to server folder
    ResultCheck = acme.CertificateInstall(ConfigFilePath, CertificateContent, ServerCommand)
    if type(ResultCheck) is list or type(ResultCheck) is str:
        TelegramMessage = (f"Certificate been renewed and installed,\nwill expires in {VerifyResult['expires']}.")
        acme.Telegram2Me(ConfigFilePath, TelegramMessage)
    elif type(ResultCheck) is int:
        TelegramMessage = (f"Certificate been renewed,\nwill expires in {VerifyResult['expires']}.\nYou may need to restart server manually.")
        acme.Telegram2Me(ConfigFilePath, TelegramMessage)
    elif type(ResultCheck) is bool:
        TelegramMessage = ("Error occurred during certificate install.\nYou may need to download and install manually.")
        acme.Telegram2Me(ConfigFilePath, TelegramMessage)
        raise Exception(CertificateContent)

# Runtime, including check validity date of certificate
try:
    CertificateMinimum = acme.ExpiresCheck(ConfigFilePath)
    if type(CertificateMinimum) is int:
        MessageText = (f"Certificate's validity date has {CertificateMinimum} days left.")
        acme.RuntimeMessage(MessageText)
    elif type(CertificateMinimum) is bool:
        AcmeScript(ConfigFilePath, ServerCommand)
    exit(0)
except Exception:
    exit(0)

# UNTEST_25J27