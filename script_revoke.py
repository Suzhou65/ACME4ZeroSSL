# -*- coding: utf-8 -*-
from acme4zerossl import ZeroSSLRevokeCA
from acme4zerossl import RuntimeMessage
from sys import exit

# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"

def Revoke(ConfigFilePath):
    # Input certificate hash manually
    CertificateID = input("Please input certificate ID (hash): ")
    # Cancel certificate
    RevokeCAResult = ZeroSSLRevokeCA(ConfigFilePath, CertificateID)
    # Status check
    if type(RevokeCAResult) is dict and RevokeCAResult['success'] == 1:
        RuntimeMessage(MessageText = (f"Certificate ID: {CertificateID} has been revoked."))
    elif type(RevokeCAResult) is dict and RevokeCAResult['success'] == 0:
        RuntimeMessage(MessageText = ("ZeroSSL REST API request successful, however unable revoke certificate."))
    elif type(RevokeCAResult) is int:
        RuntimeMessage(MessageText = (f"Unable connect ZeroSSL API, HTTP error code: {RevokeCAResult}."))
    else:
        RuntimeMessage(MessageText = ("Error occurred during revoke certificate."))
    
try:
    Revoke(ConfigFilePath)
    exit(0)
except Exception:
    exit(0)

# TestPass_25J19