from typing import List
from collections import Counter
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


def aggregate_batch_results(results: List[dict]) -> dict:
    if not results:
        return {}

    total_hands = sum(r.get("num_hands", 0) for r in results)
    if total_hands == 0:
        total_hands = 1  # avoid division by zero

    # Weighted averages for probabilities
    def weighted_avg(key: str):
        return sum(r.get(key, 0) * r.get("num_hands", 0) for r in results) / total_hands

    p5 = weighted_avg("p5")
    p6 = weighted_avg("p6")
    p5_with_gambling = weighted_avg("p5_with_gambling")
    p6_with_gambling = weighted_avg("p6_with_gambling")

    # Sum dictionaries
    def sum_dicts(keys: List[str]):
        agg = {}
        for key in keys:
            for r in results:
                for k, v in r.get(key, {}).items():
                    agg[k] = agg.get(k, 0) + v
        return agg

    matched_pattern_counts_5 = sum_dicts(["matched_pattern_counts_5"])
    matched_pattern_counts_6 = sum_dicts(["matched_pattern_counts_6"])
    matched_pattern_counts_5_withgamble = sum_dicts(
        ["matched_pattern_counts_5_withgamble"])
    matched_pattern_counts_6_withgamble = sum_dicts(
        ["matched_pattern_counts_6_withgamble"])

    # Sum scalar integers
    int_keys = [
        "rescued_5", "rescued_6",
        "gamble_attempted_5", "gamble_attempted_6",
        "gamble_failed_5", "gamble_failed_6",
        "gamble_unplayable_5", "gamble_unplayable_6",
    ]
    summed_ints = {k: sum(r.get(k, 0) for r in results) for k in int_keys}

    # Sum Counter-like dicts
    counter_keys = [
        "useful_gambles_5", "useful_gambles_6",
        "gamble_seen_5", "gamble_seen_6",
        "near_miss_counts", "blocking_card_counts",
        "ideal_hand_counts",
    ]
    summed_counters = {}
    for key in counter_keys:
        agg = Counter()
        for r in results:
            agg.update(r.get(key, {}))
        summed_counters[key] = dict(agg)

    return {
        "num_hands": total_hands,
        "used_gambling": results[0].get("used_gambling", False),
        "p5": p5,
        "p6": p6,
        "p5_with_gambling": p5_with_gambling,
        "p6_with_gambling": p6_with_gambling,
        "matched_pattern_counts_5": matched_pattern_counts_5,
        "matched_pattern_counts_6": matched_pattern_counts_6,
        "matched_pattern_counts_5_withgamble": matched_pattern_counts_5_withgamble,
        "matched_pattern_counts_6_withgamble": matched_pattern_counts_6_withgamble,
        **summed_ints,
        **summed_counters,
    }


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
        aggregated_result = aggregate_batch_results([job.result for job in batch.jobs if job.result])

    return ConsistencyJobResponse(
        job_id=batch.batch_id,
        status=status,
        result=aggregated_result,
    )
