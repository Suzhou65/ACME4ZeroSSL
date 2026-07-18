# -*- coding: utf-8 -*-
import acme4zerossl as acme
import logging
from time import sleep
from sys import exit

# Config load, dictionary or filepath
ConfigFile = "/Documents/script/acme4zerossl.config.json"
# Server reload or restart command
ServerCommand  = None

# Error handling
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
logging.basicConfig(level=logging.WARNING,filename="acme4zerossl.log",filemode="a",format=FORMAT)
# Script
def main(VerifyRetry,Interval):
    # Load object
    Rt = acme.Runtime(ConfigFile)
    Tg = acme.Telegram(ConfigFile)
    Cf = acme.Cloudflare(ConfigFile)
    Zs = acme.ZeroSSL(ConfigFile)
    # Create certificates signing request
    CSRCreateCheck = Rt.CreateCSR()
    if not isinstance(CSRCreateCheck,list):
        raise RuntimeError("Error occurred during Create CSR and Private key.")
    Rt.Message("Successful create CSR and Private key.")
    # Sending CSR to ZeroSSL
    CertCreate = Zs.Create()
    if not isinstance(CertCreate,dict):
        raise RuntimeError("Error occurred during request new certificate.")
    # Phrasing ZeroSSL verify
    VerifyData = Zs.PhrasingVerifyJSON(CertCreate,ValidationMethod="CNAME_CSR_HASH")
    if not isinstance(VerifyData,dict):
        raise RuntimeError("Error occurred during phrasing ZeroSSL verify data.")
    # Check pending certificate ID
    CertID = VerifyData.get("id",None)
    if CertID is None:
        raise RuntimeError("Certificate hash is empty.")
    Rt.Message(f"Request success, pending certificate hash: {CertID}")
    # Check CNAME domain and payload
    UpdatePayloads = [VerifyData['common_name']]
    AdditionalDomains = VerifyData.get('additional_domains')
    if AdditionalDomains:
        UpdatePayloads.append(AdditionalDomains)
    # Update CNAME via Cloudflare API
    for UpdatePayload in UpdatePayloads:
        CNAMEUpdateCheck = Cf.UpdateCNAME(UpdatePayload)
        # Check CNAME update result
        if not isinstance(CNAMEUpdateCheck,dict):
            raise RuntimeError("Error occurred during connect to Cloudflare API update CNAME.")
        else:
            Rt.Message("Successful update CNAME from Cloudflare.")
            sleep(5)
    # Wait DNS records update and active
    sleep(60)
    # Verify CNAME challenge
    CertVerifyCheck = Zs.Verification(CertID,ValidationMethod="CNAME_CSR_HASH")
    if not isinstance(CertVerifyCheck,str):
        raise RuntimeError("Error occurred during verification.")
    # Check verify status
    if CertVerifyCheck == "draft":
        raise RuntimeError("Not verified yet.")
    # Verify passed (Under CNAME and file validation, pending_validation means verify successful)
    elif CertVerifyCheck in ("pending_validation","issued"):
        Rt.Message(f"Verify successful, now downloading certificate.")
        sleep(30)
        # Download certificates, adding retry and interval in case backlog certificate issuance
        for _ in range(VerifyRetry):
            CertContent = Zs.Download(CertID)
            # Successful download certificates
            if isinstance(CertContent,dict):
                Rt.Message("Certificate has been downloaded.")
                break
            sleep(Interval)
        else:
            raise RuntimeError(f"Unable download certificate.")
    # Undefined error
    else:
        raise RuntimeError(f"Unable to check verification status, currently verification status: {CertVerifyCheck}")
    # Install certificate to server folder
    InstallCheck = Rt.Install(CertContent,ServerCommand)
    if InstallCheck is False:
        raise RuntimeError("Error occurred during certificate install. You may need to download and install manually.")
    # Get certificate expires date
    CertExpiresDate = Rt.GetNotValidAfter()
    if isinstance(InstallCheck,int):
        Tg.Message(f"Certificate been renewed, will expires in {CertExpiresDate}. You may need to restart server manually.")
        return
    elif isinstance(InstallCheck,list):
        Tg.Message(f"Certificate been renewed and installed, will expires in {CertExpiresDate}.")
        return

# Runtime, including check validity date of certificate
if __name__ == "__main__":
    try:
        Rt = acme.Runtime(ConfigFile)
        Tg = acme.Telegram(ConfigFile)
        # Default minimum is 14 days
        CertExpiresDays = Rt.ExpiresCheck()
        # Renew determination
        if CertExpiresDays is None:
            main(5,60)
            logging.info("Certificate has been renewed.")
            exit(0)
        # No need to renew
        else:
            Rt.Message(f"Certificate's validity date has {CertExpiresDays} days left.")
            logging.info(f"Certificate check complete |{CertExpiresDays} days left.")
            exit(0)
    except KeyboardInterrupt:
        logging.warning("Manually interrupt.")
        exit(0)
    except Exception as RenewedError:
        logging.exception(f"Script error |{RenewedError}")
        # Notify
        RenewedErrorMessage = str(RenewedError)
        Tg.Message(RenewedErrorMessage)
        exit(1)
# QC 2026G18
