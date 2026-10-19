# Offline-First Logging

Logging a habit completion MUST succeed with no network connection. A completion logged offline MUST be persisted locally and reconciled with the server when connectivity returns, without the user taking any extra action.

## Why this cap

The daily tracker frequently checks in from places with no signal. A check-in that requires the network would fail exactly when it is most needed, which is the failure mode behind [Streaks Break Silently](../pain_point/streaks-break-silently.md). Offline-first logging is a standing rule every feature that records or displays completions must respect.

## Scope

Applies to logging a completion and to reading the current streak. It does not require offline support for account management, settings, or analytics, which MAY require connectivity.
