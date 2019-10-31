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

# Install deps
pip install -r test_requirements.txt

# Install this module locally
pip install -e .

# Run tests
./run_tests.sh
```

## Publishing

When publishing an update you'll need to bump the version in `setup.py`.

```
./release.sh
```

## Updating in Pyodide and Faasm

Run the following in Faasm:

```
cd third-party/pyodide
source workon.sh
cd packages
rm -rf pyfaasm/build
../bin/pyodide mkpkg pyfaasm
../bin/pyodide buildpkg --package_abi=0 pyfaasm/meta.yaml
```

Make sure the output of the last function references the latest version.

Finally, in a new shell at the root of the Faasm project you need to run:
 
```
source workon.sh
pip install -U pyfaasm
inv set-up-python-package pyfaasm
```
