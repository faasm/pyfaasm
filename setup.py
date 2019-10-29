try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension


def main():
    setup(
        name="pyfaasm",
        packages=["pyfaasm"],
        version="0.0.5",
        description="Python interface for Faasm",
        author="Simon S",
        author_email="foo@bar.com",
        ext_modules=[
            Extension("_native", ["pyfaasm/native.c"])
        ]
    )


if __name__ == "__main__":
    main()
