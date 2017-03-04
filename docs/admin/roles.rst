.. highlight:: http

Roles API
=========

.. _role details:

**Data structure**

+----------------------+-----------------+--------------------------------------+
| **Field**            | Type            | Description                          |
+======================+=================+======================================+
| **id**               | integer         | Role ID                              |
+----------------------+-----------------+--------------------------------------+
| **role_name**        | string          | Role title                           |
+----------------------+-----------------+--------------------------------------+
| **description**      | string          | Role description. **Optional**       |
+----------------------+-----------------+--------------------------------------+
| **permissions**      | list of strings | Permissions list                     |
+----------------------+-----------------+--------------------------------------+


**Permission JSON**

+----------------------+-------------+---------------------------------------+
| **Field**            | Type        | Description                           |
+======================+=============+=======================================+
| **id**               | string      | Permission identificator              |
+----------------------+-------------+---------------------------------------+

.. contents:: Methods definition
   :local:
..

+--------+----------------------+-------+-------------------------------------+----------------------+
| Request                       | Token | Description                         | Permissions          |
+========+======================+=======+=====================================+======================+
| POST   | |role-create|_       | \+    | Create new role                     | roles_edit           |
+--------+----------------------+-------+-------------------------------------+----------------------+
| GET    | |role-details|_      | \+    | View role                           | roles_view           |
+--------+----------------------+-------+-------------------------------------+----------------------+
| PATCH  | |role-update|_       | \+    | Update existing role                | roles_edit           |
+--------+----------------------+-------+-------------------------------------+----------------------+
| DELETE | |role-delete|_       | \+    | Delete existing role                | roles_edit           |
+--------+----------------------+-------+-------------------------------------+----------------------+
| GET    | |roles-list|_        | \+    | List all/filtered roles             | roles_view           |
+--------+----------------------+-------+-------------------------------------+----------------------+
| GET    | |permissions-list|_  | \+    | List possible permissions           |                      |
+--------+----------------------+-------+-------------------------------------+----------------------+


----

.. _role-create:

Role create
~~~~~~~~~~~

.. |role-create| replace:: /admin/roles/


Create new role.

**Request**::

   POST /admin/roles/ HTTP/1.1
   Authorization: admin_access_token

.. code-block:: python

   {"role_name": "Some role name",
    "permissions": [
      # list of permission ids
    ]
   }

**Response body**:

.. code-block:: python

   {"id": 123,
    "role_name": "Some name 1",
    "permissions": [
      # list of permission ids
    ]
   }

----

.. _role-details:

Show role details
~~~~~~~~~~~~~~~~~

.. |role-details| replace:: /admin/roles/**{role_id}**

**Request**::

   GET /admin/roles/{role_id} HTTP/1.1
   Authorization: admin_access_token

View role details.

**Response body**:

Same as `Role create <role create_>`_

----

.. _role-update:

Update role
~~~~~~~~~~~

.. |role-update| replace:: /admin/roles/**{role_id}**

**Request**::

   PATCH /admin/roles/{role_id} HTTP/1.1
   Authorization: admin_access_token

.. code-block:: python

   {"role_name": "New role name",
    "permissions": [
      # list of permission ids
    ]
   }

**Response body**:

Same as `Role create <role create_>`_

----

.. _role-delete:

Delete role
~~~~~~~~~~~

.. |role-delete| replace:: /admin/roles/


Delete role if role is assigned to no one.

**Request**::

   DELETE /admin/roles/**{role_id}** HTTP/1.1
   Authorization: admin_access_token

.. code-block:: python

   {{'status': 'deleted'}}

----

.. _roles-list:

List roles
~~~~~~~~~~

.. |roles-list| replace:: /admin/roles/

**Request**::

   GET /admin/roles/ HTTP/1.1
   Authorization: admin_access_token

Lists of possible roles.

**Response body**:

.. code-block:: python

   [{"id": 123,
     "role_name": "Some readable name",
     "description": "",
     "permissions": [
       'user_view', 'user_add'
     ]
   },
   # ...
   {"id": 321,
     "role_name": "Some readable name 2",
     "description": "",
     "permissions": [
       # list of permission ids 2
     ]
   }]

----

.. _permissions-list:

List permissions
~~~~~~~~~~~~~~~~

.. |permissions-list| replace:: /admin/permissions/

**Request**::

   GET /admin/permissions/ HTTP/1.1
   Authorization: admin_access_token

Lists permissions, that can be mapped to roles.

**Response body**:

.. code-block:: python

   [{"id": "permission-id-1",
     "group": "group name",
   },
   ...
   {"id": "permission-id-N",
    "group": "group name",
   }]

----

