"""Reserve seats using a local or real DynamoDB-compatible client."""

import os
from threading import Barrier

import boto3
from botocore.exceptions import ClientError


LOCAL_ENDPOINT = "https://127.0.0.1:9297"


def create_dynamodb_resource():
    """Create a DynamoDB resource pointed only at the local emulator."""
    endpoint = os.environ.get("AWS_ENDPOINT_URL", "").rstrip("/")
    if endpoint != LOCAL_ENDPOINT:
        raise RuntimeError(
            f"This demo only runs against the local emulator at {LOCAL_ENDPOINT}."
        )
    return boto3.resource("dynamodb", endpoint_url=LOCAL_ENDPOINT, region_name="us-east-1")


def reserve_seat(table, show_id: str, ready_barrier: Barrier | None = None) -> dict:
    """Try to reserve one seat for a show.

    The optional barrier is used by the demo test to make two requests reach the
    inventory update together. DynamoDB evaluates the condition and update as one
    atomic operation, so only one request can claim the last seat.
    """
    if ready_barrier is not None:
        ready_barrier.wait(timeout=10)

    try:
        response = table.update_item(
            Key={"show_id": show_id},
            UpdateExpression="SET remaining = remaining - :one",
            ConditionExpression="remaining >= :one",
            ExpressionAttributeValues={":one": 1},
            ReturnValues="UPDATED_NEW",
        )
        return {"reserved": True, "remaining": int(response["Attributes"]["remaining"])}
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {"reserved": False, "reason": "sold out"}
        raise
