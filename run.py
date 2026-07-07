from __future__ import annotations

import argparse

from src.database.repository import initialize_database
from src.scheduler.run_collection import collect, run_local_scheduler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Formare price intelligence")
    parser.add_argument("--init-db", action="store_true", help="Create and seed the SQLite database.")
    parser.add_argument("--collect", action="store_true", help="Run collectors once.")
    parser.add_argument("--source", help="Run only one source by id or name.")
    parser.add_argument("--dry-run", action="store_true", help="Collect without writing to the database.")
    parser.add_argument("--update-all", action="store_true", help="Initialize DB and run all collectors.")
    parser.add_argument("--scheduler", action="store_true", help="Run local APScheduler at 08:00 and 17:00 BRT.")
    parser.add_argument(
        "--allow-simulated-fallback",
        action="store_true",
        help="Opt-in demo fallback. Simulated rows are marked as estimated_price and confidence <= 20.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.init_db or args.update_all:
        initialize_database()
        print("Database initialized.")
    if args.collect or args.update_all:
        observations = collect(
            source=args.source,
            dry_run=args.dry_run,
            allow_simulated_fallback=args.allow_simulated_fallback,
        )
        print(f"Collected {len(observations)} observations.")
    if args.scheduler:
        run_local_scheduler()
    if not any([args.init_db, args.collect, args.update_all, args.scheduler]):
        print("Nothing to do. Try --init-db, --collect, --update-all or --scheduler.")


if __name__ == "__main__":
    main()

