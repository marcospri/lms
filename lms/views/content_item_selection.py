from pyramid.view import view_config
from lms.util.lti_launch import lti_launch
from lms.util.lti_launch import lti_launch
from lms.config import env_setting
from lms.util.lti_launch import get_application_instance


@view_config(
    route_name='content_item_selection',
    renderer='lms:templates/content_item_selection/new_content_item_selection.html.jinja2',
    request_method='POST')
@lti_launch
def content_item_selection(request, _):
    """
    Render the form that teachers see to configure the module item.

    This view is only used for lms's that support link selection
    """
    consumer_key = request.params['oauth_consumer_key']
    application_instance = get_application_instance(request.db, consumer_key)
    return {
        'content_item_return_url': request.params['content_item_return_url'],
        'lti_launch_url': request.route_url('lti_launches'),
        'form_fields': {
            'lti_message_type': 'ContentItemSelection',
            'lti_version': request.params['lti_version'],
            'oauth_version': request.params['oauth_version'],
            'oauth_nonce': request.params['oauth_nonce'],
            'oauth_consumer_key': request.params['oauth_consumer_key'],
            'oauth_signature_method': request.params['oauth_signature_method'],
            'oauth_signature': request.params['oauth_signature']
        },
        'google_client_id': env_setting('GOOGLE_CLIENT_ID'),
        'google_developer_key': env_setting('GOOGLE_DEVELOPER_KEY'),
        'google_app_id': env_setting('GOOGLE_APP_ID'),
        'lms_url': application_instance.lms_url
    }
