import json
import subprocess
import sys
from typing import Any, Dict, Optional


class GraphQLApiError(Exception):
    """Raised when a GraphQL API call fails."""

    pass


class GraphQLClient:
    """A client for interacting with the GitHub GraphQL API via the gh CLI."""

    def __init__(self):
        pass

    def query(
        self, query_text: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a GraphQL query or mutation."""
        cmd = ["gh", "api", "graphql", "-f", f"query={query_text}"]

        if variables:
            for key, value in variables.items():
                if isinstance(value, int):
                    cmd.extend(["-F", f"{key}={value}"])
                elif isinstance(value, (dict, list)):
                    cmd.extend(["-f", f"{key}={json.dumps(value)}"])
                else:
                    cmd.extend(["-f", f"{key}={value}"])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            raise GraphQLApiError(f"GitHub GraphQL API error: {error_msg}")

        try:
            data = json.loads(result.stdout)
            if "errors" in data:
                # GitHub returns 200 even with some partial errors
                raise GraphQLApiError(
                    f"GraphQL errors: {json.dumps(data['errors'], indent=2)}"
                )
            return data.get("data", {})
        except json.JSONDecodeError:
            raise GraphQLApiError(
                f"Failed to parse GitHub API response: {result.stdout}"
            )

    def mutate(self, mutation_text: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GraphQL mutation."""
        return self.query(mutation_text, variables)
