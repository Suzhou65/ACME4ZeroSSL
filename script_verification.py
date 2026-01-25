# -*- coding: utf-8 -*-
import acme4zerossl as acme
import argparse
import logging
from time import sleep
from sys import exit

# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"

# Error handling
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
logging.basicConfig(level=logging.INFO, filename="error.acme4zerossl.log", filemode="a", format=FORMAT)
# Script
def main(CertificateID, ValidationMethod, VerifyRetry, Interval):
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
    if VerifyStatus == "draft":
        raise RuntimeError("Not verified yet.")
    # Verify passed, wait till issued
    elif VerifyStatus == "pending_validation":
        Rt.Message("Verify successful, waiting certificate issuance.")
        # Adding retry and interval in case backlog certificate issuance
        for _ in range(VerifyRetry):
            sleep(Interval)
            VerifyStatus = Zs.ZeroSSLVerification(CertificateID, ValidationMethod)
            if VerifyStatus == "issued":
                Rt.Message("Verify successful, certificate been issued.")
                return
        else:
            raise RuntimeError(f"Certificate wasn't issued after waiting, currently status: {VerifyStatus}")
    # Issued
    elif VerifyStatus == "issued":
        Rt.Message("Verify successful, certificate been issued.")
        return
    # Undefined error
    else:
        raise RuntimeError(f"Unable to check verify status, undefined status: {VerifyStatus}")
# Runtime
if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        # Certificate ID input selection
        parser.add_argument("--ca", nargs="?", default=None, const=None, help="Please input certificate ID (hash), omit to using cache file")
        # Validation Method selection
        parser.add_argument("--vm", nargs="?", default="CNAME_CSR_HASH", const="CNAME_CSR_HASH", help="Validation method, default is CNAME_CSR_HASH)")
        args = parser.parse_args()
        CertificateID = args.ca
        ValidationMethod = args.vm
        # Verify, Retry 5 times, period 60s
        main(CertificateID, ValidationMethod, 15, 60)
        exit(0)
    except KeyboardInterrupt:
        logging.info("Manually interrupt")
        exit(0)
    except Exception as RenewedError:
        logging.exception(f"Script error| {RenewedError}")
        exit(1)
# UNQC
