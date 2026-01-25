# -*- coding: utf-8 -*-
import acme4zerossl as acme
import logging
import argparse
from time import sleep
from sys import exit

# Config
ConfigFilePath = "/Documents/script/acme4zerossl.config.json"

# Error handling
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
logging.basicConfig(level=logging.INFO, filename="error.acme4zerossl.log", filemode="a", format=FORMAT)
# Script
def main(CertificateID, VerifyRetry, Interval):
    Rt = acme.Runtime(ConfigFilePath)
    Zs = acme.ZeroSSL(ConfigFilePath)
    # Download certificates, adding retry and interval in case backlog certificate issuance
    for _ in range(VerifyRetry):
        CertificateContent = Zs.ZeroSSLDownloadCA(CertificateID)
        if isinstance(CertificateContent, dict):
            Rt.Message("Certificate has been downloaded.")
            break
        sleep(Interval)
    else:
        raise RuntimeError(f"Unable download certificate after waiting.")
    # Install certificate to server folder
    ResultCheck = Rt.CertificateInstall(CertificateContent)
    if ResultCheck is False:
        raise RuntimeError("Error occurred during moving certificate to folder.")
    if isinstance(ResultCheck, int):
        Rt.Message("Certificate been downloaded to folder. You may need to restart server manually.")
        return
    elif isinstance(ResultCheck, list):
        Rt.Message(f"Certificate been downloaded and server has reload or restart.")
        return
# Runtime
if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        # Certificate ID input selection
        parser.add_argument("--ca", nargs="?", default=None, const=None, help="Please input certificate ID (hash), omit to using cache file")
        args = parser.parse_args()
        CertificateID = args.ca
        # Download
        main(CertificateID, 15, 60)
        exit(0)
    except KeyboardInterrupt:
        logging.info("Manually interrupt")
        exit(0)
    except Exception as ScriptError:
        logging.exception(f"Script error |{ScriptError}")
        exit(1)
# UNQC
