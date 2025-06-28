#!/bin/bash
cd /home/kavia/workspace/code-generation/reactflaskauth-115030-4445c9c9/login_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

