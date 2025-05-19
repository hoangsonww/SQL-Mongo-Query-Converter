# 1) Build stage: install the package into a clean image
FROM python:3.9-slim AS builder

LABEL org.opencontainers.image.source="https://github.com/hoangsonww/SQL-Mongo-Query-Converter"
LABEL org.opencontainers.image.description="sql_mongo_converter: convert SQL ↔ MongoDB queries."

WORKDIR /app

# copy only what's needed to install
COPY setup.py README.md ./
COPY sql_mongo_converter/ ./sql_mongo_converter/

# install package (and cache dependencies)
RUN pip install --no-cache-dir .

# 2) Final runtime image
FROM python:3.9-slim

WORKDIR /app

# copy installed package from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages/sql_mongo_converter* \
     /usr/local/lib/python3.9/site-packages/

# copy any entrypoint script if you have one, or just expose it
# e.g. an entrypoint.py that calls your package
# COPY entrypoint.py ./

# default command: show help
CMD ["python", "-m", "sql_mongo_converter", "--help"]
