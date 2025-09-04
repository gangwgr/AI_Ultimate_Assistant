#!/bin/bash

function nodes {
  omg get nodes -o wide
}

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
