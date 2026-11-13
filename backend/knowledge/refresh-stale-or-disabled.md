---
id: refresh-stale-or-disabled
title: Refresh completed but data is stale, or schedule paused
category: refresh
keywords: stale, outdated, not refreshed, last refresh old, schedule disabled, schedule paused, refresh paused, data is old
source: ReportPulse seed knowledge (verify against current Microsoft documentation)
---
## What it means
The last refresh succeeded, but it was many days ago. The report may be showing outdated data.

## Common causes
- The schedule was turned off, or it runs weekly instead of daily.
- Power BI pauses a schedule after several consecutive failures, and also when a dataset has not been used for a long time. A paused schedule needs to be switched on again.
- The last runs were manual and no schedule exists.
- The refresh is scheduled but the source has no new data.

## Steps
1. Open the model Settings and confirm the refresh schedule is on.
2. Check Refresh history for skipped or failed runs since the last success.
3. Set the frequency to match how often the business needs new data.
4. Select Refresh now to bring the data up to date.
5. Turn on failure notifications so a pause or failure is noticed sooner.
