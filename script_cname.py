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
    if isinstance(ResultCreateCSR, bool):
        Tg.Message2Me("Error occurred during Create CSR and Private key.")
        raise Exception()
    elif isinstance(ResultCreateCSR, int):
        Rt.Message("Successful create CSR and Private key.")
    # Sending CSR
    VerifyRequest = Zs.ZeroSSLCreateCA()
    # Function error
    if isinstance(VerifyRequest, bool):
        Tg.Message2Me("Error occurred during request new certificate.")
        raise Exception()
    # ZeroSSL REST API HTTP error
    elif isinstance(VerifyRequest, int):
        Tg.Message2Me(f"Unable connect ZeroSSL API, HTTP Error: {VerifyRequest}.")
        raise Exception()
    # Phrasing ZeroSSL verify
    elif isinstance(VerifyRequest, dict):
        VerifyData = Zs.ZeroSSLVerifyData(VerifyRequest, Mode="CNAME")
        Rt.Message(f"ZeroSSL API request successful, certificate hash: {VerifyData['id']}")
    # Update CNAME via Cloudflare API
    if ("additional_domains_cname") not in VerifyData:
        UpdatePayloads = [VerifyData['common_name_cname']]
    elif ("additional_domains_cname") in VerifyData:
        UpdatePayloads = [VerifyData['common_name_cname'],
                          VerifyData['additional_domains_cname']]
    # Update Cloudflare CNAME records
    for UpdatePayload in UpdatePayloads:
        ResultUpdateCFCNAME = Cf.UpdateCFCNAME(UpdatePayload)
        # Function error
        if isinstance(ResultUpdateCFCNAME, bool):
            Tg.Message2Me(f"Error occurred during update CNAME")
            raise Exception()
        # Cloudflare API HTTP error
        elif isinstance(ResultUpdateCFCNAME, int):
            Tg.Message2Me(f"Unable connect Cloudflare API, HTTP Error: {ResultUpdateCFCNAME}")
            raise Exception()
        # Check CNAME update result
        elif isinstance(ResultUpdateCFCNAME, dict):
            ResultUpdateResult = ResultUpdateCFCNAME.get("success", None)
            if ResultUpdateResult == True:
                Rt.Message("Successful update CNAME record from Cloudflare.")
                sleep(5)
            elif ResultUpdateResult == False:
                Tg.Message2Me(f"Cloudflare update Failed, {ResultUpdateCFCNAME['errors']}")
                raise Exception()
            else:
                Tg.Message2Me("Undefined error occurred during connect Cloudflare API")
                raise Exception()
        else:
            Tg.Message2Me("Undefined error occurred during update CNAME")
            raise Exception()
    # Wait DNS records update and active
    sleep(30)
    # Verify CNAME challenge
    CertificateID = VerifyData['id']
    VerifyResult = Zs.ZeroSSLVerification(CertificateID)
    # Function error
    if isinstance(VerifyResult, bool):
        Tg.Message2Me("Error occurred during CNAME verification.")
        raise Exception()
    # ZeroSSL REST API HTTP error
    elif isinstance(VerifyResult, int):
        Tg.Message2Me(f"Unable connect ZeroSSL API, HTTP Error: {VerifyResult}.")
        raise Exception()
    # Possible errors respon
    elif isinstance(VerifyResult, dict) and ("error") in VerifyResult:
        VerifyErrorStatus = VerifyResult['error'] or {}
        ErrorType = VerifyErrorStatus.get("type", "Unknown Error")
        Rt.Message(f"Error occurred during CNAME verification: {ErrorType}")
        raise Exception (ErrorType)
    # Check verify status
    elif isinstance(VerifyResult, dict) and ("status") in VerifyResult:
        VerifyStatus = VerifyResult.get("status")
        # Verify successful, wait issued
        if VerifyStatus == ("draft"):
            Rt.Message("Not Verify yet.")
            raise Exception()
        elif VerifyStatus == ("pending_validation"):
            Rt.Message("CNAME verify successful, wait certificate issued.")
            sleep(30)
        # Verify successful and been issued
        elif VerifyStatus == ("issued"):
            Rt.Message("CNAME verify successful, certificate been issued.")
            sleep(5)
    # Download certificates
    CertificateContent = Zs.ZeroSSLDownloadCA(CertificateID)
    if isinstance(CertificateContent, bool):
        Tg.Message2Me("Error occurred during certificates download.")
        raise Exception()
    elif isinstance(CertificateContent, str):
        Tg.Message2Me(f"Error occurred during download certificate. {CertificateContent}")
        raise Exception(CertificateContent)
    elif isinstance(CertificateContent, dict) and ("certificate.crt") in CertificateContent:
        Rt.Message("Certificate has been downloaded.")
        sleep(5)
    # Install certificate to server folder
    ResultCheck = Rt.CertificateInstall(CertificateContent, ServerCommand)
    ExpiresDate = VerifyResult.get("expires", None)
    if isinstance(ResultCheck, bool):
        Tg.Message2Me("Error occurred during certificate install. You may need to download and install manually.")
        raise Exception()
    elif isinstance(ResultCheck, int):
        Tg.Message2Me(f"Certificate been renewed, will expires in {ExpiresDate}. You may need to restart server manually.")
    elif isinstance(ResultCheck, (list,str)):
        Tg.Message2Me(f"Certificate been renewed and installed, will expires in {ExpiresDate}.")
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
# UNT