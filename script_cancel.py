# -*- coding: utf-8 -*-
from acme4zerossl import ZeroSSLCancelCA
from acme4zerossl import RuntimeMessage
from sys import exit

# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"

def Cancel(ConfigFilePath):
    # Input certificate hash manually
    CertificateID = input("Please input certificate ID (hash): ")
    # Cancel certificate
    CancelCAResult = ZeroSSLCancelCA(ConfigFilePath, CertificateID)
    # Status check
    if type(CancelCAResult) is dict and CancelCAResult['success'] == 1:
        RuntimeMessage(MessageText = (f"Certificate ID: {CertificateID} has been cancelled."))
    elif type(CancelCAResult) is dict and CancelCAResult['success'] == 0:
        RuntimeMessage(MessageText = ("ZeroSSL REST API request successful, however unable cancel certificate."))
    elif type(CancelCAResult) is int:
        RuntimeMessage(MessageText = (f"Unable connect ZeroSSL API, HTTP error code: {CancelCAResult}."))
    else:
        RuntimeMessage(MessageText = ("Error occurred during cancel certificate."))

try:
    Cancel(ConfigFilePath)
    exit(0)
except Exception:
    exit(0)

# TestPass_25J19