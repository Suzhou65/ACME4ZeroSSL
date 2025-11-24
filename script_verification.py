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
    Rt.Message("Manual verify start. Certificate hash reference from cache file by default.")
    CertificateID = input("Please input certificate ID (hash), or press ENTER using cache file: ")
    # Verification
    if len(CertificateID) == 0:
        Status = Zs.ZeroSSLVerification()
    else:
        Status = Zs.ZeroSSLVerification(CertificateID)
    # Check
    if type(Status) is int:
        Rt.Message(f"Unable connect ZeroSSL API, HTTP Error: {Status}.")
        raise Exception()
    elif type(Status) is bool:
        Rt.Message("Error occurred during verification.")
        raise Exception()
    # Possible errors respon
    elif type(Status) is dict and ("error") in Status:
        Rt.Message(f"{Status['error']['type']}")
        raise Exception()
    # Unverified
    elif type(Status) is dict and Status['status'] == ("draft"):
        Rt.Message("")
    # Verify successful
    elif type(Status) is dict and Status['status'] == ("pending_validation"):
        Rt.Message("Verify successful, please wait certificate issued.")
    # Issued
    elif type(Status) is dict and Status['status'] == ("issued"):
        Rt.Message("Verify successful, certificate been issued.")

# Runtime
if __name__ == "__main__":
    try:
        main()
    except Exception:
        exit(0)
# TESTPASS 25K24