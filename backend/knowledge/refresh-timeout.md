---
id: refresh-timeout
title: Scheduled refresh times out
category: refresh
keywords: timeout, timeout error, timed out, time out, refresh exceeded the maximum time, operation was cancelled, took too long, refresh too long
source: ReportPulse seed knowledge (verify limits in current Microsoft documentation)
---
## What it means
The refresh ran longer than Power BI allows for the workspace type, or a query at the data source ran longer than its own limit, so the refresh was cancelled before it finished.

## Common causes
- The dataset is too large: too many rows, or columns and tables the report does not use.
- Slow queries at the data source, or heavy Power Query transformations that cannot be pushed back to the source (no query folding).
- The refresh runs at peak hours, when the source and the gateway are busy.
- Many large tables refreshing at the same time.

## First fix: reduce the data size
Remove columns and tables the report does not use. Filter rows to the period the report needs, for example the last 2 years. Remove very wide text columns. Then select Refresh now and check Refresh history. This is the standard first step.

## If reducing the size did not help
- Turn on incremental refresh so only recent data is reloaded.
- Move heavy transformations to the source, for example a database view or a pre-aggregated table, so Power BI does less work.
- Move the schedule to off-peak hours and stagger refreshes of large datasets.
- Look at how long the refresh runs before it fails (next section).

## How long it ran points to the cause
- It fails after about 2 hours on shared (Pro) capacity, or about 5 hours on Premium capacity: this is the refresh time limit for the capacity. Load less data, use incremental refresh, or move the dataset to a larger capacity.
- It fails within minutes: usually a source-side or gateway timeout, not the overall limit. Test the slowest query directly at the source and check the gateway.
- It fails at different times on each run: the source or gateway is probably overloaded at times. Check what else runs then.

Limits can change. Confirm the current values in Microsoft documentation.
