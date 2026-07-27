FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install --no-install-recommends --yes git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /opt/mkdocs-preset/requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir --requirement /opt/mkdocs-preset/requirements.txt

COPY mkdocs.yml /opt/mkdocs-preset/mkdocs.yml.in
COPY overrides /opt/mkdocs-preset/overrides
COPY render_mkdocs_config.py /opt/mkdocs-preset/render_mkdocs_config.py
COPY entrypoint.sh /entrypoint.sh

RUN mkdir --parents /workspace \
    && chmod 777 /workspace

WORKDIR /github/workspace
ENTRYPOINT ["bash", "/entrypoint.sh"]
