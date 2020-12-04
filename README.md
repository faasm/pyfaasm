# PyFaasm

Python bindings for [Faasm](https://github.com/lsds/Faasm) host interface.

## Developing

This library will eventually be compiled to WebAssembly, but to develop it you
will need to compile it locally against the Faasm native tools. 

To build the container and run the tests:

```bash
# Build the container
python3 docker_build.py

# Run the container
docker run -it -v $(pwd):/code/pyfaasm faasm/pyfaasm /bin/bash

# Run the tests (inside the container)
./run_tests.sh
```

If you make changes to the C-extensions you need to rerun:

```
pip3 install -e .
```

## Updating in Faasm

This repo is build as part of the 
[`faasm-cpython` repo](https://github.com/faasm/faasm-cpython). See the
instructions in there.
