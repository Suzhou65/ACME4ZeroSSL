# -*- coding: utf-8 -*-
import acme4zerossl as acme
from sys import exit
# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
# Script
def main(CertificateID):
    Rt = acme.Runtime(ConfigFilePath)
    Revoke = acme.ZeroSSL(ConfigFilePath)
    # Revoke certificate
    RevokeStatus = Revoke.ZeroSSLRevokeCA(CertificateID)
    # Status check, Error
    if not isinstance(RevokeStatus, dict):
        raise RuntimeError("Error occurred during revoke.")
    # Standard response, check status
    RevokeResult = RevokeStatus.get("success")
    if RevokeResult == 1:
        Rt.Message(f"Certificate ID: {CertificateID} has been revoked.")
        return
    elif RevokeResult == 0:
        Rt.Message("ZeroSSL REST API request successful, however unable revoke certificate.")
        return
# Runtime
if __name__ == "__main__":
    try:
        # Input certificate hash manually
        CertificateID = input("Please input certificate ID (hash): ")
        # Revoke
        main(CertificateID)
        exit(0)
    except Exception:
        exit(1)
# UNQC
