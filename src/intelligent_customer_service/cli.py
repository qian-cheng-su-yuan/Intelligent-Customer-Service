from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .agent import CustomerServiceAgent
from .config import Settings
from .database import initialize_database
from .llm_client import OpenAICompatibleToolCallingClient
from .repositories import CustomerServiceRepository
from .tools import CustomerServiceTools

app = typer.Typer(help="Enterprise intelligent customer service operations CLI.")
console = Console()


def _tools(database_path: Path | None = None) -> CustomerServiceTools:
    settings = Settings()
    path = database_path or settings.database_path
    initialize_database(path, seed=True)
    return CustomerServiceTools(
        CustomerServiceRepository(path),
        refund_review_threshold=settings.refund_review_threshold,
    )


@app.command()
def chat(
    message: str = typer.Argument(..., help="Customer message."),
    customer_id: str = typer.Option("CUST-001", "--customer-id", "-c", help="Customer identifier."),
) -> None:
    settings = Settings()
    tools = _tools(settings.database_path)
    agent = CustomerServiceAgent(OpenAICompatibleToolCallingClient(settings), tools)
    result = agent.chat(message, customer_id)
    console.print(result["answer"])
    if result["tool_calls"]:
        console.print_json(data=result["tool_calls"])


@app.command()
def tool(
    name: str = typer.Argument(..., help="Tool name."),
    order_id: str = typer.Option("ORD-1001", "--order-id"),
    customer_id: str = typer.Option("CUST-001", "--customer-id"),
    amount: float = typer.Option(99.0, "--amount"),
    reason: str = typer.Option("customer request", "--reason"),
    issue_type: str = typer.Option("hardware", "--issue-type"),
    description: str = typer.Option("Device needs after-sales inspection.", "--description"),
    contact: str = typer.Option("19838622783", "--contact"),
) -> None:
    tools = _tools()
    arguments = {
        "order_id": order_id,
        "customer_id": customer_id,
        "amount": amount,
        "reason": reason,
        "issue_type": issue_type,
        "description": description,
        "contact": contact,
    }
    result = tools.execute(name, arguments)
    console.print_json(data=result)


@app.command()
def approvals() -> None:
    pending = _tools().repository.list_pending_approvals()
    table = Table(title="Pending Approvals")
    table.add_column("ID")
    table.add_column("Action")
    table.add_column("Risk")
    table.add_column("Created At")
    for approval in pending:
        table.add_row(str(approval["id"]), approval["action"], approval["risk_reason"], approval["created_at"])
    console.print(table)


@app.command()
def approve(approval_id: int, reviewer: str = typer.Option("admin", "--reviewer")) -> None:
    result = _tools().repository.approve_pending_refund(approval_id, reviewer)
    console.print_json(data=result)


@app.command()
def reject(approval_id: int, reviewer: str = typer.Option("admin", "--reviewer")) -> None:
    result = _tools().repository.reject_pending_refund(approval_id, reviewer)
    console.print_json(data=result)


@app.command()
def init_db(
    seed: bool = typer.Option(True, "--seed/--no-seed"),
    reset: bool = typer.Option(False, "--reset", help="Remove the existing SQLite database before initialization."),
) -> None:
    settings = Settings()
    initialize_database(settings.database_path, seed=seed, reset=reset)
    console.print(f"Database initialized at [bold]{settings.database_path}[/bold]. seed={seed} reset={reset}")


if __name__ == "__main__":
    app()
