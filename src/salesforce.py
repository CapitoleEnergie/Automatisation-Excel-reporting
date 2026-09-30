from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


class SalesforceError(RuntimeError):
    pass


@dataclass(frozen=True)
class SalesforceClient:
    instance_url: str
    access_token: str
    api_version: str

    @classmethod
    def from_client_credentials(cls) -> "SalesforceClient":
        login_url = os.getenv("SF_LOGIN_URL", "https://login.salesforce.com").rstrip("/")
        client_id = os.getenv("SF_CLIENT_ID")
        client_secret = os.getenv("SF_CLIENT_SECRET")
        api_version = os.getenv("SF_API_VERSION", "v66.0")

        if not client_id or not client_secret:
            raise SalesforceError("Variables SF_CLIENT_ID / SF_CLIENT_SECRET manquantes.")

        response = requests.post(
            f"{login_url}/services/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=30,
        )
        if not response.ok:
            raise SalesforceError(f"OAuth Salesforce échoué ({response.status_code}): {response.text}")

        payload = response.json()
        return cls(
            instance_url=payload["instance_url"].rstrip("/"),
            access_token=payload["access_token"],
            api_version=api_version,
        )

    def query(self, soql: str) -> list[dict[str, Any]]:
        url = f"{self.instance_url}/services/data/{self.api_version}/query"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params: dict[str, str] | None = {"q": soql}
        rows: list[dict[str, Any]] = []

        while url:
            response = requests.get(url, headers=headers, params=params, timeout=60)
            params = None
            if not response.ok:
                raise SalesforceError(
                    f"SOQL échoué ({response.status_code}): {response.text}\n{soql}"
                )

            payload = response.json()
            rows.extend(payload.get("records", []))
            next_url = payload.get("nextRecordsUrl")
            url = f"{self.instance_url}{next_url}" if next_url else ""

        return rows
