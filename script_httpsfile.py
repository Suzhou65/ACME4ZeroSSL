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
    Tg = acme.Telegram(ConfigFilePath)
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
        Tg.Message2Me(f"Unable connect ZeroSSL API, HTTP Error: {VerifyRequest}")
        raise Exception()
    # Phrasing ZeroSSL verify
    elif isinstance(VerifyRequest, dict):
        VerifyData = Zs.ZeroSSLVerifyData(VerifyRequest, Mode="FILE")
    # Check verify data
    if isinstance(VerifyData, bool):
        Rt.Message(f"Error occurred during phrasing ZeroSSL verify data.")
        raise Exception()
    elif isinstance(VerifyData, dict):
        Rt.Message(f"ZeroSSL API request successful, certificate hash: {VerifyData.get('id')}")
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
        Tg.Message2Me("Error occurred during file verification.")
        raise Exception()
    # ZeroSSL REST API HTTP error
    elif isinstance(VerifyResult, int):
        Tg.Message2Me(f"Unable connect ZeroSSL API, HTTP Error: {VerifyResult}")
        raise Exception()
    # Possible errors respon
    elif isinstance(VerifyResult, dict) and ("error") in VerifyResult:
        VerifyErrorStatus = VerifyResult.get("error",{})
        ErrorType = VerifyErrorStatus.get("type", "Unknown Error")
        Rt.Message(f"Error occurred during file verification: {ErrorType}")
        raise Exception (ErrorType)
    # Check verify status
    elif isinstance(VerifyResult, dict) and ("status") in VerifyResult:
        VerifyStatus = VerifyResult.get("status")
        # Verify successful, wait issued
        if VerifyStatus == ("draft"):
            Rt.Message("Not verified yet.")
            raise Exception()
        elif VerifyStatus == ("pending_validation"):
            Rt.Message("HTTPS file verify successful, wait certificate issued.")
            sleep(30)
        # Verify successful and been issued
        elif VerifyStatus == ("issued"):
            Rt.Message("HTTPS file verify successful, certificate been issued.")
            sleep(5)
        # Undefined error
        else:
            Rt.Message(f"Unable to check verify status, currently status: {VerifyStatus}")
            raise Exception()
    # Delete validation file
    for ValidationFile in ValidationFiles:
        Rt.CleanValidationFile(ValidationFile)
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
    ExpiresDate = VerifyResult.get("expires")
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
# UNQC
