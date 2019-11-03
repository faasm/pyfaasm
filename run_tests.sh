#!/bin/bash

# Make sure python can find Faasm libraries
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

export PYTHON_LOCAL_CHAINING=1

# Switch on Faasm debug logging
export LOG_LEVEL=debug

python -m unittest

