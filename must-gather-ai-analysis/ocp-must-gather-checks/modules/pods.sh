#!/bin/bash

# Assume BOLD and REGULAR are defined elsewhere, e.g., in helpers.sh
# BOLD='\033[1m'
# REGULAR='\033[0m'

function pods {
  echo -e "\n${BOLD}Pods Logs:${REGULAR}"
  omg get pod -A | while read ns name rest; do
    [[ "$ns" == "NAMESPACE" ]] && continue

    echo -e "\nPod: $name (Namespace: $ns)"

    # Get pod phase and container states
    echo -e "${BOLD} Pod Status Details:${REGULAR}"
    omg get pod/$name -n "$ns" -o json | jq '.status.phase, .status.containerStatuses[].state'

    echo -e "${BOLD}  Pod Logs:${REGULAR}"
    # Get container names from the pod's spec
    # Use jq -r to get raw strings, then loop through them
    CONTAINER_NAMES=$(omg get pod/$name -n "$ns" -o json | jq -r '.spec.containers[].name')

    echo -e "    --- Logs for pods ${name} in namesapce $ns ---"
    if [[ -z "$CONTAINER_NAMES" ]]; then
        omg logs pod/"$name" -n "$ns"
    else
        # Loop through each container name
        for container_name in $CONTAINER_NAMES; do
            echo -e "    --- Logs for container: ${container_name} ---"
            # Use -c/--container to specify the container name
            # Add --tail=100 or a similar limit to avoid excessively long logs
            # Add --since=10m to get recent logs, or --previous for previous container logs
            # Redirect errors to /dev/null if you don't want to see "container not found" for init containers etc.
            omg logs pod/"$name" -n "$ns" -c "$container_name" |tail -10 2>/dev/null || \
            echo "      (Could not retrieve logs for container $container_name or no recent logs)"
        done
    fi
  done
}

# Example call (assuming this is in main.sh or sourced)
# pods
