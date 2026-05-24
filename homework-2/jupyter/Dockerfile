FROM jupyter/scipy-notebook:python-3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*
USER ${NB_UID}

RUN pip install --no-cache-dir \
    psycopg2-binary==2.9.9 \
    sqlalchemy==2.0.27 \
    pyarrow==15.0.0 \
    s3fs==2024.2.0 \
    boto3==1.34.39 \
    minio==7.2.4 \
    scikit-learn==1.4.0 \
    seaborn==0.13.2 \
    plotly==5.18.0
