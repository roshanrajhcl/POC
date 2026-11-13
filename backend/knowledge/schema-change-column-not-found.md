---
id: schema-change-column-not-found
title: Source table, sheet or column renamed or removed
category: refresh
keywords: the key didn't match any rows in the table, key did not match any rows, column of the table wasn't found, the column was not found, table not found, sheet not found, DataSource.Error, Expression.Error, name changed, schema change, column renamed, file moved
source: ReportPulse seed knowledge (verify against current Microsoft documentation)
---
## What it means
A Power Query step refers to a table, sheet, file or column by name, and that name no longer exists at the source. The refresh fails at that step. Typical messages: "The key didn't match any rows in the table", "The column 'X' of the table wasn't found", or a DataSource.Error saying a file or object was not found.

## Common causes
- Someone renamed or deleted a table, sheet, view or column at the source.
- A source file was moved, renamed or replaced with a different layout.
- Column order or header names in an Excel or CSV file changed.
- A database object was dropped and recreated with a different name.

## Steps
1. Open the report in Power BI Desktop and go to Transform data.
2. Select the query named in the error and find the first step that shows an error.
3. Compare the name used in that step with what exists at the source now.
4. Update the step to the new name, or restore the original name at the source if that is the better fix.
5. Check later steps that refer to the renamed column, then Close and Apply.
6. Publish again and select Refresh now.

## Prevent it next time
Agree a change process with the owner of the source, so renames are announced. Where possible, connect to a stable view instead of the raw table.
