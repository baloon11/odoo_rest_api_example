# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from odoo import http
from odoo.http import request
from .wrappers_and_tools import check_profile  # decorators
from .wrappers_and_tools import successful_response, error_response,str_to_datetime,processing_error_situation  # response wrappers
from .wrappers_and_tools import record_to_json
from .utils import *

_logger = logging.getLogger(__name__)

project_tasks_columns_json = ('id',
                              ('tasks', [('id', 'name')]),
                              ('type_ids', [('id', 'name')])
                              )

class ProjectREST(http.Controller):

    @http.route('/api/v1/project', methods=['GET'], type='http', auth='none', csrf=False)
    @check_profile
    def check_project(self, profile, method, data, **kwargs):
        if method == 'GET':
            try:
                project_name = kwargs.get('name')
                project = request.env['project.project'].search([('name', '=', project_name)])
                if project:
                    response_dict = {'name': project.name, 'id': project.id}
                    success_text = "Project {} exists".format(project.name)
                    return successful_response(200, {'ok': True, 'description': success_text, "project": response_dict})
                else:
                    return error_response(404, {'description': '{0}, project name:{1}'.format(system_error_message(),
                                                                                              project_name)})
            except Exception as e:
                _logger.error('{0},{1}'.format(project.id, e))
                return processing_error_situation(error_text=system_error_message(project_name=project.name))
        else:
            return error_response(403)

    @staticmethod
    def _compute_project_tasks_data(project=None, filtered_tasks=None, future_date_after_3days=None):
        numbers_of_tasks = len(filtered_tasks)

        # how many tasks has one or more timesheets
        started_tasks = len(filtered_tasks.filtered(lambda task: len(task.timesheet_ids) > 0))

        # the number of tasks in which the deadline will arrive earlier than in 3 days
        deadline_tasks = filtered_tasks.filtered(
            lambda task: bool(task.date_deadline) != False and
                         str_to_datetime(project=project, task=task,
                                         value=task.date_deadline) < future_date_after_3days)
        deadline_tasks_count = len(deadline_tasks)
        return numbers_of_tasks, started_tasks, deadline_tasks_count

    @staticmethod
    def _get_backlog_sprint_with_current_task(curr_task=None):
        for curr_backlog in request.env['project.scrum.product.backlog'].search([]):
            if curr_task.id in curr_backlog.tasks_id.ids:
                return curr_backlog.sprint_id.id
            else:
                continue
        error_text = 'The task {0}(id={1}) is not tied to any backlog and any sprint'.format(curr_task.name,
                                                                                             curr_task.id)
        return processing_error_situation(error_text=error_text)


    @http.route('/api/v1/project/<int:project_id>', methods=['GET', 'PUT'], type='http', auth='none', csrf=False)
    @check_profile
    def project(self, profile, method, data, project_id, **kwargs):
        project = request.env['project.project'].search([('id', '=', project_id)])
# ------------check objects block-----------------------------
        if len(project) == 0:
            return error_response(404, {
                'description': 'Project with this id -- {0} does not exist '.format(project_id)})
            return error_response(404)

        elif len(project) > 1:
            return processing_error_situation(
                error_text="Project {} has internal system problems ".format(project.name))
# ------------------------------------------------------------
        else:
            if method == 'GET':
                scrum_project_filter = data.get('scrum_project')
                if scrum_project_filter == None:
                    return error_response(403)

                filter = data.get('filter')
                if filter == 'widget':
                    try:
                        now = datetime.now()
                        future_date_after_3days = now + timedelta(days=3)
                        # find all current sprint ids
                        current_sprint_ids = request.env['project.scrum.sprint'].search([('date_start', '<=', now.date()),
                                                                                         ('date_stop', '>=', now.date())
                                                                                         ]).ids
                        # RecordSet of Tasks objects for the current project and the current user
                        tasks = request.env['project.task'].search([('project_id', '=', project.id),
                                                                    ('user_id', '=', profile.id)
                                                                    ])
                        filtered_tasks = tasks.filtered(lambda task: task.stage_id.name in ["Future", "In progress"])

                        if scrum_project_filter == 'True':
                            # task filtration for current sprints
                            filtered_tasks = filtered_tasks.filtered(
                                lambda curr_task:
                                self._get_backlog_sprint_with_current_task(curr_task=curr_task) in current_sprint_ids)

                        numbers_of_tasks, started_tasks, deadline_tasks = self._compute_project_tasks_data(project=project,
                                                                                                           filtered_tasks=filtered_tasks,
                                                                                                           future_date_after_3days=future_date_after_3days)
                        response_dict = {"id": project.id,
                                         "numbers_of_tasks": numbers_of_tasks,
                                         # "numbers_of_tasks_current_sprint": int,
                                         "deadline_tasks": deadline_tasks,
                                         "started_tasks": started_tasks}
                        success_text = "receiving project data ({}) using 'filter':'widget' was a success".format(project.name)
                        return successful_response(200, {'ok': True, 'description': success_text, "project": response_dict})
                    except Exception as e:
                        error_text = "Project {} has internal system problems (project-'filter':'widget')".format(project.name)
                        _logger.error('{0},{1}'.format(error_text, e))
                        processing_error_situation(error_text=error_text)
                elif filter == 'tasks_columns':
                    try:
                        response_dict = record_to_json(project, project_tasks_columns_json)
                        response_dict['columns'] = response_dict['type_ids']
                        del response_dict['type_ids']
                        # return successful_response(200, response_dict) # доделать
                        success_text = "receiving project data ({}) using 'filter':'id_tasks' was a success".format(project.name)
                        return successful_response(200, {'ok': True, 'description': success_text, "project": response_dict})
                    except Exception as e:
                        error_text = "Project {} has internal system problems (project-'filter':'id_tasks')".format(project.name)
                        _logger.error('{0},{1}'.format(error_text, e))
                        processing_error_situation(error_text=error_text)
                else:
                    return error_response(403)

            elif method == 'PUT':
                delete_from_mobile_app = kwargs.get('delete_from_mobile_app')
                if delete_from_mobile_app:
                    try:
                        request.env['kiiver_mobile.delete_log'].sudo().create({'user_id': profile.id,
                                                                               'project_id': project.id
                                                                               })
                        response_dict = {'name': project.name, 'id': project.id}
                        success_text = "The project {} is not displayed in the mobile application now".format(project.name)
                        return successful_response(200, {'ok': True, 'description': success_text, "project": response_dict})
                    except Exception as e:
                        error_text = "Error. The project {} is still displayed in the mobile application".format(
                            project.name)
                        _logger.error('{0},{1}'.format(error_text, e))
                        processing_error_situation(error_text=error_text)
                else:
                    return error_response(403)
            else:
                return error_response(403)
