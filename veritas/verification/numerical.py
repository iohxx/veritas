from decimal import Decimal, InvalidOperation, localcontext
import re

NUMBER = r'-?\d{1,30}(?:\.\d{1,20})?'
RULES_VERSION = 'numerical-1'


def number(text):
    if not isinstance(text, str) or not re.fullmatch(NUMBER, text):
        raise ValueError('invalid_number')
    return Decimal(text)


def run_calculation(calc):
    base = {'kind':'numerical', 'operation':calc['operation'], 'operands':calc['operands'], 'expected':calc['expected'], 'scope':'arithmetic_only'}
    try:
        with localcontext() as ctx:
            ctx.prec = 60
            xs = [number(v) for v in calc['operands']]
            op = calc['operation']
            if op in ('subtract','divide','ratio','percentage_change','compare') and len(xs) != 2:
                raise ValueError('requires_two_operands')
            if op == 'add':
                value = sum(xs, Decimal(0))
            elif op == 'subtract':
                value = xs[0] - xs[1]
            elif op == 'multiply':
                value = Decimal(1)
                for x in xs:
                    value *= x
            elif op in ('divide', 'ratio'):
                value = xs[0] / xs[1]
            elif op == 'percentage_change':
                value = (xs[1] - xs[0]) / xs[0] * 100
            elif op == 'mean':
                value = sum(xs) / len(xs)
            elif op == 'compare':
                actual = 'less' if xs[0] < xs[1] else 'greater' if xs[0] > xs[1] else 'equal'
                return dict(base, actual=actual, outcome='pass' if actual == calc['expected'] else 'fail')
            elif op == 'convert':
                factors = {('km','m'):Decimal(1000), ('m','km'):Decimal('0.001'), ('kg','g'):Decimal(1000), ('g','kg'):Decimal('0.001'), ('h','min'):Decimal(60)}
                if len(xs) != 1:
                    raise ValueError()
                value = xs[0] * factors[(calc.get('unit_from'), calc.get('unit_to'))]
            else:
                raise ValueError()
            expected = number(calc['expected'])
            return dict(base, actual=format(value, 'f'), outcome='pass' if value == expected else 'fail')
    except (ArithmeticError, ValueError, KeyError) as exc:
        return dict(base, outcome='unavailable', reason='unsupported_or_invalid_calculation')


def extract_pure(claim):
    # Anchored grammar: appended real-world assertions are NEVER validated by this shortcut.
    match = re.fullmatch(rf'The total of ({NUMBER}(?:\s*\+\s*{NUMBER}){{1,29}}) is ({NUMBER})\.?', claim.strip(), re.IGNORECASE)
    if match:
        return {'operation':'add', 'operands':[v.strip() for v in match[1].split('+')], 'expected':match[2]}
    match = re.fullmatch(rf'({NUMBER}) is ({NUMBER})\s*% (?:greater|higher) than ({NUMBER})\.?', claim.strip(), re.IGNORECASE)
    if match:
        return {'operation':'percentage_change', 'operands':[match[3], match[1]], 'expected':match[2]}
    return None


def numerical_checks(job):
    pure = extract_pure(job.claim)
    checks = [run_calculation(pure)] if pure else []
    submitted = extract_pure(job.submitted_result)
    if submitted and job.submitted_result.strip() != job.claim.strip():
        checks.append(dict(run_calculation(submitted), scope='submitted_result_arithmetic'))
    checks.extend(run_calculation(c.model_dump()) for c in job.calculations)
    return {'version':RULES_VERSION, 'pure_arithmetic':pure is not None and job.submitted_result.strip() == job.claim.strip(), 'checks':checks}
