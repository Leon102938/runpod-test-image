# /workspace/app/main.py
from fastapi import FastAPI, BackgroundTasks
from .wan_api import (
    TI2VRequest,
    run_wan_ti2v,
    submit_job,
    get_status,
    get_result,
    WAN_ROOT, WAN_CKPT
)


from .thinksound_api import (
    TSRequest, run_thinksound, submit_ts_job, get_ts_status, get_ts_result
)

app = FastAPI(title="WAN 2.2 API", version="1.1")

@app.get("/health")
def health():
    return {"status":"ok","WAN_ROOT":WAN_ROOT,"WAN_CKPT_DIR":WAN_CKPT}

# ---- Sync (blockierend, wie gehabt) ----
@app.post("/wan/generate")
def wan_generate(request: TI2VRequest):
    return run_wan_ti2v(request)

# ---- Async Pattern: Submit → Status → Result ----
@app.post("/wan/submit")
def wan_submit(request: TI2VRequest, bg: BackgroundTasks):
    job_id = submit_job(request)
    return {"ok": True, "job_id": job_id}

@app.get("/wan/status/{job_id}")
def wan_status(job_id: str):
    return get_status(job_id)

@app.get("/wan/result/{job_id}")
def wan_result(job_id: str):
    return get_result(job_id)

@app.post("/thinksound/generate")
def ts_generate(request: TSRequest):
    return run_thinksound(request)

@app.post("/thinksound/submit")
def ts_submit(request: TSRequest):
    job_id = submit_ts_job(request)
    return {"ok": True, "job_id": job_id}

@app.get("/thinksound/status/{job_id}")
def ts_status(job_id: str):
    return get_ts_status(job_id)

@app.get("/thinksound/result/{job_id}")
def ts_result(job_id: str):
    return get_ts_result(job_id)



