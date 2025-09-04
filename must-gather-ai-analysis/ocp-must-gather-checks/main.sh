#!/bin/bash

MUSTGATHER=$1
ARGS=$#

source helpers.sh
source validate.sh

# Load all modules
source modules/infra.sh
source modules/etcd.sh
source modules/clusterversion.sh
source modules/nodes.sh
source modules/pods.sh
source modules/csr.sh
source modules/logs.sh
source modules/co.sh

validate

title "Cluster Infrastructure"
infrastructure

title "ETCD Endpoint Health"
etcdEndpointHealth

title "ETCD Endpoint Status"
etcdEndpointStatus

title "ETCD Member List"
etcdMemberList

title "Cluster Version"
clusterversion

title "Nodes"
nodes

title "Nodes YAML Details"
NodesYAMLDetail

title "CSR Approval Check"
CheckAllCSRsApproval

title "Pods Status"
pods

title "Kube-Apiserver Pod Logs"
KubeApiserver

title "Apiserver Pod Logs"
Apiserver

title "ETCD Pod Logs"
ETCDPodLogs

title "Kube Controller Manager Logs"
KubeControllerManager

title "ClusterOperators YAML detail"
ClusterOperatorsYAMLDetail