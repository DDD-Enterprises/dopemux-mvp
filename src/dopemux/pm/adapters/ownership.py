"""Explicit v2 transport binding. No local success cache, retries or downgrade."""

from urllib.parse import quote, urlsplit
import httpx

from ..ownership import (
    TransitionCommand,
    canonical_json,
    parse_json_object,
    validate_receipt,
    identifier,
)


class _Binding:
    def __init__(
        self,
        *,
        project_id,
        writer_instance_id,
        endpoint,
        principal_id,
        client_id,
        credential_supplier
    ):
        for value in (project_id, writer_instance_id, principal_id, client_id):
            identifier(value)
        parsed = urlsplit(endpoint)
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ValueError("Explicit authenticated HTTPS writer endpoint required")
        self.project_id, self.writer_instance_id = project_id, writer_instance_id
        self.principal_id, self.client_id = principal_id, client_id
        self.endpoint = endpoint.rstrip("/")
        self.credential_supplier = credential_supplier

    def _request_parts(self, body):
        body = TransitionCommand.model_validate(body).model_dump()
        credential = self.credential_supplier()
        if not isinstance(credential, str) or not credential:
            raise PermissionError("Transport credentials unavailable")
        return (
            body,
            self.endpoint
            + "/api/v2/projects/"
            + quote(self.project_id, safe="")
            + "/workflow/transition",
            {"Authorization": credential, "Content-Type": "application/json"},
        )

    def _receipt(self, response, body):
        response.raise_for_status()
        return validate_receipt(
            parse_json_object(response.content),
            body,
            project_id=self.project_id,
            principal_id=self.principal_id,
            client_id=self.client_id,
        )


class SyncOwnershipAdapter(_Binding):
    def __init__(self, *, transport=None, **binding):
        super().__init__(**binding)
        self.client = httpx.Client(
            transport=transport, timeout=10, follow_redirects=False, trust_env=False
        )

    def transition_command(self, body):
        body, url, headers = self._request_parts(body)
        return self._receipt(
            self.client.post(url, content=canonical_json(body), headers=headers), body
        )

    def close(self):
        self.client.close()


class AsyncOwnershipAdapter(_Binding):
    def __init__(self, *, transport=None, **binding):
        super().__init__(**binding)
        self.client = httpx.AsyncClient(
            transport=transport, timeout=10, follow_redirects=False, trust_env=False
        )

    async def transition_command(self, body):
        body, url, headers = self._request_parts(body)
        return self._receipt(
            await self.client.post(url, content=canonical_json(body), headers=headers), body
        )

    async def close(self):
        await self.client.aclose()
