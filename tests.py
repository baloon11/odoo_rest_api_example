# -*- coding: utf-8 -*-
from datetime import datetime
import time
import json
import requests
import os
# from random import *
# import datetime
import copy
import logging

_logger = logging.getLogger(__name__)

DEFAULT_LOGIN = 'nikita.vorobyov@1000geeks.com'
DEFAULT_PASSWORD = 'nikita.vorobyov@1000geeks.com'

DEFAULT_PROJECT_ID = '4'

DEFAULT_PROJECT_NAME = 'App Mobile'

DEFAULT_TASK_ID = '58'  # name:Task 1
NEW_COLUMN_ID = 5  # Specification col
DEFAULT_TIMESHEET_ID = '83'

host = 'http://localhost:8069'

def singin(login='', password=''):
    entry_data = {'login': login, 'password': password}
    response_dict = requests.post(host + '/api/v1/auth',data=json.dumps(entry_data)).json()
    # response_dict = requests.post(host + '/api/v1/auth', data=entry_data)#.json()
    response_data = response_dict.get('data')
    result_dict = (response_data.get('token'),
                   response_data.get('user_id'),
                   response_data.get('expires_in'),
                   response_data.get('login'),
                   response_dict.get('description'))
    if not any(result_dict):
        _logger.warning('Error singin {0},{1}'.format(response_dict.get('profile_id'), response_dict.get['login'], e))
    return result_dict


# -------------------------------
def project_get_check(name=''):
    print(
        requests.get(host + '/api/v1/project?name={0}'.format(name), headers=headers).json()
    )


def project_get_filter_tasks_columns(project_id='', scrum_project=bool()):
    project_id = DEFAULT_PROJECT_ID if not project_id else project_id
    # params = {"scrum_project": scrum_project,
    #           "filter": "tasks_columns"},
    curr_host = host + '/api/v1/project/{0}?scrum_project={1}&filter={2}'.format(project_id,
                                                                            scrum_project,
                                                                            "tasks_columns")
    # curr_host = host + '/api/v1/project/{0}'.format(project_id)

    response = requests.get(curr_host, headers=headers)
    print(response.json())
    print(response.status_code)


def project_get_filter_widget(project_id='', scrum_project=bool()):
    project_id = DEFAULT_PROJECT_ID if not project_id else project_id
    curr_host = host + '/api/v1/project/{0}?scrum_project={1}&filter={2}'.format(project_id,
                                                                                 scrum_project,
                                                                                 "widget")
    response = requests.get(curr_host, headers=headers)
    print(response.json())
    print(response.status_code)


def project_put(project_id=''):
    project_id = DEFAULT_PROJECT_ID if not project_id else project_id
    data = {"delete_from_mobile_app": True}
    response = requests.put(host + '/api/v1/project/{}'.format(project_id), headers=headers, data=data)
    print(response.json())
    print(response.status_code)

# -------------------------------
def task_get_filter_widget(project_id='', task_id=''):
    curr_host = host + '/api/v1/project/{0}/task/{1}?filter={2}'.format(project_id, task_id, "widget")
    response = requests.get(curr_host, headers=headers)
    print(response.json())
    print(response.status_code)

def task_get_filter_full(project_id='', task_id=''):
    curr_host = host + '/api/v1/project/{0}/task/{1}?filter={2}'.format(project_id, task_id, "full")
    response = requests.get(curr_host, headers=headers)
    print(response.json())
    print(response.status_code)


def task_put_column_id(project_id=None, task_id=None, column_id=None):
    data = {"column_id": column_id}
    curr_host = host + '/api/v1/project/{0}/task/{1}'.format(project_id, task_id)
    response = requests.put(curr_host, data=data, headers=headers)
    print(response.json())
    print(response.status_code)

def task_put_kanban_state(project_id=None, task_id=None, kanban_state=None):
    data = {"kanban_state": kanban_state}
    curr_host = host + '/api/v1/project/{0}/task/{1}'.format(project_id, task_id)
    response = requests.put(curr_host, data=data, headers=headers)
    print(response.json())
    print(response.status_code)


def task_put_planned_hours(project_id=None, task_id=None, planned_hours=None):
    data = {"initially_planned_hours": planned_hours}
    curr_host = host + '/api/v1/project/{0}/task/{1}'.format(project_id, task_id)
    response = requests.put(curr_host, data=data, headers=headers)
    print(response.json())
    print(response.status_code)


def timesheet_post(project_id = None, task_id = None):
    curr_unix_time = time.mktime(datetime.now().timetuple())
    print('curr_unix_time', curr_unix_time)
    data = {"task_go": curr_unix_time,
            "duration": 8.0}
    curr_host = host + '/api/v1/project/{0}/task/{1}/timesheet'.format(project_id, task_id)

    response = requests.post(curr_host, data=data, headers=headers)
    print(response.json())
    print(response.status_code)

def timesheet_put(project_id = None, task_id = None,timesheet_id=None):
    data = {
        "duration": 15.0}
    curr_host = host + '/api/v1/project/{0}/task/{1}/timesheet/{2}'.format(project_id, task_id, timesheet_id)
    response = requests.put(curr_host, data=data, headers=headers)
    print(response.json())
    print(response.status_code)


try:
    while True:
        login = input('Enter login')
        password = input('Enter password')
        login = login if login.strip() else DEFAULT_LOGIN
        password = password if password.strip() else DEFAULT_PASSWORD
        access_token, profile_id, expires_in, login, description = singin(login=login,
                                                                          password=password)  # enter in the system
        headers = {'PROFILE_ID': str(profile_id),
                   'ACCESS_TOKEN': str(access_token),
                   'EXPIRES_IN': str(expires_in),
                   # 'Content-Type': 'application/json'
                   }
        print(headers)
        if profile_id and access_token:
            break
        else:
            raise Exception('''profile_id or access_token  is empty
                               profile_id:{0},
                               access_token;{1}
                            '''.format(profile_id, access_token))
