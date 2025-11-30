# -*- coding: utf-8 -*-
import acme4zerossl as acme
from sys import exit

# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
# Script
def main():
    Rt = acme.Runtime(ConfigFilePath)
    Revoke = acme.ZeroSSL(ConfigFilePath)
    # Input certificate hash manually
    CertificateID = input("Please input certificate ID (hash): ")
    # Revoke certificate
    RevokeStatus = Revoke.ZeroSSLRevokeCA(CertificateID)
    # Status check
    if isinstance(RevokeStatus, bool):
        Rt.Message("Error occurred during revoke.")
    elif isinstance(RevokeStatus, int):
        Rt.Message(f"Unable connect ZeroSSL API, HTTP error code: {RevokeStatus}.")
        raise Exception()
    elif isinstance(RevokeStatus, dict) and ("success") in RevokeStatus:
        RevokeResult = RevokeStatus.get("success", None)
        if RevokeResult == 1:
            Rt.Message(f"Certificate ID: {CertificateID} has been revoked.")
        elif RevokeResult == 0:
            Rt.Message("ZeroSSL REST API request successful, however unable revoke certificate.")
        else:
            Rt.Message(f"Undefined status: {RevokeResult}")
            raise Exception()
    else:
        Rt.Message("Error occurred during revoke certificate.")
        raise Exception()

# Runtime
if __name__ == "__main__":
    try:
        main()
    except Exception:
        exit(0)
# TESTPASS 25K22