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
    Status = Zs.ZeroSSLVerification(CertificateID or None)
    # Check
    if isinstance(Status, bool):
        Rt.Message("Error occurred during verification.")
        raise Exception()
    elif isinstance(Status, int):
        Rt.Message(f"Unable connect ZeroSSL API, HTTP Error: {Status}.")
        raise Exception()
    # Possible errors respon
    elif isinstance(Status, dict) and ("error") in Status:
        ErrorStatus = Status['error'] or {}
        ErrorType = ErrorStatus.get("type", "Unknown Error")
        Rt.Message(ErrorType)
        raise Exception()
    elif isinstance(Status, dict) and ("status") in Status:
        VerificationStatus = Status.get("status")
        # Unverified
        if VerificationStatus == ("draft"):
            Rt.Message("Not Verify yet.")
        # Verify successful
        elif VerificationStatus == ("pending_validation"):
            Rt.Message("Verify successful, please wait certificate issued.")
        # Issued
        elif VerificationStatus == ("issued"):
            Rt.Message("Verify successful, certificate been issued.")
        # Incase ZeroSSL adding more status
        else:
            Rt.Message(VerificationStatus)
            raise Exception()
    else:
        Rt.Message(f"Unexpected Type/Format: {type(Status)} -> {Status}")
        raise Exception()

# Runtime
if __name__ == "__main__":
    try:
        main()
    except Exception:
        exit(0)
# TESTPASS 25K24