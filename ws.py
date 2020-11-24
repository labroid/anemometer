import RPi.GPIO as GPIO
import serial
import re
import sys
import time
import binascii

EN_485 = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(EN_485, GPIO.OUT)
GPIO.output(EN_485, GPIO.LOW)

# pattern = re.compile(b"\x02(.*)\x03(.*)\x0d\x0a")
bpattern = re.compile(b"\x02(?P<payload>.*)\x03(?P<checksum>.*)\x0d\x0a")
pattern = re.compile("Q,(?P<direction>.*),(?P<speed>.*),(?P<units>.*),(?P<status>.*),")

with serial.Serial("/dev/serial0", 9600, timeout=.5) as ser:
    while True:
        ser.write(b"?Q")
        s = ser.readall()
        s_str = s.decode('utf8')
        # print(s_str, end='')
        # print(" ".join(format(c, '02x') for c in s))

        match = bpattern.match(s)
        chk_sum = 0
        for c in match['payload']:
            chk_sum ^= c
        if int(match['checksum'].decode('utf8'), base=16) != chk_sum:
            print("Checksum bad")
            # TODO: Log checksum problems here
        payload = pattern.match(match['payload'].decode('utf8'))
        direction = int(payload['direction'] or 0)
        speed = float(payload['speed'])
        units = payload['units']
        status = payload['status']
        print(f"Speed: {speed}, Direction: {direction}, Units: {units}, Status: {status}")



      

