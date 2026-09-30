#!/bin/bash
# Wrapper for mcp-image that sources credentials from ~/.hermes/.env
# Hermes doesn't resolve {env:VAR} templates in mcp_servers env blocks,
# and it filters the environment for security, so we source .env directly.
set -a
source ~/.hermes/.env
IMAGE_OUTPUT_DIR=/home/migbert/images
set +a
exec npx -y mcp-image "$@"
