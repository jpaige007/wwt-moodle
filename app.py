from flask import Flask, render_template, request
import json
import time
from datetime import datetime, timedelta
import urllib.request
from azure.mgmt.resource import ResourceManagementClient
from azure.common.credentials import ServicePrincipalCredentials
from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD
import os


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def automate_form():
    if request.method == 'POST':
        if 'Moodle (LMS)' in request.form['service']:
            if is_resource_group_available(request.form['deploy_name']):
                name, email, body = parse_moodle_form(request.form)
                trigger_moodle_webhook(body)
                return get_moodle_response(name, email)
            else:
                return get_error_response()
        else:
            return get_default_response(request.form['service'])
    return get_auto_form()


def parse_moodle_form(form):
    name = form['name']
    email = form['email']
    location = form['location']
    group = form['deploy_name']
    exp_timestamp = get_formatted_timestamp(form['date'], form['time'])
    body = {}
    body['-n'] = name
    body['-e'] = email
    body['-l'] = location
    body['-g'] = group
    body['-d'] = exp_timestamp
    return name, email, body


def get_formatted_timestamp(form_date, form_time):
    exp_date = datetime.strptime(form_date + '/' + form_time, '%Y-%m-%d/%H:%M')
    return exp_date.strftime('%m/%d/%Y-%I:%M%p')


def trigger_moodle_webhook(body):
    moodle_url = 'https://s16events.azure-automation.net/webhooks?token=W%2fVGUNv7jzNfb0GHsHMP2b86Z9v8SC2NqPxJmdf3N0w%3d'
    post_data = json.dumps(body).encode('ascii')
    req = urllib.request.Request(moodle_url, data=post_data)
    response = urllib.request.urlopen(req)


def get_auto_form():
    return render_template('auto_form.html')


def get_moodle_response(name, email):
    return render_template('moodle_res.html', name=name, email=email)


def get_default_response():
    return render_template('default_response.html')


def get_error_response():
    return render_template('error.html')


def is_resource_group_available(name):
    tenant_id = os.environ['TENANT']
    sub = os.environ['SUBSCRIPTION']
    client = os.environ['CLIENT']
    key = os.environ['KEY']
    principal = ServicePrincipalCredentials(client_id=client, secret=key, tenant=tenant_id)
    resource_client = ResourceManagementClient(principal, sub)
    exist = resource_client.resource_groups.check_existence(name)
    if exist:
        return False
    return True

