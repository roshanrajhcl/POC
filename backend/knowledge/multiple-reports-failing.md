---
id: multiple-reports-failing
title: Several reports fail at the same time
category: refresh
keywords: several reports failed, many reports failing, all reports failing, same time, multiple datasets fail, shared gateway, shared source, outage
source: ReportPulse seed knowledge
---
## What it means
When more than one report fails in the same window, the cause is often shared, not specific to each report.

## Shared causes to check first
- A shared gateway is offline, overloaded or was restarted.
- A shared data source was down, slow, locked by another job, or had its credentials or firewall rules changed.
- The shared capacity was overloaded because many large refreshes ran together.
- A shared service account password expired.
- A platform incident in the Power BI service.

## How to tell
- Compare the failure times. If they cluster, suspect a shared cause.
- Compare the error messages. Different messages from the same time can still come from one outage.
- Check whether the failing reports use the same gateway or source, and whether reports that use a different one succeeded.

## Steps
1. Fix the shared cause once (gateway, source, credentials, capacity) instead of changing each report.
2. Then refresh each report manually and check Refresh history.
3. If only one report keeps failing, return to its own error.
