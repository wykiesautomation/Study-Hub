# FleetTrack 360 Production Foundation

FleetTrack 360 is a standalone fleet tracking, fleet security, diesel monitoring and fleet API platform. It is separate from AssetTrack 360.

## Working product areas
- Tenant login and role-ready user model
- Fleet overview
- Vehicle registry and vehicle details
- Drivers and historical assignments
- Device registration with one-time tokens and capability profiles
- GPS batch ingestion with duplicate and quality validation
- Validated route segmentation requiring 3 consecutive good points
- Fleet live tracking view
- Geofence registry
- Security event lifecycle and acknowledgement
- Fuel observations, transactions and possible diesel-loss event generation
- CAN/J1939 diagnostics and diagnostic-created maintenance issues
- Maintenance issue register
- API credentials and scoped integration model
- Webhook subscriptions and delivery queue model
- Vehicle CSV bulk import
- Cursor-based location, event, fuel and diagnostic feeds
- Reports and evidence workspace
- OpenAPI starter contract

## Run locally
1. Create a virtual environment.
2. Install `requirements.txt`.
3. Set `SEED_DEMO=true` only for local testing.
4. Run `flask --app wsgi:app run`.
5. Demo login when seeded: `admin@fleettrack.local` / `ChangeMe123!`.

## Production deployment
Set `DATABASE_URL`, a strong `SECRET_KEY`, and do not enable demo seed. Use the included Dockerfile or Procfile. Create the first customer and administrator through a controlled bootstrap or migration process.

## Honest readiness
This is a substantial cumulative fleet platform baseline, not a small mockup. It still requires real-device field verification, HMAC webhook dispatch workers, map tile/provider configuration, scheduled security correlation workers, full CSRF protection, formal migrations, backup/restore validation and a 160-device endurance test before a 160-truck production commitment.
