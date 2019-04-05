#!/usr/bin/env python

import pexpect
import re

# Serial ports for devices under test
dut_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1']

# Serial port for server (RPi)
server_port = '/dev/ttyUSB2'

# modulations = {'FSK150': 8, 'OFDM600': 46}
modulations = {'OFDM600': 46}

bandwidths = ['Bandwidth']

for item in list(modulations.items()):
    # print(item[0])
    # print(item[1])

    # cmd  = 'pib -sn .rf_mac.static_config.pkt_mgr.forceTxModulation -v ' + str(item[1])

    # print(cmd)

    for port in dut_ports:
        # Connect to the Device Under Test and set RF modulation
        # cmd = 'screen ' + port + ' 115200'
        # print(cmd)
        dut = pexpect.spawn('screen ' + port + ' 115200', timeout=60)
        dut.sendline()
        # dut.sendcontrol('c')
        dut.expect_exact('# ')
        # dut.sendline('pib -sn .rf_mac.static_config.pkt_mgr.forceTxModulation -v ' + str(item[1]))
        dut.sendline('date > /root/foobar')
        dut.expect_exact('# ')

        dut.sendcontrol('a')
        dut.send('k')
        dut.send('y')
        dut.kill(1)

        print('Set RF modulation to ' +  item[0] + ' for DUT on serial port ' + port)

    for payload_len in [64, 128, 256, 1024]:
    # for payload_len in [256]:

        goodputs = []

        iperf_server_cmd = 'iperf3 -1 -s'
        iperf_client_cmd = 'iperf3 -b 300K -c 3333::1 -l ' + str(payload_len) + ' -t 10 -u'
        print(iperf_server_cmd)
        print(iperf_client_cmd)

        # Start Iperf3 server
        server = pexpect.spawn('screen ' + server_port + ' 115200', timeout=60)
        server.sendline()
        server.expect_exact('pi@raspberrypi:~$ ')
        server.sendline(iperf_server_cmd)

        # Start Iperf3 client and wait for it to finish

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

        # server.sendline()
        server.expect_exact('pi@raspberrypi:~$ ')
        if ret == 0:
            lines = server.before.split('\n')
            for line in lines:
                # print line
                m = re.search(r'\s(\d+|\d+\.\d+)\sKbits/sec', line)
                if m is not None:
                    # print m.groups()[0]
                    goodputs.append(float(m.groups()[0]))

        # goodputs.sort()

        avg_goodput = round(sum(goodputs) / len(goodputs), 1)
        print avg_goodput

        server.sendcontrol('a')
        server.send('k')
        server.send('y')
        server.kill(1)
