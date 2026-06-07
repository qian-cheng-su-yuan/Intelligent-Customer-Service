from pathlib import Path

import typer
from rich.console import Console

from .config import Settings
from .database import initialize_database
from .repositories import CustomerServiceRepository

app = typer.Typer(help="Database utilities.")
console = Console()


@app.command()
def init(
    database_path: Path | None = typer.Option(None, "--database-path", "-d", help="SQLite database path."),
    seed: bool = typer.Option(False, "--seed", help="Insert initial orders and logistics records."),
    reset: bool = typer.Option(False, "--reset", help="Remove the existing SQLite database before initialization."),
) -> None:
    settings = Settings()
    path = database_path or settings.database_path
    initialize_database(path, seed=seed, reset=reset)
    console.print(f"Database initialized at [bold]{path}[/bold]. seed={seed} reset={reset}")


@app.command()
def status(database_path: Path | None = typer.Option(None, "--database-path", "-d", help="SQLite database path.")) -> None:
    settings = Settings()
    path = database_path or settings.database_path
    if not path.exists():
        console.print(f"Database does not exist at [bold]{path}[/bold].")
        raise typer.Exit(code=1)
    repo = CustomerServiceRepository(path)
    pending = repo.list_pending_approvals()
    console.print(f"Database: [bold]{path}[/bold]")
    console.print(f"Pending approvals: {len(pending)}")


if __name__ == "__main__":
    app()
