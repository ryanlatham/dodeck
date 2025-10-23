from __future__ import annotations

from functools import lru_cache

import boto3
from botocore.config import Config

from .settings import settings


def _create_resource():
    config = Config(retries={"max_attempts": 3, "mode": "standard"})
    kwargs = {
        "region_name": settings.aws_region,
        "config": config,
    }
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url

    return boto3.resource("dynamodb", **kwargs)


@lru_cache(maxsize=1)
def get_table():
    resource = _create_resource()
    return resource.Table(settings.table_name)
