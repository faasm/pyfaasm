#!/bin/bash

# Make sure python can find libraries
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/faasm/install/lib

export LOG_LEVEL=debug

python tester.py

