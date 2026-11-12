from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest

from reservations import create_dynamodb_resource, reserve_seat


@pytest.fixture
def show_table():
    dynamodb = create_dynamodb_resource()
    table_name = f"seat-demo-{uuid4().hex[:12]}"
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": "show_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "show_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    table.put_item(Item={"show_id": "concert-1", "remaining": 1})
    try:
        yield table
    finally:
        table.delete()


def test_only_one_person_gets_the_last_seat(show_table):
    """Two simultaneous requests for one seat must not oversell it."""
    both_requests_ready = Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda _: reserve_seat(show_table, "concert-1", both_requests_ready),
                range(2),
            )
        )

    assert sum(result["reserved"] for result in results) == 1
    assert sum(not result["reserved"] for result in results) == 1
    assert show_table.get_item(Key={"show_id": "concert-1"})["Item"]["remaining"] == 0
