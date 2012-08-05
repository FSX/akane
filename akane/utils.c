#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "structmember.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "buffer.h"


// Append integer to buffer
#define BUFPUTI(output, n) {\
    int n_size = intlen(n);\
    char s[n_size];\
    itoa(n, s, n_size);\
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


// Convert integer (n) to a string (s).
// From: http://en.wikibooks.org/wiki/C_Programming/C_Reference/stdlib.h/itoa
// This is a modified version. Because the length is already provided by `intlen`
// the string doesn't have to be reversed and it can just start at the end postion
// and work to the beginning.
static void itoa(int n, char s[], int l)
{
    int sign;

    s[l--] = '\0';             // Add \0 at last position

    if ((sign = n) < 0) {      // Record sign
        n = -n;                // Make n positive
        s[0] = '-';            // Add - at position 0
    }

    do {                       // Generate digits in reverse order
        s[l--] = n % 10 + '0'; // Get next digit
    } while ((n /= 10) > 0);   // Delete it
}


static PyObject *
py_redis_request(PyObject *self, PyObject *args)
{
    PyObject *parts;
    if (!PyArg_ParseTuple(args, "O!", &PyTuple_Type, &parts))
        return NULL;

    int parts_length = PyTuple_GET_SIZE(parts);
    PyObject *part;
    int part_size;

    struct buf *ob;
    ob = bufnew(64);

    bufputc(ob, '*');
    BUFPUTI(ob, parts_length);
    BUFPUTSL(ob, "\r\n");

    int i; for (i = 0;i < parts_length;i++) {
        part = PyTuple_GET_ITEM(parts, i);
        int is_unicode = PyUnicode_Check(part);
        if (is_unicode) {
            Py_INCREF(part);
            part = PyUnicode_AsEncodedString(part, "utf-8", "strict");
        }
        part_size = (int) PyBytes_GET_SIZE(part);

        bufputc(ob, '$');
        BUFPUTI(ob, part_size);
        BUFPUTSL(ob, "\r\n");
        bufput(ob, PyBytes_AS_STRING(part), part_size);
        BUFPUTSL(ob, "\r\n");

        if (is_unicode) {
            Py_DECREF(part);
        }
    }

    PyObject *new_string = PyBytes_FromStringAndSize(ob->data, ob->size);
    Py_INCREF(new_string);
    bufrelease(ob);

    return new_string;
}


static PyMethodDef utils_methods[] = {
    {"redis_request", py_redis_request, METH_VARARGS, "Create a Redis request."},
    {NULL, NULL, 0, NULL} /* Sentinel */
};


PyMODINIT_FUNC
initutils(void)
{
    PyObject *module = Py_InitModule("utils", utils_methods);
}
