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
rm -rf dist/
python setup.py sdist

# Check
twine check dist/*

# Upload
twine upload dist/*
```

## Updating in Pyodide and Faasm

You will need to update the file in Pyodide at `packages/pyfaasm/meta.yml` with the latest SHA and
file link from https://pypi.org/project/pyfaasm/.

You can then run:

```
cd third-party/pyodide
source workon.sh
cd packages
rm -rf pyfaasm/build
../bin/pyodide buildpkg --package_abi=0 pyfaasm/meta.yaml
```

Finally you need to edit `tasks/python.py` in Faasm and can run:

```
inv set-up-python-package pyfaasm
```