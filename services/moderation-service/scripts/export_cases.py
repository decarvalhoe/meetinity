"""Utility script to export moderation cases for audits."""
from __future__ import annotations

import csv
import os
from pathlib import Path

from src.config import ModerationConfig
from src.database import Base, get_engine, init_engine
from src.models import ModerationCase
from src.main import create_app


def main() -> None:
    output = Path(os.environ.get("OUTPUT", "moderation_cases.csv"))
    app = create_app()
    cfg = ModerationConfig.from_app(app)
    init_engine(cfg.database_url)
    engine = get_engine()
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        result = conn.execute(ModerationCase.__table__.select())
        rows = result.fetchall()
    with output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "content_reference", "status", "assigned_reviewer", "score", "created_at"])
        for row in rows:
            writer.writerow(
                [
                    row.id,
                    row.content_reference,
                    row.status,
                    row.assigned_reviewer,
                    row.automated_score,
                    row.created_at,
                ]
            )
    print(f"Exported {len(rows)} cases to {output}")


if __name__ == "__main__":
    main()
