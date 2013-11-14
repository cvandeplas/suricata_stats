#!/usr/bin/python
import os, argparse

threads = 8                                     # set here the number of threads configured in suricata.yaml
logfile = "/var/log/suricata/stats.log"         # path to the stats log file
zabbix_conf = "/etc/zabbix/zabbix_agentd.conf"  # (optional) Zabbix configuration file

# normally you shouldn't change this
stats_lines_per_thread = 45    # number of lines suri dumps in stats.log per thread
stats_unique = 7               # additional unique lines like FlowManagerThread
stats_numlines = ( stats_lines_per_thread * threads ) + 7 

def tail(f, n):
        stdin,stdout = os.popen2("tail -n {0} '{1}'".format(n, f))
        stdin.close()
        lines = stdout.readlines()
        stdout.close()
        return lines

# parse the arguments
parser = argparse.ArgumentParser(description='Consolidate the suricata stats file.')
parser.add_argument('-z', '--zabbix', action='store_true',
                   help='Send output to zabbix')
parser.add_argument('-q', '--quiet', action='store_true',
                   help='Be quiet (do not print to stdout)')
parser.add_argument('-v', '--verbose', action='store_true',
                   help='be more verbose')

args = parser.parse_args()

# do the math for each variable
data = {}
f_content = tail(logfile, stats_numlines)
for line in f_content:
    var, section, value = line.split('|')
    var = var.strip()
    section = section.strip()
    value = value.strip()
    try:
        data[var] = data[var] + int(value)
    except KeyError: 
        data[var] = int(value)

# build the output
stats = []
for key,value in data.items():
    stats.append("- suricata[{0}] {1}".format(key,value))

if not args.quiet:
    print ('\n'.join(stats))

if args.zabbix:
    # send to zabbix
    import platform
    hostname = platform.node()
    stdin,stdout = os.popen2("zabbix_sender -s {0} -c {1} -i -".format(hostname, zabbix_conf)) 
    stdin.write('\n'.join(stats))
    stdin.close()
    lines = stdout.readlines()
    stdout.close()
    if args.verbose:
        print lines
