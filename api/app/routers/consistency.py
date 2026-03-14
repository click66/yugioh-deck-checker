from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from typing import List, Optional
import uuid

from app.dependencies.jobs.runners import get_job_runner
from app.dependencies.jobs.registry import get_job_registry
from app.dependencies.jobs.job import Job
from app.logger import logger
from app.schemas import BaseModel


router = APIRouter(
    prefix="/consistency",
    tags=["consistency"],
)


class ConsistencyJobRequest(BaseModel):
    deckcount: int
    names: List[str]
    ratios: List[int]
    ideal_hands: List[List[str]]
    num_hands: int
    use_gambling: Optional[bool] = None


class ConsistencyJobError(BaseModel):
    code: str
    detail: str


class ConsistencyJobResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[ConsistencyJobError] = None


@router.post("/jobs/create", response_model=ConsistencyJobResponse)
async def create_job(
    payload: ConsistencyJobRequest,
    runner=Depends(get_job_runner("consistency")),
    registry=Depends(get_job_registry),
):
    if len(payload.names) != len(payload.ratios):
        raise HTTPException(
            status_code=400,
            detail="names and ratios must be the same length",
        )

    job_id = str(uuid.uuid4())

    job = Job(
        job_id=job_id,
        payload={
            "deckcount": payload.deckcount,
            "names": payload.names,
            "ratios": payload.ratios,
            "ideal_hands": payload.ideal_hands,
            "num_hands": payload.num_hands,
            "use_gambling": payload.use_gambling,
        },
    )

    try:
        await registry.create_job(job)
        await runner.run_job(job)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invoke Lambda: {e}",
        )

    response_data = {"job_id": job_id, "status": job.status}
    if hasattr(job, "result") and job.result is not None:
        response_data["result"] = job.result

    return ConsistencyJobResponse(**response_data)


@router.get("/jobs/{job_id}", response_model=ConsistencyJobResponse)
async def get_job_status(
    job_id: str,
    registry=Depends(get_job_registry),
):
    job = await registry.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    response_data = {"job_id": job.job_id, "status": job.status}

    if hasattr(job, "result") and job.result is not None:
        response_data["result"] = job.result

    if hasattr(job, "error") and job.error is not None:
        response_data["error"] = job.error

    try:
        return ConsistencyJobResponse(**response_data)
    except ValidationError as e:
        logger.info(
            f"Failed to construct ConsistencyJobResponse for job {job_id}: {e}",
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to construct response: {e}",
        )
