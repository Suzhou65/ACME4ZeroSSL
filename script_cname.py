# -*- coding: utf-8 -*-
import acme4zerossl as acme
import logging
from time import sleep
from sys import exit

# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
ServerCommand  = None

# Error handling
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
logging.basicConfig(level=logging.INFO, filename="error.acme4zerossl.log", filemode="a", format=FORMAT)
# Script
def main(VerifyRetry, Interval):
    # Load object
    Rt = acme.Runtime(ConfigFilePath)
    Tg = acme.Telegram(ConfigFilePath)
    Cf = acme.Cloudflare(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Create certificates signing request
    ResultCreateCSR = Rt.CreateCSR()
    if not isinstance(ResultCreateCSR,list):
        raise RuntimeError("Error occurred during Create CSR and Private key.")
    Rt.Message("Successful create CSR and Private key.")
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
        if not isinstance(ResultUpdateCFCNAME,dict):
            raise RuntimeError("Error occurred during connect to Cloudflare API update CNAME.")
        else:
            Rt.Message("Successful update CNAME from Cloudflare.")
            sleep(5)
    # Wait DNS records update and active
    sleep(60)
    # Verify CNAME challenge
    VerifyResult = Zs.ZeroSSLVerification(CertificateID)
    if not isinstance(VerifyResult,str):
        raise RuntimeError("Error occurred during verification.")
    # Check verify status
    if VerifyResult == "draft":
        raise RuntimeError("Not verified yet.")
    # Verify passed
    elif VerifyResult in ("pending_validation","issued"):
        # Adding retry and interval in case backlog certificate issuance
        for _ in range(VerifyRetry):
            VerifyResult = Zs.ZeroSSLVerification(CertificateID)
            if VerifyResult == "issued":
                Rt.Message(f"Verify successful")
                break
            sleep(Interval)
        else:
            raise RuntimeError(f"Unable check verification status after waiting, currently status: {VerifyResult}")
    # Undefined error
    else:
        raise RuntimeError(f"Unable to check verification status, undefined status: {VerifyResult}")
    # Download certificates, adding retry and interval in case backlog certificate issuance
    for _ in range(VerifyRetry):
        CertificateContent = Zs.ZeroSSLDownloadCA(CertificateID)
        if isinstance(CertificateContent, dict):
            Rt.Message("Certificate has been downloaded.")
            break
        sleep(Interval)
    else:
        raise RuntimeError(f"Unable download certificate after waiting.")
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
            logging.info("Certificate has been renewed")
            exit(0)
        # No need to renew
        Rt.Message(f"Certificate's validity date has {ExpiresDays} days left.")
        logging.info("Certificate renewed check complete")
        exit(0)
    except KeyboardInterrupt:
        logging.info("Manually interrupt")
        exit(0)
    except Exception as RenewedError:
        logging.exception(f"Script error| {RenewedError}")
        # Notify
        RenewedErrorMessage = str(RenewedError)
        Tg.Message2Me(RenewedErrorMessage)
        exit(1)
# UNQC
