"""
Deep Linking related views.

If an LMS (like Canvas) is configured for "deep linking" then we need to send
the results of the file picker to the LMS instead of storing it ourselves. This
is done by the front-end.

When the LMS launches us with a deep linked assignment, we will get the
document url as part of the launch params, instead of reading it from the DB in
`module_item_configurations`.

The flow is:

 - LMS calls us on `deep_linking_launch`

    The spec requires that deep linking requests have an ``lti_message_type``
    identifying the launch as a deep linking one but we don't actually rely
    on this parameter: instead we use a separate URL
    to distinguish deep linking launches.

 - In the case of LTI1.3:

    * We add configuration to enable a call back to `file_picker_to_form_fields_v13`
    * This provides the form data the front end requires to submit to the LMS

 - In the case of LTI1.1:

    * The frontend constructs itself the form it needs to send to the LMS


For more details see the LTI Deep Linking specs:

 - LTI 1.1 https://www.imsglobal.org/specs/lticiv1p0

   Especially this page:

     https://www.imsglobal.org/specs/lticiv1p0/specification-3

 - LTI 1.3 https://www.imsglobal.org/spec/lti-dl/v2p0

Canvas LMS's Content Item docs are also useful:

  https://canvas.instructure.com/doc/api/file.content_item.html

"""
from urllib.parse import urlencode, urlparse

from pyramid.view import view_config, view_defaults
from webargs import fields

from lms.security import Permissions
from lms.services import LTIAHTTPService
from lms.validation import DeepLinkingLTILaunchSchema
from lms.validation._base import JSONPyramidRequestSchema


@view_config(
    authorized_to_configure_assignments=True,
    permission=Permissions.LTI_LAUNCH_ASSIGNMENT,
    renderer="lms:templates/file_picker.html.jinja2",
    request_method="POST",
    route_name="content_item_selection",
    schema=DeepLinkingLTILaunchSchema,
)
def deep_linking_launch(context, request):
    """Handle deep linking launches."""
    application_instance = request.find_service(
        name="application_instance"
    ).get_current()
    application_instance.update_lms_data(request.params)

    context.get_or_create_course()

    request.find_service(name="lti_h").sync([context.h_group], request.params)

    context.js_config.enable_file_picker_mode(
        form_action=request.parsed_params["content_item_return_url"],
        form_fields={
            "lti_message_type": "ContentItemSelection",
            "lti_version": request.parsed_params["lti_version"],
        },
    )

    if application_instance.lti_version == "1.3.0":
        context.js_config.add_deep_linking_api()
    return {}


class DeepLinkingFieldsRequestSchema(JSONPyramidRequestSchema):
    deep_linking_settings = fields.Dict(required=False, allow_none=True)
    content_item_return_url = fields.Str(required=True)
    content = fields.Dict(required=True)

    extra_params = fields.Dict(required=False)


@view_defaults(
    request_method="POST", renderer="json", schema=DeepLinkingFieldsRequestSchema
)
class DeepLinkingFieldsViews:
    """
    Views that return the required form fields to complete a deep linking request to the LMS.

    After the user picks a document to be annotated the frontend will call these views
    to get all the necessary fields to configure the assignment submitting them in a form to the LMS.
    """

    def __init__(self, request):
        self.request = request

        self.application_instance = self.request.find_service(
            name="application_instance"
        ).get_current()

    @view_config(route_name="lti.deep_linking.form_fields")
    def file_picker_to_form_fields_v13(self):
        url = self._content_to_url(
            self.request.route_url("lti_launches"),
            self.request.parsed_params["content"],
            self.request.parsed_params.get("extra_params"),
        )

        # In LTI1.3 there's just one `JWT` field which includes all the necessary information
        return {
            "JWT": self.request.find_service(LTIAHTTPService).sign(
                {
                    "https://purl.imsglobal.org/spec/lti/claim/deployment_id": self.application_instance.deployment_id,
                    "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiDeepLinkingResponse",
                    "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
                    "https://purl.imsglobal.org/spec/lti-dl/claim/content_items": [
                        {"type": "ltiResourceLink", "url": url}
                    ],
                    "https://purl.imsglobal.org/spec/lti-dl/claim/data": self.request.parsed_params[
                        "deep_linking_settings"
                    ],
                }
            )
        }

    @staticmethod
    def _content_to_url(lti_launch_url, content, extra_params):
        """
        Translate content information from the frontend to a launch URL.

        We submit the content information to the LMS as an URL pointing to our
        `lti_launches` endpoint with any information required to identity
        the content as query parameters.
        """
        params = dict(extra_params or {})

        if content["type"] == "file":
            params["canvas_file"] = "true"
            params["file_id"] = content["file"]["id"]
        elif content["type"] == "url":
            params["url"] = content["url"]
        else:
            raise ValueError(f"Unknown content type: '{content['type']}'")

        return urlparse(lti_launch_url)._replace(query=urlencode(params)).geturl()
