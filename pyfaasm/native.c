#define PY_SSIZE_T_CLEAN
#include <Python.h>

// Some useful notes
// - Tutorial - https://realpython.com/build-python-c-extension-module/
// - Official tutorial - https://docs.python.org/3/extending/extending.html
// - Numpy example - https://dfm.io/posts/python-c-extensions/
// - Args and return values - https://docs.python.org/3/c-api/arg.html
// - Bytes objects - https://docs.python.org/3/c-api/bytes.html

// ------ Faasm core functions ------
__attribute__((weak))
long __faasm_read_input(unsigned char *buffer, long bufferLen);

__attribute__((weak))
void __faasm_write_output(const unsigned char *output, long outputLen);

// Tester function
static PyObject *hello_faasm(PyObject *self) {
    return Py_BuildValue("s", "Hello, Faasm extension!");
}

// Check input
static PyObject *check_input(PyObject *self) {
    unsigned char dummyInput[5];
    dummyInput[0] = '0';
    dummyInput[1] = '1';
    dummyInput[2] = '2';
    dummyInput[3] = '3';
    dummyInput[4] = '4';

    return PyBytes_FromStringAndSize((char*) dummyInput, 5);
}

// Get input to the function
static PyObject *faasm_get_input(PyObject *self) {
    unsigned char emptyBuf[1];
    unsigned long inputSize = __faasm_read_input(emptyBuf, 0);

    unsigned char *inputBuf = (unsigned char *) malloc(inputSize);
    __faasm_read_input(inputBuf, inputSize);

    return PyBytes_FromStringAndSize((char*) inputBuf, inputSize);
}

// Set output
static PyObject *faasm_set_output(PyObject *self, PyObject *args) {
    // Note, the type of this variable will be PyBytesObject, but the
    // Python C API just deals in generic PyObject pointers
    PyObject* outputData = NULL;

    if(!PyArg_ParseTuple(args, "S", &outputData)) {
        return NULL;
    }

    __faasm_write_output(
        (unsigned char*) PyBytes_AsString(outputData),
        PyBytes_Size(outputData)
    );

    Py_RETURN_NONE;
}

static PyMethodDef _native_methods[] = {
        {"hello_faasm", (PyCFunction) hello_faasm, METH_NOARGS, NULL},
        {"check_input", (PyCFunction) check_input, METH_NOARGS, NULL},
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