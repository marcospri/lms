from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from sqlalchemy.exc import IntegrityError

from lms.services import ApplicationInstanceNotFound
from lms.views.admin import AdminViews, logged_out, notfound
from tests.matchers import Any, temporary_redirect_to


@pytest.mark.usefixtures(
    "pyramid_config", "application_instance_service", "lti_registration_service"
)
class TestAdminViews:
    def test_index(self, pyramid_request, views):
        response = views.index()

        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instances")
        )

    @pytest.mark.parametrize(
        "view",
        ("instances", "instance_new_registration"),
    )
    def test_render_template_views(self, views, view):
        assert getattr(views, view)() == {}

    def test_instance_new_registration_post_existent_registration(
        self, lti_registration_service, pyramid_request
    ):
        pyramid_request.params["issuer"] = sentinel.issuer
        pyramid_request.params["client_id"] = sentinel.client_id

        response = AdminViews(pyramid_request).instance_new_registration_post()

        lti_registration_service.get.assert_called_once_with(
            sentinel.issuer, sentinel.client_id
        )

        assert response == {
            "lti_registration": lti_registration_service.get.return_value
        }

    def test_instance_new_registration_post_non_existent_registration(
        self, lti_registration_service, pyramid_request
    ):
        lti_registration_service.get.return_value = None

        pyramid_request.params["issuer"] = sentinel.issuer
        pyramid_request.params["client_id"] = sentinel.client_id

        response = AdminViews(pyramid_request).instance_new_registration_post()

        lti_registration_service.get.assert_called_once_with(
            sentinel.issuer, sentinel.client_id
        )

        assert response["lti_registration"].issuer == sentinel.issuer
        assert response["lti_registration"].client_id == sentinel.client_id

    def test_instance_new_registration_post_missing_params(self, pyramid_request):
        with pytest.raises(HTTPFound) as redirect_exc:
            AdminViews(pyramid_request).instance_new_registration_post()

        assert redirect_exc.value == temporary_redirect_to(
            pyramid_request.route_url("admin.instance.new.registration")
        )
        assert pyramid_request.session.peek_flash("errors")

    def test_instance_new_with_registration_id(
        self, pyramid_request_new_registration, application_instance_service
    ):
        response = AdminViews(pyramid_request_new_registration).instance_new()

        application_instance_service.create.assert_called_once_with(
            lms_url=sentinel.lms_url,
            email=sentinel.email,
            deployment_id=sentinel.deployment_id,
            developer_key=None,
            developer_secret=None,
            lti_registration_id=sentinel.lti_registration_id,
        )

        assert response == temporary_redirect_to(
            pyramid_request_new_registration.route_url(
                "admin.instance.id",
                id_=application_instance_service.create.return_value.id,
            )
        )

    def test_instance_new_with_new_registration(
        self,
        pyramid_request_new_registration,
        application_instance_service,
        lti_registration_service,
    ):
        del pyramid_request_new_registration.params["lti_registration_id"]

        response = AdminViews(pyramid_request_new_registration).instance_new()

        lti_registration_service.create.assert_called_once_with(
            issuer=sentinel.issuer,
            client_id=sentinel.client_id,
            auth_login_url=sentinel.auth_login_url,
            key_set_url=sentinel.key_set_url,
            token_url=sentinel.token_url,
        )

        application_instance_service.create.assert_called_once_with(
            lms_url=sentinel.lms_url,
            email=sentinel.email,
            deployment_id=sentinel.deployment_id,
            developer_key=None,
            developer_secret=None,
            lti_registration_id=lti_registration_service.create.return_value.id,
        )

        assert response == temporary_redirect_to(
            pyramid_request_new_registration.route_url(
                "admin.instance.id",
                id_=application_instance_service.create.return_value.id,
            )
        )

    def test_instance_new_missing_params(self, pyramid_request_new_registration):
        del pyramid_request_new_registration.params["lms_url"]

        with pytest.raises(HTTPFound) as redirect_exc:
            AdminViews(pyramid_request_new_registration).instance_new()

        assert pyramid_request_new_registration.session.peek_flash("errors")
        assert redirect_exc.value == temporary_redirect_to(
            pyramid_request_new_registration.route_url(
                "admin.instance.new.registration"
            )
        )

    def test_instance_with_duplicate(
        self, pyramid_request_new_registration, application_instance_service
    ):
        application_instance_service.create.side_effect = IntegrityError(
            Any(), Any(), Any()
        )

        response = AdminViews(pyramid_request_new_registration).instance_new()

        assert pyramid_request_new_registration.session.peek_flash("errors")
        assert response == temporary_redirect_to(
            pyramid_request_new_registration.route_url(
                "admin.instance.new.registration"
            )
        )

    def test_search_not_query(self, pyramid_request):
        response = AdminViews(pyramid_request).search()

        assert pyramid_request.session.peek_flash("errors")
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instances")
        )

    def test_search_no_results(self, pyramid_request, application_instance_service):
        application_instance_service.search.return_value = None
        pyramid_request.params["issuer"] = sentinel.issuer

        response = AdminViews(pyramid_request).search()

        application_instance_service.search.assert_called_once_with(
            consumer_key=None,
            issuer=sentinel.issuer,
            client_id=None,
            deployment_id=None,
            tool_consumer_instance_guid=None,
        )
        assert pyramid_request.session.peek_flash("errors")
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instances")
        )

    def test_search_single_result(
        self, pyramid_request, application_instance_service, application_instance
    ):
        application_instance_service.search.return_value = [application_instance]
        pyramid_request.params["issuer"] = sentinel.issuer

        response = AdminViews(pyramid_request).search()

        application_instance_service.search.assert_called_once_with(
            consumer_key=None,
            issuer=sentinel.issuer,
            client_id=None,
            deployment_id=None,
            tool_consumer_instance_guid=None,
        )
        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.instance.id",
                id_=application_instance_service.search.return_value[0].id,
            )
        )

    def test_search_multiple_results(
        self, pyramid_request, application_instance_service
    ):
        pyramid_request.params = {
            "consumer_key": sentinel.consumer_key,
            "issuer": sentinel.issuer,
            "client_id": sentinel.client_id,
            "deployment_id": sentinel.deployment_id,
            "tool_consumer_instance_guid": sentinel.tool_consumer_instance_guid,
        }

        response = AdminViews(pyramid_request).search()

        application_instance_service.search.assert_called_once_with(
            consumer_key=sentinel.consumer_key,
            issuer=sentinel.issuer,
            client_id=sentinel.client_id,
            deployment_id=sentinel.deployment_id,
            tool_consumer_instance_guid=sentinel.tool_consumer_instance_guid,
        )
        assert response == {
            "instances": application_instance_service.search.return_value
        }

    def test_show_instance_consumer_key(
        self, pyramid_request, application_instance_service
    ):
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key

        response = AdminViews(pyramid_request).show_instance()

        assert (
            response["instance"].consumer_key
            == application_instance_service.get_by_consumer_key.return_value.consumer_key
        )

    def test_show_instance_id(self, pyramid_request, application_instance_service):
        pyramid_request.matchdict["id_"] = sentinel.id

        response = AdminViews(pyramid_request).show_instance()

        assert (
            response["instance"].id
            == application_instance_service.get_by_id.return_value.id
        )

    def test_show_not_found(self, pyramid_request, application_instance_service):
        application_instance_service.get_by_consumer_key.side_effect = (
            ApplicationInstanceNotFound
        )
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key

        with pytest.raises(HTTPNotFound):
            AdminViews(pyramid_request).show_instance()

    def test_update_instance(self, pyramid_request, application_instance_service):
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key

        response = AdminViews(pyramid_request).update_instance()

        application_instance_service.get_by_consumer_key.assert_called_once_with(
            sentinel.consumer_key
        )
        application_instance = (
            application_instance_service.get_by_consumer_key.return_value
        )

        assert pyramid_request.session.peek_flash("messages")
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instance.id", id_=application_instance.id)
        )

    @pytest.mark.parametrize(
        "setting,sub_setting,value,expected",
        (
            # Boolean fields
            ("canvas", "groups_enabled", "on", True),
            ("canvas", "sections_enabled", "", False),
            ("blackboard", "files_enabled", "other", False),
            ("blackboard", "groups_enabled", "off", False),
            ("microsoft_onedrive", "files_enabled", "on", True),
            ("vitalsource", "enabled", "on", True),
            ("jstor", "enabled", "off", False),
            # String fields
            ("jstor", "site_code", "CODE", "CODE"),
            ("jstor", "site_code", "  CODE  ", "CODE"),
            ("jstor", "site_code", "", None),
            ("jstor", "site_code", None, None),
        ),
    )
    def test_update_instance_saves_ai_settings(
        self,
        pyramid_request,
        application_instance_service,
        setting,
        sub_setting,
        value,
        expected,
    ):
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key
        pyramid_request.params[f"{setting}.{sub_setting}"] = value

        AdminViews(pyramid_request).update_instance()

        application_instance = (
            application_instance_service.get_by_consumer_key.return_value
        )
        assert application_instance.settings.get(setting, sub_setting) == expected

    def test_update_instance_not_found(
        self, pyramid_request, application_instance_service
    ):
        application_instance_service.get_by_consumer_key.side_effect = (
            ApplicationInstanceNotFound
        )
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key

        with pytest.raises(HTTPNotFound):
            AdminViews(pyramid_request).update_instance()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {}
        return pyramid_request

    @pytest.fixture
    def pyramid_request_new_registration(self, pyramid_request):
        pyramid_request.params["issuer"] = sentinel.issuer
        pyramid_request.params["client_id"] = sentinel.client_id
        pyramid_request.params["email"] = sentinel.email
        pyramid_request.params["deployment_id"] = sentinel.deployment_id
        pyramid_request.params["lti_registration_id"] = sentinel.lti_registration_id
        pyramid_request.params["auth_login_url"] = sentinel.auth_login_url
        pyramid_request.params["key_set_url"] = sentinel.key_set_url
        pyramid_request.params["token_url"] = sentinel.token_url
        pyramid_request.params["lms_url"] = sentinel.lms_url

        return pyramid_request

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminViews(pyramid_request)


def test_logged_out_redirects_to_login(pyramid_request):
    response = logged_out(pyramid_request)

    assert response.status_code == 302

    assert response == temporary_redirect_to(
        pyramid_request.route_url("pyramid_googleauth.login")
    )


def test_not_found_view(pyramid_request):
    response = notfound(pyramid_request)

    assert response.status_code == 404
