#!/bin/bash

function infrastructure {
  Infrastructures=$MUSTGATHER/*/cluster-scoped-resources/config.openshift.io/infrastructures.yaml
  if [ -f $Infrastructures ]; then
    cat $Infrastructures | gsed -n '/uid/,/kind/{ //!p }'
  else
    echo -e "\n***${BOLD}infrastructures.yaml not found***\n${REGULAR}"
  fi
}
