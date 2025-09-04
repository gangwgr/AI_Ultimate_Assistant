#!/bin/bash
#
# NAME
#    must-gather analysis for cluster health
#
# Description
#    This script analyzes a must-gather to verify cluster health, deployment type, etc.

BOLD=$(tput bold)
REGULAR=$(tput sgr0)
RED='\033[0;31m'
PURPLE='\033[0;35m'
MUSTGATHER=${1}
ARGS=${#}

function validate {
	if [ ${ARGS} -eq 0 ]; then
		echo "No must-gather supplied!"
		echo "USAGE: $0 <must-gather-directory>"
		exit 1
	elif [ ${ARGS} -gt 1 ]; then
		echo "Only must-gather should be provided!"
		echo "USAGE: $0 <must-gather-directory>"
		exit 1
	elif ! [ -x "$(command -v omg)" ]; then
		echo 'Error: omg command not found!' >&2
		echo 'Visit "https://pypi.org/project/o-must-gather" for install instructions.'
		exit 1
	elif ! [ -x "$(command -v jq)" ]; then
		echo 'Error: jq command not found!' >&2
		echo 'Visit "https://stedolan.github.io/jq/download" for install instructions.'
		exit 1
	elif ! [ -x "$(command -v column)" ]; then
		echo 'Error: column command not found!' >&2
		echo '"util-linux" package needs to be installed for Red Hat based Linux Distributions.'
		echo '"bsdmainutils" package needs to be installed for Debian based Linux Distributions.'
		exit 1
	else
		rm -f ~/.omgconfig && omg use ${MUSTGATHER}
		echo -e "\n"
	fi
}

### Cluster infrastructure
function infrastructure {
	Infrastructures=$MUSTGATHER/*/cluster-scoped-resources/config.openshift.io/infrastructures.yaml
	if [ -f $Infrastructures ]; then
		cat $Infrastructures | gsed -n '/uid/,/kind/{ //!p }'
	else
		echo -e "\n***${BOLD}infrastructures.yaml not found***\n${REGULAR}"
	fi
}

### ETCD endpoint health
function etcdEndpointHealth {
	ETCDEndpointHealth=$MUSTGATHER/*/etcd_info/endpoint_health.json
	if [ -f $ETCDEndpointHealth ]; then
		cat $ETCDEndpointHealth | jq -r '(["ENDPOINT","HEALTH","TOOK"] | (.,map(length*"-"))), (.[] | [.endpoint, .health, .took]) | @tsv' | column -t
	else
		echo -e "\n***${BOLD}endpoint_health.json not found***\n${REGULAR}"
	fi
}

### ETCD endpoint status
function etcdEndpointStatus {
	ETCDEndpointStatus=$MUSTGATHER/*/etcd_info/endpoint_status.json
	if [ -f $ETCDEndpointStatus ]; then
		cat $ETCDEndpointStatus | jq -r '(["ENDPOINT","MEMBER-ID","LEADER-ID","VERSION","DB-SIZE-IN-BYTES", "RAFT-TERM", "RAFT-INDEX", "RAFT-APPLIED-INDEX"] | (.,map(length*"-"))), (.[] | [.Endpoint, .Status.header.member_id, .Status.leader, .Status.version, .Status.dbSize, .Status.header.raft_term, .Status.raftIndex, .Status.raftAppliedIndex]) | @tsv' | column -t
	else
		echo -e "\n***${BOLD}endpoint_status.json not found***\n${REGULAR}"
	fi
}

### ETCD members list
function etcdMemberList {
	ETCDMemberList=$MUSTGATHER/*/etcd_info/member_list.json
	if [ -f $ETCDMemberList ]; then
		cat $ETCDMemberList | jq -r '(["NAME","PEER-ADDRS","CLIENT-ADDRS"] | (.,map(length*"-"))), (.members[] | [.name, .peerURLs[], .clientURLs[]]) | @tsv' | column -t
	else
		echo -e "\n***${BOLD}member_list.json not found***\n${REGULAR}"
	fi
}

### Clusterversion
function clusterversion {
	ClusterVersion=$MUSTGATHER/*/cluster-scoped-resources/config.openshift.io/clusterversions.yaml
	omg get clusterversion
	if [ -f $ClusterVersion ]; then
		echo -e "\n\n${PURPLE}***ClusterVersion spec***\n${REGULAR}"
		cat $ClusterVersion | gsed -n '/uid/,/version/{ /uid/!p }'
		echo -e "\n\n${PURPLE}***ClusterVersion conditions***\n${REGULAR}"
		cat $ClusterVersion | gsed -n '/lastTransitionTime/,/desired/{ /desired/!p }'
		echo -e "\n\n${PURPLE}***ClusterVersion history***\n${REGULAR}"
		cat $ClusterVersion | gsed -n '/completionTime/,/observedGeneration/{ /observedGeneration/!p }'
	else
		echo -e "\n***${BOLD}clusterversions.yaml not found***\n${REGULAR}"
	fi
}

### Install Config
function InstallConfigYAML {
	InstallConfig=$MUSTGATHER/*/namespaces/kube-system/core/configmaps.yaml
	if [ -f $InstallConfig ]; then
		cat $InstallConfig | gsed -n '/install-config/{p; :loop n; p; /kind/q; b loop}' | grep -v kind
	else
		echo -e "\n***${BOLD}install-config.yaml not found***\n${REGULAR}"
	fi
}

### Cluster-wide proxy
function ClusterWideProxy {
	Proxy=$MUSTGATHER/*/cluster-scoped-resources/config.openshift.io/proxies/cluster.yaml
	if [ -f $Proxy ]; then
		cat $Proxy | gsed -n '/uid/,/kind/{ //!p }'
	else
		echo -e "\n***${BOLD}cluster-wide proxy details not found***\n${REGULAR}"
	fi
}

### Cluster Operators list
function ClusterOperator {
	omg get co
}

### Cluster Operators YAMLs
#function ClusterOperatorsYAML {
#	OpsDir=$MUSTGATHER/*/cluster-scoped-resources/config.openshift.io/clusteroperators/
#	if [ -d $OpsDir ]; then
#		echo -e "\n${PURPLE}*** ClusterOperators YAMLs ***\n${REGULAR}"
#		ls -1 $OpsDir/*.yaml
#	else
#		echo -e "\n***${BOLD}ClusterOperators YAML directory not found***\n${REGULAR}"
#	fi
#}

### Cluster Operators detailed YAML
function ClusterOperatorsYAMLDetail {
	coList=$(omg get co | grep -iv NAME | awk '{print $1}')
	if [ ! -z "$coList" ]; then
		echo -e "\n${PURPLE}*** CO detailed YAMLs ***\n${REGULAR}"
		for coName in $coList; do
			echo -e "\n${BOLD}CO: $coName${REGULAR}\n"
			omg get co/$coName -o yaml
		done
	else
		echo -e "\n***${BOLD}CO not found***\n${REGULAR}"
	fi
}

### Nodes status
function nodes {
	omg get nodes -o wide
}

### Nodes detailed YAML
function NodesYAMLDetail {
	NodesList=$(omg get nodes | grep -iv NAME | awk '{print $1}')
	if [ ! -z "$NodesList" ]; then
		echo -e "\n${PURPLE}*** Nodes detailed YAMLs ***\n${REGULAR}"
		for nodeName in $NodesList; do
			echo -e "\n${BOLD}Node: $nodeName${REGULAR}\n"
			omg get nodes/$nodeName -o json | jq '.status.conditions'
		done
	else
		echo -e "\n***${BOLD}Nodes not found***\n${REGULAR}"
	fi
}



### MCP, Machine, Machineset, Pods
function mcp { omg get mcp; }
function machine { omg get machine -n openshift-machine-api; }
function machineset { omg get machineset -n openshift-machine-api; }
function pods { omg get pod -o wide -A | grep -Ev 'Running|Succeeded'; }
function podRestart { omg get pod -A | awk '$5>10'; }

### Kube Apiserver logs
function KubeApiserver {
	MasterNodes=$(cat $MUSTGATHER/*/cluster-scoped-resources/core/nodes/* | grep -i "node-role.kubernetes.io/master: """ -A200 | awk '/resourceVersion/{print a}{a=$0}' | awk '{ print "kube-apiserver-" $2 }' | tr '\n' ' ')
	for i in $(echo $MasterNodes); do
		if [ -f $MUSTGATHER/*/namespaces/openshift-kube-apiserver/pods/$i/kube-apiserver/kube-apiserver/logs/current.log ]; then
			echo -e "\n${PURPLE}***$i***\n${REGULAR}"
			cat $MUSTGATHER/*/namespaces/openshift-kube-apiserver/pods/$i/kube-apiserver/kube-apiserver/logs/current.log |grep -iE "panic|fatal|err|warn|fail"
		else
			echo -e "\n***${BOLD}$i pod logs not found***\n${REGULAR}"
		fi
	done
}

### Apiserver logs
### Apiserver logs
function Apiserver {
	APISERVER_PODS=$(ls $MUSTGATHER/*/namespaces/openshift-apiserver/pods/)
	for pod in $APISERVER_PODS; do
		LOGFILE="$MUSTGATHER/*/namespaces/openshift-apiserver/pods/$pod/openshift-apiserver/openshift-apiserver/logs/current.log"
		if [ -f $LOGFILE ]; then
			echo -e "\n${PURPLE}*** $pod ***\n${REGULAR}"
			cat $LOGFILE | grep -iE "panic|fatal|err|warn|fail"
		else
			echo -e "\n***${BOLD}$pod pod logs not found***\n${REGULAR}"
		fi
	done
}


function ETCDPodLogs {
	MasterNodes=$(cat $MUSTGATHER/*/cluster-scoped-resources/core/nodes/* | grep -i "node-role.kubernetes.io/master: """ -A200 | awk '/resourceVersion/{print a}{a=$0}' | awk '{ print "etcd-" $2 }' | tr '\n' ' ')
	for i in $(echo $MasterNodes); do
		if [ -f $MUSTGATHER/*/namespaces/openshift-etcd/pods/$i/etcd/etcd/logs/current.log ]; then
			echo -e "\n${PURPLE}***$i***\n${REGULAR}"
			cat $MUSTGATHER/*/namespaces/openshift-etcd/pods/$i/etcd/etcd/logs/current.log | grep -iE "panic|fatal|err|warn|fail" 
		else
			echo -e "\n***${BOLD}$i pod logs not found***\n${REGULAR}"
		fi
	done
}

function KubeControllerManager {
	MasterNodes=$(cat $MUSTGATHER/*/cluster-scoped-resources/core/nodes/* | grep -i "node-role.kubernetes.io/master: """ -A200 | awk '/resourceVersion/{print a}{a=$0}' | awk '{ print "kube-controller-manager-" $2 }' | tr '\n' ' ')
	for i in $(echo $MasterNodes); do
		if [ -f $MUSTGATHER/*/namespaces/openshift-kube-controller-manager/pods/$i/kube-controller-manager/kube-controller-manager/logs/current.log ]; then
			echo -e "\n${PURPLE}***$i***\n${REGULAR}"
			cat $MUSTGATHER/*/namespaces/openshift-kube-controller-manager/pods/$i/kube-controller-manager/kube-controller-manager/logs/current.log | grep -iE "panic|fatal|err|warn|fail" 
		else
			echo -e "\n***${BOLD}$i pod logs not found***\n${REGULAR}"
		fi
	done
}

### Check if each CSR is approved
function CheckAllCSRsApproval() {
  CSRs=$(omg get csr | awk 'NR>1 {print $1}')
  if [ -z "$CSRs" ]; then
    echo "No CSRs found."
    return
  fi

  for csr in $CSRs; do
    approved=$(omg get csr $csr -o json | jq -e '.status.conditions[] | select(.type == "Approved" and .status == "True")' >/dev/null && echo "Approved" || echo "Not Approved")
    echo "$csr : $approved"
  done
}


function title {
	echo -e "\n${BOLD}${RED}----------${1}----------\n${REGULAR}"
}

function main {
	validate

	title "Cluster Infrastructure"
	infrastructure

	title "ETCD Endpoint Health"
	etcdEndpointHealth

	title "ETCD Endpoint Status"
	etcdEndpointStatus

	title "ETCD Member List"
	etcdMemberList

	title "Clusterversion"
	clusterversion

	title "Install Config"
	InstallConfigYAML

	title "Cluster-Wide Proxy"
	ClusterWideProxy

	title "Cluster Operators"
	ClusterOperator

	title "ClusterOperators YAMLs"
	ClusterOperatorsYAML

	title "ClusterOperators YAML detail"
	ClusterOperatorsYAMLDetail

	title "Nodes"
	nodes

	title "Nodes YAMLs"
	NodesYAMLDetail

	title "CSR details"
	CheckAllCSRsApproval

	title "MCP"
	mcp

	title "Machines"
	machine

	title "Machinesets"
	machineset

	title "Failing Pods"
	pods

	title "Pods Restart > 10"
	podRestart

	title "Kube-Apiserver Pod Logs"
	KubeApiserver

	title "Apiserver Pod Logs"
	Apiserver

	title "ETCD Pod Logs"
	ETCDPodLogs

	title "Kube Controller Manager Logs"
	KubeControllerManager
}

main
