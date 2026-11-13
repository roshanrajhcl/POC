---
id: refresh-processing-error
title: "An error occurred while processing" refresh error
category: refresh
keywords: an error occurred while processing, error occurred while processing the data, processing error, could not load data, unable to connect, failed to refresh
source: ReportPulse seed knowledge (verify against current Microsoft documentation)
---
## What it means
Power BI could not read the data source while processing the refresh. The message is generic on purpose. The real cause is in the full error details of the failed run in Refresh history.

## First fix: check the gateway connection and credentials
1. Open the workspace, go to the semantic model, then Settings.
2. Under Gateway and cloud connections, check that the gateway is online and mapped to every data source of the model.
3. Under Data source credentials, select Edit credentials and sign in again.
4. If the gateway is offline, restart the gateway service on its host machine.
5. Select Refresh now, then check Refresh history for the result.

## Other causes if that does not help
- A column, table or sheet was renamed or removed at the source (see the schema change document).
- The source server is not reachable: server down, firewall change, VPN or network change.
- The account used for the source was locked, its password changed, or its permission was removed.
- The source query itself returns an error, for example a view that now fails.

## What to look at in Refresh history
Open the failed run and select Show. Note the error code, the full message, the time the run started and ended, and the Activity ID. The wording of the detailed message usually points to gateway, credentials, schema or source.
