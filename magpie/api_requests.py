from magpie import *
import models
from models import resource_type_dict
from api_except import *
from pyramid.interfaces import IAuthenticationPolicy


def get_userid_by_token(token, authn_policy):
    cookie_helper = authn_policy.cookie
    cookie = token
    if cookie is None:
        return None
    remote_addr = '0.0.0.0'

    timestamp, userid, tokens, user_data = cookie_helper.parse_ticket(
        cookie_helper.secret,
        cookie,
        remote_addr,
        cookie_helper.hashalg
    )
    return userid


def get_user(request, user_name_or_token):
    if len(user_name_or_token) > 20:
        authn_policy = request.registry.queryUtility(IAuthenticationPolicy)
        user_id = get_userid_by_token(user_name_or_token, authn_policy)
        user = evaluate_call(lambda: UserService.by_id(user_id, db_session=request.db),
                             fallback=lambda: request.db.rollback(),
                             httpError=HTTPForbidden, msgOnFail="User id query refused by db")
        verify_param(user, notNone=True, httpError=HTTPNotFound, msgOnFail="User id not found in db")
        return user
    elif user_name_or_token == LOGGED_USER:
        curr_user = request.user
        if curr_user:
            return curr_user
        else:
            anonymous = evaluate_call(lambda: UserService.by_user_name(ANONYMOUS_USER, db_session=request.db),
                                      fallback=lambda: request.db.rollback(),
                                      httpError=HTTPForbidden, msgOnFail="Anonymous user query refused by db")
            verify_param(anonymous, notNone=True, httpError=HTTPNotFound, msgOnFail="Anonymous user not found in db")
            return anonymous
    else:
        user = evaluate_call(lambda: UserService.by_user_name(user_name_or_token, db_session=request.db),
                             fallback=lambda: request.db.rollback(),
                             httpError=HTTPForbidden, msgOnFail="User name query refused by db")
        verify_param(user, notNone=True, httpError=HTTPNotFound, msgOnFail="User name not found in db")
        return user


def get_user_matchdict_checked(request, user_name_key='user_name'):
    user_name = get_value_matchdict_checked(request, user_name_key)
    return get_user(request, user_name)


def get_group_matchdict_checked(request, group_name_key='group_name'):
    group_name = get_value_matchdict_checked(request, group_name_key)
    group = evaluate_call(lambda: GroupService.by_group_name(group_name, db_session=request.db),
                          fallback=lambda: request.db.rollback(),
                          httpError=HTTPForbidden, msgOnFail="Group query by name refused by db")
    verify_param(group, notNone=True, httpError=HTTPNotFound, msgOnFail="Group name not found in db")
    return group


def get_resource_matchdict_checked(request, resource_name_key='resource_id'):
    resource_id = get_value_matchdict_checked(request, resource_name_key)
    resource_id = evaluate_call(lambda: int(resource_id), httpError=HTTPNotAcceptable,
                                msgOnFail="Resource ID is an invalid literal for `int` type")
    resource = evaluate_call(lambda: ResourceService.by_resource_id(resource_id, db_session=request.db),
                             fallback=lambda: request.db.rollback(),
                             httpError=HTTPForbidden, msgOnFail="Resource query by id refused by db")
    verify_param(resource, notNone=True, httpError=HTTPNotFound, msgOnFail="Resource ID not found in db")
    verify_param(resource.resource_type, paramCompare=resource_type_dict, isIn=True,
                 httpError=HTTPNotAcceptable, msgOnFail="Resource type does not match any valid entry")
    return resource


def get_service_matchdict_checked(request, service_name_key='service_name'):
    service_name = get_value_matchdict_checked(request, service_name_key)
    service = evaluate_call(lambda: models.Service.by_service_name(service_name, db_session=request.db),
                            fallback=lambda: request.db.rollback(),
                            httpError=HTTPForbidden, msgOnFail="Service query by name refused by db")
    verify_param(service, notNone=True, httpError=HTTPNotFound, msgOnFail="Service name not found in db")
    return service


def get_permission_matchdict_checked(request, service_resource, permission_name_key='permission_name'):
    if isinstance(service_resource, models.Service):
        res_type_dict = resource_type_dict[service_resource.type]
    elif isinstance(service_resource, models.Resource):
        res_type_dict = resource_type_dict[service_resource.resource_type]
    else:
        raise_http(httpError=HTTPInternalServerError, detail="Invalid service/resource object",
                   content={u'service_resource': repr(type(service_resource))})
    perm_name = get_multiformat_post(request, permission_name_key)
    verify_param(perm_name, paramCompare=res_type_dict.permission_names, isIn=True,
                 httpError=HTTPBadRequest, msgOnFail="Permission not allowed for that service/resource")
    return perm_name


def get_value_matchdict_checked(request, key):
    val = request.matchdict.get(key)
    verify_param(val, notNone=True, notEmpty=True, httpError=HTTPNotAcceptable,
                 msgOnFail="Invalid value '" + str(val) + "' specified using key '" + str(key) + "'")
    return val
