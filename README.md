# PyFaasm

Python bindings for Faasm host interface.

## Build and test

```
# Venv
python3 -m venv venv
source venv/bin/activate

# Build and install
python setup.py build
python setup.py install

# Run tester
python tester.py
```

## Publishing

When publishing an update you'll need to bump the version.

```
# If not already installed
pip install twine

# Clear existing dist and build
rm -rf dist/ build/
python setup.py sdist

# Check
twine check dist/*

# Upload
twine upload dist/*
```

## Updating in Pyodide and Faasm

Run the following in Faasm:

```
cd third-party/pyodide
source workon.sh
bin/pyodide mkpkg pyfaasm
cd packages
rm -rf pyfaasm/build
../bin/pyodide buildpkg --package_abi=0 pyfaasm/meta.yaml
```
 
Finally, in a new shell at the root of the Faasm project you need to run:
 
```
source workon.sh
inv set-up-python-package pyfaasm
```
