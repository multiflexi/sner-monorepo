"""job controler"""

import base64
import json
import os
import time
import uuid
from datetime import datetime
from http import HTTPStatus

import jsonschema
from flask import current_app, jsonify, redirect, render_template, request, Response, url_for
from sqlalchemy.sql.expression import func

import sner.agent.protocol
from sner.server import db
from sner.server.controller.scheduler import blueprint
from sner.server.form import GenericButtonForm
from sner.server.model.scheduler import Job, Queue, Target


@blueprint.route('/job/list')
def job_list_route():
	"""list jobs"""

	jobs = Job.query.all()
	return render_template('scheduler/job/list.html', jobs=jobs, generic_button_form=GenericButtonForm())


#TODO: post? csfr protection?
@blueprint.route('/job/assign')
@blueprint.route('/job/assign/<queue_id>')
def job_assign_route(queue_id=None):
	"""assign job for worker"""

	def wait_for_lock(table):
		"""wait for database lock"""
		#TODO: passive wait for lock
		while True:
			try:
				db.session.execute('LOCK TABLE %s' % table)
				break
			except Exception:
				db.session.rollback()
				time.sleep(0.01)

	assignment = {}
	wait_for_lock(Target.__tablename__)

	if queue_id:
		if queue_id.isnumeric():
			queue = Queue.query.filter(Queue.id == int(queue_id)).one_or_none()
		else:
			queue = Queue.query.filter(Queue.name == queue_id).one_or_none()
	else:
		# select highest priority active task with some targets
		queue = Queue.query.filter(Queue.active, Queue.targets.any()).order_by(Queue.priority.desc()).first()

	if queue:
		assigned_targets = []
		for target in Target.query.filter(Target.queue == queue).order_by(func.random()).limit(queue.group_size):
			assigned_targets.append(target.target)
			db.session.delete(target)

		if assigned_targets:
			assignment = {
				"id": str(uuid.uuid4()),
				"module": queue.task.module,
				"params": queue.task.params,
				"targets": assigned_targets}
			job = Job(id=assignment["id"], assignment=json.dumps(assignment), queue=queue)
			db.session.add(job)

	# at least, we have to clear the lock
	db.session.commit()
	return jsonify(assignment)


@blueprint.route('/job/output', methods=['POST'])
def job_output_route():
	"""receive output from assigned job"""

	try:
		jsonschema.validate(request.json, schema=sner.agent.protocol.output)
		job_id = request.json['id']
		retval = request.json['retval']
		output = base64.b64decode(request.json['output'])
	except Exception:
		return Response(status=HTTPStatus.BAD_REQUEST)

	output_file = os.path.join(current_app.config['SNER_OUTPUT_DIRECTORY'], job_id)
	with open(output_file, 'wb') as ftmp:
		ftmp.write(output)

	job = Job.query.filter(Job.id == job_id).one_or_none()
	job.retval = retval
	job.output = output_file
	job.time_end = datetime.utcnow()
	db.session.commit()

	return Response(status=HTTPStatus.OK)


@blueprint.route('/job/delete/<job_id>', methods=['GET', 'POST'])
def job_delete_route(job_id):
	"""delete job"""

	job = Job.query.get(job_id)
	form = GenericButtonForm()

	if form.validate_on_submit():
		if job.output:
			os.remove(job.output)
		db.session.delete(job)
		db.session.commit()
		return redirect(url_for('scheduler.job_list_route'))

	return render_template('button_delete.html', form=form, form_url=url_for('scheduler.job_delete_route', job_id=job_id))
