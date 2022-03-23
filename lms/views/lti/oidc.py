import uuid
from urllib.parse import urlencode

from pyramid.httpexceptions import HTTPForbidden, HTTPFound
from pyramid.view import view_config

from lms.services import LTIRegistrationService
from lms.validation import OIDCRequestSchema


@view_config(
    route_name="lti.oidc",
    request_method=("POST", "GET"),
    schema=OIDCRequestSchema,
)
def oidc_view(request):
    """
    View for the second step of the OIDC authentication flow.

    http://www.imsglobal.org/spec/security/v1p0/#step-2-authentication-request

    We have to check we have a corresponding registration based on the `iss` 
    and `client_id` params and redirect back to the LMS.
    """
    params = request.parsed_params

    registration = request.find_service(LTIRegistrationService).get(
        issuer=params["iss"], client_id=params["client_id"]
    )
    if not registration:
        raise HTTPForbidden(
            f"""Registration not found. iss:'{params["iss"]}', client_id:'{params["client_id"]}'"""
        )

    params = {
        # Hardcoded values from:
        # http://www.imsglobal.org/spec/security/v1p0/#step-2-authentication-request
        "scope": "openid",
        "response_type": "id_token",
        "response_mode": "form_post",
        "prompt": "none",
        "login_hint": params["login_hint"],
        "lti_message_hint": params["lti_message_hint"],
        "client_id": params["client_id"],
        "state": uuid.uuid4().hex,
        "nonce": uuid.uuid4().hex,
        # The value will be configured when registering the tool in the LMS and
        # will be different depending on the message type. For example, it will
        # be an lti_launch endpoint for launches and content_item_selection / 
        # deeplinking for LMSs that support it while creating or editing 
        # assignments.
        "redirect_uri": params["target_link_uri"],
    }
    return HTTPFound(location=f"{registration.auth_login_url}?{urlencode(params)}")
