# Bugfix fixture

`parse_timeout` regressed when an explicit `0` was supplied: the old truthiness fallback treated it as missing and returned the default. Identify the root cause, make the smallest fix, add or preserve regression coverage, and do not change invalid-input behavior.
