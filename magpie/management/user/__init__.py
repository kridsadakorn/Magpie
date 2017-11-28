import logging
logger = logging.getLogger(__name__)

# above this value is considered a token, refuse longer username creation
USER_NAME_MAX_LENGTH = 64


def includeme(config):

    logger.info('Adding user ...')
    # Add all the rest api routes
    config.add_route('users', '/users')
    config.add_route('user', '/users/{user_name}')
    config.add_route('user_groups', 'users/{user_name}/groups')
    config.add_route('user_group', '/users/{user_name}/groups/{group_name}')
    config.add_route('user_services', '/users/{user_name}/services')
    config.add_route('user_service_permissions', '/users/{user_name}/services/{service_name}/permissions')
    config.add_route('user_service_permission', '/users/{user_name}/services/{service_name}/permissions/{permission_name}')
    config.add_route('user_service_resources', '/users/{user_name}/services/{service_name}/resources')

    config.add_route('user_resources', '/users/{user_name}/resources')
    config.add_route('user_resources_type', '/users/{user_name}/resources/types/{resource_type}')
    config.add_route('user_resource_permissions', '/users/{user_name}/resources/{resource_id}/permissions')
    config.add_route('user_resource_permission', '/users/{user_name}/resources/{resource_id}/permissions/{permission_name}')

    config.scan()
