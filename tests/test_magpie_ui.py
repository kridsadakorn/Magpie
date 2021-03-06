#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_magpie_ui
----------------------------------

Tests for :mod:`magpie.ui` module.
"""

import re
import unittest
from typing import TYPE_CHECKING

# NOTE: must be imported without 'from', otherwise the interface's test cases are also executed
import tests.interfaces as ti
from magpie.constants import get_constant
from magpie.models import Route
from magpie.permissions import Access, Permission, PermissionSet, PermissionType, Scope
from magpie.services import ServiceAPI, ServiceWPS
from tests import runner, utils
from tests.utils import TestVersion

if TYPE_CHECKING:
    from typing import Union

    from magpie.typedefs import Str


@runner.MAGPIE_TEST_UI
@runner.MAGPIE_TEST_LOCAL
class TestCase_MagpieUI_NoAuth_Local(ti.Interface_MagpieUI_NoAuth, unittest.TestCase):
    # pylint: disable=C0103,invalid-name
    """
    Test any operation that do not require any AuthN/AuthZ (``MAGPIE_ANONYMOUS_GROUP`` & ``MAGPIE_ANONYMOUS_USER``).

    Use a local Magpie test application.
    """

    __test__ = True

    @classmethod
    def setUpClass(cls):
        cls.app = utils.get_test_magpie_app()
        cls.url = cls.app  # to simplify calls of TestSetup (all use .url)
        cls.cookies = None
        # note: admin credentials to setup data on test instance as needed, but not to be used for these tests
        cls.grp = get_constant("MAGPIE_ADMIN_GROUP")
        cls.usr = get_constant("MAGPIE_TEST_ADMIN_USERNAME", raise_missing=False, raise_not_set=False)
        cls.pwd = get_constant("MAGPIE_TEST_ADMIN_PASSWORD", raise_missing=False, raise_not_set=False)
        cls.setup_admin()
        cls.test_user_name = get_constant("MAGPIE_TEST_USER", default_value="unittest-no-auth_ui-user-local",
                                          raise_missing=False, raise_not_set=False)
        cls.test_group_name = get_constant("MAGPIE_TEST_GROUP", default_value="unittest-no-auth_ui-group-local",
                                           raise_missing=False, raise_not_set=False)
        cls.test_service_type = ServiceWPS.service_type
        cls.test_service_name = "magpie-unittest-service-wps"


@runner.MAGPIE_TEST_UI
@runner.MAGPIE_TEST_LOCAL
class TestCase_MagpieUI_UsersAuth_Local(ti.Interface_MagpieUI_UsersAuth, unittest.TestCase):
    # pylint: disable=C0103,invalid-name
    """
    Test any operation that require logged user AuthN/AuthZ, but lower than ``MAGPIE_ADMIN_GROUP``.

    Use a local Magpie test application.
    """

    __test__ = True

    @classmethod
    def setUpClass(cls):
        cls.grp = get_constant("MAGPIE_ADMIN_GROUP")
        cls.usr = get_constant("MAGPIE_TEST_ADMIN_USERNAME", raise_missing=False, raise_not_set=False)
        cls.pwd = get_constant("MAGPIE_TEST_ADMIN_PASSWORD", raise_missing=False, raise_not_set=False)
        cls.app = utils.get_test_magpie_app()
        cls.url = cls.app  # to simplify calls of TestSetup (all use .url)
        cls.version = utils.TestSetup.get_Version(cls)
        cls.setup_admin()
        cls.login_admin()
        cls.test_user_name = get_constant("MAGPIE_TEST_USER", default_value="unittest-user-auth_ui-user-local",
                                          raise_missing=False, raise_not_set=False)
        cls.test_group_name = get_constant("MAGPIE_TEST_GROUP", default_value="unittest-user-auth_ui-group-local",
                                           raise_missing=False, raise_not_set=False)


@runner.MAGPIE_TEST_UI
@runner.MAGPIE_TEST_LOCAL
class TestCase_MagpieUI_AdminAuth_Local(ti.Interface_MagpieUI_AdminAuth, unittest.TestCase):
    # pylint: disable=C0103,invalid-name
    """
    Test any operation that require at least ``MAGPIE_ADMIN_GROUP`` AuthN/AuthZ.

    Use a local Magpie test application.
    """

    __test__ = True

    @classmethod
    def setUpClass(cls):
        cls.grp = get_constant("MAGPIE_ADMIN_GROUP")
        cls.usr = get_constant("MAGPIE_TEST_ADMIN_USERNAME", raise_missing=False, raise_not_set=False)
        cls.pwd = get_constant("MAGPIE_TEST_ADMIN_PASSWORD", raise_missing=False, raise_not_set=False)
        cls.app = utils.get_test_magpie_app()
        cls.url = cls.app  # to simplify calls of TestSetup (all use .url)
        cls.cookies = None
        cls.version = utils.TestSetup.get_Version(cls)
        cls.headers, cls.cookies = utils.check_or_try_login_user(cls.url, cls.usr, cls.pwd, use_ui_form_submit=True)
        cls.require = "cannot run tests without logged in user with '{}' permissions".format(cls.grp)
        cls.setup_admin()
        cls.login_admin()

        cls.test_user_name = get_constant("MAGPIE_TEST_USER", default_value="unittest-admin-auth_ui-user-local",
                                          raise_missing=False, raise_not_set=False)
        cls.test_group_name = get_constant("MAGPIE_TEST_GROUP", default_value="unittest-admin-auth_ui-group-local",
                                           raise_missing=False, raise_not_set=False)
        cls.test_service_type = ServiceAPI.service_type
        cls.test_service_name = "magpie-unittest-ui-admin-local-service"
        cls.test_resource_type = Route.resource_type_name

        cls.test_service_parent_resource_type = ServiceAPI.service_type
        cls.test_service_parent_resource_name = "magpie-unittest-ui-tree-parent"
        cls.test_service_child_resource_type = Route.resource_type_name
        cls.test_service_child_resource_name = "magpie-unittest-ui-tree-child"

    @runner.MAGPIE_TEST_LOCAL   # not implemented for remote URL
    @runner.MAGPIE_TEST_STATUS
    @runner.MAGPIE_TEST_FUNCTIONAL
    def test_EditService_Goto_AddChild_BackTo_EditService(self):
        """
        Verifies that UI button redirects are working for the following workflow:
            0. Starting on "Service View", press "Add Child" button (redirects to "New Resource" form)
            1. Fill form and press "Add" button (creates the service resource and redirects to "Service View")
            2. Back on "Service View", <new-resource> is visible in the list.

        Note:
            Only implemented locally with form submission of ``TestApp``.
        """
        try:
            # make sure any sub-resource are all deleted to avoid conflict, then recreate service to add sub-resource
            utils.TestSetup.delete_TestService(self, override_service_name=self.test_service_parent_resource_name)
            body = utils.TestSetup.create_TestService(self,
                                                      override_service_name=self.test_service_parent_resource_name,
                                                      override_service_type=self.test_service_parent_resource_type)
            svc_res_id = body["service"]["resource_id"]
            form = {"add_child": None, "resource_id": str(svc_res_id)}
            path = "/ui/services/{}/{}".format(self.test_service_parent_resource_type,
                                               self.test_service_parent_resource_name)
            resp = utils.TestSetup.check_FormSubmit(self, form_match=form, form_submit="add_child", path=path)
            utils.check_val_is_in("New Resource", resp.text, msg=utils.null)    # add resource page reached
            data = {
                "resource_name": self.test_service_child_resource_name,
                "resource_type": self.test_service_child_resource_type,
            }
            resp = utils.TestSetup.check_FormSubmit(self, form_match="add_resource_form", form_submit="add_child",
                                                    form_data=data, previous_response=resp)
            for res_name in (self.test_service_parent_resource_name, self.test_service_child_resource_name):
                if TestVersion(self.version) >= TestVersion("3.0"):
                    find = "<div class=\"tree-key\">{}</div>".format(res_name)
                    text = resp.text.replace("\n", "").replace("  ", "")  # ignore formatting of source file
                else:
                    find = "<div class=\"tree-item\">{}</div>".format(res_name)
                    text = resp.text
                utils.check_val_is_in(find, text, msg=utils.null)
        finally:
            utils.TestSetup.delete_TestService(self, override_service_name=self.test_service_parent_resource_name)

    @runner.MAGPIE_TEST_LOCAL   # not implemented for remote URL
    @runner.MAGPIE_TEST_STATUS
    @runner.MAGPIE_TEST_PERMISSIONS
    @runner.MAGPIE_TEST_FUNCTIONAL
    def test_EditUser_ApplyPermissions(self):
        """
        Verifies that UI button operations are working for the following workflow:
            0. Goto Edit User page.
            1. Change ``service-type`` tab to display services of type :class:`ServiceAPI`.
            2. Set new permissions onto an existing resources and submit them with ``Apply`` button.
            3. Verify the permissions are selected and displayed on page reload.
            4. Remove and modify permission from existing resource and submit.
            5. Validate that changes are reflected.

        Note:
            Only implemented locally with form submission of ``TestApp``.
        """
        utils.warn_version(self, "update permission modifiers with option select", "3.0", skip=True)

        # make sure any sub-resource are all deleted to avoid conflict, then recreate service to add sub-resource
        utils.TestSetup.delete_TestService(self)
        body = utils.TestSetup.create_TestService(self)
        info = utils.TestSetup.get_ResourceInfo(self, override_body=body)
        svc_id, svc_name = info["resource_id"], info["service_name"]
        res_name = "resource1"
        sub_name = "resource2"
        body = utils.TestSetup.create_TestResource(self, parent_resource_id=svc_id, override_resource_name=res_name)
        info = utils.TestSetup.get_ResourceInfo(self, override_body=body)
        res_id = info["resource_id"]
        body = utils.TestSetup.create_TestResource(self, parent_resource_id=res_id, override_resource_name=sub_name)
        info = utils.TestSetup.get_ResourceInfo(self, override_body=body)
        sub_id = info["resource_id"]
        utils.TestSetup.create_TestGroup(self)
        utils.TestSetup.create_TestUser(self)

        # utilities for later tests
        def to_ui_permission(permission):
            # type: (Union[Str, PermissionSet]) -> Str
            return permission.explicit_permission if isinstance(permission, PermissionSet) else ""

        def check_ui_resource_permissions(perm_form, resource_id, permissions):
            select_res_id = "permission_resource_{}".format(resource_id)
            select_options = perm_form.fields[select_res_id]  # contains multiple select, one per applicable permission
            utils.check_val_equal(len(select_options), 2, msg="Always 2 select combobox expected (read and write).")
            select_values = [select.value for select in select_options]
            if not permissions:
                utils.check_all_equal(["", ""], select_values, msg="When no permission is selected, values are empty")
                return
            # value must match exactly the *explicit* permission representation
            for r_perm in permissions:
                utils.check_val_is_in(r_perm, select_values)

        def check_api_resource_permissions(resource_permissions):
            for _r_id, _r_perms in resource_permissions:
                urp_path = "/users/{}/resources/{}/permissions".format(self.test_user_name, _r_id)
                urp_resp = utils.test_request(self, "GET", urp_path)
                urp_body = utils.check_response_basic_info(urp_resp)
                ur_perms = [perm.json() for perm in _r_perms if isinstance(perm, PermissionSet)]
                for perm in ur_perms:
                    perm["type"] = PermissionType.DIRECT.value
                permissions = urp_body["permissions"]
                for perm in permissions:
                    perm.pop("reason", None)  # >= 3.4, don't care for this test
                utils.check_all_equal(permissions, ur_perms, any_order=True)

        # 0. goto user edit page (default first service selected)
        path = "/ui/users/{}/default".format(self.test_user_name)
        resp = utils.test_request(self, "GET", path)
        # 1. change to 'api' service-type, validate created test resources are all displayed in resource tree
        resp = resp.click(self.test_service_type)  # tabs are '<a href=...>{service-type}</a>'
        body = utils.check_ui_response_basic_info(resp)
        text = body.replace("\n", "").replace("  ", "")  # ignore HTML formatting
        tree_keys = re.findall(r"<div class=\"tree-key\">(.*?)</div>", text)
        for r_name in [svc_name, res_name, sub_name]:
            utils.check_val_is_in(r_name, tree_keys, msg="Resource '{}' expected to be listed in tree.".format(r_name))

        # 2. apply new permissions
        # 2.1 validate all initial values of permissions are empty
        res_form_name = "resources_permissions"  # form that wraps the displayed resource tree
        res_form_submit = "edit_permissions"     # id of the Apply 'submit' input of the form
        res_perm_form = resp.forms[res_form_name]
        for r_id in [svc_id, res_id, sub_id]:
            check_ui_resource_permissions(res_perm_form, r_id, [])
        # 2.2 apply new
        # NOTE: because tree-view is created by reversed order of permissions, we must provide them as [WRITE, READ]
        svc_perm1 = PermissionSet(Permission.READ, Access.ALLOW, Scope.RECURSIVE)
        svc_perms = ["", svc_perm1]
        res_perm1 = PermissionSet(Permission.READ, Access.DENY, Scope.RECURSIVE)
        res_perm2 = PermissionSet(Permission.WRITE, Access.ALLOW, Scope.RECURSIVE)
        res_perms = [res_perm2, res_perm1]
        sub_perm1 = PermissionSet(Permission.READ, Access.ALLOW, Scope.MATCH)
        sub_perms = ["", sub_perm1]
        data = {
            # set value for following correspond to 'select' option that was chosen
            "permission_resource_{}".format(svc_id): [to_ui_permission(perm) for perm in svc_perms],
            "permission_resource_{}".format(res_id): [to_ui_permission(perm) for perm in res_perms],
            "permission_resource_{}".format(sub_id): [to_ui_permission(perm) for perm in sub_perms],
        }
        resp = utils.TestSetup.check_FormSubmit(self, previous_response=resp, form_match=res_perm_form,
                                                form_submit=res_form_submit, form_data=data)

        # 3. validate result
        # 3.1 validate displayed UI permissions
        res_perm_form = resp.forms[res_form_name]
        check_ui_resource_permissions(res_perm_form, svc_id, [to_ui_permission(perm) for perm in svc_perms])
        check_ui_resource_permissions(res_perm_form, res_id, [to_ui_permission(perm) for perm in res_perms])
        check_ui_resource_permissions(res_perm_form, sub_id, [to_ui_permission(perm) for perm in sub_perms])
        # 3.2 validate applied using API (to make sure that changes are not only reflected in UI)
        check_api_resource_permissions([(svc_id, svc_perms), (res_id, res_perms), (sub_id, sub_perms)])

        # 4. remove permission: this is equivalent to re-apply the ones we want to keep without the one to remove
        #    modify permission: this is detected by combo of (res-id, perm-name) with different (access, scope)
        svc_perms_mod = ["", ""]  # remove the previous (READ, ALLOW, RECURSIVE)
        res_perm1_mod = PermissionSet(Permission.READ, Access.ALLOW, Scope.RECURSIVE)  # DENY -> ALLOW
        res_perms_mod = [res_perm2, res_perm1_mod]  # second WRITE permission is unchanged
        sub_perms_mod = sub_perms  # all unchanged for this resource
        data = {
            "permission_resource_{}".format(svc_id): [to_ui_permission(perm) for perm in svc_perms_mod],
            "permission_resource_{}".format(res_id): [to_ui_permission(perm) for perm in res_perms_mod],
            "permission_resource_{}".format(sub_id): [to_ui_permission(perm) for perm in sub_perms_mod],
        }
        resp = utils.TestSetup.check_FormSubmit(self, previous_response=resp, form_match=res_perm_form,
                                                form_submit=res_form_submit, form_data=data)

        # 5. validate applied permissions modifications
        res_perm_form = resp.forms[res_form_name]
        check_ui_resource_permissions(res_perm_form, svc_id, [to_ui_permission(perm) for perm in svc_perms_mod])
        check_ui_resource_permissions(res_perm_form, res_id, [to_ui_permission(perm) for perm in res_perms_mod])
        check_ui_resource_permissions(res_perm_form, sub_id, [to_ui_permission(perm) for perm in sub_perms_mod])
        check_api_resource_permissions([(svc_id, svc_perms_mod), (res_id, res_perms_mod), (sub_id, sub_perms_mod)])


@runner.MAGPIE_TEST_UI
@runner.MAGPIE_TEST_REMOTE
class TestCase_MagpieUI_NoAuth_Remote(ti.Interface_MagpieUI_NoAuth, unittest.TestCase):
    # pylint: disable=C0103,invalid-name
    """
    Test any operation that do not require any AuthN/AuthZ (``MAGPIE_ANONYMOUS_GROUP`` & ``MAGPIE_ANONYMOUS_USER``).

    Use an already running remote bird server.
    """

    @classmethod
    def setUpClass(cls):
        cls.url = get_constant("MAGPIE_TEST_REMOTE_SERVER_URL")
        cls.version = utils.TestSetup.get_Version(cls)
        # note: admin credentials to setup data on test instance as needed, but not to be used for these tests
        cls.grp = get_constant("MAGPIE_ADMIN_GROUP")
        cls.usr = get_constant("MAGPIE_TEST_ADMIN_USERNAME", raise_missing=False, raise_not_set=False)
        cls.pwd = get_constant("MAGPIE_TEST_ADMIN_PASSWORD", raise_missing=False, raise_not_set=False)
        cls.setup_admin()
        cls.test_user_name = get_constant("MAGPIE_TEST_USER", default_value="unittest-no-auth_ui-user-remote",
                                          raise_missing=False, raise_not_set=False)
        cls.test_group_name = get_constant("MAGPIE_TEST_GROUP", default_value="unittest-no-auth_ui-group-remote",
                                           raise_missing=False, raise_not_set=False)
        cls.test_service_type = ServiceWPS.service_type
        cls.test_service_name = "magpie-unittest-service-wps"


@runner.MAGPIE_TEST_UI
@runner.MAGPIE_TEST_REMOTE
class TestCase_MagpieUI_UsersAuth_Remote(ti.Interface_MagpieUI_UsersAuth, unittest.TestCase):
    # pylint: disable=C0103,invalid-name
    """
    Test any operation that require logged AuthN/AuthZ, but lower than ``MAGPIE_ADMIN_GROUP``.

    Use an already running remote bird server.
    """

    @classmethod
    def setUpClass(cls):
        cls.url = get_constant("MAGPIE_TEST_REMOTE_SERVER_URL")
        cls.usr = get_constant("MAGPIE_TEST_ADMIN_USERNAME", raise_missing=False, raise_not_set=False)
        cls.pwd = get_constant("MAGPIE_TEST_ADMIN_PASSWORD", raise_missing=False, raise_not_set=False)
        cls.setup_admin()
        cls.login_admin()
        cls.version = utils.TestSetup.get_Version(cls)
        cls.test_user_name = get_constant("MAGPIE_TEST_USER", default_value="unittest-user-auth_ui-user-remote",
                                          raise_missing=False, raise_not_set=False)
        cls.test_group_name = get_constant("MAGPIE_TEST_GROUP", default_value="unittest-user-auth_ui-group-remote",
                                           raise_missing=False, raise_not_set=False)


@runner.MAGPIE_TEST_UI
@runner.MAGPIE_TEST_REMOTE
class TestCase_MagpieUI_AdminAuth_Remote(ti.Interface_MagpieUI_AdminAuth, unittest.TestCase):
    # pylint: disable=C0103,invalid-name
    """
    Test any operation that require at least ``MAGPIE_ADMIN_GROUP`` AuthN/AuthZ.

    Use an already running remote bird server.
    """

    @classmethod
    def setUpClass(cls):
        cls.grp = get_constant("MAGPIE_ADMIN_GROUP")
        cls.usr = get_constant("MAGPIE_TEST_ADMIN_USERNAME", raise_missing=False, raise_not_set=False)
        cls.pwd = get_constant("MAGPIE_TEST_ADMIN_PASSWORD", raise_missing=False, raise_not_set=False)
        cls.url = get_constant("MAGPIE_TEST_REMOTE_SERVER_URL")
        cls.headers, cls.cookies = utils.check_or_try_login_user(cls.url, cls.usr, cls.pwd)
        cls.require = "cannot run tests without logged in '{}' user".format(cls.grp)
        cls.setup_admin()
        cls.login_admin()
        cls.version = utils.TestSetup.get_Version(cls)
        cls.test_user_name = get_constant("MAGPIE_TEST_USER", default_value="unittest-admin-auth_ui-user-remote",
                                          raise_missing=False, raise_not_set=False)
        cls.test_group_name = get_constant("MAGPIE_TEST_GROUP", default_value="unittest-admin-auth_ui-group-remote",
                                           raise_missing=False, raise_not_set=False)
        cls.test_service_type = ServiceAPI.service_type
        cls.test_service_name = "magpie-unittest-ui-admin-remote-service"
