import json
import sqlite3
from pathlib import Path
from typing import Any

from .database import connect


class CustomerServiceRepository:
    def __init__(self, database_path: Path | str):
        self.database_path = Path(database_path)

    def _execute(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        connection = connect(self.database_path)
        cursor = connection.execute(sql, params)
        connection.commit()
        connection.close()
        return cursor

    def _fetch_one(self, sql: str, params: tuple[Any, ...]) -> dict[str, Any] | None:
        with connect(self.database_path) as connection:
            row = connection.execute(sql, params).fetchone()
            return dict(row) if row else None

    def _fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with connect(self.database_path) as connection:
            rows = connection.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def get_order(self, order_id: str, customer_id: str) -> dict[str, Any] | None:
        return self._fetch_one(
            "SELECT * FROM orders WHERE order_id = ? AND customer_id = ?",
            (order_id, customer_id),
        )

    def list_orders(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM orders ORDER BY paid_at DESC, order_id DESC")

    def get_logistics(self, order_id: str, customer_id: str) -> dict[str, Any] | None:
        return self._fetch_one(
            """
            SELECT logistics.*
            FROM logistics
            JOIN orders ON logistics.order_id = orders.order_id
            WHERE logistics.order_id = ? AND orders.customer_id = ?
            """,
            (order_id, customer_id),
        )

    def create_repair_ticket(self, payload: dict[str, Any]) -> dict[str, Any]:
        with connect(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO repair_tickets(order_id, customer_id, issue_type, description, contact)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    payload["order_id"],
                    payload["customer_id"],
                    payload["issue_type"],
                    payload["description"],
                    payload["contact"],
                ),
            )
            connection.commit()
            ticket_id = cursor.lastrowid
        return self.get_ticket(ticket_id)

    def get_ticket(self, ticket_id: int) -> dict[str, Any]:
        ticket = self._fetch_one("SELECT * FROM repair_tickets WHERE id = ?", (ticket_id,))
        if ticket is None:
            raise ValueError(f"ticket {ticket_id} not found")
        return ticket

    def list_tickets(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM repair_tickets ORDER BY id DESC")

    def create_refund(self, payload: dict[str, Any]) -> dict[str, Any]:
        with connect(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO refunds(order_id, customer_id, amount, reason)
                VALUES (?, ?, ?, ?)
                """,
                (payload["order_id"], payload["customer_id"], payload["amount"], payload["reason"]),
            )
            connection.commit()
            refund_id = cursor.lastrowid
        refund = self._fetch_one("SELECT * FROM refunds WHERE id = ?", (refund_id,))
        if refund is None:
            raise ValueError(f"refund {refund_id} not found")
        return refund

    def list_refunds(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM refunds ORDER BY id DESC")

    def create_pending_approval(self, action: str, payload: dict[str, Any], risk_reason: str) -> dict[str, Any]:
        with connect(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO pending_approvals(action, payload_json, risk_reason)
                VALUES (?, ?, ?)
                """,
                (action, json.dumps(payload, ensure_ascii=False), risk_reason),
            )
            connection.commit()
            approval_id = cursor.lastrowid
        return self.get_approval(approval_id)

    def get_approval(self, approval_id: int) -> dict[str, Any]:
        approval = self._fetch_one("SELECT * FROM pending_approvals WHERE id = ?", (approval_id,))
        if approval is None:
            raise ValueError(f"approval {approval_id} not found")
        approval["payload"] = json.loads(approval.pop("payload_json"))
        return approval

    def list_pending_approvals(self) -> list[dict[str, Any]]:
        approvals = self._fetch_all("SELECT * FROM pending_approvals WHERE status = 'pending' ORDER BY id DESC")
        for approval in approvals:
            approval["payload"] = json.loads(approval.pop("payload_json"))
        return approvals

    def approve_pending_refund(self, approval_id: int, reviewer: str) -> dict[str, Any]:
        with connect(self.database_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM pending_approvals WHERE id = ?", (approval_id,)).fetchone()
            if row is None:
                raise ValueError(f"approval {approval_id} not found")
            approval = dict(row)
            if approval["status"] != "pending":
                raise ValueError(f"approval {approval_id} has already been {approval['status']}")
            if approval["action"] != "request_refund":
                raise ValueError(f"approval {approval_id} is not a refund action")

            payload = json.loads(approval["payload_json"])
            refund_cursor = connection.execute(
                """
                INSERT INTO refunds(order_id, customer_id, amount, reason)
                VALUES (?, ?, ?, ?)
                """,
                (payload["order_id"], payload["customer_id"], payload["amount"], payload["reason"]),
            )
            connection.execute(
                """
                UPDATE pending_approvals
                SET status = 'approved', reviewer = ?, reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (reviewer, approval_id),
            )
            refund_id = refund_cursor.lastrowid
            connection.commit()
        updated = self.get_approval(approval_id)
        refund = self._fetch_one("SELECT * FROM refunds WHERE id = ?", (refund_id,))
        if refund is None:
            raise ValueError(f"refund {refund_id} not found")
        return {"status": updated["status"], "approval": updated, "refund": refund}

    def reject_pending_refund(self, approval_id: int, reviewer: str) -> dict[str, Any]:
        with connect(self.database_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM pending_approvals WHERE id = ?", (approval_id,)).fetchone()
            if row is None:
                raise ValueError(f"approval {approval_id} not found")
            approval = dict(row)
            if approval["status"] != "pending":
                raise ValueError(f"approval {approval_id} has already been {approval['status']}")
            if approval["action"] != "request_refund":
                raise ValueError(f"approval {approval_id} is not a refund action")

            connection.execute(
                """
                UPDATE pending_approvals
                SET status = 'rejected', reviewer = ?, reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (reviewer, approval_id),
            )
            connection.commit()
        updated = self.get_approval(approval_id)
        return {"status": updated["status"], "approval": updated}
