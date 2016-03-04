#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, request

import os
import json
import thread
from ctypes import *
from functools import wraps
from flask import request, Response

from redmine import Redmine

app = Flask(__name__, static_folder='', static_url_path='')

currentAppDir = os.path.dirname(__file__)
from redmine.exceptions import AuthError
import logging
REDMINE_SERVER_URL="http://127.0.0.1:8080"

ID_NONTRAITE=1
ID_TRAITE=2
ID_ENCOUR=3

logger = logging.getLogger('Redmine')

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    global redmine
    global current_user
    try:
        redmine = Redmine(REDMINE_SERVER_URL, username=username, password=password)
        current_user = redmine.auth()
    except AuthError:
        logger.error('Exception with Redmine authentificate. Username or password invalid.')
        return False
    return True

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def custom_fields(t):
    return  { s['name']:s['value'] for s in t.custom_fields }
def prix(t):
    try: 
        fields=custom_fields(t).get('prix','0')
        return float(fields)
    except:
        return 0.

def prix_project(project_id):
    project = redmine.project.get(project_id)
    issues = redmine.issue.filter(status_id='*')
    issues2 = filter(lambda x:x.project.id==project.id, issues)
    return sum([prix(ticket) for ticket in issues2 ])


# permet d'obtenir les ressources statiques (img, css, js, fonts, etc.)
@app.route('/resource/<path:path>')
def getResource(path):
    return app.send_static_file(os.path.join('resources', path))

    

@app.route('/project/<project_id>')
@requires_auth
def project(project_id):
    auth = request.authorization
    print auth.username

    projects = redmine.project.all()
    projects2 = [{"name":project.name,"prix":prix_project(project.id),"id":project.id} for project in projects]
    
    ticket_encours= redmine.issue.filter(assigned_to_id=current_user.id,status_id=ID_ENCOUR)
    ticket_encours = [ticket for ticket in  ticket_encours if ticket.project.id == int(project_id)]
    ticket_traites= redmine.issue.filter(assigned_to_id=current_user.id,status_id=ID_TRAITE)
    ticket_traites = [ticket for ticket in  ticket_traites if ticket.project.id == int(project_id)]
    ticket_nontraites= redmine.issue.filter(assigned_to_id=current_user.id,status_id=ID_NONTRAITE)
    ticket_nontraites = [ticket for ticket in  ticket_nontraites if ticket.project.id == int(project_id)]
    tickets = {"encours":ticket_encours,
             "traites":ticket_traites,
             "nontraites":ticket_nontraites,
             "lencours":len(ticket_encours),
             "ltraites":len(ticket_traites),
             "lnontraites":len(ticket_nontraites)
             }
    project = [project for project in projects2 if project['id'] == int(project_id)][0]
    return render_template('project.html',user=auth.username,projects=projects2,tickets=tickets,project=project)

    
@app.route('/')
@requires_auth
def index():
    auth = request.authorization
    print auth.username

    projects = redmine.project.all()
    projects2 = [{"name":project.name,"prix":prix_project(project.id),"id":project.id} for project in projects]
    
    ticket_encours= redmine.issue.filter(assigned_to_id=current_user.id,status_id=ID_ENCOUR)
    list(ticket_encours)
    ticket_traites= redmine.issue.filter(assigned_to_id=current_user.id,status_id=ID_TRAITE)
    list(ticket_traites)
    ticket_nontraites= redmine.issue.filter(assigned_to_id=current_user.id,status_id=ID_NONTRAITE)
    list(ticket_nontraites)
    tickets = {"encours":ticket_encours.total_count,
             "traites":ticket_traites.total_count,
             "nontraites":ticket_nontraites.total_count
             }
    return render_template('index.html',user=auth.username,projects=projects2,tickets=tickets)


if __name__ == '__main__':
    app.config.update(
        DEBUG=True
    )
    app.run()
