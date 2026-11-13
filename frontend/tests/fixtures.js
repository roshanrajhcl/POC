// The two validation files from the brief, used by the "Try a sample" buttons and the self-check.
const NAMES = ['KR', 'AU', 'NZ', 'CN', 'FR', 'PT', 'PL', 'IT', 'UKIE'].map((c) => `${c}_Accrual detail Report`)

export const REFRESH_SAMPLE = [
  ['Yes', 'Completed', '', '10/4/2026, 10:08:23 PM'],
  ['Yes', 'Completed', '', '10/11/2026, 10:07:31 PM'],
  ['Yes', 'Failed', 'Timeout error', '9/28/2026, 11:13:40 AM'],
  ['Yes', 'Failed', 'An error occurred while processing', '9/27/2026, 11:27:50 PM'],
  ['Yes', 'Completed', '', '10/25/2026, 10:06:31 PM'],
  ['No', 'Not Configured', '', ''],
  ['No', 'Not Configured', '', ''],
  ['No', 'Not Configured', '', ''],
  ['No', 'Not Configured', '', ''],
].map(([enabled, status, error, last], i) => ({
  'Report Name': NAMES[i],
  'Refresh Enabled': enabled,
  'Refresh Status': status,
  'Error Message': error,
  'Last Refresh': last,
}))

export const RLS_SAMPLE = NAMES.map((name, i) => ({
  'Report Name': name,
  RLS_Implemented: i < 5 ? 'no' : 'Yes',
  Checked_On: '11/13/2026',
}))
