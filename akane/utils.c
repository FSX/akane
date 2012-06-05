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


typedef struct {
    PyObject_HEAD
    struct buf *ib; // Unused
    PyObject *data;
    int multi_bulk_parts;
    int read_next; // -1 = don't read; 0 = read next chunk; >0 = read N bytes
} utils_ReplyParserObject;


static void
utils_ReplyParser_dealloc(utils_ReplyParserObject* self)
{
    Py_DECREF(Py_None);
    self->ob_type->tp_free((PyObject*) self);
}


static PyObject *
utils_ReplyParser_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    utils_ReplyParserObject *self = (utils_ReplyParserObject *) type->tp_alloc(type, 0);
    if (!self) {
        return NULL;
    }

    return (PyObject *) self;
}


static int
utils_ReplyParser_init(utils_ReplyParserObject *self, PyObject *args, PyObject *kwds)
{
    self->data = Py_None;
    Py_INCREF(Py_None);

    self->multi_bulk_parts = 0;
    self->read_next = -1;
    return 0;
}


static PyObject *
utils_ReplyParser_feed(utils_ReplyParserObject* self, PyObject *args)
{
    unsigned char *text;
    size_t text_size;
    if (!PyArg_ParseTuple(args, "s#", &text, &text_size))
        return NULL;

    char type = *text++; // Pop type character
    text_size -= 3; // Set correct text size
    text[text_size] = '\0'; // Chop off \r\n
    

    switch (type) {
        case '+':
            self->data = PyString_FromStringAndSize(text, text_size);
            self->read_next = -1;
            break;
        case '-':
            break;
        case ':':
            self->data = PyInt_FromString(text, NULL, 10); 
            self->read_next = -1;
            break;
        case '$':
            break;
        case '*':
            break;
        default:
            self->read_next = -1;
    }
    
    return PyInt_FromLong(self->read_next);
}


static PyObject *
utils_ReplyParser_gets(utils_ReplyParserObject* self)
{
    return self->data;
}


static PyMemberDef utils_ReplyParser_members[] = {
    {NULL}  /* Sentinel */
};


static PyMethodDef utils_ReplyParser_methods[] = {
    {"feed", (PyCFunction) utils_ReplyParser_feed, METH_VARARGS,
        "Feed the reply parser data."},
    {"gets", (PyCFunction) utils_ReplyParser_gets, METH_NOARGS,
        "Get the data from the buffer."},
    {NULL}  /* Sentinel */
};


static PyMethodDef utils_methods[] = {
    {"redis_request", py_redis_request, METH_VARARGS, "Create a Redis request."},
    {NULL, NULL, 0, NULL} /* Sentinel */
};


static PyTypeObject utils_ReplyParserType = {
    PyObject_HEAD_INIT(&PyType_Type)
    0, /*ob_size*/
    "utils.ReplyParser", /*tp_name*/
    sizeof(utils_ReplyParserObject), /*tp_basicsize*/
    0, /*tp_itemsize*/
    (destructor) utils_ReplyParser_dealloc, /*tp_dealloc*/
    0, /*tp_print*/
    0, /*tp_getattr*/
    0, /*tp_setattr*/
    0, /*tp_compare*/
    0, /*tp_repr*/
    0, /*tp_as_number*/
    0, /*tp_as_sequence*/
    0, /*tp_as_mapping*/
    0, /*tp_hash */
    0, /*tp_call*/
    0, /*tp_str*/
    0, /*tp_getattro*/
    0, /*tp_setattro*/
    0, /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT, /*tp_flags*/
    "Redis reply parser.", /* tp_doc */
    0, /* tp_traverse */
    0, /* tp_clear */
    0, /* tp_richcompare */
    0, /* tp_weaklistoffset */
    0, /* tp_iter */
    0, /* tp_iternext */
    utils_ReplyParser_methods, /* tp_methods */
    utils_ReplyParser_members, /* tp_members */
    0, /* tp_getset */
    0, /* tp_base */
    0, /* tp_dict */
    0, /* tp_descr_get */
    0, /* tp_descr_set */
    0, /* tp_dictoffset */
    (initproc) utils_ReplyParser_init, /* tp_init */
    0, /* tp_alloc */
    utils_ReplyParser_new, /* tp_new */
};


PyMODINIT_FUNC
initutils(void)
{
    utils_ReplyParserType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&utils_ReplyParserType) < 0)
        return;

    PyObject *module = Py_InitModule("utils", utils_methods);

    Py_INCREF(&utils_ReplyParserType);
    PyModule_AddObject(module, "ReplyParser", (PyObject *) &utils_ReplyParserType);
}
