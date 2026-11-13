---
id: unknown-error-triage
title: Triage method for an unfamiliar error
category: general
keywords: unknown error, unfamiliar error, new error, unexpected error, error code, never seen, unclear error message, general troubleshooting
source: ReportPulse seed knowledge
---
## Principle
When an error is new, do not guess a fix. Narrow down where the failure happens, then change one thing at a time and record the result.

## Steps
1. Get the full error. The validation file often shows only a short message. Refresh history has the full text, the error code and the Activity ID.
2. Find the last successful refresh and ask what changed since then: the report, the source data or structure, credentials, the gateway or its host, the network, the capacity.
3. Classify the failure from the wording: connection or gateway, credentials or permission, missing or renamed object, data or type problem, time limit, memory or size limit.
4. Reproduce it: refresh the same model in Power BI Desktop. If it fails there too, the problem is in the model or the source, not the service. If it works in Desktop, suspect the gateway, credentials or capacity.
5. Isolate: refresh one table or query at a time to find the one that fails.
6. Change one thing, retest, and write down the outcome before changing anything else.
7. If nothing narrows it down, escalate with a complete summary (see the escalation document).

## Be honest about uncertainty
If the message does not match anything familiar, say so, state the most likely categories, and ask for the missing information instead of presenting a guess as a fact.
