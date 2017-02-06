
def setup_routes(app, users_handler, roles_handler):
    add_route = app.router.add_route
    add_route('GET', '/', users_handler.index)

    # user login
    add_route('POST', '/auth/login', users_handler.login)

    # user crud
    add_route('POST', '/admin/user/', users_handler.user_create)
    add_route('GET', '/admin/user/{uid}', users_handler.user_details)
    add_route('PATCH', '/admin/user/{uid}', users_handler.user_update)
    add_route('DELETE', '/admin/user/{uid}', users_handler.user_delete)
    add_route('GET', '/admin/user/', users_handler.users_list)

    # roles crud
    add_route('POST', '/admin/roles/', roles_handler.role_create)
    add_route('GET', '/admin/roles/{role_id}', roles_handler.role_details)
    add_route('PATCH', '/admin/roles/{role_id}', roles_handler.role_update)
    add_route('DELETE', '/admin/roles/{role_id}', roles_handler.role_delete)
    add_route('GET', '/admin/roles/', roles_handler.roles_list)

    # list permissions
    add_route('GET', '/admin/permissions', roles_handler.list_permissions)

    # user roles
    add_route('GET', '/admin/user/{uid}/roles', roles_handler.get_user_roles)
    add_route('PUT', '/admin/user/{uid}/roles',
              roles_handler.update_user_roles)
