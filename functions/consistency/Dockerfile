FROM python:3.14-slim-trixie AS build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


FROM build AS dev-build

ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=0
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked


FROM build AS prod-build

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_INSTALLER_METADATA=1
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv export --frozen --no-emit-workspace --no-dev --no-editable -o requirements.txt && \
    uv pip install -r requirements.txt --target /app
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked


FROM public.ecr.aws/lambda/python:3.14

COPY --from=prod-build /app ${LAMBDA_TASK_ROOT}
CMD ["app.main.lambda_handler"]
