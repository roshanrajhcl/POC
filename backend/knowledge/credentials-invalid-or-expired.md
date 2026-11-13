---
id: credentials-invalid-or-expired
title: Data source credentials invalid or expired
category: refresh
keywords: credentials, invalid credentials, the credentials provided for the data source are invalid, password changed, token expired, OAuth, login failed, access denied, authentication failed, unauthorized, expired
source: ReportPulse seed knowledge (verify against current Microsoft documentation)
---
## What it means
The stored sign-in for the data source no longer works, so the refresh cannot read the data.

## Common causes
- The password of the account used for the source changed or expired.
- An OAuth sign-in token expired, for example after a password change, a multi-factor authentication or conditional access change, or a long period without use.
- The account was locked, disabled, or lost permission on the source.
- A service principal secret expired.
- Credentials were never saved after publishing.

## Steps
1. Open the workspace, then the semantic model, then Settings.
2. Under Data source credentials, select Edit credentials for each source.
3. Choose the right authentication method and sign in again. Use a shared service account, not a personal account, where policy allows.
4. Confirm outside Power BI that the account can still sign in to the source and has permission on the tables used.
5. Select Refresh now and check Refresh history.

If credentials keep expiring, ask for a service account with a non-expiring password policy, or review how often the secret or token is renewed.
