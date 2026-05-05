# -*- coding: utf-8 -*-
import acme4zerossl as acme
import logging
from time import sleep
from sys import exit

# Config load, dictionary or filepath
ConfigFile = "/Documents/script/acme4zerossl.config.json"

# Error handling
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
logging.basicConfig(level=logging.WARNING,filename="cpanel.log",filemode="a",format=FORMAT)

# Script
def main(VerifyRetry,Interval):
    # Load object
    Rt = acme.Runtime(ConfigFile)
    Zs = acme.ZeroSSL(ConfigFile)
    Cf = acme.Cloudflare(ConfigFile)
    Cp = acme.Cpanel(ConfigFile)
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
    # Save certificate to folder
    InstallCheck = Rt.Install(CertContent)
    if InstallCheck is False:
        raise RuntimeError("Error occurred during certificate install. You may need to download and install manually.")
    if isinstance(InstallCheck,int):
        Rt.Message("Certificate has been downloaded to folder, now uploading to cPanel.")
    # Upload certificate
    CertUploadCheck = Cp.UploadCertificate()
    if not isinstance(CertUploadCheck,dict):
        raise RuntimeError("Error occurred during upload certificate via cPanel UAPI.")
    # Upload private key
    PrivateKeyUploadCheck = Cp.UploadPrivateKey()
    if not isinstance(PrivateKeyUploadCheck,dict):
        raise RuntimeError("Error occurred during upload private key via cPanel UAPI.")
    # Upload CA bundle and install
    CertInstallCheck = Cp.Install()
    # cPanel respon may timeout
    if CertInstallCheck is False:
        raise RuntimeError("Error occurred during install certificate via cPanel UAPI.")
    else:
        CertExpiresDate = CertCreate.get("expires","Unknown")
    # Check certificate install
    cPanelCheckResult = Cp.CertificateCheck()
    if cPanelCheckResult is False:
        raise RuntimeError("Error occurred during check certificate installed status.")
    elif isinstance(cPanelCheckResult,list) and len(cPanelCheckResult) == 2:
        RemainDays,ValidityDays = cPanelCheckResult
        if RemainDays >= (ValidityDays - 3):
            Tg.Message(f"Certificate been renewed and installed, will expires in {CertExpiresDate}.")
            return
        else:
            Tg.Message(f"Certificate been renewed but not immediately installed after signed, will expires in {CertExpiresDate}.")
            return
    else:
        raise RuntimeError("Unable to verify certificate status.")

# Runtime, including check validity date of certificate
if __name__ == "__main__":
    Cp = acme.Cpanel(ConfigFile)
    Tg = acme.Telegram(ConfigFile)
    Rt = acme.Runtime(ConfigFile)
    try:
        # Check cPanle hosting server certificate
        CertExpiresDays = Cp.CertificateCheck()
        # Unable check
        if isinstance(CertExpiresDays,list) and len(CertExpiresDays) == 2:
            RemainDays,ValidityDays = CertExpiresDays
            if RemainDays <= 14:
                main(5,60)
                logging.info("Certificate has been renewed.")
                exit(0)
            # No need to renew
            else:
                Rt.Message(f"Certificate's validity date has {RemainDays} days left.")
                logging.info(f"Certificate check complete |{RemainDays} days left.")
                exit(0)
        else:
            raise RuntimeError("Unable to check certificate status from cPanel.")
    except KeyboardInterrupt:
        logging.warning("Manually interrupt.")
        exit(0)
    except Exception as RenewedError:
        logging.exception(f"Script error |{RenewedError}")
        # Notify
        RenewedErrorMessage = str(RenewedError)
        Tg.Message(RenewedErrorMessage)
        exit(1)
# QC 2026E04
