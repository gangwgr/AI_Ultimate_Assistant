#!/bin/bash

BOLD=$(tput bold)
REGULAR=$(tput sgr0)
RED='\033[0;31m'
PURPLE='\033[0;35m'

function title {
  echo -e "\n${BOLD}${RED}----------${1}----------\n${REGULAR}"
}
