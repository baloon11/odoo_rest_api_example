# -*- coding: utf-8 -*-
import logging
from bs4 import BeautifulSoup
from odoo import http
from odoo.http import request
from .wrappers_and_tools import check_profile  # decorators
from .wrappers_and_tools import successful_response, error_response,str_to_datetime,processing_error_situation, str_to_float  # response wrappers
from .wrappers_and_tools import record_to_json
from .utils import *
_logger = logging.getLogger(__name__)

tasks_columns_json = (
    'id',
    'description',
    ('tag_ids', [('id', 'name')]),
    ('timesheet_ids', [('id',
                        'name',
                        'date',
                        'unit_amount',
                        ('user_id', (('partner_id', ('name',),),))
                        )]
     ),

    ('incidents', [('id',
                    'name',
                    'task_number',
                    ('project_id', ('name',)),
                    'progress',
                    'description',
                    ('creator_id', ('id', ('partner_id', ('name',)))),
                    ('task_id', ('name',))
                    )]
     )
)


class TaskREST(http.Controller):

    @staticmethod
    def _get_sprint_with_current_task(curr_task=None):
        for curr_backlog in request.env['project.scrum.product.backlog'].search([]):
            if curr_task.id in curr_backlog.tasks_id.ids:
                return curr_backlog.sprint_id
            else:
                continue
        error_text = 'The task {0}(id={1}) is not tied to any sprint'.format(curr_task.name, curr_task.id)
        return processing_error_situation(error_text=error_text)


    @http.route('/api/v1/project/<int:project_id>/task/<int:task_id>', methods=['GET', 'PUT'], type='http', auth='none', csrf=False)
    @check_profile
    def task(self, profile, method, data, project_id, task_id, **kwargs):
        task = request.env['project.task'].search([('id', '=', task_id)])
        project = request.env['project.project'].search([('id', '=', project_id)])
