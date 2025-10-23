from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from .dynamodb import get_table


class RepositoryError(Exception):
    """Base repository error."""


class DuplicateCollaboratorError(RepositoryError):
    """Raised when collaborator already attached."""


class CollaboratorNotFoundError(RepositoryError):
    """Raised when collaborator is missing."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _deck_pk(deck_id: str) -> str:
    return f"DECK#{deck_id}"


def _deck_sk(deck_id: str) -> str:
    return "DECK"


def _do_sk(do_id: str) -> str:
    return f"DO#{do_id}"


def _owner_access_pk(owner_sub: str) -> str:
    return f"ACCESS#USER#{owner_sub}"


def _collab_access_pk(email: str) -> str:
    return f"ACCESS#EMAIL#{email}"


def _access_sk(name_lower: str, deck_id: str) -> str:
    return f"DECK#{name_lower}#{deck_id}"


def _chunk(items: List[dict], size: int = 25) -> Iterable[List[dict]]:
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]


def create_deck(owner_sub: str, name: str) -> Dict[str, Any]:
    table = get_table()
    client = table.meta.client
    deck_id = str(uuid4())
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("name required")
    name_lower = clean_name.lower()
    now = _now_iso()

    deck_item = {
        "PK": _deck_pk(deck_id),
        "SK": _deck_sk(deck_id),
        "deckId": deck_id,
        "name": clean_name,
        "nameLower": name_lower,
        "ownerSub": owner_sub,
        "collaborators": {},
        "createdAt": now,
        "updatedAt": now,
    }

    owner_access_item = {
        "PK": _owner_access_pk(owner_sub),
        "SK": _access_sk(name_lower, deck_id),
        "deckId": deck_id,
        "name": clean_name,
        "nameLower": name_lower,
        "ownerSub": owner_sub,
        "access": "owner",
    }

    client.transact_write_items(
        TransactItems=[
            {
                "Put": {
                    "TableName": table.name,
                    "Item": deck_item,
                    "ConditionExpression": "attribute_not_exists(PK)",
                }
            },
            {
                "Put": {
                    "TableName": table.name,
                    "Item": owner_access_item,
                }
            },
        ]
    )
    return deck_item


def _query_all(table, **kwargs):
    results: List[Dict[str, Any]] = []
    response = table.query(**kwargs)
    results.extend(response.get("Items", []))
    while "LastEvaluatedKey" in response:
        kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        response = table.query(**kwargs)
        results.extend(response.get("Items", []))
    return results


def list_access_rows(owner_sub: str, email: Optional[str], visibility: str, search: Optional[str]) -> List[Dict[str, Any]]:
    table = get_table()
    condition_search = None
    if search:
        search_lower = search.lower()
        condition_search = Key("SK").begins_with(f"DECK#{search_lower}")

    items: List[Dict[str, Any]] = []

    def _query(pk_value: str):
        key_condition = Key("PK").eq(pk_value)
        if condition_search is not None:
            key_condition = key_condition & condition_search
        return _query_all(table, KeyConditionExpression=key_condition)

    if visibility in {"mine", "all"}:
        items.extend(_query(_owner_access_pk(owner_sub)))
    if visibility in {"shared", "all"} and email:
        items.extend(_query(_collab_access_pk(email)))

    # Deduplicate by deckId keeping owner preference
        dedup: Dict[str, Dict[str, Any]] = {}
    for item in items:
        deck_id = item["deckId"]
        existing = dedup.get(deck_id)
        if not existing or item.get("access") == "owner":
            dedup[deck_id] = item
    return list(dedup.values())


def batch_load_decks(deck_ids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    table = get_table()
    client = table.meta.client
    keys = [
        {"PK": _deck_pk(deck_id), "SK": _deck_sk(deck_id)}
        for deck_id in deck_ids
    ]
    if not keys:
        return {}

    result: Dict[str, Dict[str, any]] = {}
    for chunk in _chunk(keys, size=100):
        response = client.batch_get_item(
            RequestItems={table.name: {"Keys": chunk}}
        )
        for item in response.get("Responses", {}).get(table.name, []):
            result[item["deckId"]] = item
    return result


def get_deck(deck_id: str) -> Optional[Dict[str, Any]]:
    table = get_table()
    response = table.get_item(
        Key={"PK": _deck_pk(deck_id), "SK": _deck_sk(deck_id)}
    )
    return response.get("Item")


def rename_deck(deck: Dict[str, Any], new_name: str) -> Dict[str, Any]:
    table = get_table()
    client = table.meta.client
    deck_id = deck["deckId"]
    new_clean = new_name.strip()
    if not new_clean:
        raise ValueError("name required")
    new_lower = new_clean.lower()
    now = _now_iso()

    update = {
        "Update": {
            "TableName": table.name,
            "Key": {"PK": _deck_pk(deck_id), "SK": _deck_sk(deck_id)},
            "UpdateExpression": "SET #n = :name, nameLower = :nameLower, updatedAt = :now",
            "ConditionExpression": "ownerSub = :owner",
            "ExpressionAttributeNames": {"#n": "name"},
            "ExpressionAttributeValues": {
                ":name": new_clean,
                ":nameLower": new_lower,
                ":now": now,
                ":owner": deck["ownerSub"],
            },
        }
    }

    operations = [update]

    old_lower = deck.get("nameLower", new_lower)
    owner_sub = deck["ownerSub"]
    operations.append(
        {
            "Delete": {
                "TableName": table.name,
                "Key": {
                    "PK": _owner_access_pk(owner_sub),
                    "SK": _access_sk(old_lower, deck_id),
                },
            }
        }
    )
    operations.append(
        {
            "Put": {
                "TableName": table.name,
                "Item": {
                    "PK": _owner_access_pk(owner_sub),
                    "SK": _access_sk(new_lower, deck_id),
                    "deckId": deck_id,
                    "name": new_clean,
                    "nameLower": new_lower,
                    "ownerSub": owner_sub,
                    "access": "owner",
                },
            }
        }
    )

    collaborators = deck.get("collaborators") or {}
    for email in collaborators.keys():
        operations.append(
            {
                "Delete": {
                    "TableName": table.name,
                    "Key": {
                        "PK": _collab_access_pk(email),
                        "SK": _access_sk(old_lower, deck_id),
                    },
                }
            }
        )
        operations.append(
            {
                "Put": {
                    "TableName": table.name,
                    "Item": {
                        "PK": _collab_access_pk(email),
                        "SK": _access_sk(new_lower, deck_id),
                        "deckId": deck_id,
                        "name": new_clean,
                        "nameLower": new_lower,
                        "ownerSub": owner_sub,
                        "access": "collaborator",
                    },
                }
            }
        )

    for chunk in _chunk(operations, size=25):
        client.transact_write_items(TransactItems=chunk)

    deck["name"] = new_clean
    deck["nameLower"] = new_lower
    deck["updatedAt"] = now
    return deck


def delete_deck(deck: Dict[str, Any]) -> None:
    table = get_table()
    client = table.meta.client
    deck_id = deck["deckId"]
    pk = _deck_pk(deck_id)

    items = _query_all(table, KeyConditionExpression=Key("PK").eq(pk))
    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})

    access_operations = [
        {
            "Delete": {
                "TableName": table.name,
                "Key": {
                    "PK": _owner_access_pk(deck["ownerSub"]),
                    "SK": _access_sk(deck.get("nameLower", ""), deck_id),
                },
            }
        }
    ]
    collaborators = deck.get("collaborators") or {}
    for email in collaborators.keys():
        access_operations.append(
            {
                "Delete": {
                    "TableName": table.name,
                    "Key": {
                        "PK": _collab_access_pk(email),
                        "SK": _access_sk(deck.get("nameLower", ""), deck_id),
                    },
                }
            }
        )

    for chunk in _chunk(access_operations, size=25):
        client.transact_write_items(TransactItems=chunk)


def add_collaborator(deck: Dict[str, Any], email: str) -> Dict[str, Any]:
    table = get_table()
    client = table.meta.client
    deck_id = deck["deckId"]
    now = _now_iso()
    expression_names = {"#email": email}
    expression_values = {
        ":meta": {"addedAt": now},
        ":owner": deck["ownerSub"],
        ":now": now,
    }

    try:
        client.transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "TableName": table.name,
                        "Key": {"PK": _deck_pk(deck_id), "SK": _deck_sk(deck_id)},
                        "UpdateExpression": "SET updatedAt = :now, collaborators.#email = :meta",
                        "ConditionExpression": "ownerSub = :owner AND attribute_not_exists(collaborators.#email)",
                        "ExpressionAttributeNames": expression_names,
                        "ExpressionAttributeValues": expression_values,
                    }
                },
                {
                    "Put": {
                        "TableName": table.name,
                        "Item": {
                            "PK": _collab_access_pk(email),
                            "SK": _access_sk(deck.get("nameLower", ""), deck_id),
                            "deckId": deck_id,
                            "name": deck["name"],
                            "nameLower": deck.get("nameLower", ""),
                            "ownerSub": deck["ownerSub"],
                            "access": "collaborator",
                        },
                    }
                },
            ]
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] in {"ConditionalCheckFailedException", "TransactionCanceledException"}:
            raise DuplicateCollaboratorError from exc
        raise

    collaborators = deck.setdefault("collaborators", {})
    collaborators[email] = {"addedAt": now}
    deck["updatedAt"] = now
    return deck


def remove_collaborator(deck: Dict[str, Any], email: str) -> Dict[str, Any]:
    table = get_table()
    client = table.meta.client
    deck_id = deck["deckId"]
    now = _now_iso()

    try:
        client.transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "TableName": table.name,
                        "Key": {"PK": _deck_pk(deck_id), "SK": _deck_sk(deck_id)},
                        "UpdateExpression": "REMOVE collaborators.#email SET updatedAt = :now",
                        "ConditionExpression": "ownerSub = :owner AND attribute_exists(collaborators.#email)",
                        "ExpressionAttributeNames": {"#email": email},
                        "ExpressionAttributeValues": {
                            ":owner": deck["ownerSub"],
                            ":now": now,
                        },
                    }
                },
                {
                    "Delete": {
                        "TableName": table.name,
                        "Key": {
                            "PK": _collab_access_pk(email),
                            "SK": _access_sk(deck.get("nameLower", ""), deck_id),
                        },
                    }
                },
            ]
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] in {"ConditionalCheckFailedException", "TransactionCanceledException"}:
            raise CollaboratorNotFoundError from exc
        raise

    collaborators = deck.get("collaborators") or {}
    collaborators.pop(email, None)
    deck["updatedAt"] = now
    return deck


def list_dos(deck_id: str) -> List[Dict[str, Any]]:
    table = get_table()
    items = _query_all(
        table,
        KeyConditionExpression=Key("PK").eq(_deck_pk(deck_id)),
    )
    dos = [item for item in items if item["SK"].startswith("DO#")]
    return dos


def get_do(deck_id: str, do_id: str) -> Optional[Dict[str, Any]]:
    table = get_table()
    response = table.get_item(
        Key={"PK": _deck_pk(deck_id), "SK": _do_sk(do_id)}
    )
    return response.get("Item")


def create_do(deck_id: str, text: str) -> Dict[str, Any]:
    table = get_table()
    do_id = str(uuid4())
    now = _now_iso()
    item = {
        "PK": _deck_pk(deck_id),
        "SK": _do_sk(do_id),
        "deckId": deck_id,
        "doId": do_id,
        "text": text.strip(),
        "completed": False,
        "createdAt": now,
        "updatedAt": now,
    }
    table.put_item(Item=item, ConditionExpression="attribute_not_exists(PK)")
    return item


def update_do(do_item: Dict[str, Any], text: Optional[str], completed: Optional[bool]) -> Dict[str, Any]:
    table = get_table()
    now = _now_iso()
    update_expr_parts: List[str] = []
    expr_attr_values: Dict[str, Any] = {":now": now}
    expr_attr_names: Dict[str, str] = {}

    if text is not None:
        update_expr_parts.append("#text = :text")
        expr_attr_values[":text"] = text.strip()
        expr_attr_names["#text"] = "text"
        do_item["text"] = text.strip()
    if completed is not None:
        update_expr_parts.append("completed = :completed")
        expr_attr_values[":completed"] = completed
        do_item["completed"] = completed

    if not update_expr_parts:
        return do_item

    update_expr_parts.append("updatedAt = :now")

    update_kwargs = {
        "Key": {"PK": _deck_pk(do_item["deckId"]), "SK": _do_sk(do_item["doId"])},
        "UpdateExpression": "SET " + ", ".join(update_expr_parts),
        "ExpressionAttributeValues": expr_attr_values,
    }
    if expr_attr_names:
        update_kwargs["ExpressionAttributeNames"] = expr_attr_names

    table.update_item(**update_kwargs)

    do_item["updatedAt"] = now
    return do_item


def delete_do(deck_id: str, do_id: str) -> None:
    table = get_table()
    table.delete_item(Key={"PK": _deck_pk(deck_id), "SK": _do_sk(do_id)})
