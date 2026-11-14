import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class PriceRepository:
    def __init__(self, db_path: str = "data/flight_prices.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS price_history (
                pk TEXT NOT NULL,
                sk TEXT NOT NULL,
                trip_name TEXT NOT NULL,
                route TEXT NOT NULL,
                departure_date TEXT NOT NULL,
                airline TEXT NOT NULL,
                price REAL NOT NULL,
                notified INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (pk, sk)
            )
            """
        )
        self.conn.commit()

    def _build_pk(self, trip_name: str) -> str:
        return f"TRIP#{trip_name.upper()}"

    def get_stats(self, trip_name: str) -> dict:
        pk = self._build_pk(trip_name)
        cursor = self.conn.execute(
            "SELECT AVG(price), MIN(price), COUNT(*) FROM price_history WHERE pk = ?",
            (pk,),
        )
        avg_price, min_price, count = cursor.fetchone()

        last_notified_cursor = self.conn.execute(
            """
            SELECT price FROM price_history
            WHERE pk = ? AND notified = 1
            ORDER BY sk DESC LIMIT 1
            """,
            (pk,),
        )
        row = last_notified_cursor.fetchone()

        return {
            "avg_price": float(avg_price) if avg_price else None,
            "min_price": float(min_price) if min_price else None,
            "count": count or 0,
            "last_notified_price": row[0] if row else None,
        }

    def save_price(self, flight: dict, notified: bool):
        pk = self._build_pk(flight["trip_name"])
        sk = datetime.now(timezone.utc).isoformat()

        self.conn.execute(
            """
            INSERT INTO price_history (pk, sk, trip_name, route, departure_date, airline, price, notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pk,
                sk,
                flight["trip_name"],
                flight["route"],
                flight["departure_date"],
                flight["airline"],
                flight["price"],
                1 if notified else 0,
            ),
        )
        self.conn.commit()

    def get_history(self, trip_name: str | None = None, limit: int = 50) -> list[dict]:
        if trip_name:
            pk = self._build_pk(trip_name)
            cursor = self.conn.execute(
                """
                SELECT trip_name, route, departure_date, airline, price, notified, sk
                FROM price_history
                WHERE pk = ?
                ORDER BY sk DESC LIMIT ?
                """,
                (pk, limit),
            )
        else:
            cursor = self.conn.execute(
                """
                SELECT trip_name, route, departure_date, airline, price, notified, sk
                FROM price_history
                ORDER BY sk DESC LIMIT ?
                """,
                (limit,),
            )

        rows = cursor.fetchall()
        return [
            {
                "trip_name": r[0],
                "route": r[1],
                "departure_date": r[2],
                "airline": r[3],
                "price": r[4],
                "notified": bool(r[5]),
                "collected_at": r[6],
            }
            for r in rows
        ]    