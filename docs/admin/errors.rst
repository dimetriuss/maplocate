Errors
======

Response structure
~~~~~~~~~~~~~~~~~~

Error responses looks like following:

.. code-block:: http

   HTTP/1.1 400 Bad Request
   Content-Type: application/json; charset=utf-8
   Content-Length: ...

   {"error_code": 400,
    "error_subcode": 1,
    "error_reason": "Invalid JSON body",
    "error": {
       "fields": {
           "field_name": "Field error description"
       }
    }
   }

Fields description:

+-----------------------+---------------+-----------------------------------+
| **Field**             | Type          | Description                       |
+=======================+===============+===================================+
| **error_code**        | integer       | Duplicates HTTP status code       |
+-----------------------+---------------+-----------------------------------+
| **error_subcode**     | integer       | Error sub-code.                   |
+-----------------------+---------------+-----------------------------------+
| **error_reason**      | string        | Generic description of error      |
|                       |               | (eg: fields validation).          |
+-----------------------+---------------+-----------------------------------+
| **error**             | dict          | Dictionary holding more specific  |
|                       |               | error description/details.        |
+-----------------------+---------------+-----------------------------------+

Other fields in ``error`` dict are optional and depends on error type (code/sub-code)


--------

Error codes
~~~~~~~~~~~

.. include:: _errors.rst