except Exception as e:
    print('Error in singin method {}'.format(e))

Menu = [
    '1. Project (only GET request) check by the name',
    '2. Project (only GET request) check (filter tasks columns)',
    '3. Project (only GET request) (filter widget)',
    '4. Project (only PUT request) Delete project from the mobile app DB',
    # ------------------------------------------
    '5. Task (only GET request)(filter widget)',
    '6. Task (only PUT request)(column_id)',
    '7. Task (only PUT request)(kanban_state)',
    '8. Task (only PUT request)(planned_hours)',
    '9. Task (only GET request)(filter full)',
    # ------------------------------------------
    '10. Timesheet (only POST request)',
    '11. Timesheet (only PUTrequest)'

]


# ---------------------------------------------
def check_scrum_project_input(scrum_project_flag):
    try:
        scrum_project_flag = int(scrum_project_flag)
        if scrum_project_flag in [0, 1]:
            return True if scrum_project_flag == 1 else False
        else:
            print('Error in the project scrum_project input. Please, try once more')
    except ValueError:
        print('ValueError-- input data is not a number')
    except Exception as e:
        print(e)


# ---------------------------------------------


while True:
    print('\n')
    for b in Menu:
        print(b)
    print('\n')
    block = input('Enter block')
    os.system("clear")

    if block == '1':
        name = input('Enter Project name')
        name = DEFAULT_PROJECT_NAME if not name else name
        project_get_check(name=name.strip())

    elif block == '2':
        project_id = input('Enter Project id')
        project_id = DEFAULT_PROJECT_ID if not project_id else project_id
        scrum_project_flag = input('is the project scrum_project True-->1, False-->0  ')
        scrum_project = check_scrum_project_input(scrum_project_flag)
        project_get_filter_tasks_columns(project_id=project_id.strip(), scrum_project=scrum_project)

    elif block == '3':
        project_id = input('Enter Project id')
        project_id = DEFAULT_PROJECT_ID if not project_id else project_id
        scrum_project_flag = input('is the project scrum_project True-->1, False-->0  ')
        scrum_project = check_scrum_project_input(scrum_project_flag)
        project_get_filter_widget(project_id=project_id.strip(), scrum_project=scrum_project)

    elif block == '4':
        project_id = input('Enter Project id')
        project_id = DEFAULT_PROJECT_ID if not project_id else project_id
        project_put(project_id=project_id.strip())


    elif block == '5':
        project_id = input('Enter Project id')
        project_id = DEFAULT_PROJECT_ID if not project_id else project_id
        task_id = input('Enter Task id')
        task_id = DEFAULT_TASK_ID if not task_id else task_id
        task_get_filter_widget(project_id=project_id.strip(), task_id=task_id.strip())
#---------------------------------
    elif block == '6':
        project_id = input('Enter Project id')
        project_id = DEFAULT_PROJECT_ID if not project_id else project_id

        task_id = input('Enter Task id')
        task_id = DEFAULT_TASK_ID if not task_id else task_id

        column_id = input('Enter Column id')
        column_id = NEW_COLUMN_ID if not column_id else column_id

        task_put_column_id(project_id=project_id.strip(), task_id=task_id.strip(),column_id=int(column_id))

#---------------------------------
    elif block == '7':
        project_id = input('Enter Project id')
        project_id = DEFAULT_PROJECT_ID if not project_id else project_id

        task_id = input('Enter Task id')
        task_id = DEFAULT_TASK_ID if not task_id else task_id

        kanban_state = input('Enter kanban_state: 1-red, 2-green,3-gray')
        if kanban_state.strip()=='1':
            kanban_state='blocked'

        if kanban_state.strip()=='2':
            kanban_state='done'

        if kanban_state.strip()=='3':
            kanban_state='normal'


        task_put_kanban_state(project_id=project_id.strip(), task_id=task_id.strip(),kanban_state = kanban_state)

#---------------------------------

    elif block == '8':
        project_id = input('Enter Project id')
        project_id = DEFAULT_PROJECT_ID if not project_id else project_id

        task_id = input('Enter Task id')
        task_id = DEFAULT_TASK_ID if not task_id else task_id

        planned_hours = input('Enter planned hours: ')
        task_put_planned_hours(project_id=project_id.strip(), task_id=task_id.strip(),planned_hours = planned_hours.strip())

#---------------------------------
    elif block == '9':
        project_id = input('Enter Project id')
        project_id = DEFAULT_PROJECT_ID if not project_id else project_id
        task_id = input('Enter Task id')
        task_id = DEFAULT_TASK_ID if not task_id else task_id
        task_get_filter_full(project_id=project_id.strip(), task_id=task_id.strip())
#---------------------------------
    elif block == '10':
        project_id = input('Enter Project id')
        project_id = DEFAULT_PROJECT_ID if not project_id else project_id
        task_id = input('Enter Task id')
        task_id = DEFAULT_TASK_ID if not task_id else task_id
        timesheet_post(project_id=project_id.strip(), task_id=task_id.strip())
#---------------------------------
    elif block == '11':
        project_id = input('Enter Project id')
        project_id = DEFAULT_PROJECT_ID if not project_id else project_id

        task_id = input('Enter Task id')
        task_id = DEFAULT_TASK_ID if not task_id else task_id

        timesheet_id = input('Enter Timesheet id')
        timesheet_id = DEFAULT_TIMESHEET_ID if not timesheet_id else timesheet_id

        timesheet_put(project_id=project_id.strip(), task_id=task_id.strip(), timesheet_id=timesheet_id.strip())
