from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from app.dependencies.jobs.runners import get_job_runner
from app.dependencies.jobs.registry import get_job_registry
from app.dependencies.jobs.job import BatchJob, Job
from app.schemas import BaseModel

"""
Same contract endpoints as V1, but supporting batching the jobs
"""

router = APIRouter(
    prefix="/v2/consistency",
    tags=["consistency_v2"],
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
async def create_batch_job(
    payload: ConsistencyJobRequest,
    runner=Depends(get_job_runner("consistency")),
    registry=Depends(get_job_registry),
    batch_size: int = 4,
):
    if payload.num_hands > 1_000_000:
        raise HTTPException(
            status_code=400,
            detail="Requested test hands exceeds maximum permitted",
        )

    if len(payload.names) != len(payload.ratios):
        raise HTTPException(
            status_code=400,
            detail="names and ratios must be the same length",
        )

    jobs: list[Job] = []
    hands_per_job = payload.num_hands // batch_size
    for _ in range(batch_size):
        job = Job(
            payload={
                "deckcount": payload.deckcount,
                "names": payload.names,
                "ratios": payload.ratios,
                "ideal_hands": payload.ideal_hands,
                "num_hands": hands_per_job,
                "use_gambling": payload.use_gambling,
            }
        )
        jobs.append(job)

    batch = BatchJob(jobs=jobs)

    try:
        # store jobs in registry
        batch_id = await registry.create_batch(batch)

        # trigger each job
        for job in batch.jobs:
            await runner.run_job(job)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invoke Lambda: {e}",
        )

    return ConsistencyJobResponse(job_id=batch_id, status="pending")


@router.get("/jobs/{batch_id}", response_model=ConsistencyJobResponse)
async def get_batch_job_status(
    batch_id: str,
    registry=Depends(get_job_registry),
):
    batch: BatchJob = await registry.get_batch_job(batch_id)

    if not batch.jobs:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Determine batch status
    statuses = {job.status for job in batch.jobs}
    if "failed" in statuses:
        status = "failed"
    elif "pending" in statuses or "running" in statuses:
        status = "running"
    elif all(job.status == "completed" for job in batch.jobs):
        status = "completed"
    else:
        status = "unknown"

    # Aggregate results if all complete
    aggregated_result = None
    if status == "completed":
        aggregated_result = {}
        for job in batch.jobs:
            if job.result:
                for k, v in job.result.items():
                    aggregated_result[k] = aggregated_result.get(k, 0) + v

    return ConsistencyJobResponse(
        job_id=batch.batch_id,
        status=status,
        result=aggregated_result,
    )
