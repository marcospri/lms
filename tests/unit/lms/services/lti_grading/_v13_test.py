from unittest.mock import Mock, sentinel

import pytest
from freezegun import freeze_time
from h_matchers import Any
from pytest import param

from lms.services.exceptions import ExternalRequestError, StudentNotInCourse
from lms.services.lti_grading._v13 import LTI13GradingService


class TestLTI13GradingService:
    @freeze_time("2022-04-04")
    def test_read_lti_result(self, svc, response, ltia_http_service):
        ltia_http_service.request.return_value.json.return_value = response
        svc.line_item_url = "https://lms.com/lineitems?param=1"

        score = svc.read_result(sentinel.user_id)

        ltia_http_service.request.assert_called_once_with(
            "GET",
            "https://lms.com/lineitems/results?param=1",
            scopes=svc.LTIA_SCOPES,
            params={"user_id": sentinel.user_id},
            headers={"Accept": "application/vnd.ims.lis.v2.resultcontainer+json"},
        )
        assert score == response[-1]["resultScore"] / response[-1]["resultMaximum"]

    def test_read_lti_result_empty(self, svc, ltia_http_service):
        ltia_http_service.request.side_effect = ExternalRequestError(
            response=Mock(status_code=404)
        )

        score = svc.read_result(sentinel.user_id)

        assert not score

    def test_read_lti_result_raises(self, svc, ltia_http_service):
        ltia_http_service.request.side_effect = ExternalRequestError(
            response=Mock(status_code=500)
        )

        with pytest.raises(ExternalRequestError):
            svc.read_result(sentinel.user_id)

    def test_read_empty_lti_result(self, svc, ltia_http_service):
        ltia_http_service.request.return_value.json.return_value = []

        assert not svc.read_result(sentinel.user_id)

    @pytest.mark.parametrize(
        "bad_response",
        (
            param([{"resultScore": None, "resultMaximum": 100}], id="TypeError"),
            param([{"resultScore": 1, "resultMaximum": 0}], id="ZeroDivisionError"),
            param([{"resultScore": 1}], id="KeyError (max)"),
            param([{"resultMaximum": 10}], id="KeyError (score)"),
        ),
    )
    def test_read_bad_response_lti_result(self, svc, ltia_http_service, bad_response):
        ltia_http_service.request.return_value.json.return_value = bad_response

        assert not svc.read_result(sentinel.user_id)

    @freeze_time("2022-04-04")
    def test_record_result(self, svc, ltia_http_service):
        svc.line_item_url = "https://lms.com/lineitems?param=1"

        response = svc.record_result(sentinel.user_id, sentinel.score)

        ltia_http_service.request.assert_called_once_with(
            "POST",
            "https://lms.com/lineitems/scores?param=1",
            scopes=svc.LTIA_SCOPES,
            json={
                "scoreMaximum": 1,
                "scoreGiven": sentinel.score,
                "userId": sentinel.user_id,
                "timestamp": "2022-04-04T00:00:00+00:00",
                "activityProgress": "Completed",
                "gradingProgress": "FullyGraded",
            },
            headers={"Content-Type": "application/vnd.ims.lis.v1.score+json"},
        )
        assert response == ltia_http_service.request.return_value

    def test_record_result_raises_ExternalRequestError(self, svc, ltia_http_service):
        ltia_http_service.request.side_effect = ExternalRequestError(
            response=Mock(status_code=500)
        )

        with pytest.raises(ExternalRequestError):
            svc.record_result(sentinel.user_id, sentinel.score)

    @pytest.mark.parametrize(
        "code,text",
        [
            (400, "User could not be found:"),
            (403, "User in requested score is not enrolled in the org unit"),
        ],
    )
    def test_record_result_raises_StudentNotInCourse(
        self, svc, ltia_http_service, code, text
    ):
        ltia_http_service.request.side_effect = ExternalRequestError(
            response=Mock(status_code=code, text=text)
        )

        with pytest.raises(StudentNotInCourse):
            svc.record_result(sentinel.user_id, sentinel.score)

    def test_record_result_doesnt_raise_max_submissions(self, svc, ltia_http_service):
        ltia_http_service.request.side_effect = ExternalRequestError(
            response=Mock(
                status_code=422,
                text="maximum number of allowed attempts has been reached",
            )
        )

        response = svc.record_result(sentinel.user_id, sentinel.score)

        assert not response

    def test_create_line_item(self, svc, ltia_http_service):
        response = svc.create_line_item(
            sentinel.resource_link_id,
            sentinel.label,
            sentinel.score_maximum,
        )

        ltia_http_service.request.assert_called_once_with(
            "POST",
            svc.line_item_container_url,
            scopes=svc.LTIA_SCOPES,
            json={
                "scoreMaximum": sentinel.score_maximum,
                "label": sentinel.label,
                "resourceLinkId": sentinel.resource_link_id,
            },
            headers={"Content-Type": "application/vnd.ims.lis.v2.lineitem+json"},
        )
        assert response == ltia_http_service.request.return_value.json.return_value

    def test_record_result_calls_hook(self, svc, ltia_http_service):
        my_hook = Mock(return_value={"my_dict": 1})

        svc.record_result(sentinel.user_id, score=1.5, pre_record_hook=my_hook)

        my_hook.assert_called_once_with(request_body=Any.dict(), score=1.5)
        ltia_http_service.request.assert_called_once_with(
            "POST",
            "http://example.com/lineitem/scores",
            scopes=svc.LTIA_SCOPES,
            json={"my_dict": 1},
            headers={"Content-Type": "application/vnd.ims.lis.v1.score+json"},
        )

    @pytest.fixture
    def response(self):
        return [
            {
                "id": "https://lms.example.com/context/2923/lineitems/1/results/5323497",
                "scoreOf": "https://lms.example.com/context/2923/lineitems/1",
                "userId": "5323497",
                "resultScore": 0.83,
                "resultMaximum": 1,
                "comment": "This is exceptional work.",
            }
        ]

    @pytest.fixture
    def svc(self, ltia_http_service):
        return LTI13GradingService(
            "http://example.com/lineitem",
            "http://example.com/linesitems",
            ltia_http_service,
        )
