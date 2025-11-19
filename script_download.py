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
    Rt.Message("Certificate manual download script start.\r\nDownload certificate hash reference from cache file by default.")
    # Input certificate hash manually
    CertificateID = input("Please input certificate ID (hash), or press ENTER using cache file: ")
    # Download certificate payload
    if len(CertificateID) == 0:
        CertificateContent = Zs.ZeroSSLDownloadCA()
    else:
        CertificateContent = Zs.ZeroSSLDownloadCA(CertificateID)
    # Check
    if type(CertificateContent) is bool:
        Rt.Message("Error occurred during certificates download.")
        raise Exception()
    elif type(CertificateContent) is str:
        Rt.Message(f"Error occurred during download certificate.\r\n{CertificateContent}")
        raise Exception()
    # Download certificate and save to folder
    elif type(CertificateContent) is dict and ("certificate.crt") in CertificateContent:
        ResultCheck = Rt.CertificateInstall(CertificateContent)
    if type(ResultCheck) is list or type(ResultCheck) is str:
        Rt.Message(f"Certificate been downloaded.\r\nYou may need to restart server manually.")
    elif type(ResultCheck) is bool:
        Rt.Message("Error occurred during certificate saving.")
        raise Exception()
# Runtime
if __name__ == "__main__":
    try:
        main()
    except Exception:
        exit(0)
#