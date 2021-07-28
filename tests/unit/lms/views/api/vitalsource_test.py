import pytest

from lms.views.api.vitalsource import VitalSourceAPIViews

pytestmark = pytest.mark.usefixtures("http_service")


class TestVitalSourceAPIViews:
    def test_book_info_returns_metadata(
        self, pyramid_request, vitalsource_service, api_book_info
    ):
        vitalsource_service.book_info.return_value = api_book_info

        pyramid_request.matchdict["book_id"] = "BOOKSHELF-TUTORIAL"

        metadata = VitalSourceAPIViews(pyramid_request).book_info()

        assert metadata == {
            "id": api_book_info["vbid"],
            "title": api_book_info["title"],
            "cover_image": api_book_info["resource_links"]["cover_image"],
        }

    def test_table_of_contents_returns_chapter_data(
        self, pyramid_request, vitalsource_service, api_book_table_of_contents
    ):
        vitalsource_service.book_toc.return_value = api_book_table_of_contents

        pyramid_request.matchdict["book_id"] = "BOOKSHELF-TUTORIAL"
        toc = VitalSourceAPIViews(pyramid_request).table_of_contents()
        assert toc == api_book_table_of_contents["table_of_contents"]

    @pytest.fixture
    def api_book_table_of_contents(self):
        return {
            "table_of_contents": [
                {"title": "chapter 1", "cfi": "XXXX", "page": "1"},
                {"title": "chapter 2", "cfi": "XXXX", "page": "2"},
                {"title": "chapter 3", "cfi": "XXXX", "page": "3"},
                {"title": "chapter 4", "cfi": "XXXX", "page": "4"},
            ]
        }

    @pytest.fixture
    def api_book_info(self):
        return {
            "vbid": "VBID",
            "title": "BOOK  TITLE",
            "resource_links": {
                "cover_image": "http://cover_image/url",
            },
        }
