import os
import settings
from redis_manager import redis_client
from logging import getLogger
import shutil
from cmd_manage import CmdManage
import signal
import os
logger = getLogger(__name__)

class SFTManage:
    ClientCliOutput = settings.CLIENT_CLI_OUTPUT
    # 执行的训练指令
    ClientCli = 'cogmait-ft'
    ModelRootPath = settings.MODEL_ROOT_DIR

    class JobStatus:
        Finished = 'FINISHED'
        Failed = 'FAILED'
        Running = 'RUNNING'

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.exit_code_key = f'{job_id}:exitcode'
        self.stdout_key = f'{job_id}:stdout'
        self.stderr_key = f'{job_id}:stderr'
        self.model_name_key = f'{job_id}:model'
        self.exec_lock_key = f'{job_id}:execlock'

        os.makedirs(os.path.join(self.ClientCliOutput, job_id), exist_ok=True)
        self.job_exec_dir = os.path.join(self.ClientCliOutput, job_id)
        os.makedirs(self.job_exec_dir, exist_ok=True)

        self.result_dir = os.path.join(self.job_exec_dir, 'job_result')
        os.makedirs(self.result_dir, exist_ok=True)

        self.pid_path = os.path.join(self.result_dir, 'pid')
        self.stdout_path = os.path.join(self.result_dir, 'stdout')
        self.stderr_path = os.path.join(self.result_dir, 'stderr')

        # 指令生成预训练模型的输出目录
        self.model_output_dir = os.path.join(self.job_exec_dir, 'model_output')
        os.makedirs(self.model_output_dir, exist_ok=True)

    @classmethod
    def get_model_path(cls):
        """
        获取模型列表
        """
        model_list = []
        for model in os.listdir(cls.ModelRootPath):
            if os.path.isdir(os.path.join(cls.ModelRootPath, model)):
                model_list.append(model)
        return model_list

    def get_result(self):
        pid = None
        if os.path.exists(self.pid_path):
            pid = self.read_file(self.pid_path)
        exit_code = redis_client.get(self.exit_code_key)
        stdout = redis_client.get(self.stdout_key)
        stderr = redis_client.get(self.stderr_key)
        return pid, exit_code, stdout, stderr

    def read_file(self, file_path: str) -> str:
        """
        读取文件内容，确保返回有效的字符串
        """
        try:
            if not os.path.exists(file_path):
                return None
            with open(file_path, 'rb') as f:
                content = f.read().strip()
                return content.decode('utf-8', errors='ignore') if content else None
        except Exception as e:
            logger.error(f'Failed to read file {file_path}: {e}')
            return None
        
    def run_job(self, options: str, commands: dict):
        try:
            print("run_job:", self.job_id)
            lock_result = self.set_exec_lock_key()
            if not lock_result:
                logger.info(f'job is already canceled, job_id: {self.job_id}')
                return
            
            # 解析参数
            self.parse_commands(commands)
            # 执行命令
            stdout_file = open(self.stdout_path, 'wb')
            stderr_file = open(self.stderr_path, 'wb')
            pid_file = open(self.pid_path, 'wb')
           
            pid, code = CmdManage.execute_cmd(self.ClientCli, 
                                              options, commands,
                                              stdout=stdout_file, 
                                              stderr=stderr_file, 
                                              pid_file=pid_file)
            logger.info(f'job {self.job_id} finished, pid: {pid}, exit_code: {code}')
            # 将输出结果写进redis
            try:
                with open(self.stdout_path, 'rb') as f:
                    exex_stdout = f.read().decode('utf-8', errors='ignore')
                with open(self.stderr_path, 'rb') as f:
                    exex_stderr = f.read().decode('utf-8', errors='ignore')
                self.write_result(code, exex_stdout, exex_stderr)
            except Exception as e:
                logger.error(f'Failed to read output files: {e}')
                self.write_result(code, '', str(e))

        except Exception as e:
            logger.error(f'Failed to set exec lock key: {e}')
            self.write_result(1, '', str(e))
        finally:
            self.delete_exec_lock_key()
    
    
    def cancel_job(self):
        pid, exit_code, stdout, stderr = self.get_result()
        logger.info(f'cancel job job_id: {self.job_id}, pid: {pid}, exit_code: {exit_code}, stdout: {stdout}, stderr: {stderr}')
        if exit_code is not None:
            # 任务已执行结束，无需cancel
            return
        # 没有exitcode 但是有pid说明还在进行中
        if pid is not None:
            try:
                pid_value = int(pid)
                os.kill(pid_value, signal.SIGKILL)
                logger.info(f'Killed process with PID {pid_value}')
            except (ProcessLookupError, ValueError) as e:
                logger.error(f'Failed to kill process with PID {pid}: {e}')
        # 说明任务还未执行，可能在队列中或解析参数的过程
        self.set_exec_lock_key()

    def delete_job(self):
        # 先取消任务
        self.cancel_job()

    def publish_job(self, model_name: str):
        model_output_dir = self.model_output_dir
        publish_model_path = os.path.join(self.ModelRootPath, model_name)
        if not os.path.exists(model_output_dir):
            raise Exception(f'model not found, [{model_output_dir}] not exist')
        if os.path.exists(publish_model_path):
            raise Exception(f'model already exists, [{publish_model_path}] already exist')
        else:
            os.makedirs(publish_model_path, exist_ok=True)
            shutil.move(model_output_dir, publish_model_path)

        # 存储发布的模型名称
        redis_client.set_no_expiration(self.model_name_key, model_name)

    def cancel_publish_job(self, model_name: str):
        pub_model_name = redis_client.get(self.model_name_key)
        if pub_model_name != model_name:
            raise Exception(f'model not found, [{model_name}] not exist')
        publish_model_dir = os.path.join(self.ModelRootPath, model_name)
        if os.path.exists(publish_model_dir):
            shutil.rmtree(publish_model_dir)
            shutil.move(publish_model_dir, self.model_output_dir)

    def get_job_status(self):
        """
        获取任务执行状态
        :return: 运行状态, 原因
        """
        pid, exit_code, stdout, stderr = self.get_result()
        logger.info(f'get job status job_id: {self.job_id}, pid: {pid}, exit_code: {exit_code}, stdout: {stdout}, stderr: {stderr}')
        if exit_code is not None:
            try:
                if int(exit_code) == 0:
                    return self.JobStatus.Finished, stdout
                return self.JobStatus.Failed, f'{stderr}\n{stdout}'
            except (ValueError, TypeError) as e:
                logger.error(f'Failed to parse exit_code {exit_code}: {e}')
                return self.JobStatus.Failed, f'无效的退出代码: {exit_code}, 错误: {stderr}\n{stdout}'
        if pid is not None:
            return self.JobStatus.Running, ''
        # 还未开始执行，队列中或解析参数中
        return self.JobStatus.Running, ''

    def get_job_log(self):
        """
        获取任务执行日志
        :return: 日志内容
        """
        log_path = os.path.join(self.model_output_dir, 'trainer_log.jsonl')
        if not os.path.exists(log_path):
            logger.info(f'log not found, [{log_path}] is not exist')
            return ''
        with open(log_path, 'r') as f:
            return f.read()
    
    def write_result(self, exit_code: int, stdout: str, stderr: str):
        """
        将执行结果写入Redis
        """
        try:
            redis_client.set_no_expiration(self.exit_code_key, int(exit_code))
            redis_client.set_no_expiration(self.stdout_key, stdout)
            redis_client.set_no_expiration(self.stderr_key, stderr)
        except Exception as e:
            logger.error(f"Error writing results to Redis: {e}")
            # 即使Redis写入失败，也不要抛出异常，让流程继续
    
    def delete_result(self):
        redis_client.delete(self.exit_code_key)
        redis_client.delete(self.stdout_key)
        redis_client.delete(self.stderr_key)
        shutil.rmtree(self.job_exec_dir)
    
    def set_exec_lock_key(self):
        """
        设置任务锁，防止同一任务被重复执行
        返回：成功返回True，失败返回False
        """
        try:
            print("set_exec_lock_key:{}".format(self.exec_lock_key))
            result = redis_client.setNx(self.exec_lock_key, 1)
            return result is True
        except Exception as e:
            logger.error(f"Failed to set exec lock key: {e}")
            return False
    
    def delete_exec_lock_key(self):
        redis_client.delete(self.exec_lock_key)
        
    def parse_commands(self, commands):
        pass
