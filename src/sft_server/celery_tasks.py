from celery import Celery
from sft_server.sft_manage import SFTManage
celery_app = Celery(
    "finetune_tasks",
    broker="redis://localhost:6379/0"
)

@celery_app.task()
def finetune_task(job_id: str, options: str, commands: dict):
    sft_manage = SFTManage()
    sft_manage.finetune(job_id, options, commands)