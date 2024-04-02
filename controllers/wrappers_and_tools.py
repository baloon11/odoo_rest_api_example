# -*- coding: utf-8 -*-
import functools
import base64
import werkzeug.wrappers
import pytz
import datetime
import unicodedata
import json
import random
import logging
import base64
import  copy
import traceback
import sys
import os
import hashlib
from datetime import date, timedelta

from odoo import http
from odoo.tools import config
from odoo.http import request
from odoo.exceptions import AccessError, AccessDenied
from odoo import fields


from odoo.modules.registry import Registry
import redis

_logger = logging.getLogger(__name__)

DB_NAME = config.get('db_name')

def get_ir_config_parameter_data():
    access_token_expires_in = config.get('access_token_expires_in')
    redis_host = config.get('redis_host')
    redis_port = config.get('redis_port')
    redis_db = config.get('redis_db')
    redis_password = config.get('redis_password')
    return access_token_expires_in, redis_host, redis_port, redis_db, redis_password

expires_in, redis_host, redis_port, redis_db, redis_password = get_ir_config_parameter_data()

class RedisTokenStore(object):

    def __init__(self, host='localhost', port=6379, db=0, password=None):
        self.rs = redis.StrictRedis(host=host, port=port, db=db, password=password)
        # Connection test
        try:
            res = self.rs.get('foo')
            _logger.info("<REDIS> Successful connect to Redis-server.")
        except:
            _logger.error("<REDIS> ERROR: Failed to connect to Redis-server!")
            print("<REDIS> ERROR: Failed to connect to Redis-server!")

    def save_all_tokens(self, access_token, expires_in,user_id ):
        # refresh_token, refresh_expires_in,
        # access_token
        self.rs.set(access_token,
                    json.dumps({'user_id': user_id}),
                    expires_in
                    )

    def fetch_by_access_token(self, access_token):
        key = access_token
        _logger.info("<REDIS> Fetch by access token.")
        data = self.rs.get(key).decode('utf-8')
        if data:
            return json.loads(data)
        else:
            return None

    def delete_access_token(self, access_token):
        self.rs.delete(access_token)

    def expire_access_token(self, access_token='', time=int()):
        self.rs.expire(access_token, time)

def create_redis_token_store_object():
    try:
        # expires_in, redis_host, redis_port, redis_db, redis_password = get_ir_config_parameter_data()
        if redis_host and redis_port:
            token_store = RedisTokenStore(
                host=redis_host,
                port=int(redis_port),
                db=int(redis_db),
                password=redis_password)
            return token_store
        else:
            error_descrip = "redis_host or redis_port is empty"
            error = 'redis_host_or_redis_port_is_empty'
            _logger.error(error_descrip)
            return error_response(401)
    except:
        error_descrip = "Error in creating token_store object"
        error = 'Error_in_creating_token_store_object'
        _logger.error(error_descrip)
        return error_response(401)

def generate_token(length=40):
    random_data = os.urandom(100)
    hash_gen = hashlib.new('sha512')
    hash_gen.update(random_data)
    return hash_gen.hexdigest()[:length]

def api_auth_set_token(login = '',password = '', uid=None):

    # Empty 'db' or 'login' or 'password:
    if not DB_NAME or not login or not password:
        error_descrip = "Empty value of 'db' or 'login' or 'password'!"
        error = 'empty_db_or_login_or_password'
        _logger.error(error_descrip)
        return error_response(401)

    # Login in Odoo database:
    try:
        request.session.authenticate(DB_NAME, login, password, uid=uid)
    except:
        # Invalid database:
        error_descrip = "Invalid database!"
        error = 'invalid_database'
        _logger.error(error_descrip)
        return error_response(401)

    uid = request.session.uid

    # Odoo login failed:
    if not uid:
        error_descrip = "Odoo User authentication failed!"
        error = 'odoo_user_authentication_failed'
        _logger.error(error_descrip)
        return error_response(401)

    # Generate tokens
    access_token = generate_token()

    # Save all tokens in store
    token_store=create_redis_token_store_object()
    token_store.save_all_tokens(
        access_token=access_token,
        expires_in=expires_in,
        user_id=uid
    )
    _logger.info("Save OAuth2 tokens of user in Redis store...")
    return {
        'token': access_token,
        'expires_in': expires_in,
        'user_id': uid
    }

def check_token():
    # Get access token from http header
    access_token = request.httprequest.headers.get('ACCESS_TOKEN')
    if not access_token:
        error_descrip = "No access token was provided in request header!"
        error = 'no_access_token'
        _logger.error(error_descrip)
        raise AccessDenied

    # Validate access token
    token_store = create_redis_token_store_object()
    access_token_data = token_store.fetch_by_access_token(access_token)
    if not access_token_data:
        error_descrip = "Token is expired or invalid!"
        error = 'expired_or_invalid_token'
        _logger.error(error_descrip)
        raise AccessDenied
    #extend the life of the token
    token_store.expire_access_token( access_token=access_token, time=int(expires_in))
    # Set session UID from current access token
    request.session.uid = access_token_data['user_id']
    request.uid = request.session.uid


