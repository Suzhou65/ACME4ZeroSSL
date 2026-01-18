# -*- coding: utf-8 -*-
import acme4zerossl as acme
from sys import exit
# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
# Script
def main(CertificateID):
    Rt = acme.Runtime(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Cancel certificate
    CancelStatus = Zs.ZeroSSLCancelCA(CertificateID)
    # Status check, Error
    if not isinstance(CancelStatus, dict):
        raise RuntimeError("Error occurred during cancel.")
    # Standard response, check status
    CancelResult = CancelStatus.get("success")
    if CancelResult == 1:
        Rt.Message(f"Certificate ID: {CertificateID} has been cancelled.")
        return
    elif CancelResult == 0:
        Rt.Message("ZeroSSL REST API request successful, however unable cancel certificate.")
        return
# Runtime
if __name__ == "__main__":
    try:
        # Input certificate hash manually
        CertificateID = input("Please input certificate ID (hash): ")
        # Cancel
        main(CertificateID)
        exit(0)
    except Exception:
        exit(1)
# UNQC
