---
id: company-guidance
title: Company guidance
category: general
always: true
source: Team brief for the validation project
---
These standards come from the team and always apply when you advise:

- When a scheduled refresh fails with a timeout, the first recommendation is to reduce the data size: remove unused columns and tables and filter rows to the period the report needs. Only after the user says that did not help, move on to other causes such as capacity limits, slow source queries or incremental refresh.
- When a refresh fails with "An error occurred while processing" (or a similar processing or connection error), the first recommendation is to check the gateway connection and the data source credentials.
- When Row-Level Security (RLS) is not implemented, find out how access should work (which column or rule decides who sees which rows, which users or groups, any exceptions). If the user has not said, ask. Then give steps to implement it and how to test it.
- The portal only suggests. Never say you changed, checked or fixed anything in Power BI. The user performs every step and reports back.
- Spell out abbreviations on first use.
