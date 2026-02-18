# -*- coding: utf-8 -*-
import logging
from pathlib import Path
import requests
import subprocess
from sys import exit
# Error handling
FORMAT = "%(asctime)s |%(levelname)s |%(message)s"
logging.basicConfig(level=logging.INFO,filename="selfsign.log",filemode="a",format=FORMAT)

# Signing certificate
class SelfSignedCertificate():
    # Configuration
    def __init__(self):
        self.IpIfy4 = "https://api.ipify.org?format=json"
        self.IpIfy6 = "https://api64.ipify.org/?format=json"
        # CSR config
        self.Days         = 47
        self.Country      = "JP"
        self.State        = "Tokyo Metropolis"
        self.Locality     = "Toshima"
        self.Organization = "Tsukinomori Girl's Academy"
        self.Unit         = "Concert Band Club"
        self.CSRConfig    = "selfsigned_certificate.conf"
        # CSR config path
        self.ConfigFolder = Path.cwd()
        # Certificate folder path, None as default path
        self.CertFolder   = None
        # Certificate and private key name
        self.PrivateKey   = "selfsigned_certificate.key"
        self.Certificate  = "selfsigned_certificate.crt"
        # Server command
        self.WebServer    = None
    # Check IP address
    def LocalAddressCheck4(self):
        try:
            with requests.get(self.IpIfy4,timeout=30) as AddressCheck4:
                if AddressCheck4.status_code == 200:
                    AddressCheck4JSON = AddressCheck4.json()
                    return AddressCheck4JSON.get("ip") or None
                else:
                    logging.error(f"Unable get IPv4 address |HTTP error: {AddressCheck4.status_code}")
                    return None
        except Exception as AddressCheck4Error:
            logging.error(f"Unable get IPv4 address |Error: {AddressCheck4Error}")
            return None
    def LocalAddressCheck6(self):
        try:
            with requests.get(self.IpIfy6,timeout=30) as AddressCheck6:
                if AddressCheck6.status_code == 200:
                    AddressCheck6JSON = AddressCheck6.json()
                    return AddressCheck6JSON.get("ip") or None
                else:
                    logging.error(f"Unable get IPv6 address |HTTP error: {AddressCheck6.status_code}")
                    return None
        except Exception as AddressCheck6Error:
            logging.error(f"Unable get IPv6 address |Error: {AddressCheck6Error}")
            return None

    # Certificate Signing Request Config
    def CreateCSR(self,Address4,Address6):
        try:
            CSRConfig4 = f"IP.1 = {Address4}" if isinstance(Address4,str) and Address4.strip() else ""
            CSRConfig6 = f"IP.2 = {Address6}" if isinstance(Address6,str) and Address6.strip() else ""
            CSRConfigContents = [
                # BasicConfig
                "[req]",
                "default_bits = 2048",
                "default_md = sha256",
                "utf8 = yes",
                "string_mask = utf8only",
                "prompt = no",
                "req_extensions = x509_v3_req",
                "distinguished_name = req_distinguished_name",
                # X509BasicConstraints
                "[x509_v3_req]",
                "basicConstraints = CA:FALSE",
                "keyUsage = digitalSignature, keyEncipherment",
                "extendedKeyUsage = serverAuth",
                "subjectAltName = @alt_names",
                "[alt_names]",
                "DNS.1 = localhost",
                CSRConfig4,CSRConfig6,
                # DistinguishedInfo
                "[req_distinguished_name]",
                f"countryName = {self.Country}",
                f"stateOrProvinceName = {self.State}",
                f"localityName = {self.Locality}",
                f"organizationName = {self.Organization}",
                f"organizationalUnitName = {self.Unit}",
                "commonName = localhost"]
            # CSR config
            CSRConfigFile = self.ConfigFolder / self.CSRConfig
            with CSRConfigFile.open("w",encoding="utf-8") as CSRSignConfig:
                # Drop empty configuration
                for CSRConfigLine in filter(None,CSRConfigContents):
                    CSRSignConfig.write(CSRConfigLine + "\n")
        except Exception as CreateCSRError:
            raise RuntimeError(f"Unable create CSR Configuration file |{CreateCSRError}")

    # Create Certificate
    def CertificateSigning(self):
        # CSR path
        CSRConfigFile = self.ConfigFolder / self.CSRConfig
        if not CSRConfigFile.exists():
            raise RuntimeError("Cannot found CSR configuration file")
        # Certificate path
        if self.CertFolder is None or not str(self.CertFolder).strip():
            CertificatesDIR = self.ConfigFolder
        elif isinstance(self.CertFolder,str):
            CertificatesDIR = Path(self.CertFolder)
        elif isinstance(self.CertFolder,Path):
            CertificatesDIR = self.CertFolder
        else:
            raise RuntimeError("CSR configuration file path error")
        CertificatesDIR.mkdir(parents=True,exist_ok=True)
        KeyoutFileStr      = str(CertificatesDIR / self.PrivateKey)
        CertificateFileStr = str(CertificatesDIR / self.Certificate)
        CSRConfigFileStr   = str(CSRConfigFile)
        # OpenSSL generate command
        OpensslCommand = ["openssl","req","-x509","-new",
                          "-nodes","-sha256","-utf8","-days",f"{self.Days}","-newkey","rsa:2048",
                          "-keyout",f"{KeyoutFileStr}","-out",f"{CertificateFileStr}","-config",f"{CSRConfigFileStr}",
                          "-extensions","x509_v3_req"]
        # Generate certificate
        try:
            OpenSSLStatus = subprocess.Popen(OpensslCommand,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            stdout,stderr = OpenSSLStatus.communicate()
            if OpenSSLStatus.returncode != 0:
                raise RuntimeError(f"Error occurred during certificate and private key |Output:{stdout} |Error:{stderr}")
        except Exception as CertificateSigningRequestError:
            logging.exception(CertificateSigningRequestError)
            raise RuntimeError(f"Unbale create certificate and private key |Error{CertificateSigningRequestError}")
        # Server reload
        if self.WebServer is not None and isinstance(self.WebServer, list):
            try:
                ServerStatus = subprocess.Popen(
                    self.WebServer, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                # Discard output
                stdout, stderr = ServerStatus.communicate()
                # Check if reboot command successful
                if ServerStatus.returncode != 0:
                    raise RuntimeError(f"Error occurred during server reload/restart |Output:{stdout} |Error:{stderr}")
            except Exception as ServerReloadError:
                raise RuntimeError(f"Error occurred during server reload/restart |{ServerReloadError}")
# Runtime
try:
    SelfSignCa = SelfSignedCertificate()
    Address4 = SelfSignCa.LocalAddressCheck4()
    Address6 = SelfSignCa.LocalAddressCheck6()
    SelfSignCa.CreateCSR(Address4,Address6)
    SelfSignCa.CertificateSigning()
    logging.info("Successful create self-signed certificate")
    exit(0)
except Exception as RunTimeError:
    logging.warning(f"Script error |{RunTimeError}")
    exit(1)
# QC 2026B18