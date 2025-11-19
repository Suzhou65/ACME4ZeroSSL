# -*- coding: utf-8 -*-
import acme4zerossl as acme
from sys import exit

# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
# Script
def main():
    Rt = acme.Runtime(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Input certificate hash manually
    CertificateID = input("Please input certificate ID (hash): ")
    # Cancel certificate
    CancelCAResult = Zs.ZeroSSLCancelCA(CertificateID)
    # Status check
    if type(CancelCAResult) is dict and CancelCAResult['success'] == 1:
        Rt.Message(f"Certificate ID: {CertificateID} has been cancelled.")
    elif type(CancelCAResult) is dict and CancelCAResult['success'] == 0:
        Rt.Message("ZeroSSL REST API request successful, however unable cancel certificate.")
    elif type(CancelCAResult) is int:
        Rt.Message(f"Unable connect ZeroSSL API, HTTP error code: {CancelCAResult}.")
    else:
        Rt.Message("Error occurred during cancel certificate.")
# Runtime
if __name__ == "__main__":
    try:
        main()
    except Exception:
        exit(0)
#