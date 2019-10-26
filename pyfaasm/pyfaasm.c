#include <Python.h>

// Some useful notes: https://realpython.com/build-python-c-extension-module/

__attribute__((weak))
long __faasm_read_input(unsigned char *buffer, long bufferLen);

static PyObject *hello_faasm(PyObject *self) {
    return Py_BuildValue("s", "Hello, Faasm extension!");
}

static PyObject *faasm_get_input(PyObject *self) {
    unsigned char emptyBuf[1];
    long input_size = __faasm_read_input(emptyBuf, 0);

    unsigned char *inputBuf = (unsigned char *) malloc(input_size);
    __faasm_read_input(inputBuf, input_size);

    return Py_BuildValue("s", (char *) inputBuf);
}

static PyMethodDef pyfaasm_funcs[] = {
        {"hello_faasm", (PyCFunction) hello_faasm, METH_NOARGS, NULL},
        {"faasm_get_input", (PyCFunction) faasm_get_input, METH_NOARGS, NULL},
        {NULL}
};

static struct PyModuleDef pyfaasmmodule = {
        PyModuleDef_HEAD_INIT,
        "pyfaasm",
        "Python interface for Faasm",
        -1,
        pyfaasm_funcs
};

PyMODINIT_FUNC PyInit_pyfaasm(void) {
    return PyModule_Create(&pyfaasmmodule);
}