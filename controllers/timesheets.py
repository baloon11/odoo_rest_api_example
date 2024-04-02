# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from copy import deepcopy
import time
from odoo import http
from odoo.http import request
from .wrappers_and_tools import check_profile  # decorators
from .wrappers_and_tools import successful_response, error_response,str_to_datetime,processing_error_situation, str_to_float  # response wrappers
from .utils import *
_logger = logging.getLogger(__name__)


class TimesheetREST(http.Controller):

    @staticmethod
    def _get_timesheet_input_data(project_id=int(), task_id=int(), kwargs={}):
        project = request.env['project.project'].search([('id', '=', project_id)])
        task = request.env['project.task'].search([('id', '=', task_id)])
        success_response_dict = {'ok': True,
                                 'description': '',
                                 "project": {},
                                 'task': {},
                                 "timesheet": {
                                     "task_go": None,
                                     "duration": None}
                                 }
        task_go = kwargs.get('task_go')
        if task_go:
            task_go = int(float(kwargs.get('task_go')))
            task_go = datetime.fromtimestamp(task_go)

        duration = kwargs.get('duration')
        if duration:
            duration = str_to_float(duration)
        return project, task, success_response_dict, task_go, duration

    @staticmethod
    def _update_timesheet_dict(success_response_dict={},project=None, task=None, timesheet=None, success_text=''):
        success_response_dict['project'] = {"id": project.id}
        success_response_dict['task'] = {"id": task.id}
        # -------
        timesheet_date = str_to_datetime(project=project, task=task, value=timesheet.date)
        success_response_dict['timesheet']['task_go'] = int(time.mktime(timesheet_date.timetuple()))
        success_response_dict['timesheet']['duration'] = timesheet.unit_amount
        # -------
        success_response_dict['description'] = success_text
        return success_response_dict

    @http.route('/api/v1/project/<int:project_id>/task/<int:task_id>/timesheet', methods=['POST'], type='http', auth='none', csrf=False)
    @check_profile
    def timesheet_post(self, profile, method, data, project_id, task_id, **kwargs):
        project, task, success_response_dict, task_go, duration = self._get_timesheet_input_data(project_id=project_id,
                                                                                                 task_id=task_id,
                                                                                                 kwargs=kwargs)
        # ------------check objects block-----------------------------
        if len(project) == 0:
            return error_response(404, {
                'description': 'Project with this id -- {0} does not exist '.format(project_id)})
            return error_response(404)

        elif len(project) > 1:
            return processing_error_situation(
                error_text="Project {} has internal system problems ".format(project.name))

        elif len(task) == 0:
            return error_response(404, {
                'description': 'Task with this id -- {0} does not exist '.format(task_id)})
            return error_response(404)

        elif len(task) > 1:
            return processing_error_situation(
                error_text="Task {} has internal system problems ".format(task.name))
        # ----------------------------------------------------------
        elif method == 'POST':
            try:
                employee = request.env['hr.employee'].search([('user_id', '=', request.session.uid)])
                timesheet = request.env['account.analytic.line'].sudo().create({
                                                                                'task_id': task.id,
                                                                                'name': 'timesheet from app',
                                                                                'date': task_go,
                                                                                'unit_amount': duration,
                                                                                'account_id': project.analytic_account_id.id,
                                                                                'employee_id': employee.id
                                                                                })
                success_text = "Timesheet was created successfully using mob app"
                success_response_dict = self._update_timesheet_dict(success_response_dict=deepcopy(success_response_dict),
                                                                    project=project, task=task,
                                                                    timesheet=timesheet,
                                                                    success_text=success_text)
                return successful_response(201, success_response_dict)
            except Exception as e:
                error_text = "Timesheet {} has internal system problems (creating a timesheet)".format(timesheet.name)
                _logger.error('{0},{1}'.format(error_text, e))
                processing_error_situation(error_text=error_text)

        elif method != 'POST':
            return error_response(403)


    @http.route('/api/v1/project/<int:project_id>/task/<int:task_id>/timesheet/<int:timesheet_id>', methods=['PUT'], type='http', auth='none', csrf=False)
    @check_profile
    def timesheet_put(self, profile, method, data, project_id, task_id, timesheet_id, **kwargs):
        project, task, success_response_dict, task_go, duration = self._get_timesheet_input_data(project_id=project_id,
                                                                                                 task_id=task_id,
                                                                                                 kwargs=kwargs)
        timesheet = request.env['account.analytic.line'].search([('id', '=', timesheet_id)])

        # ------------check objects block-----------------------------
        if len(project) == 0:
            return error_response(404, {
                'description': 'Project with this id -- {0} does not exist '.format(project_id)})
            return error_response(404)

        elif len(project) > 1:
            return processing_error_situation(
                error_text="Project {} has internal system problems ".format(project.name))

        elif len(task) == 0:
            return error_response(404, {
                'description': 'Task with this id -- {0} does not exist '.format(task_id)})
            return error_response(404)

        elif len(task) > 1:
            return processing_error_situation(
                error_text="Task {} has internal system problems ".format(task.name))

        elif len(timesheet) == 0:
            return error_response(404, {
                'description': 'Timesheet with this id -- {0} does not exist '.format(timesheet_id)})
            return error_response(404)

        elif len(timesheet) > 1:
            return processing_error_situation(
                error_text="Timesheet {} has internal system problems ".format(timesheet.name))
        # ----------------------------------------------------------
        elif method == 'PUT':
            try:
                res_dict = {}
                if task_go:
                    res_dict['date'] = task_go
                if duration:
                    res_dict['unit_amount'] = duration


                timesheet.sudo().write(res_dict)
                success_text = "Timesheet was updated successfully using mob app"
                success_response_dict = self._update_timesheet_dict(success_response_dict=deepcopy(success_response_dict),
                                                                    project=project, task=task,
                                                                    timesheet=timesheet,
                                                                    success_text=success_text)
                return successful_response(200, success_response_dict)
            except Exception as e:
                error_text = "Timesheet {} has internal system problems (update a timesheet)".format(timesheet.name)
                _logger.error('{0},{1}'.format(error_text, e))
                processing_error_situation(error_text=error_text)

        elif method != 'PUT':
            return error_response(403)
