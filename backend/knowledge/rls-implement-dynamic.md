---
id: rls-implement-dynamic
title: Implement dynamic RLS with a user mapping table
category: rls
keywords: dynamic RLS, USERPRINCIPALNAME, user mapping table, UserAccess, one role, lookup user email, many users, maintain access, security groups mapping
source: ReportPulse seed knowledge (verify against current Microsoft documentation)
---
## When to use it
Use dynamic RLS when many users or many values make one role per value hard to maintain, or access changes often.

## Steps
1. Create a mapping table with one row per user and allowed value, for example UserAccess with the columns UserEmail and Country. A user with several countries has several rows. Load it into the model.
2. Create one role, for example Country_Access.
3. Add a Data Analysis Expressions (DAX) filter on the table that holds the access column. One pattern that avoids two-way relationships: [Country] IN CALCULATETABLE(VALUES(UserAccess[Country]), UserAccess[UserEmail] = USERPRINCIPALNAME())
4. Another pattern: put the filter [UserEmail] = USERPRINCIPALNAME() on the UserAccess table and relate UserAccess to the dimension with the option to apply the security filter in both directions. Use this carefully because two-way filters can slow the model.
5. Test with View as and enter a user's email in Other user. Confirm the rows match the mapping table.
6. Publish. In the Power BI service add everyone who should use the report to the role, or add a security group that contains them.

## Notes
- The name USERPRINCIPALNAME returns is the sign-in name, usually the email address. The mapping table must match it exactly, including letter case and spelling.
- Keep the mapping table current. A user missing from it sees no data.
- Maintain the mapping table in the source system, not by hand in the report, so access changes do not need a republish.
