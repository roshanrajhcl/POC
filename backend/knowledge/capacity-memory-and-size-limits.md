---
id: capacity-memory-and-size-limits
title: Capacity memory and dataset size limits
category: refresh
keywords: not enough memory, memory limit, resource governing, out of memory, dataset size limit, exceeded the limit, premium capacity, capacity overloaded, capacity, shared capacity, 1 GB, model too large
source: ReportPulse seed knowledge (limits change, verify in current Microsoft documentation)
---
## What it means
Each workspace runs on a capacity with limits on memory, model size and refresh time. A refresh that needs more than the limit is cancelled, often with a message about memory, resource governing or exceeding a limit.

## Common causes
- The model is large: many rows, high-cardinality columns (for example unique IDs or timestamps down to the second), wide text columns.
- Several large datasets refresh at the same time on the same capacity, so memory is shared.
- A refresh needs roughly double the model size in memory while it loads the new copy.
- The workspace is on shared capacity with the smaller limits instead of Premium or Fabric capacity.

## Steps
1. Reduce the model: remove unused columns and tables, lower the precision of date and time columns, and avoid keeping unique text keys that are not needed.
2. Use incremental refresh so each refresh handles less data.
3. Stagger schedules so large datasets do not refresh together.
4. Check the capacity metrics (your Power BI administrator can see them) for memory and overload at the failure time.
5. If the model must stay large, ask the administrator about a larger capacity.

Limits depend on the license and capacity type and change over time. Confirm current values in Microsoft documentation.
