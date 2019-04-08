#!/usr/bin/env python

from pexpect import pxssh
import pexpect
import re
import time

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

            iperf_server_cmd = 'iperf -s -u -U -V'
            # iperf_client_cmd = 'iperf -b ' + str(bandwidth) + 'K -c 3333::1 -l ' + str(payload_len) + ' -t 10 -u -V'
            iperf_client_cmd = 'iperf -b ' + str(bandwidth) + 'K -c 3333::1 -l ' + str(payload_len) + ' -t 5 -u -V'

            # print(iperf_server_cmd)
            print(iperf_client_cmd)

            # Start Iperf server
            # server = pexpect.spawn('screen ' + server_port + ' 115200', timeout=60)
            # server.sendline()
            server = pxssh.pxssh()
            server.login('192.168.2.2', 'pi')
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
                    print m.groups()[0]
                    # goodputs.append(float(m.groups()[0]))

            # goodputs.sort()

            # avg_goodput = round(sum(goodputs) / len(goodputs), 1)
            # print avg_goodput


            server.sendcontrol('a')
            server.send('k')
            server.send('y')
            server.kill(1)
