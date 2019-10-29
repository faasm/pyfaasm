#define PY_SSIZE_T_CLEAN
#include <Python.h>

// Some useful notes
// - Tutorial - https://realpython.com/build-python-c-extension-module/
// - Official tutorial - https://docs.python.org/3/extending/extending.html
// - Numpy example - https://dfm.io/posts/python-c-extensions/

// ------ Faasm core functions ------
__attribute__((weak))
long __faasm_read_input(unsigned char *buffer, long bufferLen);

__attribute__((weak))
void __faasm_write_output(const unsigned char *output, long outputLen);

// Tester function
static PyObject *hello_faasm(PyObject *self) {
    return Py_BuildValue("s", "Hello, Faasm extension!");
}

// Get input to the function
static PyObject *faasm_get_input(PyObject *self) {
    unsigned char emptyBuf[1];
    long inputSize = __faasm_read_input(emptyBuf, 0);

    unsigned char *inputBuf = (unsigned char *) malloc(inputSize);
    __faasm_read_input(inputBuf, inputSize);

    // See https://docs.python.org/3/c-api/arg.html#building-values on building values from C
    return Py_BuildValue("s#", (char *) inputBuf, inputSize);
}

// Set output
static PyObject *faasm_set_output(PyObject *self, PyObject *args) {
    Py_buffer* outputData = NULL;

    // See https://docs.python.org/3/c-api/arg.html#parsing-arguments on parsing args from python to C
    if(!PyArg_ParseTuple(args, "s#", &outputData)) {
        return NULL;
    }

    __faasm_write_output((unsigned char*) outputData->buf, outputData->len);

    Py_RETURN_NONE;
}

static PyMethodDef _native_methods[] = {
        {"hello_faasm", (PyCFunction) hello_faasm, METH_NOARGS, NULL},
        {"faasm_get_input", (PyCFunction) faasm_get_input, METH_NOARGS, NULL},
        {"faasm_set_output", (PyCFunction) faasm_set_output, METH_VARARGS, NULL},
        {NULL, NULL, 0, NULL}
};

static struct PyModuleDef _nativemodule = {
        PyModuleDef_HEAD_INIT,
        "_native",
        "C bindings for Faasm functions",
        -1,
        _native_methods
};

PyMODINIT_FUNC
PyInit__native(void) {
    return PyModule_Create(&_nativemodule);
}