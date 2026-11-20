FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 fastest \
    && useradd --uid 10001 --gid 10001 fastest

ENV PORT=8000 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/fastest/production

COPY production/fastest_release/__init__.py production/fastest_release/__main__.py \
     production/fastest_release/advisor.py production/fastest_release/api.py production/fastest_release/artifacts.py \
     production/fastest_release/healthcheck.py production/fastest_release/http.py \
     production/fastest_release/profiles.py production/fastest_release/research.py production/fastest_release/scaling.py \
     production/fastest_release/validation.py production/fastest_release/profile-interaction.js ./fastest_release/
COPY production/fastest_cost/*.py production/fastest_cost/illustrative.json ./fastest_cost/
COPY production/fastest_fit/__init__.py production/fastest_fit/page.py ./fastest_fit/
COPY production/fastest_goals/*.py ./fastest_goals/
COPY production/fastest_image/__init__.py production/fastest_image/__main__.py production/fastest_image/intake.py production/fastest_image/render.py production/fastest_image/plan.json ./fastest_image/
COPY production/fastest_prices/__init__.py production/fastest_prices/artifacts.py production/fastest_prices/result.py production/fastest_prices/validation.py ./fastest_prices/
COPY production/fastest_text/*.py production/fastest_text/plan.json ./fastest_text/
COPY production/fastest_serving/__init__.py ./fastest_serving/
COPY production/fastest_pilot_bundle.py ./
COPY opendesign/mockups/llm-observatory/catalog-hardware-sources.json opendesign/mockups/llm-observatory/catalog-hardware.json opendesign/mockups/llm-observatory/catalog-identities.json opendesign/mockups/llm-observatory/catalog-runtimes.json /opt/fastest/opendesign/mockups/llm-observatory/

USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=60s --timeout=15s --start-period=5s CMD python -m fastest_release.healthcheck "http://127.0.0.1:$PORT"
ENTRYPOINT ["tini", "--", "sh", "-c", "exec python -m fastest_release serve --trusted-host \"127.0.0.1:$PORT\" \"$@\" --host 0.0.0.0 --port \"$PORT\"", "fastest-release"]
