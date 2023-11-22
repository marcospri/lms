from datetime import timedelta
from typing import Callable
from urllib.parse import parse_qs, urlparse

from lms.models import EmailUnsubscribe
from lms.services.exceptions import ExpiredJWTError, InvalidJWTError
from lms.services.jwt import JWTService
from lms.services.upsert import bulk_upsert
from lms.services.user_preferences import UserPreferencesService


class UnrecognisedURLError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


KEY_PREFIX = "instructor_email_digests.days."


class EmailPreferencesService:
    DAY_KEYS = [f"{KEY_PREFIX}{day}" for day in [1, 2, 3, 4, 5, 6, 7]]

    def __init__(  # pylint:disable=too-many-arguments
        self,
        db,
        secret: str,
        route_url: Callable,
        jwt_service: JWTService,
        user_preferences_service: UserPreferencesService,
    ):
        self._db = db
        self._secret = secret
        self._route_url = route_url
        self._jwt_service = jwt_service
        self._user_preferences_service = user_preferences_service

    def unsubscribe_url(self, h_userid, tag):
        """Return an email unsubscribe URL for the given h_userid.

        The URL will contain a scoped and time-limited authentication token for
        the given h_userid in a query param.
        """
        token = self._generate_token(h_userid, tag)
        return self._route_url("email.unsubscribe", _query={"token": token})

    def preferences_url(self, h_userid):
        """Return a URL for the email preferences page for the given h_userid.

        The URL will contain a scoped and time-limited authentication token for
        the given h_userid in a query param.
        """
        token = self._generate_token(h_userid)
        return self._route_url("email.preferences", _query={"token": token})

    def unsubscribe(self, token):
        """Create a new entry in EmailUnsubscribe based on the email and tag encode in `token`."""
        data = self._decode_token(token)

        bulk_upsert(
            self._db,
            model_class=EmailUnsubscribe,
            values=[data],
            index_elements=["h_userid", "tag"],
            update_columns=["updated"],
        )

    def h_userid(self, url: str) -> str:
        """Return the decoded h_userid from the given URL.

        `url` should be a URL generated by one of this service's methods above.

        :raises UnrecognisedURLError: if the given URL does not appear to be
            one generated by this service
        :raises InvalidTokenError: if the URL's authentication token is invalid
            or has expired
        """
        try:
            token = parse_qs(urlparse(url).query)["token"][0]
        except (KeyError, ValueError) as err:
            raise UnrecognisedURLError() from err

        try:
            return self._decode_token(token)["h_userid"]
        except (ExpiredJWTError, InvalidJWTError) as err:
            raise InvalidTokenError() from err

    def get_preferences(self, h_userid) -> dict:
        """Return h_userid's email preferences.

        Changes to the returned dict will *not* be automatically saved to
        the DB: you must call set_preferences() below.
        """
        preferences = self._user_preferences_service.get(h_userid)

        for key in self.DAY_KEYS:
            preferences.preferences.setdefault(key, True)

        return {key: preferences.preferences[key] for key in self.DAY_KEYS}

    def set_preferences(self, h_userid, new_preferences):
        """Create or update h_userid's email preferences."""
        self._user_preferences_service.set(
            h_userid,
            {
                key: new_preferences[key]
                for key in new_preferences
                if key in self.DAY_KEYS
            },
        )

    def _generate_token(self, h_userid, tag=None):
        payload = {"h_userid": h_userid}

        if tag is not None:
            payload["tag"] = tag

        return self._jwt_service.encode_with_secret(
            payload, self._secret, lifetime=timedelta(days=30)
        )

    def _decode_token(self, token):
        return self._jwt_service.decode_with_secret(token, self._secret)


def factory(_context, request):
    return EmailPreferencesService(
        request.db,
        secret=request.registry.settings["jwt_secret"],
        route_url=request.route_url,
        jwt_service=request.find_service(iface=JWTService),
        user_preferences_service=request.find_service(UserPreferencesService),
    )
