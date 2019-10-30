# PyFaasm

Python bindings for Faasm host interface.

## Installing native Faasm tools

To test integration with Faasm via the emulator, in the Faasm project root:

```
source workon.sh
inv install-native-tools
```

## Build and test

```
# Venv
python3 -m venv venv
source venv/bin/activate

# Install locally
pip install -e .

# Run tester
./run_tester.sh
```

## Publishing

When publishing an update you'll need to bump the version in `setup.py`.

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
pip install -U pyfaasm
inv set-up-python-package pyfaasm
```
