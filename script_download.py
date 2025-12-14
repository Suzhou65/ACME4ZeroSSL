# -*- coding: utf-8 -*-
import acme4zerossl as acme
from sys import exit

# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"

# Script
def main():
    Rt = acme.Runtime(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Print prompt
    Rt.Message("Certificate manual download script start. Download certificate hash reference from cache file by default.")
    # Input certificate hash manually
    CertificateID = input("Please input certificate ID (hash), or press ENTER using cache file: ")
    # Download certificate payload
    CertificateContent = Zs.ZeroSSLDownloadCA(CertificateID or None)
    # Check
    if isinstance(CertificateContent, bool):
        Rt.Message("Error occurred during certificates download.")
        raise Exception()
    elif isinstance(CertificateContent, str):
        Rt.Message(f"Error occurred during download certificate. Error status: {CertificateContent}")
        raise Exception()
    # Download certificate and save to folder
    elif isinstance(CertificateContent, dict) and ("certificate.crt") in CertificateContent:
        Rt.Message(f"Downloading certificate...")
    ResultCheck = Rt.CertificateInstall(CertificateContent)
    if isinstance(ResultCheck, bool):
        Rt.Message("Error occurred during certificate saving.")
        raise Exception()
    elif isinstance(ResultCheck, int):
        Rt.Message("Certificate been downloaded to folder. You may need to restart server manually.")
    elif isinstance(ResultCheck, (list,str)):
        Rt.Message(f"Certificate been downloaded and server has reload or restart.")
# Runtime
if __name__ == "__main__":
    try:
        main()
    except Exception:
        exit(0)
# QC 2025L14
