---
id: rls-testing-and-troubleshooting
title: Testing RLS and fixing RLS problems
category: rls
keywords: RLS not working, view as shows all rows, user sees no data, sees everything, admin sees all data, role not applied, test as role, multiple roles, RLS bypass, blank report, RLS troubleshooting
source: ReportPulse seed knowledge (verify against current Microsoft documentation)
---
## How to test
In Power BI Desktop use Modeling, View as and pick the role (and Other user for dynamic RLS). In the service open the semantic model, then Security, and use Test as role. Always test with a real example user from each group.

## If a tester sees all the rows
- They are a workspace Admin, Member or Contributor, or otherwise have edit permission on the model. RLS does not restrict these people. Test with a Viewer account or with Test as role.
- The role was not selected in View as, or the person is also a member of a role with no filter.
- The filter is on a table that does not filter the fact table because of a missing or inactive relationship, or a relationship direction that blocks it.

## If a user sees no data
- For dynamic RLS, the user's sign-in name is not in the mapping table, or the spelling or case differs from what USERPRINCIPALNAME returns.
- The filter value has extra spaces or a different case than the data.
- The user is not a member of any role, so the report rejects or shows nothing, depending on how the report is shared.

## Other points
- A person in several roles sees the union of the rows allowed by each role.
- For a live connection to an Analysis Services model, RLS is defined at the source, not in the report.
- Changes to roles need the report to be republished, and role membership is changed in the service.
- Sharing through apps, Analyze in Excel or exported data still follows RLS for Viewers.
