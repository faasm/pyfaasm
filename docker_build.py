from subprocess import run
from os import environ
from copy import copy


def main():
    shell_env = copy(environ)
    shell_env.update({"DOCKER_BUILDKIT": "1"})

    run(
        "docker build -t faasm/pyfaasm .",
        shell=True,
        check=True,
        env=shell_env,
    )


if __name__ == "__main__":
    main()
