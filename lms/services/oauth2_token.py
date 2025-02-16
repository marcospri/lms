import datetime
from functools import lru_cache

from sqlalchemy.orm.exc import NoResultFound

from lms.models import OAuth2Token
from lms.models.oauth2_token import Service
from lms.services.exceptions import OAuth2TokenError


class OAuth2TokenService:
    """Save and retrieve OAuth2Tokens from the DB."""

    def __init__(self, db, application_instance, user_id):
        """
        Return a new TokenStore.

        :param db: the SQLAlchemy session
        :param application_instance: the ApplicationInstance to use for tokens
        :param user_id: the LTI user ID to user for tokens
        """
        self._db = db
        self._application_instance = application_instance
        self._user_id = user_id

    def save(self, access_token, refresh_token, expires_in, service=Service.LMS):
        """
        Save an OAuth 2 token to the DB.

        If there's already an OAuth2Token for the user's consumer key and user
        ID then overwrite its values. Otherwise create a new OAuth2Token and
        add it to the DB.
        """
        try:
            oauth2_token = self.get(service)
        except OAuth2TokenError:
            oauth2_token = OAuth2Token(
                application_instance=self._application_instance,
                user_id=self._user_id,
                service=service,
            )
            self._db.add(oauth2_token)

        oauth2_token.access_token = access_token
        oauth2_token.refresh_token = refresh_token
        oauth2_token.expires_in = expires_in
        oauth2_token.received_at = datetime.datetime.utcnow()

    @lru_cache(maxsize=1)
    def get(self, service=Service.LMS):
        """
        Return the user's saved OAuth 2 token from the DB.

        :raise OAuth2TokenError: if we don't have an OAuth 2 token for the user
        """
        try:
            return (
                self._db.query(OAuth2Token)
                .filter_by(
                    application_instance=self._application_instance,
                    user_id=self._user_id,
                    service=service,
                )
                .one()
            )
        except NoResultFound as err:
            raise OAuth2TokenError(
                "We don't have an OAuth 2 token for this user"
            ) from err


def oauth2_token_service_factory(_context, request, user_id: str | None = None):
    return OAuth2TokenService(
        request.db,
        request.lti_user.application_instance,
        user_id or request.lti_user.user_id,
    )
