# -*- coding: utf-8 -*-
import acme4zerossl
from sys import exit
from time import sleep

# !!!!! WARNING !!!!! UNTESTED SCRIPT
# Configuration file
ConfigPath = "/Users/User_Name/Documents/ACME4ZeroSSL/acme4zerossl.config.json"
# Server reload or restart
ServerReloadCommand = ["sudo", "service", "apache2", "reload"]

# Create certificates signing request
acme4zerossl.CreateCertSigningRequest(ConfigPath)
# Start renew certificate
CreateCertificateStatus = acme4zerossl.ZeroSSLCreateCertificate(ConfigPath)
if type(CreateCertificateStatus) is dict:
    print(f"ZeroSSL API request successful, certificate hash: {CreateCertificateStatus["id"]}")
elif type(CreateCertificateStatus) is bool:
    ErrorCreateCertificate = ("Error occurred during request new certificate, please check the error log.")
    acme4zerossl.SendAlertViaTelegram(ConfigPath, MessagePayload = ErrorCreateCertificate)
    print(ErrorCreateCertificate)
    exit()
# Update Cloudflare CNAME Records
GetCnameRecordsID = acme4zerossl.Configuration(ConfigPath)
CnameRecordsID = GetCnameRecordsID["CloudflareCNAME"]["CNAMERecordsID"]
# Check multiple domains
if "Cname2" not in CreateCertificateStatus:
    UpdateDnsRecordCname = [
        CnameRecordsID[0], CreateCertificateStatus["Cname1"][0], CreateCertificateStatus["Cname1"][1]]
    UpdateCnameStatus = acme4zerossl.CloudflareUpdateSpecifyCname(ConfigPath, UpdateDnsRecordCname)
    if type(UpdateCnameStatus) is dict and UpdateCnameStatus["success"] == True:
        print("Successful update CNAME record from Cloudflare.")
        sleep(5)
    else:
        ErrorUpdateCname = ("Error occurred during update CNAME, please check the error log.")
        acme4zerossl.SendAlertViaTelegram(ConfigPath, MessagePayload = ErrorUpdateCname)
        print(ErrorUpdateCname)
        exit()
elif "Cname2" in CreateCertificateStatus:
    UpdateDnsRecordCnames = [
        [CnameRecordsID[0], CreateCertificateStatus["Cname1"][0], CreateCertificateStatus["Cname1"][1]],
        [CnameRecordsID[1], CreateCertificateStatus["Cname2"][0], CreateCertificateStatus["Cname2"][1]]]
    for UpdateDnsRecordCname in UpdateDnsRecordCnames:
        UpdateCnameStatus = acme4zerossl.CloudflareUpdateSpecifyCname(ConfigPath, UpdateDnsRecordCname)
        if type(UpdateCnameStatus) is dict and UpdateCnameStatus["success"] == True:
            print("successful update CNAME record from Cloudflare.")
            sleep(5)
        else:
            ErrorUpdateCname = ("Error occurred during update CNAME, please check the error log.")
            acme4zerossl.SendAlertViaTelegram(ConfigPath, MessagePayload = ErrorUpdateCname)
            print(ErrorUpdateCname)
            exit()
sleep(15)
# Verification
VerificationStatus = acme4zerossl.ZeroSSLVerification(ConfigPath, ValidationMethod = "CNAME_CSR_HASH", CertificateValidation = CreateCertificateStatus)
if type(VerificationStatus) is dict and VerificationStatus["status"] == "pending_validation":
    print("CNAME verify successful.")
    sleep(25)
elif type(VerificationStatus) is dict and VerificationStatus["status"] == "issued":
    print("CNAME verify successful and certificate has been issued.")
elif type(VerificationStatus) is dict and "error" in VerificationStatus:
    ErrorVerification = VerificationStatus["error"]["type"]
    acme4zerossl.SendAlertViaTelegram(ConfigPath, MessagePayload = ErrorVerification)
    print(ErrorVerification)
    exit()
else:
    ErrorVerification = ("Error occurred during verify CNAME, please check the error log.")
    acme4zerossl.SendAlertViaTelegram(ConfigPath, MessagePayload = ErrorVerification)
    print(ErrorVerification)
    exit()
# Download certificate
CertificatePayload = acme4zerossl.ZeroSSLDownloadCertificate(ConfigPath, CertificateValidation = CreateCertificateStatus)
# Install certificate
if type(CertificatePayload) is dict:
    StatusRenew = acme4zerossl.CertificateInstallation(ConfigPath, CertificatePayload, ServerReloadCommand)
    if type(StatusRenew) is int:
        RenewSuccessful = (f"Certificate has been install, will expires at {VerificationStatus["expires"]}")
        acme4zerossl.SendAlertViaTelegram(ConfigPath, MessagePayload = RenewSuccessful)
        print(RenewSuccessful)
        exit()
    elif type(StatusRenew) is bool:
        ErrorInstall = ("Error occurred during download certificate and install, please check the error log.")
        acme4zerossl.SendAlertViaTelegram(ConfigPath, MessagePayload = ErrorInstall)
        print(ErrorInstall)
        exit()
elif type(CertificatePayload) is bool:
    ErrorDownload = ("Error occurred during download certificate, please check the error log.")
    acme4zerossl.SendAlertViaTelegram(ConfigPath, MessagePayload = ErrorDownload)
    print(ErrorDownload)
    exit()
