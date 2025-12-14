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
    CancelStatus = Zs.ZeroSSLCancelCA(CertificateID)
    # Status check, Error
    if isinstance(CancelStatus, bool):
        Rt.Message("Error occurred during cancel.")
    # ZeroSSL REST API HTTP error
    elif isinstance(CancelStatus, int):
        Rt.Message(f"Unable connect ZeroSSL API, HTTP error code: {CancelStatus}.")
        raise Exception()
    # Standard response, check status code
    elif isinstance(CancelStatus, dict):
        CancelResult = CancelStatus.get("success",{})
        if CancelResult == 1:
            Rt.Message(f"Certificate ID: {CertificateID} has been cancelled.")
        elif CancelResult == 0:
            Rt.Message("ZeroSSL REST API request successful, however unable cancel certificate.")
        else:
            Rt.Message(f"Undefined status: {CancelResult}")
            raise Exception()
    else:
        Rt.Message("Error occurred during cancel certificate.")
        raise Exception()
# Runtime
if __name__ == "__main__":
    try:
        main()
    except Exception:
        exit(0)
# QC 2025L14
