"""API Gateway HTTP API v2 adapter for the existing Flask application."""
import base64
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Response
from bot import app


def handler(event, context):
    http = event['requestContext']['http']
    headers = event.get('headers') or {}
    body = event.get('body') or ''
    payload = base64.b64decode(body) if event.get('isBase64Encoded') else body.encode('utf-8')
    builder = EnvironBuilder(
        path=event.get('rawPath', http.get('path', '/')),
        query_string=event.get('rawQueryString', ''),
        base_url='https://' + event['requestContext']['domainName'],
        method=http['method'], headers=headers, data=payload,
    )
    try:
        environ = builder.get_environ()
        # API Gateway context is trusted; Host/Forwarded headers are caller-controlled.
        query = event.get('rawQueryString', '')
        environ['twilio.external_url'] = (
            'https://' + event['requestContext']['domainName']
            + event.get('rawPath', http.get('path', '/'))
            + ('?' + query if query else '')
        )
        response = Response.from_app(app, environ)
        return {'statusCode': response.status_code,
                'headers': dict(response.headers),
                'body': response.get_data(as_text=True), 'isBase64Encoded': False}
    finally:
        builder.close()
