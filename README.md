# Grab a free machine from beaker

Depends on the `bkr` command.  Works with Python 2 and 3.

This script will ask beaker for a list of free machines that match the below
criteria.  If there are any matching machines, it will request them.  If there
aren't any machines, the script will wait 30 seconds and try again.

We're looking for a machine:

* 3 or more CPUs
* 32GB or more of RAM
* x86_64
* 120GB or larger disk
* not virtualized

The recipe will install either RHEL 7.2, RHEL 7.3, RHEL 7.4 or CentOS on the
newly acquired machine.

You should run this a few times.  In the "My jobs" section of the web UI, you
will see a bunch of jobs with a status of "Queued".  That means that you didn't
get to the machine fast enough, and someone else has already grabbed it.  When
you see a status of "In progress" or "Running", you won the lottery.  You
should then cancel the other jobs.

## Usage

```
usage: grab_free_machine.py [-h] [-a ATTEMPTS] [-v, --verbose] distro

positional arguments:
  distro                rhel-latest, rhel-72, rhel-73, rhel-74, centos

optional arguments:
  -h, --help            show this help message and exit
  -a ATTEMPTS, --attempts ATTEMPTS
                        How many free machines at most should we try to
                        acquire?
  -v, --verbose         verbose
```

## License

GPL-2
