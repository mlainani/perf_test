#!/usr/bin/env python

from datetime import datetime
from pexpect import pxssh
import argparse
import csv
import pexpect
import re
import subprocess
import sys
import time

# Tested modulations with associated PIB value and list of bandwidths in Kbits/sec
modulations = {'FSK150': (8, [5, 15, 20, 25, 35, 40, 45, 55, 60, 65, 75, 150]),
               'OFDM600': (46, [5, 35, 40, 60, 65, 120, 125, 295, 300, 310, 400, 600 ])}

payload_lengths = [64, 128, 256, 1024]

# Serial ports for devices under test
dut_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1']

duration = '5'

def run_test(dual_test, modulation_name, server_addr, mgmt_addr, user_name):
    # Dictionnary keys will be the different payload lengths
    goodputs = {}
    
    print 'dual:', dual_test, modulation_name, server_addr, mgmt_addr, user_name

    dual_cmd_token = ' -d' if dual_test else ''
    dual_filename_token = '_dual' if dual_test else ''

    modulation_pib_value = modulations[modulation_name][0];
    modulation_bandwidths = modulations[modulation_name][1];

    print 'PIB value:', modulation_pib_value
    print 'Bandwidths:', modulation_bandwidths

    ping6_cmd = 'ping6 -c 1 -s 8 -W 10 ' + server_addr

    for port in dut_ports:
        # Connect to the Device Under Test and set RF modulation
        dut = pexpect.spawn('screen ' + port + ' 115200', timeout=60)
        dut.sendline()
        dut.expect_exact('# ')
        dut.sendline('pib -sn .rf_mac.static_config.pkt_mgr.forceTxModulation -v ' + str(modulation_pib_value))
        # dut.sendline('date > /root/foobar')
        dut.expect_exact('# ')

        dut.sendcontrol('a')
        dut.send('k')
        dut.send('y')
        dut.kill(1)

        print 'Set RF modulation to', modulation_name, 'for DUT on serial port', port

    for payload_len in payload_lengths:
        goodputs[payload_len] = []
        tmp_csv_filename = str(payload_len) + '_' + modulation_name + '_' + datetime.now().strftime('%b%d-%H-%M') + dual_filename_token + '.csv'
        for bandwidth in modulation_bandwidths:
            # Server reachability test loop
            print str(datetime.now()), 'Entering server reachability test loop...'
            while True:
                ret = subprocess.call(ping6_cmd, shell=True, stdout=open("/dev/null", 'w'), stderr=open("/dev/null", 'w'))
                if (ret == 0):
                    print str(datetime.now()), 'iPerf server is reachable: proceeding with test'
                    break

            iperf_server_cmd = 'iperf -s -u -V'
            iperf_client_cmd = 'iperf -b ' + str(bandwidth) + 'K -c ' + server_addr + dual_cmd_token + ' -l ' + str(payload_len) + ' -t ' + duration + ' -u -V'

            # print(iperf_server_cmd)
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            # print(datetime.now())
            print str(datetime.now()), iperf_server_cmd

            # Start iPerf server
            server = pxssh.pxssh()
            server.login(mgmt_addr, user_name)
            server.sendline()
            server.prompt()
            server.sendline(iperf_server_cmd)
            print str(datetime.now()), "Server started"            

            # Start iPerf client and wait for it to finish
            print str(datetime.now()), iperf_client_cmd
            pexpect.run(iperf_client_cmd)
            print str(datetime.now()), "Client Finished. Waiting for server to finish..."

            # iPerf2 doesn't have the one-off option found in iPerf3 that makes
            # the server return after it's done receiving packets. We need to
            # wait sufficient time before killing the server process. This
            # 'sufficient time' was determined empirically.
            time.sleep(20)

            # server.sendcontrol('c')
            server.sendcontrol('z')
            server.sendline()
            ret = server.prompt()

            if ret == True:
                print str(datetime.now()), "Server has finished"
                lines = server.before.split('\n')
                for line in lines:                
                    print str(datetime.now()), line
                    m = re.search(r'\s(\d+|\d+\.\d+)\sKbits/sec', line)                    
                    if ( m is not None ) and ( len(line.split('/')) > 2 ):
                        # print m.groups()[0]
                        goodputs[payload_len].append(float(m.groups()[0]))
                        break
                # if nothing is found, append an empty slot
                if m is None:
                    goodputs[payload_len].append("")
                    
                with open(tmp_csv_filename, 'w') as f:
                    writer = csv.writer(f, quoting=csv.QUOTE_NONE)
                    writer.writerow(['Input Data Rate (Kbps)', 'Goodput (kbps) for ' + str(payload_len) + 'B packets'])
                    writer.writerow([None, str(payload_len) + 'B'])
                    rows = zip(modulation_bandwidths, goodputs[payload_len])
                    for row in rows:
                        writer.writerow(row)

                print str(datetime.now()), modulation_name, str(payload_len)+"B, " + str(bandwidth) + "K->", goodputs[payload_len]
                server.sendline('pkill -KILL iperf')                

            else:
                print "Error while retrieving from server. Killing server process."

            server.logout

    # Create CSV file for the current modulation
    fmt = '%b%d-%H-%M'
    now = datetime.now()
    csv_filename = modulation_name + '_' + now.strftime(fmt) + dual_filename_token + '.csv'
    with open(csv_filename, 'w') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONE)
        writer.writerow(['Input Data Rate (Kbps)', 'Goodput (kbps) for different Packet Sizes', None, None, None])
        writer.writerow([None, '64B', '128B', '256B', '1024B'])
        rows = zip(modulation_bandwidths, goodputs[64], goodputs[128], goodputs[256], goodputs[1024])
        # rows = zip(modulation_bandwidths, goodputs[256], goodputs[1024])
        for row in rows:
            writer.writerow(row)

    for port in dut_ports:
        # Connect to the Device Under Test and set RF modulation
        dut = pexpect.spawn('screen ' + port + ' 115200', timeout=60)
        dut.sendline()
        dut.expect_exact('# ')
        dut.sendline('pib -sn .mas.status.f0_core.TxTimeTable1hRf -v 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000')
        # dut.sendline('date > /root/foobar')
        dut.expect_exact('# ')

        dut.sendcontrol('a')
        dut.send('k')
        dut.send('y')
        dut.kill(1)

        print 'TX time Accumulated on RF is RESET for DUT on serial port', port

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''

