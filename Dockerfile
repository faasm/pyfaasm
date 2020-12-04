FROM faasm/cpp-sysroot:0.0.13

RUN apt-get install -y \
    python3-dev \
    python3-pip

WORKDIR /code/pyfaasm
COPY . .
RUN pip3 install -r test_requirements.txt

RUN pip3 install -e .
