# -*- coding: utf-8 -*-
import acme4zerossl as acme
from time import sleep
from sys import exit
# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
ServerCommand  = None
# Script
def main(VerifyRetry, Interval):
    Rt = acme.Runtime(ConfigFilePath)
    Tg = acme.Telegram(ConfigFilePath)
    Cf = acme.Cloudflare(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Create certificates signing request
    ResultCreateCSR = Rt.CreateCSR()
    if not isinstance(ResultCreateCSR, list):
        raise RuntimeError("Error occurred during Create CSR and Private key.")
    Rt.Message("Successful create CSR and Private key.")
    # Sending CSR
    VerifyRequest = Zs.ZeroSSLCreateCA()
    if not isinstance(VerifyRequest, dict):
        raise RuntimeError("Error occurred during request new certificate.")
    # Phrasing ZeroSSL verify
    VerifyData = Zs.ZeroSSLVerifyData(VerifyRequest, ValidationMethod="CNAME_CSR_HASH")
    if not isinstance(VerifyData, dict):
        raise RuntimeError("Error occurred during phrasing ZeroSSL verify data.")
    CertificateID = VerifyData.get("id", None)
    if CertificateID is None:
        raise RuntimeError("Certificate hash is empty.")
    Rt.Message(f"ZeroSSL API request successful, certificate hash: {CertificateID}")
    # Update CNAME via Cloudflare API
    UpdatePayloads = [VerifyData['common_name']]
    AdditionalDomains = VerifyData.get('additional_domains')
    if AdditionalDomains:
        UpdatePayloads.append(AdditionalDomains)
    # Update Cloudflare CNAME records
    for UpdatePayload in UpdatePayloads:
        ResultUpdateCFCNAME = Cf.UpdateCFCNAME(UpdatePayload)
        # Check CNAME update result
        if not isinstance(ResultUpdateCFCNAME, dict):
            raise RuntimeError("Error occurred during connect to Cloudflare API update CNAME.")
        else:
            Rt.Message("Successful update CNAME from Cloudflare.")
            sleep(5)
    # Wait DNS records update and active
    sleep(30)
    # Verify CNAME challenge
    VerifyResult = Zs.ZeroSSLVerification(CertificateID, ValidationMethod="CNAME_CSR_HASH")
    if not isinstance(VerifyResult, str):
        raise RuntimeError("Error occurred during CNAME verification.")
    # Check verify status
    if VerifyResult == ("draft"):
        raise RuntimeError("Not verified yet.")
    # Verify passed, wait till issued
    elif VerifyResult == ("pending_validation"):
        Rt.Message("CNAME verify successful, wait certificate issued.")
        for _ in range(VerifyRetry):
            sleep(Interval)
            VerifyResult = Zs.ZeroSSLVerification(CertificateID, ValidationMethod="CNAME_CSR_HASH")
            if VerifyResult == ("issued"):
                Rt.Message("CNAME verify successful, certificate been issued.")
                break
        else:
            raise RuntimeError(f"Certificate not issued after waiting, status: {VerifyResult}")
    # Issued
    elif VerifyResult == ("issued"):
        Rt.Message("CNAME verify successful, certificate been issued.")
        sleep(5)
    # Undefined error
    else:
        raise RuntimeError(f"Unable to check verify status, undefined status: {VerifyResult}")
    # Download certificates
    CertificateContent = Zs.ZeroSSLDownloadCA(CertificateID)
    if not isinstance(CertificateContent, dict):
        raise RuntimeError("Error occurred during certificates download.")
    Rt.Message("Certificate has been downloaded.")
    sleep(5)
    # Install certificate to server folder
    ResultCheck = Rt.CertificateInstall(CertificateContent, ServerCommand)
    if ResultCheck is False:
        raise RuntimeError("Error occurred during certificate install. You may need to download and install manually.")
    # Get certificate expires date
    ExpiresDate = VerifyData.get("expires","unknown")
    if isinstance(ResultCheck, int):
        Tg.Message2Me(f"Certificate been renewed, will expires in {ExpiresDate}. You may need to restart server manually.")
        return
    elif isinstance(ResultCheck, list):
        Tg.Message2Me(f"Certificate been renewed and installed, will expires in {ExpiresDate}.")
        return
# Runtime, including check validity date of certificate
if __name__ == "__main__":
    try:
        Rt = acme.Runtime(ConfigFilePath)
        Tg = acme.Telegram(ConfigFilePath)
        # Default minimum is 14 days
        ExpiresDays = Rt.ExpiresCheck()
        # Renew determination
        if ExpiresDays is None:
            main(5,60)
            exit(0)
        # No need to renew
        Rt.Message(f"Certificate's validity date has {ExpiresDays} days left.")
        exit(0)
    except Exception as RenewedError:
        RenewedErrorMessage = str(RenewedError)
        Tg.Message2Me(RenewedErrorMessage)
        exit(1)
# UNQC
