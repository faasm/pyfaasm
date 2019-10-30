#!/bin/bash

# Make sure python can find Faasm libraries
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/faasm/install/lib

# Switch on Faasm debug logging
export LOG_LEVEL=debug

python -m unittest

