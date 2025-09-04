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