#------------check objects block-----------------------------
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
#----------------------------------------------------------
        else:
            success_response_dict = {'ok': True,
                                     'description': '',
                                     "project": {},
                                     'task': {}
                                     }
            if method == 'GET':
                filter = data.get('filter')
                if filter == 'widget':
                    try:
                        success_response_dict['project'] = {"id": project.id}
                        #----------task dict------------
                        success_response_dict['task']['id'] = task.id
                        success_response_dict['task']['column'] = task.stage_id.name
                        success_response_dict['task']['kanban_state'] = task.kanban_state
                        success_response_dict['task']['deadline'] = task.date_deadline
                        #star marked
                        success_response_dict['task']['status_in_work'] = True if task.priority == 1 else False
                        success_response_dict['task']['initially_planned_hours'] = task.planned_hours
                        success_response_dict['task']['already_marked_time'] = task.effective_hours
                        #-------------------------------
                        success_text = "receiving task data ({}) using 'filter':'widget' was a success".format(task.name)
                        success_response_dict['description'] = success_text
                        return successful_response(200, success_response_dict)
                    except Exception as e:
                        error_text = "Task {} has internal system problems  (task-'filter':'widget')".format(task.name)
                        _logger.error('{0},{1}'.format(error_text, e))
                        processing_error_situation(error_text=error_text)
                elif filter == 'full':
                    try:
                        success_response_dict['project'] = {"id": project.id}
                        #-------------------------------
                        success_response_dict['task'] = record_to_json(task,tasks_columns_json)
                        #------------add data  fields---------------------------------
                        success_response_dict['task']['creator_by'] = task.creator_id.partner_id.name
                        success_response_dict['task']['progress'] = round(task.progress)
                        success_response_dict['task']['description'] = BeautifulSoup(task.description,features="lxml").get_text()

                        #------------add sprint block---------------------------------
                        success_response_dict['task']['sprint']={}
                        curr_sprint = self._get_sprint_with_current_task(curr_task=task)
                        success_response_dict['task']['sprint']['id'] =curr_sprint.id
                        success_response_dict['task']['sprint']['name'] = curr_sprint.name
                        success_response_dict['task']['sprint']['release'] = curr_sprint.release_id.name

                        # -----------reformat of the timesheets block ----------------
                        for curr_timesheet in success_response_dict['task']['timesheet_ids']:
                            curr_timesheet['employee']=curr_timesheet['user_id']['partner_id']['name']
                            del curr_timesheet['user_id']

                            curr_timesheet['description'] = curr_timesheet['name']
                            del curr_timesheet['name']

                            curr_timesheet['duration'] = curr_timesheet['unit_amount']
                            del curr_timesheet['unit_amount']
                        # -----------reformat of the incidents block ----------------
                        for curr_incident in success_response_dict['task']['incidents']:
                            curr_incident['progress'] = round(curr_incident['progress'])

                            curr_incident['homework']=curr_incident['name']
                            del curr_incident['name']

                            curr_incident['project'] = curr_incident['project_id']['name']
                            del curr_incident['project_id']

                            curr_incident['task'] = '[{0}] {1}'.format(curr_incident['task_number'],
                                                                       curr_incident['task_id']['name'])
                            del curr_incident['task_id']
                            del curr_incident['task_number']

                            curr_incident['description'] = BeautifulSoup(curr_incident['description'],
                                                                         features="lxml").get_text()

                            curr_incident['creator_by'] = curr_incident['creator_id']['partner_id']['name']
                            curr_incident['creator_id'] = curr_incident['creator_id']['id']
                        #---------------------------------------------------------------
                        success_text = "".format()
                        success_response_dict['description'] = success_text
                        return successful_response(200, success_response_dict)
                    except Exception as e:
                        error_text = "".format()
                        _logger.error('{0},{1}'.format(error_text, e))
                        processing_error_situation(error_text=error_text)
                else:
                    return error_response(403)
            elif method == 'PUT':
                column_id = data.get('column_id')
                kanban_state = data.get('kanban_state')
                planned_hours = data.get('initially_planned_hours')

                if column_id:
                    try:
                        success_response_dict['project'] = {"id": project.id}
                        #-------------------------------
                        success_response_dict['task']['id'] = task.id
                        # works only as raw sql request
                        update_col_request = 'UPDATE project_task SET stage_id = {0} WHERE id = {1};'.format(column_id,
                                                                                                             task.id)
                        request._cr.execute(update_col_request)
                        success_response_dict['task']['column_id'] = task.stage_id.id
                        #-------------------------------
                        success_text = "moving task ({0}) to a column {1} was successful".format(task.name,task.stage_id.id)
                        success_response_dict['description'] = success_text
                        return successful_response(200, success_response_dict)
                    except Exception as e:
                        error_text = "the task {} has internal system problems (moving task to another column)".format(task.name)
                        _logger.error('{0},{1}'.format(error_text, e))
                        processing_error_situation(error_text=error_text)

                elif kanban_state:
                    try:
                        success_response_dict['project'] = {"id": project.id}
                        #-------------------------------
                        success_response_dict['task']['id'] = task.id
                        task.sudo().write({"kanban_state": kanban_state})
                        success_response_dict['task']['kanban_state'] = task.kanban_state
                        #-------------------------------
                        success_text = "{0}: task status change was successful (new status:{1})".format(task.name,task.kanban_state)
                        success_response_dict['description'] = success_text
                        return successful_response(200, success_response_dict)
                    except Exception as e:
                        error_text = "Task {} has internal system problems (changing status)".format(task.name)
                        _logger.error('{0},{1}'.format(error_text, e))
                        processing_error_situation(error_text=error_text)

                elif planned_hours:
                    try:
                        success_response_dict['project'] = {"id": project.id}
                        #-------------------------------
                        success_response_dict['task']['id'] = task.id
                        task.sudo().write({"planned_hours": str_to_float(planned_hours)})
                        success_response_dict['task']['initially_planned_hours'] = task.planned_hours
                        #-------------------------------
                        success_text = "{0}:task planned_hours change was successful (new planned_hours:{1})".format(task.name,task.planned_hours)
                        success_response_dict['description'] = success_text
                        return successful_response(200, success_response_dict)
                    except Exception as e:
                        error_text = "Task {} has internal system problems (changing planned_hours)".format(task.name)
                        _logger.error('{0},{1}'.format(error_text, e))
                        processing_error_situation(error_text=error_text)

                elif not all([column_id, kanban_state, planned_hours]):
                    return error_response(403)
            else:
                return error_response(403)
