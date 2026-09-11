"""Research arithmetic/counterexample verifier; NOT a DCA/production implementation.

Run inside this folder with: python arastirma_oracle.py
No production imports, order state machine, fee/reserve formula, API, or persistence.
"""
from decimal import Decimal, localcontext, Inexact, Rounded, FloatOperation
from fractions import Fraction
from pathlib import Path
import json
import platform

HERE = Path(__file__).resolve().parent

def main():
    checks = []
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append({'id': name, 'result': 'PASS', 'scope': 'RESEARCH_EXAMPLE_ONLY'})

    data = json.loads((HERE/'fixture.json').read_text(encoding='utf-8'))
    original_text = data['original_qty']
    price_text = data['declared_limit']
    rows = []
    with localcontext() as ctx:
        ctx.prec = 60
        ctx.traps[Inexact] = True
        ctx.traps[Rounded] = True
        ctx.traps[FloatOperation] = True
        quantity = Decimal(original_text)
        price = Decimal(price_text)
        filled = Decimal('0')
        gross = Decimal('0')
        fees = Decimal('0')
        rational_filled = Fraction(0)
        rational_gross = Fraction(0)
        rational_fees = Fraction(0)
        for index, row in enumerate(data['supplied_fill_vectors'], 1):
            q = Decimal(row['qty'])
            fee = Decimal(row['supplied_fee_amount'])
            check(f'Q{index}_fixture_positive_quantity', q > 0)
            check(f'Q{index}_fixture_no_overfill', filled + q <= quantity)
            filled += q
            gross += q * price
            fees += fee
            leaves = quantity - filled
            rational_filled += Fraction(row['qty'])
            rational_gross += Fraction(row['qty']) * Fraction(price_text)
            rational_fees += Fraction(row['supplied_fee_amount'])
            expected = data['literal_reference_rows'][index-1]
            actual = dict(filled=str(filled), leaves=str(leaves), gross_notional=str(gross), supplied_quote_fee_total=str(fees))
            for field in actual:
                check(f'Q{index}_{field}_literal', Decimal(actual[field]) == Decimal(expected[field]))
            check(f'Q{index}_conservation', Fraction(filled) + Fraction(leaves) == Fraction(original_text))
            check(f'Q{index}_rational_quantity', Fraction(filled) == rational_filled)
            check(f'Q{index}_rational_notional', Fraction(gross) == rational_gross)
            check(f'Q{index}_rational_fee', Fraction(fees) == rational_fees)
            rows.append(actual)
        check('Q_final_gross_average_reference', gross / filled == Decimal('100.10'))

        # These are direct mathematical comparison checks, not a candidate generator.
        for case in data['comparison_vectors']:
            value, limit = Decimal(case['extreme']), Decimal(case['limit'])
            answer = value < limit if case['side'] == 'BUY' else value > limit
            rational_answer = Fraction(case['extreme']) < Fraction(case['limit']) if case['side'] == 'BUY' else Fraction(case['extreme']) > Fraction(case['limit'])
            check(case['id']+'_decimal', answer is case['strict_expected'])
            check(case['id']+'_rational', rational_answer is case['strict_expected'])

    # Information-theoretic counterexample; no simulated execution assumed.
    a = [Fraction(x) for x in data['ohlc_counterexample']['path_a']]
    b = [Fraction(x) for x in data['ohlc_counterexample']['path_b']]
    def ohlc(path):
        return [path[0], max(path), min(path), path[-1]]
    expected_ohlc = [Fraction(x) for x in ['105','115','85','105']]
    check('OHLC_paths_are_distinct', a != b)
    check('OHLC_same_literal_summary', ohlc(a) == ohlc(b) == expected_ohlc)
    check('OHLC_high_low_order_differs', a.index(max(a)) < a.index(min(a)) and b.index(min(b)) < b.index(max(b)))

    # Deliberately illustrate why float input is not a source of exact decimal intent.
    check('FLOAT_decimal_string_and_binary_float_differ', Fraction('0.1') != Fraction(0.1))
    check('JSON_fixture_strings_preserved', json.loads(json.dumps(data)) == data)
    result = {
        'status': 'PASS_RESEARCH_EXAMPLES_ONLY',
        'production_gate_status': 'DEFER_LOCAL_CODE_REQUIRED',
        'python_runtime_version': platform.python_version(),
        'checked_reference_rows': rows,
        'check_count': len(checks),
        'checks': checks,
        'not_tested': ['actual reducer', 'adapter wiring', 'reserve lifecycle', 'anchor', 'domain position cost', 'net fee asset allocation', 'duplicate/late handling', 'production timing', 'legacy regression', 'persistence recovery'],
        'fee_note': 'Literal synthetic input amounts; no fee formula or venue fee rate is defined.',
        'unknown_domain_fields': {'reserve': 'LOCAL-CODE-REQUIRED', 'anchor': 'LOCAL-CODE-REQUIRED', 'domain_position_cost': 'LOCAL-CODE-REQUIRED'}
    }
    (HERE/'oracle_sonucu.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'check_count':len(checks),'production_gate_status':result['production_gate_status']},ensure_ascii=False))

if __name__ == '__main__':
    main()