def check_int_and_zero(val=None, error_text=''):
    try:
        return int(val) if val else False
    except ValueError as e:
        _logger.error(error_text or e)
        return False

def process_data(request_data):
    processed_data = {}
    for key,value in request_data.items():
        if value == 'undefined':
            value = None
        processed_data[key] = value
    return processed_data

def check_profile(func):
    #check profile_id and token
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            check_token()
        except Exception as e:
            _logger.error(e)
            return error_response(401)
        if not request.httprequest.headers.get('PROFILE_ID', False):
            return error_response(401)
        user = request.env['res.users'].browse(check_int_and_zero(request.httprequest.headers['PROFILE_ID']))
        # profile = request.env['res.partner'].sudo().browse(196)
        # if len(profile) == 0 or not profile.proof_email:
        if len(user) == 0:
            return error_response(401)
        data = {}
        stream = request.httprequest.stream.read().decode('utf-8')
        if len(stream) > 0:
            data = process_data(json.loads(stream))
        if data:
            data = process_data(data)
            kwargs.update(data)
            # kwargs = data
        if kwargs:
            kwargs = process_data(kwargs)
            data.update(kwargs)
            # data = kwargs
        try:
            return func(self, user, request.httprequest.method, data, *args, **kwargs)
        except Exception as e:
            _logger.error(e)
            return error_response(401)
    return wrapper


def error_handler(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except AccessError as e:
            _logger.error(e)
            return error_response(401)
        except Exception as e:
            _logger.error(e)
            return error_response(200, {'ok': False,"description": 'there are system problems for the authorization process'})
    return wrapper


def successful_response(status, data=None):
    if data is None:
        data = {}
    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        # headers=['Access-Control-Allow-Origin: *'],
        response=json.dumps(data),
    )


def error_response(status, data=None):
    if data is None:
        data = {}
    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        # headers = None,
        response=json.dumps(data),
    )


def record_to_json(record, fields_list):
    result = {}
    for field in fields_list:
        if type(field) == str:
            val = record[field]
            if hasattr(val, 'id'):
                val = val.id
            if record._name == 'ir.attachment' and field == 'db_datas':

                # In the current time there are two variants for storing files using ir.attachment table:
                # 1. as a binary string (in the column db_datas ). This variant we use for store files that was received  from api.
                # 2. as a path file (in the column  store_fname ). This variant we use for store files that was received  from  odoo backoffice.
                # This two variants are processed in this block of the  code.
                try:
                    # only for attached files stored in the binary string in the column db_datas
                    result[field] = record[field].decode('utf-8')
                except:
                    filename_query = "SELECT store_fname FROM ir_attachment WHERE id = {0};".format(record.id)
                    request.env.cr.execute(filename_query)
                    filename = request.env.cr.fetchone()[0]
                    full_file_path = "{0}/filestore/{1}/{2}".format(config.get('data_dir'), DB_NAME, filename)
                    with open(full_file_path, 'rb') as f:
                        result[field] =  base64.b64encode(f.read()).decode('utf-8')
            else:
                result[field] = val if type(val) == bool or (val or '0' in str(val)) else ""
                # if value is boolean instance  or None  it will change to  empty string ""
                if isinstance(result[field], bool):
                    result[field] = ""
        else:
            f_name, f_list = field[0], field[1]

            if type(f_list) == list:
                f_list = f_list[0]
                result[f_name] = []
                recs = record[f_name]
                for rec in recs:
                    result[f_name] += [record_to_json(rec, f_list)]
                if len(result[f_name]) == 0:
                    result[f_name] = ""
            else:
                rec = record[f_name]
                if type(f_list) == str:
                    f_list = (f_list,)
                result[f_name] = record_to_json(rec, f_list)
    return result


def processing_error_situation(error_text=str()):
    _logger.error(error_text)
    error_response(200, {'ok': False,
                         'description': error_text})


def str_to_bool(input_str):
    try:
        return True if input_str.lower() == 'true' else False
    except Exception as e:
        error_text = 'Error in convert str to boolean'
        _logger.error('{0},{1}'.format(error_text+'(function str_to_bool)', e))
        processing_error_situation(error_text=error_text)

def str_to_float(input_str):
    try:
        return float(input_str)
    except Exception as e:
        error_text = 'Error in convert str to float'
        _logger.error('{0},{1}'.format(error_text+'(function str_to_float)', e))
        processing_error_situation(error_text=error_text)




def str_to_datetime(project=None, task=None, value=str()):
    try:
        return fields.Datetime.from_string(value)
    except ValueError as v_e:
        error_text = 'incorrect data format for deadline date in in task {0} (project{1})'.format(task.name,
                                                                                                  project.name)
        _logger.error('{0},{1}'.format(error_text, v_e))
        processing_error_situation(error_text=error_text)
    except Exception as e:
        error_text = ' deadline date in in task {0} (project{1} -- general error {2})'.format(task.name,
                                                                                               project.name, e)

        _logger.error('{0},{1}'.format(error_text, e))
        processing_error_situation(error_text=error_text)

