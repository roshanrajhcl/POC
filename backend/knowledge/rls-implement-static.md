---
id: rls-implement-static
title: Implement static RLS roles with DAX filters
category: rls
keywords: static RLS, create role, manage roles, DAX filter, Country equals, add users to role, security tab, role per country, implement RLS, set up RLS
source: ReportPulse seed knowledge (verify against current Microsoft documentation)
---
## Create the roles in Power BI Desktop
1. Go to Modeling, then Manage roles, and select Create.
2. Name the role, for example KR_Users.
3. Select the table that holds the access column and add a filter with a Data Analysis Expressions (DAX) expression, for example [Country] = "KR".
4. Repeat for each country or value, for example AU_Users with [Country] = "AU".
5. For people who should see everything, create a role with no filter on the table, for example Finance_Leads.
6. Save the roles.

## Make the filter reach the data
If the access column is in a dimension table, make sure the relationship from the dimension to the fact table filters in the direction of the fact table. A role filter on a table filters only that table and the tables it filters through relationships.

## Test before publishing
Use Modeling, View as, select a role, and confirm that only that role's rows show. Test each role, and a combination if one person can be in two roles.

## Assign members in the Power BI service
1. Publish the report.
2. Open the workspace, find the semantic model, and open Security from its menu.
3. Select a role and add users, security groups or mail-enabled groups. Save.
4. Use Test as role in the service to confirm what a member sees.

Remember that a person in several roles sees the combined rows of all their roles.
