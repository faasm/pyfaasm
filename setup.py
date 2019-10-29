try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension


def main():
    PKG_NAME = "pyfaasm"

    setup(
        name=PKG_NAME,
        packages=[PKG_NAME],
        version="0.0.8",
        description="Python interface for Faasm",
        long_description="""## Faasm Python bindings\nSee main repo at https://github.com/lsds/Faasm.""",
        long_description_content_type="text/markdown",
        author="Simon S",
        author_email="foo@bar.com",
        url="https://github.com/lsds/Faasm",
        ext_modules=[
            Extension("pyfaasm.cfaasm", ["pyfaasm/cfaasm.c"])
        ]
    )


if __name__ == "__main__":
    main()
