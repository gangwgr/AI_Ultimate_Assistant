#!/bin/bash

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
    echo 'Error: omg command not found!'
    exit 1
  elif ! [ -x "$(command -v jq)" ]; then
    echo 'Error: jq command not found!'
    exit 1
  elif ! [ -x "$(command -v column)" ]; then
    echo 'Error: column command not found!'
    exit 1
  else
    rm -f ~/.omgconfig && omg use ${MUSTGATHER}
    echo -e "\n"
  fi
}
