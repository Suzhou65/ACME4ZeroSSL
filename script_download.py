# -*- coding: utf-8 -*-
import acme4zerossl as acme
from sys import exit
# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
# Script
def main(CertificateID):
    Rt = acme.Runtime(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Download certificate payload
    CertificateContent = Zs.ZeroSSLDownloadCA(CertificateID)
    # Status check, Error
    if not isinstance(CertificateContent, dict):
        raise RuntimeError("Error occurred during certificates download.")
    # Download
    Rt.Message(f"Downloading certificate...")
    ResultCheck = Rt.CertificateInstall(CertificateContent)
    if ResultCheck is False:
        raise RuntimeError("Error occurred during certificate saving.")
    if isinstance(ResultCheck, int):
        Rt.Message("Certificate been downloaded to folder. You may need to restart server manually.")
        return
    elif isinstance(ResultCheck, list):
        Rt.Message(f"Certificate been downloaded and server has reload or restart.")
        return
# Runtime
if __name__ == "__main__":
    try:
        Rt = acme.Runtime(ConfigFilePath)
        # Print prompt
        Rt.Message("Certificate manual download script. Download certificate hash reference from cache file by default.")
        # Input certificate hash manually
        CertificateID = input("Please input certificate ID (hash), or press ENTER using cache file: ")
        # Download
        main(CertificateID)
        exit(0)
    except Exception:
        exit(1)
# UNQC
