---
id: rls-overview
title: Row-Level Security (RLS) overview
category: rls
keywords: RLS, row-level security, row level security, restrict data, each user sees own data, country access, data security, who can see what, not implemented
source: ReportPulse seed knowledge (verify against current Microsoft documentation)
---
## What it is
Row-Level Security (RLS) limits which rows of data each person sees in the same report. One report and one model can serve many countries or teams, and each person sees only their own rows.

## Why it matters
Without RLS, anyone with access to the report can see all the data in the model, for example every country's accruals in a finance report. The validation file flags this when RLS_Implemented is no.

## Two common designs
- Static roles: one role per value, for example a KR role with the filter Country equals KR. Simple, but needs a new role for each new value.
- Dynamic RLS: one role. A mapping table lists which user may see which values, and the filter uses the signed-in user's name. Easier to maintain when people or values change.

## Information needed to implement it
- Which column decides access (Country, Region, Entity, Cost centre).
- Which users or groups map to which values.
- Any exceptions, for example leads who see everything.
- Whether the model imports data or uses DirectQuery.

## Things to know
- RLS is defined in the model in Power BI Desktop, tested there, and then members are assigned to roles in the Power BI service.
- RLS restricts Viewers. People with edit access (workspace Admin, Member, Contributor) are not restricted.
