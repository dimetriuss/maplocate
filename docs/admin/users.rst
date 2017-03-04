.. highlight:: http

User API
========

**Data structure**

+----------------------+-------------+---------------------------------------+
| **Field**            | Type        | Description                           |
+======================+=============+=======================================+
| **uid**              | integer     | User ID                               |
+----------------------+-------------+---------------------------------------+
| **login**            | string      | User's login                          |
+----------------------+-------------+---------------------------------------+
| **firstname**        | string      | User's first name. *May be blank*     |
+----------------------+-------------+---------------------------------------+
| **lastname**         | string      | User's last name. *May be blank*      |
+----------------------+-------------+---------------------------------------+
| **roles**            | list of str | User's roles                          |
+----------------------+-------------+---------------------------------------+
| **disabled**         | bool        | Status                                |
+----------------------+-------------+---------------------------------------+
| **is_superuser**     | bool        | Super user status                     |
+----------------------+-------------+---------------------------------------+

.. contents:: Methods definition
   :local:
..

+--------+----------------------+-------+-------------------------------------+---------------------------------+
| Request                       | Token | Description                         | Permissions                     |
+========+======================+=======+=====================================+=================================+
| POST   | |user-authorize|_    | --    | User authorization                  |                                 |
+--------+----------------------+-------+-------------------------------------+---------------------------------+
| POST   | |user-create|_       | \+    | Add new user                        | users_add                       |
+--------+----------------------+-------+-------------------------------------+---------------------------------+
| GET    | |user-details|_      | \+    | Get user data                       | users_view                      |
+--------+----------------------+-------+-------------------------------------+---------------------------------+
| PATCH  | |user-update|_       | \+    | Update user's profile               | users_edit, users_reset_password|
+--------+----------------------+-------+-------------------------------------+---------------------------------+
| DELETE | |user-delete|_       | \+    | Delete user                         | **superuser**                   |
+--------+----------------------+-------+-------------------------------------+---------------------------------+
| GET    | |users-list|_        | \+    | List all users                      | users_view                      |
+--------+----------------------+-------+-------------------------------------+---------------------------------+
| GET    | |users-roles-list|_  | \+    | Get user's roles                    | users_view                      |
+--------+----------------------+-------+-------------------------------------+---------------------------------+
| PUT    | |users-roles-edit|_  | \+    | Update user's roles                 | users_roles_edit                |
+--------+----------------------+-------+-------------------------------------+---------------------------------+

.. _user-authorize:

User authorization
~~~~~~~~~~~~~~~~~~

.. |user-authorize| replace:: /auth/login

**Request**::

   POST /auth/login HTTP/1.1

   { "username": "bob@email.com",
     "password": "Password",
   }

Verifies and issues :term:`access token` to admin/manager for next operations.

**Response body**:

.. code-block:: python

   {"access_token": "",                   # access token string
    "user": {
        "uid": "some-unique-user-id",     
        "login": "bob@email.com",         # same as 'username' in request
        "firstname": "Bob",               # first name
        "lastname": "Last",               # last name
        "disabled": False,                # enabled/disabled user account
        "is_superuser": False,            # super user status
        "roles": [{
            "id": 1,
            "name": "Role name"
        }]                                # list of assigned roles.
        }
    }

----

.. _user-create:

Register new user account
~~~~~~~~~~~~~~~~~~~~~~~~~

.. |user-create| replace:: /admin/users/


Create new user account.

**Request**::

   POST /admin/users/ HTTP/1.1
   Authorization: admin_access_token

.. code-block:: python

   {"login": "bob@email.com",         # user email
    "firstname": "Bob",               # first name
    "lastname": "Last",               # last name
    "disabled": False,                # enabled/disabled user account
    "password": "password",           # user password (not empty)
    "is_superuser": False,            # optional, super user status
    }

----

.. _user-details:

Get user details
~~~~~~~~~~~~~~~~

.. |user-details| replace:: /admin/users/**{uid}**

**Request**::

   GET /admin/users/{uid} HTTP/1.1
   Authorization: admin_access_token

Fetch user details


**Response body**:

.. code-block:: python

    {
        "uid": "unique-user-id",
        "login": "...",
        "firstname": "Bob",
        "lastname": "Last",
        "disabled": False,
        "is_superuser": False,

        "roles": [{
               "id": 1,
               "name": "Role name"
        }]
    }

----

.. _user-update:

Update user's profile
~~~~~~~~~~~~~~~~~~~~~

.. |user-update| replace:: /admin/users/**{uid}**

**Request**::

   PATCH /admin/users/{uid} HTTP/1.1
   Authorization: admin_access_token

For changing other user password, additional permission *user_reset_password* is required.

.. code-block:: python

   {"login": "bob@email.com",         # (optional) user email
    "firstname": "Bob",               # (optional) first name
    "lastname": "Last",               # (optional) last name
    "disabled": False,                # (optional) enabled/disabled user account
    "password": "password",           # (optional) old password (not empty)
    "newpassword": "password",        # (optional) new password (not empty)
    }

----

.. _user-delete:

Delete user
~~~~~~~~~~~

.. |user-delete| replace:: /admin/users/**{uid}**

**Request**::

   DELETE /admin/users/{uid} HTTP/1.1
   Authorization: admin_access_token

Delete user. Only super user has right to delete users. Super user
can not delete other super users.

**Response body**:

.. code-block:: python

   {"status": "deleted"}


----

.. _users-list:

List users
~~~~~~~~~~

.. |users-list| replace:: /admin/users/

**Request**::

   GET /admin/users/ HTTP/1.1
   Authorization: admin_access_token

Lists users.

.. code-block:: python

    {
        "filter": {
            "email": 'bob@email.com',     # (optional) user email
            "fullname": 'Bob'             # (optional) user name
        }
    }

**Response body**:

.. code-block:: python

    [
        {
            "uid": "unique-user-id-1",
            "login": "...",
            "firstname": "Bob",
            "lastname": "Last",
            "disabled": False,
            "is_superuser": False,

            "roles": [{
                   "id": 1,
                   "name": "Role name 1"
            }]
        },
        ...
        {
            "uid": "unique-user-id-N",
            "login": "...",
            "firstname": "Sam",
            "lastname": "Second",
            "disabled": False,
            "roles": [{
                "id": 1,
                "name": "Role name 2"
            }]
        }
    ]


----

.. _users-roles-list:

List user's roles
~~~~~~~~~~~~~~~~~

.. |users-roles-list| replace:: /admin/users/**{uid}**/roles

**Request**::

   GET /admin/users/{uid}/roles HTTP/1.1
   Authorization: admin_access_token

Get list of all roles, assigned to user

**Response**:

.. code-block:: python

   [{"id": "role-id-1",
     "role_name": "Some name",
     "description": "",
     "permissions": [] # list of permissions
    },
    # ...
    {"id": "role-id-N",
     "role_name": "Some name N",
     "description": "",
     "permissions": [] # list of permissions
    }]

----

.. _users-roles-edit:

Update user's roles
~~~~~~~~~~~~~~~~~~~

.. |users-roles-edit| replace:: /admin/users/**{uid}**/roles

**Request**::

   PUT /admin/users/{uid}/roles HTTP/1.1
   Authorization: admin_access_token

   [id-1,
    ...
    id-N
   ]

Update roles, assigned to user (replaces whole roles list).

----
