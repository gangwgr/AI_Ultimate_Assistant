#!/bin/bash

function CheckAllCSRsApproval {
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
