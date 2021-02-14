#!/usr/bin/python

from ansible.module_utils.basic import *

from datetime import datetime, timezone
from kubernetes import config, client
import requests
import os
import sys
import base64
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import cryptography.x509
from cryptography.hazmat.backends import default_backend


# Disable InsecureRequestWarning warnings while connecting to OpenShift API
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# Check if code is running in OpenShift
if "KUBERNETES_SERVICE_HOST" in os.environ and "KUBERNETES_SERVICE_PORT" in os.environ:
    config.load_incluster_config()
else:
    config.load_kube_config()


# Function to validate and approve csr
def valiate_approve_csr(csrList, nodeInfoList):


    # Initialize empty lists
    approvedBootStrappedNodes, approvedNodes, approvedNodesToLabel, approvedCSRs = [], [], [], []

    # a reference to the API  
    certs_api = client.CertificatesV1beta1Api()

    for csrName in csrList:


        #Initialize variables
        csrType, dnsName, ip = None, None, None

        # obtain the body of the CSR we want to sign
        body = certs_api.read_certificate_signing_request_status(csrName)

        # Decode base64 string to pem format csr 
        decodedCertificate = base64.b64decode(body.spec.request).decode('utf-8')

        # Load pem format csr 
        try:
            certificate = cryptography.x509.load_pem_x509_csr(bytes(decodedCertificate, encoding='utf8'), default_backend())
        except Exception:
            print("Error loading CSR")
            sys.exit(1)


        if 'bootstrapper' in body.spec.username and 'system:node:' not in body.spec.username:

            csrType = "bootstrapper"

            dnsName = certificate.subject.get_attributes_for_oid(cryptography.x509.oid.NameOID.COMMON_NAME)[0].value.split(':')[2]

            print("Certificate DNS: {}".format(dnsName))

        elif 'bootstrapper' not in body.spec.username and 'system:node:'  in body.spec.username:

            csrType = "node"

            crt_san_data = certificate.extensions.get_extension_for_oid(cryptography.x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)

            dnsName = crt_san_data.value.get_values_for_type(cryptography.x509.DNSName)[0]

            ip = crt_san_data.value.get_values_for_type(cryptography.x509.IPAddress)[0]

            print("Certificate DNS: {}".format(dnsName))
            print("Certificate IP Address: {}".format(ip))

        else:
            print("Unknown CSR type")
            sys.exit(1)

        if ( ( csrType == "node" and next((item for item in nodeInfoList if item["node"] == dnsName), None) and 
             next((item for item in nodeInfoList if item["ip"] == str(ip)), None) ) or 
             ( csrType == "bootstrapper" and next((item for item in nodeInfoList if item["node"] == dnsName), None))):
 
            # create an approval condition
            approval_condition = client.V1beta1CertificateSigningRequestCondition(
                last_update_time=datetime.now(timezone.utc).astimezone(),
                message='This certificate was approved by CSR Approval Operator',
                reason='Validated and approved by CSR Approval Operator',
                type='Approved')

            # patch the existing `body` with the new conditions
            # you might want to append the new conditions to the existing ones
            body.status.conditions = [approval_condition]

            # patch the Kubernetes object
            response = certs_api.replace_certificate_signing_request_approval(csrName, body)
            
            #Increase count of approvedCSRCount variable 
            approvedCSRs.append(csrName)

            if (csrType == 'node' and any('label' in d for d in nodeInfoList if d['node'] == dnsName)):
                approvedNodesToLabel.append({"node": dnsName, "label": ''.join([d['label'] for d in nodeInfoList if d['node'] == dnsName])})
                approvedNodes.append(dnsName)
            elif (csrType == 'node' and not any('label' in d for d in nodeInfoList if d['node'] == dnsName)):
                approvedNodes.append(dnsName)
            elif csrType == "bootstrapper":
                approvedBootStrappedNodes.append(dnsName)
  
    return approvedNodes, approvedCSRs, approvedNodesToLabel, approvedBootStrappedNodes


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        csr_list=dict(type="list", required=True),
        node_info_list=dict(type="list", required=True),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    # test_list = list(module.params['csr_list'])

    for csr in module.params['csr_list']:
        print(csr)

    approvedNodeList, approvedCSRList, approvedNodesToLabel, approvedBootStrappedNodes = valiate_approve_csr(module.params['csr_list'], module.params['node_info_list'])

    result = dict(
        changed=False,
        approvedCSRCount=0,
        approvedNodes='',
        approvedCSRs='',
        approvedNodesToLabel='',
        approvedBootStrappedNodes=''
    )

    if len(approvedCSRList):
        result['approvedCSRCount']             = len(approvedCSRList)
        result['approvedCSRs']                 = approvedCSRList
        result['approvedNodes']                = approvedNodeList
        result['approvedNodesToLabel']         = approvedNodesToLabel
        result['approvedBootStrappedNodes']    = approvedBootStrappedNodes
        result['changed']                      = True
        
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()