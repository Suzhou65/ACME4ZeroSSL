# -*- coding: utf-8 -*-
import acme4zerossl as acme
import argparse
import logging
from sys import exit

# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"

# Error handling
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
logging.basicConfig(level=logging.INFO, filename="error.acme4zerossl.log", filemode="a", format=FORMAT)
# Script
def main(CertificateID, RevokeReason):
    Rt = acme.Runtime(ConfigFilePath)
    Revoke = acme.ZeroSSL(ConfigFilePath)
    # Revoke certificate
    RevokeStatus = Revoke.ZeroSSLRevokeCA(CertificateID, RevokeReason)
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
        parser = argparse.ArgumentParser()
        # Certificate ID
        parser.add_argument("--ca", nargs="1", help="Please input certificate ID (hash)")
        # Revoke reason
        parser.add_argument("--vr", nargs="?", default=None, const=None, help="Revoke reason, default is Unspecified")
        args = parser.parse_args()
        CertificateID = args.ca
        RevokeReason = args.vr
        # Revoke
        main(CertificateID, RevokeReason)
        exit(0)
    except KeyboardInterrupt:
        logging.info("Manually interrupt")
        exit(0)
    except Exception as RenewedError:
        logging.exception(f"Script error| {RenewedError}")
        exit(1)
# UNQC
