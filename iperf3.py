#!/usr/bin/env python

import pexpect, time
import re

# Serial ports for devices under test
dut_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1']

# Serial port for server (RPi)
server_port = '/dev/ttyUSB2'

# modulations = {'FSK150': 8, 'OFDM600': 46}
modulations = {'OFDM600': 46}

# Client side bandwith in Kbits/sec
bandwidths = [10, 15, 20, 25, 30, 35, 40, 50, 65, 70, 75, 100, 120, 125, 130, 150, 275, 295, 300, 310, 325, 350, 400]

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
        for bandwidth in bandwidths:

            goodputs = []

            iperf_server_cmd = 'iperf3 -1 -s'
            iperf_client_cmd = 'iperf3 -b ' + str(bandwidth) + 'K -c 3333::1 -l ' + str(payload_len) + ' -t 10 -u'
        
            # print(iperf_server_cmd)
            print(iperf_client_cmd)

            # Start Iperf3 server
            server = pexpect.spawn('screen ' + server_port + ' 115200', timeout=60)
            server.sendline()
            server.expect_exact('pi@raspberrypi:~$ ')
            server.sendline(iperf_server_cmd)

            # delay between starting server and client
            time.sleep(0.5)
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
