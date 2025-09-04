## Kube Apiserver logs
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