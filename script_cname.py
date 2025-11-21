# -*- coding: utf-8 -*-
import acme4zerossl as acme
from time import sleep
from sys import exit

# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
# Apache2       ['systemctl', 'reload', 'apache2']
# Nginx         ['service', 'nginx', 'restart']
ServerCommand  = None

# Script
def main():
    Rt = acme.Runtime(ConfigFilePath)
    Tg = acme.Telegram(ConfigFilePath)
    Cf = acme.Cloudflare(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Create certificates signing request
    ResultCreateCSR = Rt.CreateCSR()
    if type(ResultCreateCSR) is bool:
        Tg.Message2Me("Error occurred during Create CSR and Private key.")
        raise Exception()
    elif type(ResultCreateCSR) is int:
        Rt.Message("Successful create CSR and Private key.")
    # Sending CSR
    VerifyRequest = Zs.ZeroSSLCreateCA()
    if type(VerifyRequest) is int:
        Tg.Message2Me(f"Unable connect ZeroSSL API, HTTP Error: {VerifyRequest}.")
        raise Exception()
    elif type(VerifyRequest) is bool:
        Tg.Message2Me("Error occurred during request new certificate.")
        raise Exception()
    # Phrasing ZeroSSL verify
    elif type(VerifyRequest) is dict:
        VerifyData = Zs.ZeroSSLVerifyData(VerifyRequest, Mode="CNAME")
        Rt.Message(f"ZeroSSL API request successful, certificate hash: {VerifyData['id']}")
    # Update CNAME via Cloudflare API
    if ("additional_domains_cname") not in VerifyData:
        UpdatePayloads = [VerifyData['common_name_cname']]
    elif ("additional_domains_cname") in VerifyData:
        UpdatePayloads = [VerifyData['common_name_cname'],
                          VerifyData['additional_domains_cname']]
    for UpdatePayload in UpdatePayloads:
        ResultUpdateCFCNAME = Cf.UpdateCFCNAME(UpdatePayload)
        if type(ResultUpdateCFCNAME) is dict and ResultUpdateCFCNAME['success'] == True:
            Rt.Message("Successful update CNAME record from Cloudflare.")
            sleep(5)
        elif type(ResultUpdateCFCNAME) is dict and ResultUpdateCFCNAME['success'] == False:
            Tg.Message2Me(f"Cloudflare update Failed, {ResultUpdateCFCNAME['errors']}")
            raise Exception()
        elif type(ResultUpdateCFCNAME) is int:
            Tg.Message2Me(f"Unable connect Cloudflare API, HTTP Error: {ResultUpdateCFCNAME}")
            raise Exception()
        else:
            raise Exception()
    # Wait DNS records update and active
    sleep(30)
    # Verify CNAME challenge
    CertificateID = VerifyData['id']
    VerifyResult = Zs.ZeroSSLVerification(CertificateID)
    if type(VerifyResult) is int:
        Tg.Message2Me(f"Unable connect ZeroSSL API, HTTP Error: {VerifyResult}.")
        raise Exception()
    elif type(VerifyResult) is bool:
        Tg.Message2Me("Error occurred during CNAME verification.")
        raise Exception()
    elif type(VerifyResult) is dict and ("error") in VerifyResult:
        Tg.Message2Me(f"{VerifyResult['error']['type']}")
        raise Exception (VerifyResult['error']['type'])
    # Verify successful, wait issued
    elif type(VerifyResult) is dict and VerifyResult['status'] == ("pending_validation"):
        Rt.Message("CNAME verify successful, wait certificate issued.")
        sleep(30)
    # Verify successful and been issued
    elif type(VerifyResult) is dict and VerifyResult['status'] == ("issued"):
        Rt.Message("CNAME verify successful, certificate been issued.")
        sleep(5)
    # Download certificates
    CertificateContent = Zs.ZeroSSLDownloadCA(CertificateID)
    if type(CertificateContent) is bool:
        Tg.Message2Me("Error occurred during certificates download.")
        raise Exception()
    elif type(CertificateContent) is str:
        Tg.Message2Me(f"Error occurred during download certificate. {CertificateContent}")
        raise Exception(CertificateContent)
    elif type(CertificateContent) is dict and ("certificate.crt") in CertificateContent:
        Rt.Message("Certificate has been downloaded.")
        sleep(5)
    # Install certificate to server folder
    ResultCheck = Rt.CertificateInstall(CertificateContent, ServerCommand)
    if type(ResultCheck) is list or type(ResultCheck) is str:
        Tg.Message2Me(f"Certificate been renewed and installed, will expires in {VerifyResult['expires']}.")
    elif type(ResultCheck) is int:
        Tg.Message2Me(f"Certificate been renewed, will expires in {VerifyResult['expires']}. You may need to restart server manually.")
    elif type(ResultCheck) is bool:
        Tg.Message2Me("Error occurred during certificate install. You may need to download and install manually.")
        raise Exception()
# Runtime, including check validity date of certificate
if __name__ == "__main__":
    try:
        Rt = acme.Runtime(ConfigFilePath)
        # Minimum is 14 days
        CertificateMinimum = Rt.ExpiresCheck()
        if type(CertificateMinimum) is int:
            Rt.Message(f"Certificate's validity date has {CertificateMinimum} days left.")
        elif type(CertificateMinimum) is bool:
            main()
    except Exception:
        exit(0)
# TESTPASS 25K21