from fastapi import FastAPI, Body
from fastapi.responses import ORJSONResponse
from fastapi.exceptions import RequestValidationError
import sys
import uvicorn
from celery_tasks import finetune_task
from loguru import logger
from sft_manage import SFTManage
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/v1.0/sft/job")
async def finetune(job_id: str=Body(...), options: str=Body(...), commands: dict=Body(...)):
    logger.info(f"Finetune task started: {job_id}, {options}, {commands}")
    # 异步调用接口，不会立即执行，而是将任务添加到队列中，等待执行
    finetune_task.delay(job_id, options, commands)
    return {"status_code": 200, "status_message": "success"}

@app.get('/v2.1/sft/model')
def get_all_model():
    model_list = SFTManage.get_all_model()
    return {"status_code": 200, "status_message": "success", "data": model_list}


@app.post("/v1.0/sft/job/status")
async def job_status(job_id: str=Body(...)):
    sft_manage = SFTManage()
    status = sft_manage.get_job_status(job_id)
    return {"status_code": 200, "status_message": "success", "status": status}

@app.delete("/v1.0/sft/job")
async def delete_job(job_id: str=Body(...)):
    sft_manage = SFTManage()
    sft_manage.delete_job(job_id)
    return {"status_code": 200, "status_message": "success"}

@app.post("/v1.0/sft/job/cancel")
async def cancel_job(job_id: str=Body(...)):
    sft_manage = SFTManage()
    sft_manage.cancel_job(job_id)
    return {"status_code": 200, "status_message": "success"}

@app.post("/v1.0/sft/job/log")
async def get_job_log(job_id: str=Body(...)):
    sft_manage = SFTManage()
    log = sft_manage.get_job_log(job_id)
    return {"status_code": 200, "status_message": "success", "log": log}

@app.post("/v1.0/sft/job/publish")
async def publish_job(job_id: str=Body(...), model_name: str=Body(...)):
    sft_manage = SFTManage(job_id)
    sft_manage.publish_job(model_name)
    return {"status_code": 200, "status_message": "success"}

@app.post("/v1.0/sft/job/cancel_publish")
async def cancel_publish_job(job_id: str=Body(...), model_name: str=Body(...)):
    sft_manage = SFTManage(job_id)
    sft_manage.cancel_publish_job(model_name)
    return {"status_code": 200, "status_message": "success"}

@app.get("/v1.0/sft/job/model_list")
async def get_model_list():
    model_list = SFTManage.get_model_list()
    return {"status_code": 200, "status_message": "success", "data": model_list}

if __name__ == "__main__":
    port = 8001
    if sys.argv.__len__() > 1:
        port = int(sys.argv[1])
    uvicorn.run(app, host="0.0.0.0", port=port)