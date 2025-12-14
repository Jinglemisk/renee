"""Output formatting for CLI commands.

Provides both JSON output for AI agents and human-readable output for developers.
"""

import json
import sys
from typing import Any

from renee.errors import ReneeError


class OutputFormatter:
    """Format CLI output based on mode (JSON or human-readable).

    The formatter provides consistent output formatting across all CLI commands:
    - JSON mode: Machine-parseable structured output for AI agents
    - Human mode: Colorized, readable output for developers

    Example:
        >>> formatter = OutputFormatter(json_mode=True)
        >>> formatter.success("Entity created", {"id": 42})
        {"status": "success", "message": "Entity created", "data": {"id": 42}}
    """

    def __init__(self, json_mode: bool = False) -> None:
        """Initialize the output formatter.

        Args:
            json_mode: If True, output JSON. If False, output human-readable text.
        """
        self.json_mode = json_mode

    def success(self, message: str, data: Any = None) -> None:
        """Print a success message.

        Args:
            message: Success message to display
            data: Optional data to include in output
        """
        if self.json_mode:
            output: dict[str, Any] = {"status": "success", "message": message}
            if data is not None:
                output["data"] = data
            print(json.dumps(output, indent=2, default=str))
        else:
            print(f"Success: {message}")
            if data is not None:
                if isinstance(data, (dict, list)):
                    print(json.dumps(data, indent=2, default=str))
                else:
                    print(str(data))

    def error(self, message: str, details: str | None = None) -> None:
        """Print an error message.

        Args:
            message: Error message to display
            details: Optional detailed error information
        """
        if self.json_mode:
            output: dict[str, Any] = {"status": "error", "message": message}
            if details:
                output["details"] = details
            print(json.dumps(output, indent=2, default=str), file=sys.stderr)
        else:
            print(f"Error: {message}", file=sys.stderr)
            if details:
                print(f"  {details}", file=sys.stderr)

    def renee_error(self, error: ReneeError) -> None:
        """Print a structured ReneeError.

        Args:
            error: The ReneeError to display
        """
        if self.json_mode:
            print(json.dumps({"ok": False, "error": error.to_dict()}, indent=2, sort_keys=True))
        else:
            print(f"Error: {error.payload.message}", file=sys.stderr)
            if error.payload.hint:
                print(f"Hint: {error.payload.hint}", file=sys.stderr)

    def info(self, message: str, data: Any = None) -> None:
        """Print an informational message.

        Args:
            message: Info message to display
            data: Optional data to include in output
        """
        if self.json_mode:
            output: dict[str, Any] = {"status": "info", "message": message}
            if data is not None:
                output["data"] = data
            print(json.dumps(output, indent=2, default=str))
        else:
            print(f"Info: {message}")
            if data is not None:
                if isinstance(data, (dict, list)):
                    print(json.dumps(data, indent=2, default=str))
                else:
                    print(str(data))

    def table(self, headers: list[str], rows: list[list[Any]]) -> None:
        """Print data in table format.

        Args:
            headers: Column headers
            rows: List of rows (each row is a list of values)
        """
        if self.json_mode:
            # Convert to list of dicts for JSON
            table_data = []
            for row in rows:
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        row_dict[header] = row[i]
                table_data.append(row_dict)
            print(json.dumps(table_data, indent=2, default=str))
        else:
            # Simple text table
            if not rows:
                print("(empty)")
                return

            # Calculate column widths
            col_widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    if i < len(col_widths):
                        col_widths[i] = max(col_widths[i], len(str(cell)))

            # Print header
            header_line = " | ".join(
                headers[i].ljust(col_widths[i]) for i in range(len(headers))
            )
            print(header_line)
            print("-" * len(header_line))

            # Print rows
            for row in rows:
                row_line = " | ".join(
                    str(row[i]).ljust(col_widths[i]) if i < len(row) else " " * col_widths[i]
                    for i in range(len(headers))
                )
                print(row_line)

    def list_items(self, items: list[Any], title: str | None = None) -> None:
        """Print a list of items.

        Args:
            items: Items to display
            title: Optional title for the list
        """
        if self.json_mode:
            output: dict[str, Any] = {"items": items}
            if title:
                output["title"] = title
            print(json.dumps(output, indent=2, default=str))
        else:
            if title:
                print(f"{title}:")
            for item in items:
                print(f"  - {item}")

    def dict_output(self, data: dict[str, Any], title: str | None = None) -> None:
        """Print a dictionary.

        Args:
            data: Dictionary to display
            title: Optional title
        """
        if self.json_mode:
            output: dict[str, Any] = {"data": data}
            if title:
                output["title"] = title
            print(json.dumps(output, indent=2, default=str))
        else:
            if title:
                print(f"{title}:")
            print(json.dumps(data, indent=2, default=str))
