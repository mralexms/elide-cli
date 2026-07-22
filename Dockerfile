# Builds the eliude-cli wheel. The build itself runs at `docker run` time
# (not at `docker build` time) so the result lands in whatever directory is
# volume-mounted at /dist, e.g.:
#   docker build -t eliude-cli-builder .
#   docker run --rm -v "$PWD/../dist:/dist" eliude-cli-builder
# (or via docker-compose: `docker compose run --rm cli-builder`)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /src

RUN pip install --no-cache-dir build

COPY . .

CMD ["python", "-m", "build", "--wheel", "--outdir", "/dist"]
