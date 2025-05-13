from celery import Celery
from sft_manage import SFTManage
from settings import settings
celery_app = Celery(
    "finetune_tasks",
    broker=settings.redis_url
)

@celery_app.task()
def finetune_task(job_id: str, options: str, commands: dict):
    sft_manage = SFTManage(job_id)
    sft_manage.run_job(options, commands)