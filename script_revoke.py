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
    if type(RevokeStatus) is dict and RevokeStatus['success'] == 1:
        Rt.Message(f"Certificate ID: {CertificateID} has been revoked.")
    elif type(RevokeStatus) is dict and RevokeStatus['success'] == 0:
        Rt.Message("ZeroSSL REST API request successful, however unable revoke certificate.")
        raise Exception()
    elif type(RevokeStatus) is int:
        Rt.Message(f"Unable connect ZeroSSL API, HTTP error code: {RevokeStatus}.")
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
#