"""Independent rational arithmetic checks for the proposed document examples.

No DCABOT imports: passing proves these vectors, not the bot implementation.
"""
from fractions import Fraction as F
import json

checks = []
def check(name, actual, expected):
    if actual != expected:
        raise AssertionError((name, actual, expected))
    checks.append({"id": name, "result": "PASS", "exact_value": str(actual)})

check("fixed_capital", F(100)+4*F(50), F(300))
check("geometric_capital", F(100)+F(50)*(F(2)**8-1)/(2-1), F(12850))
check("second_anchor_level", F(100)*(1-2*F('0.1')), F(80))
check("weighted_average", (F(100)+F(90))/2, F(95))
check("partial_exit_cost", F(190)-F('.5')*95, F('142.5'))
check("partial_exit_realized", F('.5')*(110-95), F('7.5'))
check("remaining_unrealized", F('1.5')*(100-95), F('7.5'))
tp=(F(2)*95+F('.19')+F('1.9'))/(F(2)*(1-F('.001')))
check("net_tp_root", tp, F(32015,333))
check("net_at_rounded_tp", 2*(F('96.15')-95)-F('.19')-F('.001')*2*F('96.15'), F('1.9177'))
check("net_at_gross_tp", 2*(F('95.95')-95)-F('.19')-F('.001')*2*F('95.95'), F('1.5181'))
check("liquidation_long_toy", (F(100)-10)/(1-F('.005')), F(18000,199))
check("peak_drawdown", (F(120)-100)/120, F(1,6))
check("tick_floor", (F('100.13')//F('.25'))*F('.25'), F(100))
print(json.dumps({"scope": "DOCUMENT_RATIONAL_VECTORS_ONLY", "checks": checks}, indent=2))
