# SPDX-License-Identifier: AGPL-3.0-only
"""Classification of proven F2.3 events only. Does not detect or control anything."""
MAJOR = frozenset({'session_started', 'session_resumed', 'edge', 'milestone', 'stop'})
CRITICAL = frozenset({'signal_lost', 'no_contact'})

def significance(kind, previous, current):
    if kind in CRITICAL:return 'critical', 100
    if kind == 'device_changed' and previous and current['status'] != 'IDLE':
        before, after = previous['devices'], current['devices']
        if any(before.get(k) is True and after.get(k) is False for k in ('ble','handy','intiface','tcode')):
            return 'critical', 100
    if kind in MAJOR:return 'major', 50
    return 'routine', 10
