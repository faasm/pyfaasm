#!/bin/bash

# Make sure python can find Faasm libraries
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib:$FAASM_THIRD_PARTY_LIBS

export PYTHON_LOCAL_CHAINING=1

# Faasm logging
export LOG_LEVEL=info

python3 -m unittest

