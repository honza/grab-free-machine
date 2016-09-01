#!/usr/bin/env python

"""

grab_free_machine
Copyright (C) 2016 --- Honza Pokorny

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Grab a free machine from beaker
===============================

Depends on the ``bkr`` command.  Only tested with Python 2.

This script will ask beaker for a list of free machines that match the below
criteria.  If there are any matching machines, it will request them.  If there
aren't any machines, the script will wait 30 seconds and try again.

The machine criteria are spread between the ``FILTER`` and the ``bkr_command``.

We're looking for a machine:

* > 3 CPUs
* > 11GB of RAM
* x86_64
* > 120GB disk
* not virtualized

The recipe will install RHEL 7.2 on the newly acquired machine.

You should run this a few times.  In the "My jobs" section of the web UI, you
will see a bunch of jobs with a status of "Queued".  That means that you didn't
get to the machine fast enough, and someone else has already grabbed it.  When
you see a status of "In progress" or "Running", you won the lottery.  You
should then cancel the other jobs.
"""
import sys
from subprocess import check_output, CalledProcessError
from datetime import datetime
from time import sleep

DISTRO = {
    'rhel': """
          <distro_family op="=" value="RedHatEnterpriseLinux7"/>
          <distro_variant op="=" value="Server"/>
          <distro_name op="=" value="RHEL-7.2"/>
    """,
    'centos': '<distro_name op="=" value="CentOS-7"/>'
}


JOB_TEMPLATE = """
<job retention_tag="scratch">
  <whiteboard></whiteboard>
  <recipeSet priority="High">
    <recipe whiteboard="" role="RECIPE_MEMBERS" ks_meta="" kernel_options=""
            kernel_options_post="">
      <autopick random="false"/>
      <watchdog panic="ignore"/>
      <packages/>
      <ks_appends/>
      <repos/>
      <distroRequires>
        <and>
          {distro}
          <distro_arch op="=" value="x86_64"/>
        </and>
      </distroRequires>
      <hostRequires force="{host}"/>
      <partitions/>
      <task name="/distribution/install" role="STANDALONE"/>
      <task name="/distribution/reservesys" role="STANDALONE">
        <params>
          <param name="RESERVETIME" value="518400"/>
        </params>
      </task>
    </recipe>
  </recipeSet>
</job>
"""

FILTER = """
<hostRequires>
  <and>
    <key_value key="PROCESSORS" op=">" value="3"/>
    <memory op=">" value="11000" />
    <key_value key="DISKSPACE" op=">" value="120000" />
    <hypervisor op="=" value="" />
  </and>
</hostRequires>
"""


def timestamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def log(message):
    print '[{}] {}'.format(timestamp(), message)


def job(host, distro):
    log('Processing job for host {}'.format(host))
    return JOB_TEMPLATE.format(host=host, distro=distro)


def job_filename():
    return 'job-' + timestamp()


def submit_job(xml):
    filename = job_filename()

    with open(filename, 'w') as f:
        f.write(xml)

    log('Submitting job')

    if VERBOSE:
        log(xml)

    try:
        check_output(['bkr', 'job-submit', filename])
    except CalledProcessError:
        log('job submission failed')


def bkr_command():
    xml = "--xml-filter='{}'".format(FILTER.replace('\n', ''))
    return [
        'bkr',
        'list-systems',
        '--free',
        '--arch=x86_64',
        '--type=Machine',
        xml
    ]


def find_free():
    log('Checking for free machines...')
    try:
        output = check_output(bkr_command())
        return output.split('\n')
    except CalledProcessError:
        return


def validate_distro(distro):
    xml = DISTRO.get(distro)

    if not xml:
        print 'Wrong distro. Choices: RHEL or CentOs'
        sys.exit(1)

    return xml


def main(distro):
    submitted_jobs = 0

    distro = validate_distro(distro)

    while True:
        machines = find_free()

        if not machines:
            log('No machines, sleeping...')
            sleep(30)
            continue

        for machine in machines:
            if not machine:
                continue

            if submitted_jobs == 3:
                break

            submit_job(job(machine, distro))
            submitted_jobs += 1

        break


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('distro', help='rhel or centos')
    parser.add_argument('-v, --verbose', action='store_true',
                        dest='verbose', help='verbose')
    args = parser.parse_args()

    global VERBOSE
    VERBOSE = args.verbose

    main(args.distro.lower())
