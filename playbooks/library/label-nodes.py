#!/usr/bin/python

from ansible.module_utils.basic import *

from kubernetes import client, config
import requests
import os
import sys
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Disable InsecureRequestWarning warnings while connecting to OpenShift API
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# Check if code is running in OpenShift
if "KUBERNETES_SERVICE_HOST" in os.environ and "KUBERNETES_SERVICE_PORT" in os.environ:
    config.load_incluster_config()
else:
    config.load_kube_config()


def labelNode(nodeInfoList):

    api_instance = client.CoreV1Api()
    labelledNodeList = []
     
    for item in nodeInfoList:
        dictLabel = {}
        for label in item['label'].split(','):
            dictLabel[label.split('=')[0].strip()]=label.split('=')[1].strip()

        body = {
            "metadata": {
                "labels": dictLabel
            }
        }

        api_response = api_instance.patch_node(item['node'], body)

        labelledNodeList.append(item['node'])

    return labelledNodeList


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        node_info_list=dict(type="list", required=True),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)


    labelledNodeList = labelNode( module.params['node_info_list'])

    result = dict(
        changed=False,
        labelledNodeCount=0,
        labelledNodeList=''
    )

    if len(labelledNodeList):
        result['labelledNodeCount']  = len(labelledNodeList)
        result['labelledNodeList']   = labelledNodeList
        result['changed']            = True
        
    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()