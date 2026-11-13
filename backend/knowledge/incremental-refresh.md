---
id: incremental-refresh
title: Incremental refresh
category: refresh
keywords: incremental refresh, RangeStart, RangeEnd, partitions, refresh only recent data, large fact table, refresh policy
source: ReportPulse seed knowledge (verify against current Microsoft documentation)
---
## What it does
Instead of reloading the whole table on every refresh, Power BI keeps older data as it is and reloads only a recent window, for example the last few days. This cuts refresh time and load on the source.

## Requirements
- The table has a date or date and time column that does not change for a row.
- The source can filter by that column efficiently, ideally with query folding (see the query folding document).
- Two Power Query parameters named RangeStart and RangeEnd, of type Date/Time, are used to filter the table.

## Steps
1. In Power Query create the parameters RangeStart and RangeEnd (Date/Time) with sample values.
2. Filter the date column: greater than or equal to RangeStart and less than RangeEnd. Confirm the filter folds to the source.
3. In Power BI Desktop right-click the table, choose Incremental refresh, and set how much history to keep and how much recent data to refresh.
4. Publish the model and refresh it in the service.

## Watch out
- The very first refresh after publishing loads the full history, so it can be slow and may itself hit the time limit. Keep the stored history shorter at first, or ask your administrator about options for the first load.
- If the filter does not fold, each partition still reads the whole source table and nothing is saved.
- Do not change the date column used for the policy afterwards without republishing carefully.
