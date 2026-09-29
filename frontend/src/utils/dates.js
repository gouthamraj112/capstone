// API timestamps are timezone-naive source clock readings; preserve the wall time.
export const formatTimestamp = value => String(value ?? '').replace('T', ' ').slice(0, 19)
export const formatDate = value => String(value ?? '').slice(0, 10)
export const formatClock = value => String(value ?? '').replace('T', ' ').slice(11, 16)
