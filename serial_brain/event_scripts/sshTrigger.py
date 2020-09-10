import paramiko
try:
    from event_scripts.sshTriggerCfg import Settings as cfg
except:
    from sshTriggerCfg import Settings as cfg
from time import sleep

user = cfg["user"]
pwd = cfg["pwd"]
ip = cfg["ip"]
cmd = cfg["cmd"]


def trigger_script():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, 22, user, pwd)
    sleep(0)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stderr)
    print(stdout)
    outlines = stdout.readlines()
    resp = ''.join(outlines)
    print(resp)


def main():
    trigger_script()


if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
    main()
