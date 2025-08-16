#!/bin/bash

while true; do
  # Perform the request and capture the HTTP status code and response
  response=$(curl -s -i http://localhost:8000/items)
  status=$(echo "$response" | grep HTTP | awk '{print $2}')
  # Print status and response (single line)
  echo "Status: $status | $(echo "$response" | tr '\n' ' ' | sed 's/  */ /g')"
  # Exit if status is not 200
  if [ "$status" != "200" ]; then
    exit 0
  fi
  sleep 0.02
done
