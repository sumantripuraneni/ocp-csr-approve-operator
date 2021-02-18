# ocp-csr-approve-operator
An operator to approve OpenShift Certificate Signing Requests (CSR) generated during node addition to OpenShift Container Platform 4. 

This operator provides the following functionality:

*  Watch the CSR endpoint for CSR requests
*  Decide if the CSR should be approved or not
*  Approve and update CSR status
*  Optionally label the approved node(s)


## Introduction

Kubernetes includes support for [TLS
bootstrapping](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet-tls-bootstrapping/)
for Nodes, which OpenShift makes use of.

Kubelet needs two certificates for its normal operation:

* **Client certificate** - for securely communicating with the Kubernetes API
  server
* **Server certificate** - for use in its own local https endpoint, [used by
  the API server to talk back to
  kubelet](https://kubernetes.io/docs/concepts/architecture/master-node-communication/#apiserver-to-kubelet)

When a new host is provisioned, kubelet will start and communicates to the CSR
(Certificate Signing Request) API endpoint to request signed client and server
certificates.  It issues this request using [bootstrap
credentials](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet-tls-bootstrapping/#initial-bootstrap-authentication)
that it finds on its local filesystem.

At this point, these CSRs must be approved.  They can be manually [approved
through the API using
kubectl](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet-tls-bootstrapping/#kubectl-approval),
or [kube-controller-manager can be configured to approve
them](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet-tls-bootstrapping/#kube-controller-manager-configuration).
Alternatively, some custom component could be built to approve CSRs through the
API, which is what OpenShift has done.


## Motivation

In user provisioned installer (UPI) disconnected environment, `cluster-machine-approver` cannot approve Certificate Signing Requests (CSR). Initailly, we leveraged Ansible to approve the CSR's in our provisioning playbooks/roles, however overall node provisioning process was taking quite a time waiting for CSR's to appear and approve the CSR's, when adding a huge number of nodes (example 20 nodes) to the cluster. So, this operator was developed to approve the OpenShift CSR's.


## CSR Approval Workflow

Assuming a custom resource(CR) was created with required details (as example of custom resource shown below), this operator follow below steps

*  Get list of Certificate Signing Requests (CSR) 
*  Prepares a list of Certificate Signing Requests (CSR) waiting for approval
*  Extract and validate Certificate Signing Request (CSR) 
    *  Extracts DNS (for bootstrap CSR) , DNS and IP Address (for node CSR) from Certificate Signing Requests waiting for approval
    *  Validate and approve a bootstarp CSR 
      *   The username in the CSR must be system:serviceaccount:openshift-machine-config-operator:node-bootstrapper
      *   The groups in the CSR must be system:serviceaccounts:openshift-machine-config-operator, system:serviceaccounts, and system:authenticated
      *  Validate Certificate Signing Request (DNS) with data from custom resource 
      *  Approve Certificate Signing Request (CSR), if the DNS (for bootstrap CSR) , DNS and IP Address matches (for node CSR) matches with customr resource data
*  Optionally, label the node with the label data provided in customr resource
    

#### Sample Custom Resources

An example of custom resource without  `label` key

```yaml
apiVersion: csrapprover.redhat.com/v1alpha1
kind: Csrapprove
metadata:
  name: csrapprove-worker-1
  namespace: ocp-csr-approve-operator-system
spec:
  nodes_info: '[ {"node": "ocp4-worker-1.example.com", "ip": "100.240.10.120"} ]'

```

An example of custom resource with  `label` key
```yaml
apiVersion: csrapprover.redhat.com/v1alpha1
kind: Csrapprove
metadata:
  name: csrapprove-ocsnode02
  namespace: ocp-csr-approve-operator-system
spec:
  nodes_info: '[ {"node": "ocp4-ocsnode02.example.com", "ip": "100.240.64.1", "label": "node-role.kubernetes.io/storage=, foo=bar"} ]'
```
