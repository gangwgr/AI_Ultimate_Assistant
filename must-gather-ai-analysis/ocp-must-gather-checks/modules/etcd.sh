#!/bin/bash

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