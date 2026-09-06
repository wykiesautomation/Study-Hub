# Production Roadmap

## Already implemented
Core fleet data, web workflows, API ingestion, capability gates, security lifecycle, fuel observations, diagnostics, bulk import, credentials and cursor feeds.

## Acceptance before 160-truck rollout
1. PostgreSQL production migrations and indexes.
2. Five-truck pilot with hardwired LTE trackers.
3. GPS, ignition, external power, tamper and backup battery verification.
4. Fuel sensor calibration and slosh filtering per tank profile.
5. Real webhook sender with HMAC SHA-256, exponential retry and dead-letter replay.
6. Background workers for offline detection, after-hours movement, geofence and diesel loss.
7. Map provider configuration and route-history load testing.
8. Rate limits, audit logs, CSRF, password reset and MFA for administrators.
9. Database backup and disaster recovery test.
10. 160-device staged endurance test.
