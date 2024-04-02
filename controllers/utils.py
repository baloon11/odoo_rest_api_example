# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)


def system_error_message(**kwargs):
    '''
    :param kwargs:{'project_name':str,'task_name':str,'additional_message':additional_message}
    :return: prepared  error message
    '''
    task_name = kwargs.get('task_name')
    project_name = kwargs.get('project_name')
    additional_message = kwargs.get('additional_message')
    res_message = ''
    if not project_name:
        res_message = 'a project with that name does not exist'
    elif project_name and not task_name:
        res_message = 'the project {} has internal system problems'.format(project_name)
    elif task_name and project_name:
        res_message = 'the project {{0}} or the task {{1}} has internal system problems'.format(project_name, task_name)
    if additional_message:
        res_message += res_message
    return res_message



































