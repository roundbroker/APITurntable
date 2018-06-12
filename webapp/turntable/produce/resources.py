# encoding: utf-8

from . import blueprint

from turntable.visitor_business import VisitorBusiness
from turntable.exceptions import BusinessException
from turntable.models import WebCall, WebCallRequestHttp11
from flask import request, g, session, redirect, url_for, current_app
from urllib.parse import urlparse
import json
import hashlib

supported_http_methods = ('GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'PATCH')

@blueprint.route('/<string:producer_uuid>', methods=supported_http_methods)
@blueprint.route('/<string:producer_uuid>/<path:extra_path>', methods=supported_http_methods)
def produce(producer_uuid, extra_path=None):
    app = current_app
    flask_error_400 = json.dumps({'success':False}), 400

    app.logger.info("Handling new request for producer=<{}>".format(producer_uuid))

    try:
        # Retrieve the raw query part of the query
        args = urlparse(request.url).query

        username = "turntable"
        gravatar_url = "https://www.gravatar.com/avatar/{}".format(hashlib.md5(username.encode('utf-8')).hexdigest())

        # lets transform this message into a mattermost query
        payload = {
            "channel": "platform-changes",
            "username": username,
            "icon_url": gravatar_url,
            "text": request.get_data(as_text=True)
        }

        headers = {k: v for k, v in request.headers.items()}
        headers['Content-Type'] = 'application/json'

        httpreq = WebCallRequestHttp11(
            method=request.method,
            headers={k: v for k, v in request.headers.items()},
            cookies=request.cookies,
            body=payload,
            source_ip=request.remote_addr,
            source_url=request.url,
            extra_path=extra_path,
            args=args)

        VisitorBusiness().publish(producer_uuid, WebCall(httpreq))
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

    except BusinessException as e:
        app.logger.info("Error while handling the request for producer=<{}>: {}".format(producer_uuid, e))
        return flask_error_400

    except Exception as e:
        app.logger.info("Error while handling the request for producer=<{}>: {}".format(producer_uuid, e))
        return flask_error_400
