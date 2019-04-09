#!/usr/bin/env python

from datetime import datetime
from pexpect import pxssh
import csv
import pexpect
import re
import time

payload_lengths = [64, 128, 256, 1024]
# payload_lengths = [256, 1024]

# Dictionnary keys are the above payload lengths
goodputs = {}

# Serial ports for devices under test
dut_ports = ['/dev/ttyUSB1', '/dev/ttyUSB2']

# Serial port for server (RPi). Not necessary with ASIC
server_port = '/dev/ttyUSB2'

# Ip addr for server
server_ip_addr = '10.0.30.2'

# IPERF Settings
client_ip_addr  = 'bbbb::1' # CLient IP Addr
duration        = '5'
report_interval = '1'

# Tested modulations with associated PIB value and list of bandwidths in Kbits/sec
modulations = {'FSK150': (8, [5, 10, 15, 20, 25, 30, 35, 40, 50, 55, 60, 65, 70, 75, 100, 120, 125, 130, 150, 275, 295, 300, 310, 325, 350, 400]),
               'OFDM600': (46, [5, 10, 15, 20, 25, 30, 35, 40, 50, 55, 60, 65, 70, 75, 100, 120, 125, 130, 150, 275, 295, 300, 310, 325, 350, 400])}

# modulations = {'OFDM600': (46, [150, 400])}

for item in list(modulations.items()):
    modulation_name = item[0];
    modulation_pib_value = item[1][0];
    modulation_bandwidths = item[1][1]

    print(modulation_name)
    print(modulation_pib_value)
    print(modulation_bandwidths)

    # cmd  = 'pib -sn .rf_mac.static_config.pkt_mgr.forceTxModulation -v ' + str(modulation_pib_value)

    # print(cmd)

    # continue
    # exit(0)
    
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

        print('Set RF modulation to ' +  item[0] + ' for DUT on serial port ' + port)

    for payload_len in payload_lengths:
        goodputs[payload_len] = []
        for bandwidth in modulation_bandwidths:

            iperf_server_cmd = 'iperf -s -u -V'
            # iperf_client_cmd = 'iperf -b ' + str(bandwidth) + 'K -c 3333::1 -l ' + str(payload_len) + ' -t 10 -u -V'
            iperf_client_cmd = 'iperf -b ' + str(bandwidth) + 'K -c ' + client_ip_addr + ' -l ' + str(payload_len) + ' -t ' + duration + ' -u -V'

            # print(iperf_server_cmd)
            print(iperf_client_cmd)

            # Start Iperf server
            # server = pexpect.spawn('screen ' + server_port + ' 115200', timeout=60)
            # server.sendline()
            server = pxssh.pxssh()
            server.login(server_ip_addr, 'kong')
            # server.expect_exact('pi@raspberrypi:~$ ')
            server.prompt()
            server.sendline(iperf_server_cmd)

            # Start Iperf client and wait for it to finish

            # Set command prompt to something more specific
            COMMAND_PROMPT = r"\[PEXPECT\]\$ "
            client = pexpect.spawn('/bin/bash', timeout=60)
            client.sendline (r"PS1='[PEXPECT]\$ '")
            client.expect(COMMAND_PROMPT)
            client.sendline(iperf_client_cmd)
            ret = client.expect(COMMAND_PROMPT)
            if ret == 0:
                print 'Client has finished\n'
                client.kill(1)

            time.sleep(10)

            server.sendcontrol('c')
            server.sendcontrol('c')
            server.prompt()
            # server.expect_exact('pi@raspberrypi:~$ ')
            if ret == 0:
                lines = server.before.split('\n')
            for line in lines:
                print line
                m = re.search(r'\s(\d+|\d+\.\d+)\sKbits/sec', line)
                if m is not None:
                    # print m.groups()[0]
                    goodputs[payload_len].append(float(m.groups()[0]))
                    print str(payload_len)+"B, " + str(bandwidth) + "K->", goodputs[payload_len]

            # goodputs.sort()

            # avg_goodput = round(sum(goodputs) / len(goodputs), 1)
            # print avg_goodput

            server.logout
            # server.sendcontrol('a')
            # server.send('k')
            # server.send('y')
            # server.kill(1)

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
