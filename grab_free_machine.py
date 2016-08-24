"""
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
from subprocess import check_output, CalledProcessError
from datetime import datetime
from time import sleep


JOB_TEMPLATE = """
<job retention_tag="scratch">
  <whiteboard></whiteboard>
  <recipeSet priority="High">
    <recipe whiteboard="" role="RECIPE_MEMBERS" ks_meta="" kernel_options="" kernel_options_post="">
      <autopick random="false"/>
      <watchdog panic="ignore"/>
      <packages/>
      <ks_appends/>
      <repos/>
      <distroRequires>
        <and>
          <distro_name op="=" value="CentOS-7"/>
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
    return datetime.now().strftime('%Y%m%d-%H%M%S')


def log(message):
    print '[{}] {}'.format(timestamp(), message)


def job(host):
    log('Processing job for host {}'.format(host))
    return JOB_TEMPLATE.format(host=host)


def job_filename():
    return 'job-' + timestamp()


def submit_job(xml):
    filename = job_filename()
    with open(filename, 'w') as f:
        f.write(xml)

    log('Submitting job in file {}'.format(filename))

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


def main():
    submitted_jobs = 0

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

            submit_job(job(machine))
            submitted_jobs += 1

        break


if __name__ == '__main__':
    main()
