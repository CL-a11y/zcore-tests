import serial
import os
import sys
import re
import time
import threading
import subprocess

BASE = 'linux/'
CHECK_FILE = BASE + 'baremetal-test-ones.txt'
OUTPUT_FILE = BASE + 'stdout-zcore'
OUTPUT_NET = BASE + 'netout-zcore'
TMP_FILE = BASE + 'tmp-zcore'
TIMEOUT = 60
FAILED = ["failed","ERROR","panicked"]
passed = set()
failed = set()
timeout = set()


def rcv_data():
    while True:
        rcv=serial.readline()
        rcv=rcv.decode() 
        print(rcv)
        with open(OUTPUT_FILE, 'a') as f:
            f.write(rcv)
        with open(TMP_FILE, 'a') as f:
            f.write(rcv)

if __name__=='__main__':
    serialName = "/dev/ttyUSB0"
    serial=serial.Serial(serialName,115200,timeout=3600)

    
    if not serial.isOpen():
        print("open failed >",serial.name)
        with open(OUTPUT_FILE, 'w') as f: print("open failed >", serial.name, file=f)
        sys.exit()

    print("open succeed >",serial.name)
    with open(OUTPUT_FILE, 'w') as f: print("open succeed >", serial.name, file=f)

    th=threading.Thread(target=rcv_data)
    th.setDaemon(True)
    th.start()

    with open(CHECK_FILE, 'r') as f:
       allow_files = set([case.strip() for case in f.readlines()])
    for cmd in allow_files:
        with open(TMP_FILE, 'w') as f: print("", file=f)
        basename = os.path.basename(cmd)
        cmd = cmd + '\n'
        serial.write(cmd.encode())
        start_time = time.time()
        while True:
            with open(TMP_FILE, 'r') as f: output = f.read()
            if re.search(r"/ # [\r\n]", output):
                time.sleep(1)
                break_out_flag = False
                for pattern in FAILED:
                    if re.search(pattern, output):
                        break_out_flag = True
                        failed.add(cmd)
                        os.rename(TMP_FILE, BASE+"failed-"+basename)
                        break
                if not break_out_flag:
                    passed.add(cmd)
                    os.rename(TMP_FILE, BASE+"passed-"+basename)
                break
            if time.time() - start_time > TIMEOUT:
                break_out_flag = False
                for pattern in FAILED:
                    if re.search(pattern, output):
                        break_out_flag = True
                        failed.add(cmd)
                        os.rename(TMP_FILE, BASE+"failed-"+basename)
                        break
                if not break_out_flag:
                    timeout.add(cmd)
                    os.rename(TMP_FILE, BASE+"timeout-"+basename)
                break
    
    print("=======================================")
    print("PASSED num: ", len(passed))
    print("=======================================")
    print("FAILED num: ", len(failed))
    if len(failed) > 0: print(failed)
    print("=======================================")
    print("TIMEOUT num: ", len(timeout))
    if len(timeout) > 0: print(timeout)
    print("=======================================")
    print("Total tested num: ", len(allow_files)) 
    print("=======================================")