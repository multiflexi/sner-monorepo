# This file is part of sner4 project governed by MIT license, see the LICENSE.txt file.
"""
scheduler commands
"""

import sys
from ipaddress import ip_address, summarize_address_range
from pathlib import Path
from shutil import copy2
from time import sleep

import click
from flask import current_app
from flask.cli import with_appcontext

from sner.server.extensions import db
from sner.server.parser.manymap import ManymapParser
from sner.server.parser.nmap import NmapParser
from sner.server.scheduler.core import enumerate_network, job_delete, queue_enqueue
from sner.server.scheduler.models import Job, Queue, Target


@click.group(name='scheduler', help='sner.server scheduler management')
def command():
    """scheduler commands container"""


@command.command(name='enumips', help='enumerate ip address range')
@click.argument('targets', nargs=-1)
@click.option('--file', type=click.File('r'))
def enumips_command(targets, **kwargs):
    """enumerate ip address range"""

    targets = list(targets)
    if kwargs['file']:
        targets += kwargs['file'].read().splitlines()
    for target in targets:
        print('\n'.join(enumerate_network(target)))


@command.command(name='rangetocidr', help='convert range specified addr space to series of cidr')
@click.argument('start')
@click.argument('end')
def rangetocidr_command(start, end):
    """summarize net rage into cidrs"""

    for tmp in summarize_address_range(ip_address(start), ip_address(end)):
        print(tmp)


@command.command(name='queue-enqueue', help='add targets to queue')
@click.argument('queue_name')
@click.argument('argtargets', nargs=-1)
@click.option('--file', type=click.File('r'))
@with_appcontext
def queue_enqueue_command(queue_name, argtargets, **kwargs):
    """enqueue targets to queue"""

    queue = Queue.query.filter(Queue.name == queue_name).one_or_none()
    if not queue:
        current_app.logger.error('no such queue')
        sys.exit(1)

    argtargets = list(argtargets)
    if kwargs['file']:
        argtargets.extend(kwargs['file'].read().splitlines())
    queue_enqueue(queue, argtargets)
    sys.exit(0)


@command.command(name='queue-flush', help='flush all targets from queue')
@click.argument('queue_name')
@with_appcontext
def queue_flush_command(queue_name):
    """flush targets from queue"""

    queue = Queue.query.filter(Queue.name == queue_name).one_or_none()
    if not queue:
        current_app.logger.error('no such queue')
        sys.exit(1)

    db.session.query(Target).filter(Target.queue_id == queue.id).delete()
    db.session.commit()
    sys.exit(0)


@command.command(name='queue-prune', help='delete all associated jobs')
@click.argument('queue_name')
@with_appcontext
def queue_prune_command(queue_name):
    """delete all jobs associated with queue"""

    queue = Queue.query.filter(Queue.name == queue_name).one_or_none()
    if not queue:
        current_app.logger.error('no such queue')
        sys.exit(1)

    for job in Job.query.filter(Job.queue_id == queue.id).all():
        job_delete(job)
    sys.exit(0)


PLANNER_POSTDISCO_QUEUE = 'inet version scan basic'
PLANNER_LOOP_SLEEP = 60


@command.command(name='planner', help='run planner daemon')
@with_appcontext
@click.option('--oneshot', is_flag=True)
def planner(**kwargs):
    """run planner daemon"""

    archive_dir = Path(current_app.config['SNER_VAR']) / 'planner_archive'
    archive_dir.mkdir(parents=True, exist_ok=True)

    loop = True
    while loop:
        for trail in ['sner', 'sweep']:
            # trails: sner is main, sweep is prio

            disco_queues_ids = db.session.query(Queue.id).filter(Queue.name.like(f'{trail}_%_disco %'))
            postdisco_queue = Queue.query.filter(Queue.name.like(f'{trail}_%_data {PLANNER_POSTDISCO_QUEUE}')).one_or_none()
            for finished_job in Job.query.filter(Job.queue_id.in_(disco_queues_ids), Job.retval == 0).all():
                current_app.logger.debug('parsing services from %s', finished_job)
                queue_enqueue(postdisco_queue, NmapParser.service_list(finished_job.output_abspath, exclude_states=['filtered', 'closed']))
                copy2(finished_job.output_abspath, archive_dir)
                job_delete(finished_job)

            data_queues_ids = db.session.query(Queue.id).filter(Queue.name.like(f'{trail}_%_data %'))
            for finished_job in Job.query.filter(Job.queue_id.in_(data_queues_ids), Job.retval == 0).all():
                current_app.logger.debug('importing service scan from %s', finished_job)
                ManymapParser.import_file(finished_job.output_abspath)
                copy2(finished_job.output_abspath, archive_dir)
                job_delete(finished_job)

        sleep(PLANNER_LOOP_SLEEP)
        if kwargs['oneshot']:
            loop = False
