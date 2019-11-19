from os import environ
from os.path import join

try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

# Detect whether this is a wasm build
if environ.get("WASM_CC"):
    is_wasm_build = True
else:
    is_wasm_build = False


def main():
    PKG_NAME = "pyfaasm"
    FAASM_LIBS = ["faasm", "emulator"]
    FAASM_INSTALL = "/usr/local"

    extension_kwargs = {
        "sources": ["pyfaasm/cfaasm.c"],
    }

    if not is_wasm_build:
        # Include native libraries in native build to allow emulation
        extension_kwargs.update({
            "libraries": FAASM_LIBS,
            "library_dirs": [join(FAASM_INSTALL, "lib")],
            "include_dirs": [join(FAASM_INSTALL, "include")],
        })

    setup(
        name=PKG_NAME,
        packages=[PKG_NAME],
        version="0.1.4",
        description="Python interface for Faasm",
        long_description="""## Faasm Python bindings\nSee main repo at https://github.com/lsds/Faasm.""",
        long_description_content_type="text/markdown",
        author="Simon S",
        author_email="foo@bar.com",
        url="https://github.com/lsds/Faasm",
        ext_modules=[Extension("pyfaasm.cfaasm", **extension_kwargs)]
    )


if __name__ == "__main__":
    main()
