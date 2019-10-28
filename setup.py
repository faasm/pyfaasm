try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension


def main():
    setup(
        name="pyfaasm",
        version="0.0.4",
        description="Python interface for Faasm",
        author="Simon S",
        author_email="foo@bar.com",
        ext_modules=[
            Extension("pyfaasm", ["pyfaasm/pyfaasm.c"])
        ]
    )


if __name__ == "__main__":
    main()
