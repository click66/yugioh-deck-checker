from fastapi import Request


def get_job_runner(key: str):
    async def _get_runner(request: Request):
        runners = request.app.state.job_runners
        if key not in runners:
            raise RuntimeError(f"No runner found for key {key}")
        return runners[key]
    return _get_runner
