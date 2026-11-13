---
id: refresh-not-configured
title: No scheduled refresh configured
category: refresh
keywords: not configured, no schedule, scheduled refresh not set, refresh disabled, manual refresh only, refresh enabled no
source: ReportPulse seed knowledge (verify limits in current Microsoft documentation)
---
## What it means
The report's data only changes when someone refreshes it by hand, so it falls out of date.

## Why it happens
- A schedule was never set up after publishing.
- Credentials or a gateway were not configured, so the schedule could not be turned on.
- The schedule was switched off on purpose or by an earlier failure.

## Set up a scheduled refresh
1. Open the workspace, find the semantic model of the report, and open Settings.
2. Under Data source credentials, enter and save the credentials.
3. If the source is on-premises, map it to a gateway under Gateway and cloud connections.
4. Expand Refresh, turn on "Configure a refresh schedule", and pick the frequency and time zone.
5. Add refresh times. Pro allows up to 8 a day and Premium up to 48 (verify current limits). Select Apply.
6. Turn on failure notifications so the owners get an email when a refresh fails.

## Choosing times
Pick times after the source data is updated, and avoid the busiest hours of the source and the gateway.
