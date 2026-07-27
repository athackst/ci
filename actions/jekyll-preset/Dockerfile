FROM ruby:3.3.4-slim-bookworm

ARG SEMILITERATE_REF=402ba963ac40968b999dda76ec1c2e9f1ba70f92

ENV BUNDLE_GEMFILE=/opt/jekyll-preset/Gemfile \
    PATH=/opt/semiliterate/bin:${PATH}

RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
        build-essential \
        git \
        python3 \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/semiliterate \
    && python -m pip install --no-cache-dir --upgrade pip==26.1.2 \
    && python -m pip install --no-cache-dir \
        PyYAML==6.0.3 \
        "semiliterate @ git+https://github.com/PrimerPages/semiliterate.git@${SEMILITERATE_REF}"

COPY Gemfile Gemfile.lock /opt/jekyll-preset/
RUN bundle install --jobs 4 --retry 3

COPY _config.yml /opt/jekyll-preset/_config.yml.in
COPY semiliterate.yml /opt/jekyll-preset/semiliterate.yml
COPY render_jekyll_config.py /opt/jekyll-preset/render_jekyll_config.py
COPY entrypoint.sh /entrypoint.sh

RUN mkdir --parents /workspace \
    && chmod 777 /workspace

WORKDIR /github/workspace
ENTRYPOINT ["bash", "/entrypoint.sh"]
