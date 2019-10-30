from os.path import join

try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension


def main():
    PKG_NAME = "pyfaasm"
    FAASM_LIBS = ["faasm", "emulator"]
    FAASM_INSTALL = "/usr/local/faasm/install/"

    setup(
        name=PKG_NAME,
        packages=[PKG_NAME],
        version="0.0.11",
        description="Python interface for Faasm",
        long_description="""## Faasm Python bindings\nSee main repo at https://github.com/lsds/Faasm.""",
        long_description_content_type="text/markdown",
        author="Simon S",
        author_email="foo@bar.com",
        url="https://github.com/lsds/Faasm",
        ext_modules=[
            Extension(
                "pyfaasm.cfaasm",
                sources=["pyfaasm/cfaasm.c"],
                libraries=FAASM_LIBS,
                library_dirs=[join(FAASM_INSTALL, "lib")],
                include_dirs=[join(FAASM_INSTALL, "include")],
            )
        ]
    )


if __name__ == "__main__":
    main()
