Maplocate REST API Documentation
================================

**REST method definitions**

Possible contexts:
 * *Collection* --- A logicaly similar group of objects. For example list of users (``/admin/users/``), list of roles (``/admin/roles/``), etc.
 * *Object*     --- A single object inside a collection. For example user object (``/admin/users/1``), role object (``/admin/roles/1``), etc.


+------------+------------+----------------------------------------+
| Method     | Context    | Description                            |
+============+============+========================================+
| **GET**    | Collection | Returns all (or filtered) objects from |
|            |            | collection.                            |
+------------+------------+----------------------------------------+
| **GET**    | Object     | Returns single object details.         |
+------------+------------+----------------------------------------+
| **POST**   | Collection | Creates new single object or bulk of   |
|            |            | objects within collection.             |
+------------+------------+----------------------------------------+
| **PATCH**  | Collection | Update many objects within the         |
|            |            | collection. Implementation is          |
|            |            | optional.                              |
+------------+------------+----------------------------------------+
| **PATCH**  | Object     | Partially updates single object        |
|            |            | within collection.                     |
+------------+------------+----------------------------------------+
| **PUT**    | Object     | Replaces whole object                  |
|            |            | within collection.                     |
+------------+------------+----------------------------------------+
| **DELETE** | Object     | Deletes single object or               |
|            |            | bulk of objects withing collection.    |
+------------+------------+----------------------------------------+


RESTful API Reference
---------------------

.. toctree::
   :maxdepth: 2

   users
   roles

API Errors Reference
--------------------

.. toctree::
   :maxdepth: 2

   errors

API Permissions Reference
-------------------------

.. toctree::
   :maxdepth: 2

   permissions
