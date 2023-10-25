import re
from functools import lru_cache
from typing import Optional
from urllib.parse import unquote, urlencode, urlparse

from lms.product.plugin.misc import MiscPlugin
from lms.services.vitalsource import VSBookLocation


class CanvasMiscPlugin(MiscPlugin):
    def post_launch_assignment_hook(self, request, js_config, assignment):
        """
        Configure grading during a launch.

        In canvas we use Speed Grader, we configure the frontend to use it.
        """
        lti_params = request.lti_params
        lti_user = request.lti_user

        # For students in Canvas with grades to submit we need to enable
        # Speedgrader settings for gradable assignments
        # `lis_result_sourcedid` associates a specific user with an
        # assignment.
        if (
            assignment.is_gradable
            and lti_user.is_learner
            and lti_params.get("lis_result_sourcedid")
        ):
            js_config.add_canvas_speedgrader_settings(assignment.document_url)

        # We add a `focused_user` query param to the LTI launch URL
        # we send to canvas with student submissions.
        # Later, when Canvas uses these URLs to launch
        # us when a teacher grades the assignment in SpeedGrader we read that value and
        # filter the annotations on the client to only show the ones by that student.
        if focused_user := request.params.get("focused_user"):
            js_config.set_focused_user(focused_user)

    @lru_cache(1)
    def get_document_url(
        self, request, assignment, historical_assignment
    ) -> Optional[str]:
        """
        Get the configured document for this LTI launch.

        This will try all known methods for finding out, and will return None
        if no configuration can be found.
        """
        deep_linked_parameters = self.get_deep_linked_assignment_configuration(request)

        for document_url_source in (
            self._from_deep_linking_provided_url,
            self._from_canvas_file,
            self._from_legacy_vitalsource_book,
        ):
            if document_url := document_url_source(request, deep_linked_parameters):
                return document_url

        return None

    # If the URL looks like "schema%3a" (schema:) it's double-encoded
    # https://www.rfc-editor.org/rfc/rfc3986#section-3.1
    _ENCODED_URL = re.compile("^[a-z][a-z0-9+.-]*%3a", re.IGNORECASE)

    @classmethod
    def _from_deep_linking_provided_url(cls, _request, deep_linked_configuration: dict):
        """
        Get the URL from the deep linking information.

        This is the parameter we send during deep linking configuration coming
        back to us from the LMS.
        """

        if url := deep_linked_configuration.get("url"):
            # Work around a bug in Canvas's handling of LTI Launch URLs in
            # SpeedGrader launches where query params get double-encoded.
            # See https://github.com/instructure/canvas-lms/issues/1486
            if cls._ENCODED_URL.match(url):
                url = unquote(url)

        return url

    @classmethod
    def _from_canvas_file(cls, request, deep_linked_configuration: dict):
        """
        Get a Canvas file URL.

        These values are ephemeral and can't be stored.
        """

        if (
            deep_linked_configuration.get("canvas_file")
            and (course_id := request.lti_params.get("custom_canvas_course_id"))
            and (file_id := deep_linked_configuration["file_id"])
        ):
            return f"canvas://file/course/{course_id}/file_id/{file_id}"

        return None

    @classmethod
    def _from_legacy_vitalsource_book(cls, _request, deep_linked_configuration: dict):
        """
        Respond to a legacy configured VitalSource assignment.

        Newer Vitalsource assignments are configured with document URLs like
        `vitalsource://...`
        """
        if deep_linked_configuration.get("vitalsource_book"):
            return VSBookLocation(
                book_id=deep_linked_configuration["book_id"],
                cfi=deep_linked_configuration.get("cfi"),
            ).document_url

        return None

    def get_deep_linked_assignment_configuration(self, request) -> dict:
        params = {}

        possible_parameters = [
            "group_set",
            # VS, legacy method
            "vitalsource_book",
            "book_id",
            "cfi",
            # Canvas files
            "canvas_file",
            "file_id",
            # General document url of other types
            "url",
        ]

        for param in possible_parameters:
            if value := request.params.get(param):
                params[param] = value

        return params

    def get_deeplinking_launch_url(self, request, assignment_configuration: dict):
        route_name = "lti_launches"
        if request.json.get("single_lti_endpoint"):
            # If we are using the single-endpoint flow, point to that
            route_name = "lti.launch"

        # In canvas we encode the assignment configuration as query parameters.
        url = (
            urlparse(request.route_url(route_name))
            ._replace(query=urlencode(assignment_configuration))
            .geturl()
        )
        return url

    @classmethod
    def factory(cls, _context, _request):
        return cls()
