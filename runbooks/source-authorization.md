# Source Authorization Runbook

## Purpose

Validate the license, owner decision, organization scope, HTTPS domain allowlist, and explicit fetch permission required before an external source is used operationally.

## Usage

Run `python scripts/source_authorization_preflight.py --request <authorization-json> --environment validation`. A successful result means only that the authorization evidence is structurally complete. It does not fetch the source, register it, or declare its content accurate.

Program owners may then use `POST /v1/sources/authorized` with the validated authorization object and source metadata. The route attaches the authorization evidence to the organization-scoped source record; it still performs no network fetch.

The default external refresh path fails closed unless the source record carries `authorization_status: authorized`. Synthetic rehearsals may inject an explicit fixture fetcher, but those runs must remain labeled synthetic and non-production.

## Safety boundary

The authorization record must link to a license, decision, approval, or source-authorization reference. Production source use additionally requires deployment-owner approval and current source freshness review. The preflight always reports `network_fetch_performed: false` and `external_state_changed: false`.
