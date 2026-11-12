"""Intentionally buggy starting point for the seat reservation demo."""

from threading import Barrier

from botocore.exceptions import ClientError


def reserve_seat(table, show_id: str, ready_barrier: Barrier | None = None) -> dict:
    """Try to reserve a seat, but incorrectly allow inventory below zero."""
    if ready_barrier is not None:
        ready_barrier.wait(timeout=10)

    try:
        response = table.update_item(
            Key={"show_id": show_id},
            UpdateExpression="SET remaining = remaining - :one",
            ExpressionAttributeValues={":one": 1},
            ReturnValues="UPDATED_NEW",
        )
        return {"reserved": True, "remaining": int(response["Attributes"]["remaining"])}
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {"reserved": False, "reason": "sold out"}
        raise
