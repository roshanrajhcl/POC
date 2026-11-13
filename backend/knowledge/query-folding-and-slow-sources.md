---
id: query-folding-and-slow-sources
title: Slow source queries and query folding
category: refresh
keywords: slow query, query folding, native query, source performance, long running query, heavy transformations, Power Query slow, database slow
source: ReportPulse seed knowledge (verify against current Microsoft documentation)
---
## What it means
Power BI refresh time is dominated by how long the source takes to answer and how much work Power Query does after receiving the data. When Power Query steps can be translated into one source query, this is called query folding, and the source does the heavy work. When folding breaks, Power BI downloads a lot of data and transforms it itself, which is much slower.

## How to check
- In Power Query, right-click a step and see whether View Native Query is available. If it is greyed out, the step does not fold.
- Note which step is the first one that stops folding. Steps after it do not fold either.

## Steps to improve
1. Move filters, column removal and joins earlier, before the step that breaks folding.
2. Replace heavy Power Query logic with a database view or a pre-aggregated table at the source.
3. Remove columns and rows you do not need as early as possible.
4. Test the slowest query directly at the source with the same filters, and ask the database owner to check indexes and load at the refresh time.
5. Avoid refreshing many large tables at the same moment. Stagger the schedules.

## If the source itself is slow
Compare the query time in the source's own tools with the refresh duration. If the source needs most of the time, the fix is at the source (indexes, views, resource limits), not in Power BI.
