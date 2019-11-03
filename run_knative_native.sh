#!/bin/bash

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
export LOG_LEVEL=debug

python pyfaasm/knative_native.py

