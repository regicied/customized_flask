import socket
import paramiko
from config import SSH_TIMEOUT
from backend.myException.myExecption import MySSHError
from backend.common.loghandler import ServiceLog
from subprocess import check_output, CalledProcessError
from paramiko.ssh_exception import AuthenticationException, NoValidConnectionsError

# SSH_TIMEOUT = 5


class ScriptHandler:
    sftp = None
    ssh = None

    def __init__(self, host, name, password, port=22, job_id=None):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(host, port, name, password, timeout=SSH_TIMEOUT)
        except PermissionError:
            msg = 'Permission denied'
            raise MySSHError(msg)
        except AuthenticationException:
            # Authentication failed.
            msg = 'Authentication failed'
            # raise MyRuntimeError('Authentication failed', 500)
            raise MySSHError(msg)
        except NoValidConnectionsError:
            msg = 'unable to connect to the host'
            # [Errno None] Unable to connect to port 2200 on 100.98.97.186
            # raise MyRuntimeError('unable to connect to the host', 500)
            raise MySSHError(msg)
        except TimeoutError:
            msg = 'unable to reach the host'
            # A connection attempt failed because the connected party did not properly respond after a period of time,
            # or established connection failed because connected host has failed to respond
            # raise MyRuntimeError('unable to reach the host', 500)
            raise MySSHError(msg)
        except socket.timeout:
            msg = 'unable to reach the host'
            # A connection attempt failed because the connected party did not properly respond after a period of time,
            # or established connection failed because connected host has failed to respond
            # raise MyRuntimeError('unable to reach the host', 500)
            raise MySSHError(msg)
        except OSError as e:
            msg = e.strerror
            raise MySSHError(msg)
        self.ssh = ssh
        self.source = None
        if job_id:
            self.job_id = job_id

    def __del__(self):
        if self.ssh:
            self.ssh.close()
        if self.sftp:
            self.sftp.close()

    def source_file(self, path):
        self.source = path

    def execute_cmd(self, cmd):
        if self.source:
            cmd = 'source %s; %s' % (self.source, cmd)
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        ServiceLog.info(cmd)
        output = stdout.read()
        err_info = stderr.read()
        if err_info:
            if type(err_info) == bytes:
                ServiceLog.error(err_info)
                # raise RuntimeError('ssh cmd error: %s' % err_info)
        if type(output) == bytes:
            output = str(output, 'utf-8')
        return output

    def scp_file(self, file, target):
        if not self.sftp:
            sftp = self.ssh.open_sftp()
            self.sftp = sftp
        self.sftp.put(file, target)
        ServiceLog.info('put file from %s to %s' % (file, target))

    def get_file(self, target, file):
        if not self.sftp:
            sftp = self.ssh.open_sftp()
            self.sftp = sftp
        self.sftp.get(target, file)
        ServiceLog.info('get file from %s to %s' % (target, file))


def call_subprocess(cmd, host=False):
    flag = True
    try:
        if host:
            cmd = 'ssh %s "%s"' % (host, cmd)
        result = check_output(cmd, shell=True)
    except CalledProcessError as e:
        result = e
        flag = False
    return result, flag
