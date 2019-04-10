#!/usr/bin/env python

from datetime import datetime
from pexpect import pxssh
import argparse
import csv
import pexpect
import re
import sys
import time

# Tested modulations with associated PIB value and list of bandwidths in Kbits/sec
modulations = {'FSK150': (8, [5, 10, 15, 20, 25, 30, 35, 40, 50, 55, 60, 65, 70, 75, 100, 120, 125, 130, 150, 275, 295, 300, 310, 325, 350, 400]),
               'OFDM600': (46, [5, 10, 15, 20, 25, 30, 35, 40, 50, 55, 60, 65, 70, 75, 100, 120, 125, 130, 150, 275, 295, 300, 310, 325, 350, 400])}

payload_lengths = [64, 128, 256, 1024]

# Serial ports for devices under test
dut_ports = ['/dev/ttyUSB1', '/dev/ttyUSB2']

duration = '5'

def run_test(dual_test, modulation_name, server_addr, mgmt_addr, user_name):
    # Dictionnary keys will be the different payload lengths
    goodputs = {}
    
    print 'dual:', dual_test, modulation_name, server_addr, mgmt_addr, user_name

    dual = ' -d' if dual_test else ''

    modulation_pib_value = modulations[modulation_name][0];
    modulation_bandwidths = modulations[modulation_name][1];

    print 'PIB value:', modulation_pib_value
    print 'Bandwidths:', modulation_bandwidths

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
        for bandwidth in modulation_bandwidths:

            iperf_server_cmd = 'iperf -s -u -V'
            iperf_client_cmd = 'iperf -b ' + str(bandwidth) + 'K -c ' + server_addr + dual + ' -l ' + str(payload_len) + ' -t ' + duration + ' -u -V'

            # print(iperf_server_cmd)
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            # print(datetime.now())
            print str(datetime.now()), iperf_client_cmd

            # Start iPerf server
            server = pxssh.pxssh()
            server.login(mgmt_addr, user_name)
            server.sendline()
            server.prompt()
            server.sendline(iperf_server_cmd)

            # Start iPerf client and wait for it to finish
            pexpect.run(iperf_client_cmd)
            print str(datetime.now()), "Client Finished. Waiting for server to finish..."

            # iPerf2 doesn't have the one-off option found in iPerf3 that makes
            # the server return after it's done receiving packets. We need to
            # wait sufficient time before killing the server process. This
            # 'sufficient time' was determined empirically.
            time.sleep(20)

            server.sendcontrol('c')
            server.sendcontrol('c')
            ret = server.prompt()
            if ret == True:
                print str(datetime.now()), "Server has finished"
                lines = server.before.split('\n')
                for line in lines:                
                    print str(datetime.now()), line
                    m = re.search(r'\s(\d+|\d+\.\d+)\sKbits/sec', line)
                    if m is not None:
                        # print m.groups()[0]
                        goodputs[payload_len].append(float(m.groups()[0]))
                        print str(datetime.now()), str(payload_len)+"B, " + str(bandwidth) + "K->", goodputs[payload_len]
            else:
                print "Error while retrieving from server"
                exit(-1)

            server.logout

    # Create CSV file for the current modulation
    fmt = '%b%d-%H-%M'
    now = datetime.now()
    csv_filename = modulation_name + '_' + now.strftime(fmt) + '.csv'
    with open(csv_filename, 'w') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONE)
        writer.writerow(['Input Data Rate (Kbps)', 'Goodput (kbps) for different Packet Sizes', None, None, None])
        writer.writerow([None, '64B', '128B', '256B', '1024B'])
        rows = zip(modulation_bandwidths, goodputs[64], goodputs[128], goodputs[256], goodputs[1024])
        # rows = zip(modulation_bandwidths, goodputs[256], goodputs[1024])
        for row in rows:
            writer.writerow(row)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''

DESCRIPTION:

The script will create a CSV file in the current directory to collect
the goodput measurements for the given modulation for a predefined
list of target bandwidths.

EXAMPLES:

  ./iperf.py -m ofdm600 -s 3333::1 -t 192.168.2.2 -u kong

  ./iperf.py -d -m fsk150 -s 3333::1 -t 192.168.2.2 -u kong


LIMITATIONS:

Only FSK150 and OFDM600 RF modulations are supported

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

    if modulation not in modulations:
        print args.modulation, 'is not a supported modulation'
        sys.exit(1)

    run_test(dual_test, modulation, server_addr, mgmt_addr, user_name)
