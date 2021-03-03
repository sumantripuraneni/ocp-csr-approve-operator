#!/usr/bin/python

from ansible.module_utils.basic import *

from kubernetes import client, config
import requests
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Disable InsecureRequestWarning warnings while connecting to OpenShift API
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# Check if code is running in OpenShift
if "KUBERNETES_SERVICE_HOST" in os.environ and "KUBERNETES_SERVICE_PORT" in os.environ:
    config.load_incluster_config()
else:
    config.load_kube_config()

#Function to taint nodes
def taintNode(nodeInfoList):

    api_instance = client.CoreV1Api()
    taintedNodeList = []

    for item in nodeInfoList:
        taints_list = []
        for taint in item["taint"].split(","):
            taintDict = {}
            taintDict["key"] = taint.split("=")[0].strip()
            taintDict["value"] = taint.split("=")[1].strip().split(":")[0]
            taintDict["effect"] = taint.split(":")[1].strip()
            taints_list.append(taintDict)

        body = {"spec": {"taints": taints_list}}

        api_response = api_instance.patch_node(item["node"], body=body)

        taintedNodeList.append(item["node"])

    return taintedNodeList


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        node_info_list=dict(type="list", required=True),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    taintedNodeList = taintNode(module.params["node_info_list"])

    result = dict(changed=False, taintedNodeCount=0, taintedNodeList="")

    if len(taintedNodeList):
        result["taintedNodeCount"] = len(taintedNodeList)
        result["taintedNodeList"] = taintedNodeList
        result["changed"] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
