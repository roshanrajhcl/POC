---
id: gateway-offline-or-unmapped
title: Gateway offline, unreachable or not mapped
category: refresh
keywords: gateway is offline, gateway not reachable, cannot connect to the gateway, on-premises data gateway, gateway cluster, data source not mapped, DM_GWPipeline, gateway unavailable
source: ReportPulse seed knowledge (verify against current Microsoft documentation)
---
## What it means
Datasets that read on-premises or private-network sources refresh through an on-premises data gateway. If the gateway is offline, cannot reach the source, or the dataset is not mapped to it, the refresh fails.

## Common causes
- The gateway service is stopped, or the host machine is off, asleep, restarted or out of disk space.
- A network or firewall change blocks the gateway from the source or from the Power BI service.
- The dataset's data source is not mapped to the gateway, or the server and database names do not match the gateway's data source exactly.
- The gateway runs in personal mode, which stops working when that person's machine is off or signed out.
- The gateway version is very old.

## Steps
1. In the Power BI service open the gateway settings and check the status of the gateway cluster. It should be online.
2. On the host machine, check that the On-premises data gateway service is running and restart it if not.
3. Open the semantic model Settings, then Gateway and cloud connections, and map each data source to the gateway. Server and database names must match the gateway data source exactly.
4. Test the connection from the gateway data source page.
5. If it worked before, ask what changed on the host or the network: patching, restarts, firewall, account changes.
6. Select Refresh now and check Refresh history.

For a shared gateway serving many reports, one outage can make many reports fail at the same time.
