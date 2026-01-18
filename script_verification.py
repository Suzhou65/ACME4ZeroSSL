# -*- coding: utf-8 -*-
import acme4zerossl as acme
from time import sleep
from sys import exit
# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"
# Validation Method
ValidationMethod = "CNAME_CSR_HASH"
# Script
def main(CertificateID, VerifyRetry, Interval):
    Rt = acme.Runtime(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Prompt
    Rt.Message(f"Validation method set: {ValidationMethod}")
    # Verification
    VerifyStatus = Zs.ZeroSSLVerification(CertificateID, ValidationMethod)
    # Check
    if not isinstance(VerifyStatus, str):
        raise RuntimeError("Error occurred during verification.")
    # Check verify status
    if VerifyStatus == ("draft"):
        raise RuntimeError("Not verified yet.")
    # Verify passed, wait till issued
    elif VerifyStatus == ("pending_validation"):
        Rt.Message("Verify successful, wait certificate issued.")
        for _ in range(VerifyRetry):
            sleep(Interval)
            VerifyStatus = Zs.ZeroSSLVerification(CertificateID, ValidationMethod)
            if VerifyStatus == ("issued"):
                Rt.Message("Verify successful, certificate been issued.")
                return
        else:
            raise RuntimeError(f"Certificate not issued after waiting, status: {VerifyStatus}")
    # Issued
    elif VerifyStatus == ("issued"):
        Rt.Message("Verify successful, certificate been issued.")
        return
    # Undefined error
    else:
        raise RuntimeError(f"Unable to check verify status, undefined status: {VerifyStatus}")
# Runtime
if __name__ == "__main__":
    try:
        Rt = acme.Runtime(ConfigFilePath)
        # Print prompt
        Rt.Message("Manual verify start. Certificate hash reference from cache file by default.")
        CertificateID = input("Please input certificate ID (hash), or press ENTER using cache file: ")
        # Verify, Retry 5 times, period 60s
        main(CertificateID,5,60)
        exit(0)
    except Exception:
        exit(1)
# UNQC
