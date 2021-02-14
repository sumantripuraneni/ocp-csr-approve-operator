# ocp-csr-approve-operator
An operator to approve OpenShift Certificate Signing Requests (CSR) generated during node addition to OpenShift Container Platform 4. 

This operator provides the following functionality:

*  Watch the CSR endpoint for CSR requests
*  Decide if the CSR should be approved or not
*  Approve and update CSR status
*  Optionally label the approved node 


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

In user provisioned installer (UPI) disconnected environment, `cluster-machine-approver` cannot be leveraged to approve CSR's. 
