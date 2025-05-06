from typing import BinaryIO, List
from logging import getLogger
import subprocess
import os
import signal
logger = getLogger(__name__)

class CmdManage:
    @classmethod
    def execute_cmd(cls,
                    cmd: str,
                    options: str,
                    commands: dict,
                    stdout: BinaryIO,
                    stderr: BinaryIO,
                    pid_file: BinaryIO):
        cmd = cls.parse_commands(cmd, options, commands)
        logger.info(f'execute cmd: {cmd}')
        try:
            p = subprocess.Popen(cmd, 
                                shell=True,
                                preexec_fn=os.setsid,
                                stderr=stderr,
                                stdout=stdout
                            )
             # 写pid到文件内
            if pid_file:
                pid_file.write(str(p.pid).encode())
                pid_file.close()

            exit_code = p.wait()
            return p.pid, exit_code
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            raise Exception(f'timeout in execute cmd, [{cmd}]')
        except Exception as e:
            raise Exception(f'err in execute cmd: [{e}]')
    def parse_commands(cls, cmd, options: List[str], commands: dict):
        cmd = f'{cmd} {" ".join(options)}'
        for key, value in commands.items():
            cmd += f' --{key} {value}'
        return cmd


