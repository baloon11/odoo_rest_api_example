# -*- coding: utf-8 -*-
import logging
import json
from odoo import http
from odoo.http import request
from .wrappers_and_tools import api_auth_set_token  # work with Tokens
from .wrappers_and_tools import error_handler, check_profile  # decorators
from .wrappers_and_tools import DB_NAME
from .wrappers_and_tools import successful_response, error_response  # response wrappers

_logger = logging.getLogger(__name__)


class AuthREST(http.Controller):
    @http.route('/api/v1/auth', methods=['POST'], type='http', auth='none', csrf=False)
    @error_handler
    def singin(self, *args, **kwargs):
        vals = json.loads(request.httprequest.stream.read().decode('utf-8'))
        login = vals.get('login', False)
        password = vals.get('password', False)
        token_dict = api_auth_set_token(login=login, password=password)
        if request.session.authenticate(DB_NAME, login, password, uid=token_dict['user_id']):
            user = request.env['res.users'].sudo().browse(token_dict['user_id'])

            # will  returns
            # {
            # data:{'access_token': access_token,
            # '      expires_in': expires_in,
            #        'user_id': user.id,
            #        'login': user.login},
            # 'ok':True,
            # "description": "successfully authorized"}
            token_dict['login']= user.login
            result_dict = {'data': token_dict,
                           'ok': True,
                           "description": "successfully authorized"}
            return successful_response(200, result_dict)
        else:
            return error_response(401)
