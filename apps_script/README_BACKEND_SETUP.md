# StudyHub Paper + Memo Pipeline

## What this fixes
- Reads only approved source pages listed in the `Sources` sheet.
- Detects PDF/ZIP links and pairs papers with likely matching memoranda.
- Rejects incomplete or unsupported records.
- Prevents duplicate paper/memo URL pairs.
- Downloads each paper and memo with three retries.
- Verifies PDF (`%PDF`) and ZIP (`PK`) signatures before saving.
- Saves into the configured Google Drive Source Library structure.
- Records failures in Queue and RunLog instead of silently losing files.

## Deploy
1. Create or open the StudyHub Google Apps Script project.
2. Copy every file from `apps_script/` into the project.
3. In Script Properties set `SHEET_ID` and `SOURCE_LIBRARY_ID`.
4. Run `setupStudyHub()` once and grant permissions.
5. Add approved page URLs to the `Sources` sheet and set `enabled` to `TRUE`.
6. Set Script Property `DISCOVERY_MODE` to `LIVE` only when ready.
7. Run `runDiscoveryNow()` and inspect Queue.
8. Run `runDownloadBatch()` and confirm both files are saved.
9. Run `installPipelineTriggers()` for hourly discovery and 15-minute download batches.

## Important
The scanner cannot guarantee every paper on the internet. It processes approved source pages and reports missing metadata, unpaired files, HTTP failures, invalid files, duplicates, and save errors for review.