DESCRIPTION:

This script will perform a series of UDP goodput measurements for a
user-selected RF modulation for combination of varying payload lengths
and target bandwidths. The list of payload lengths and the the one of
target bandwidths are both hardcoded.

The script will interact with the local host, acting as the iPerf
client, and a remote host acting as the server. The remote host is
accessed using SSH. This script will also interact with the two
devices under test using a serial port connection. The list of serial
ports is hardcoded.

The results for the measurements are written to a CSV file created in
the current directory. File name starts with the selected modulation
name in uppercase.

EXAMPLES:

  ./iperf.py -m ofdm600 -s 3333::1 -t 192.168.2.2 -u kong

  ./iperf.py -d -m fsk150 -s 3333::1 -t 192.168.2.2 -u kong

DEPENDENCIES:

This script relies on the Pexpect Python module for automating
interaction with the Iperf client and server as well as with the
devices under test.

It also relies on the GNU Screen terminal multiplexer to access the
Linux console of the devices under test.

LIMITATIONS:

Only FSK150 and OFDM600 RF modulations are supported.

'''
    )

    parser.add_argument('-d', '--dualtest', action='store_true', help='do a bidirectional test simultaneously')
    parser.add_argument('-m', '--modulation', required=True, help='RF modulation used in the ACT network; used to form results CSV file name')
    parser.add_argument('-s', '--serveraddr', required=True, help='iPerf server IPv6 address')
    parser.add_argument('-t', '--mgmtaddr', required=True, help='iPerf server IPv4 address to use for the SSH management connection')
    parser.add_argument('-u', '--username', required=True, help='user name for the server management SSH connection')

    args = parser.parse_args()

    dual_test = args.dualtest
    modulation = args.modulation.upper()
    server_addr = args.serveraddr
    mgmt_addr = args.mgmtaddr
    user_name = args.username

    # Check that GNU Screen is installed
    if pexpect.which('screen') == None:
        print "Please install GNU Screen with e.g. 'sudo apt install screen'"
        sys.exit(1)

    # Check that serial ports are valid and usable
    for port in dut_ports:
        cmd = "stty -F " + port + ' speed'
        p = subprocess.Popen(cmd, shell=True, stderr=open("/dev/null", 'w'), stdout=open("/dev/null", 'w'))
        while p.poll() is None:
            continue
        if (p.returncode != 0):
            print port, 'is not a valid serial port or is already in use'
            sys.exit(1)

    if modulation not in modulations:
        print args.modulation, 'is not a supported modulation'
        sys.exit(1)

    run_test(dual_test, modulation, server_addr, mgmt_addr, user_name)
