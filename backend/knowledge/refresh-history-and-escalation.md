---
id: refresh-history-and-escalation
title: Reading refresh history and escalating
category: refresh
keywords: refresh history, activity id, request id, error details, escalate, support ticket, contact administrator, collect logs, gateway logs, how to report an error, what to send
source: ReportPulse seed knowledge (verify against current Microsoft documentation)
---
## Where to find the real error
In the Power BI service open the workspace, then the semantic model, then Refresh history. Select Show on the failed run. It lists the start and end time, the status, the full error message and an Activity ID or Request ID. The start and end times tell you how long the refresh ran before failing, which often separates a time limit from a source problem.

## What to collect before escalating
- The full error text, the error code, and the Activity ID or Request ID.
- Start time, end time and duration of the failed run, and the time of the last success.
- Workspace name, semantic model name, and whether the workspace is on shared, Premium or Fabric capacity.
- Whether the source is cloud or on-premises, and the gateway name if there is one.
- What changed recently: report, source, credentials, gateway host, network.
- Every fix already tried and the result of each.

## Who to contact
Start with the Power BI workspace administrator or the gateway administrator. If they cannot resolve it, open a support request with Microsoft and include the items above. A complete summary saves several rounds of questions.

## Gateway logs
For gateway problems the administrator can export the gateway logs from the gateway application and attach them to the request.
