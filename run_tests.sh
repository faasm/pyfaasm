#!/bin/bash

# Make sure python can find Faasm libraries
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

export PYTHON_LOCAL_CHAINING=1

# Faasm logging
export LOG_LEVEL=info

python -m unittest

