#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "buffer.h"


// Append integer to buffer
#define BUFPUTI(output, n) {\
    int n_size = intlen(n);\
    char s[n_size];\
    itoa(n, s);\
    bufput(output, s, n_size);\
}



// Calculate the number of bytes needed to represent an integer as string.
// From Hiredis (hiredis.c), BSD license.
static int intlen(int i) {
    int len = 0;
    if (i < 0) {
        len++;
        i = -i;
    }
    do {
        len++;
        i /= 10;
    } while(i);
    return len;
}


// Reverse string in place.
// From: http://en.wikibooks.org/wiki/C_Programming/C_Reference/stdlib.h/itoa
static void reverse(char s[])
{
    int i, j;
    char c;

    for (i = 0, j = strlen(s)-1; i<j; i++, j--) {
        c = s[i];
        s[i] = s[j];
        s[j] = c;
    }
}


// Convert integer (n) to a string (s).
// From: http://en.wikibooks.org/wiki/C_Programming/C_Reference/stdlib.h/itoa
static void itoa(int n, char s[])
{
    int i, sign;

    if ((sign = n) < 0)        // Record sign
        n = -n;                // Make n positive
    i = 0;
    do {                       // Generate digits in reverse order
        s[i++] = n % 10 + '0'; // Get next digit
    } while ((n /= 10) > 0);   // Delete it
    if (sign < 0)
        s[i++] = '-';
    s[i] = '\0';
    reverse(s);
}


static PyObject *
py_redis_cmd(PyObject *self, PyObject *args)
{
    PyObject * parts;
    if (!PyArg_ParseTuple(args, "O!", &PyTuple_Type, &parts))
        return NULL;

    int parts_length = PyTuple_GET_SIZE(parts);
    PyObject *part;
    int part_size;

    struct buf *ob;
    ob = bufnew(64);

    bufput(ob, "*", 1);
    BUFPUTI(ob, parts_length);
    bufput(ob, "\r\n", 2);

    int i; for (i = 0;i < parts_length;i++) {
        part = PyTuple_GET_ITEM(parts, i);
        if (PyUnicode_Check(part))
            part = PyUnicode_AsEncodedString(part, "utf-8", "strict");
        part_size = (int) PyBytes_GET_SIZE(part);

        bufput(ob, "$", 1);
        BUFPUTI(ob, part_size);
        bufput(ob, "\r\n", 2);
        bufput(ob, PyBytes_AS_STRING(part), part_size);
        bufput(ob, "\r\n", 2);
    }

    PyObject *new_string = PyBytes_FromStringAndSize(ob->data, ob->size);
    bufrelease(ob);

    return new_string;
}



static PyMethodDef utils_methods[] = {
    {"redis_cmd", py_redis_cmd, METH_VARARGS, "Create a Redis command."},
    {NULL, NULL, 0, NULL} /* Sentinel */
};


#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "utils",
    NULL,
    -1,
    utils_methods,
    NULL,
    NULL,
    NULL,
    NULL
};


PyObject *
PyInit_utils(void)
{
    PyObject *module = PyModule_Create(&moduledef);
    return module;
}
#else
PyMODINIT_FUNC
initutils(void)
{
    PyObject *module = Py_InitModule("utils", utils_methods);
}
#endif
