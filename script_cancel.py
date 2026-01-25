# -*- coding: utf-8 -*-
import acme4zerossl as acme
import logging
import argparse
from sys import exit

# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"

# Error handling
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
logging.basicConfig(level=logging.INFO, filename="error.acme4zerossl.log", filemode="a", format=FORMAT)
# Script
def main(CertificateID):
    # Load object
    Rt = acme.Runtime(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Cancel certificate
    CancelStatus = Zs.ZeroSSLCancelCA(CertificateID)
    # Status check, Error
    if not isinstance(CancelStatus, dict):
        raise RuntimeError("Error occurred during cancel.")
    # Standard response, check status
    CancelResult = CancelStatus.get("success")
    if CancelResult == 1:
        Rt.Message(f"Certificate ID: {CertificateID} has been cancelled.")
        return
    elif CancelResult == 0:
        Rt.Message("ZeroSSL REST API request successful, however unable cancel certificate.")
        return
# Runtime
if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        # Certificate ID
        parser.add_argument("--ca", nargs="1", help="Please input certificate ID (hash)")
        args = parser.parse_args()
        CertificateID = args.ca
        # Cancel
        main(CertificateID)
        exit(0)
    except KeyboardInterrupt:
        logging.info("Manually interrupt")
        exit(0)
    except Exception as ScriptError:
        logging.exception(f"Script error |{ScriptError}")
        exit(1)
# UNQC
