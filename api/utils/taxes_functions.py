from decimal import Decimal

from api.models import HEAD, MARRIED_JOINTLY, MARRIED_SEPARATELY, SINGLE, WIDOWER

SINGLE_WITHHOLDING_STANDARD_RATE = (
    {'level_amount': Decimal('0.00'), 'base_withholding': Decimal('0.00'), 'percentage': Decimal('0.00')},
    {'level_amount': Decimal('12400.00'), 'base_withholding': Decimal('0.00'), 'percentage': Decimal('0.10')},
    {'level_amount': Decimal('22275.00'), 'base_withholding': Decimal('987.50'), 'percentage': Decimal('0.12')},
    {'level_amount': Decimal('52525.00'), 'base_withholding': Decimal('4617.50'), 'percentage': Decimal('0.22')},
    {'level_amount': Decimal('97925.00'), 'base_withholding': Decimal('14605.50'), 'percentage': Decimal('0.24')},
    {'level_amount': Decimal('175700.00'), 'base_withholding': Decimal('33271.50'), 'percentage': Decimal('0.32')},
    {'level_amount': Decimal('219750.00'), 'base_withholding': Decimal('47367.50'), 'percentage': Decimal('0.35')},
    {'level_amount': Decimal('530800.00'), 'base_withholding': Decimal('156235.00'), 'percentage': Decimal('0.37')},
)

SINGLE_WITHHOLDING_DUAL_RATE = (
    {'level_amount': Decimal('0.00'), 'base_withholding': Decimal('0.00'), 'percentage': Decimal('0.00')},
    {'level_amount': Decimal('6200.00'), 'base_withholding': Decimal('0.00'), 'percentage': Decimal('0.10')},
    {'level_amount': Decimal('11138.00'), 'base_withholding': Decimal('493.75'), 'percentage': Decimal('0.12')},
    {'level_amount': Decimal('26263.00'), 'base_withholding': Decimal('2308.75'), 'percentage': Decimal('0.22')},
    {'level_amount': Decimal('48963.00'), 'base_withholding': Decimal('7302.75'), 'percentage': Decimal('0.24')},
    {'level_amount': Decimal('87850.00'), 'base_withholding': Decimal('16635.75'), 'percentage': Decimal('0.32')},
    {'level_amount': Decimal('109875.00'), 'base_withholding': Decimal('23683.75'), 'percentage': Decimal('0.35')},
    {'level_amount': Decimal('265400.00'), 'base_withholding': Decimal('78117.50'), 'percentage': Decimal('0.37')},
)

HOH_WITHHOLDING_STANDARD_RATE = (
    {'level_amount': Decimal('0.00'), 'base_withholding': Decimal('0.00'), 'percentage': Decimal('0.00')},
    {'level_amount': Decimal('18650.00'), 'base_withholding': Decimal('0.00'), 'percentage': Decimal('0.10')},
    {'level_amount': Decimal('32750.00'), 'base_withholding': Decimal('1410.00'), 'percentage': Decimal('0.12')},
    {'level_amount': Decimal('72350.00'), 'base_withholding': Decimal('6162.00'), 'percentage': Decimal('0.22')},
    {'level_amount': Decimal('104150.00'), 'base_withholding': Decimal('13158.00'), 'percentage': Decimal('0.24')},
    {'level_amount': Decimal('181950.00'), 'base_withholding': Decimal('31830.00'), 'percentage': Decimal('0.32')},
    {'level_amount': Decimal('226000.00'), 'base_withholding': Decimal('45926.00'), 'percentage': Decimal('0.35')},
    {'level_amount': Decimal('537050.00'), 'base_withholding': Decimal('154793.50'), 'percentage': Decimal('0.37')},
)

HOH_WITHHOLDING_DUAL_RATE = (
    {'level_amount': Decimal('0.00'), 'base_withholding': Decimal('0.00'), 'percentage': Decimal('0.00')},
    {'level_amount': Decimal('9325.00'), 'base_withholding': Decimal('0.00'), 'percentage': Decimal('0.10')},
    {'level_amount': Decimal('16375.00'), 'base_withholding': Decimal('705.00'), 'percentage': Decimal('0.12')},
    {'level_amount': Decimal('36175.00'), 'base_withholding': Decimal('3081.00'), 'percentage': Decimal('0.22')},
    {'level_amount': Decimal('52075.00'), 'base_withholding': Decimal('6579.00'), 'percentage': Decimal('0.24')},
    {'level_amount': Decimal('90975.00'), 'base_withholding': Decimal('15915.00'), 'percentage': Decimal('0.32')},
    {'level_amount': Decimal('113000.00'), 'base_withholding': Decimal('22963.00'), 'percentage': Decimal('0.35')},
    {'level_amount': Decimal('268525.00'), 'base_withholding': Decimal('77396.75'), 'percentage': Decimal('0.37')},
)

MARRIED_WITHHOLDING_STANDARD_RATE = (
    {'level_amount': Decimal('0.00'), 'base_withholding': Decimal('0.00'), 'percentage': Decimal('0.00')},
    {'level_amount': Decimal('24800.00'), 'base_withholding': Decimal('0.00'), 'percentage': Decimal('0.10')},
    {'level_amount': Decimal('44550.00'), 'base_withholding': Decimal('1975.00'), 'percentage': Decimal('0.12')},
    {'level_amount': Decimal('105050.00'), 'base_withholding': Decimal('9235.00'), 'percentage': Decimal('0.22')},
    {'level_amount': Decimal('195850.00'), 'base_withholding': Decimal('29211.00'), 'percentage': Decimal('0.24')},
    {'level_amount': Decimal('351400.00'), 'base_withholding': Decimal('66543.00'), 'percentage': Decimal('0.32')},
    {'level_amount': Decimal('439500.00'), 'base_withholding': Decimal('94735.00'), 'percentage': Decimal('0.35')},
    {'level_amount': Decimal('646850.00'), 'base_withholding': Decimal('167307.50'), 'percentage': Decimal('0.37')},
)

MARRIED_WITHHOLDING_DUAL_RATE = (
    {'level_amount': Decimal('0.00'), 'base_withholding': Decimal('0.00'), 'percentage': Decimal('0.00')},
    {'level_amount': Decimal('12400.00'), 'base_withholding': Decimal('0.00'), 'percentage': Decimal('0.10')},
    {'level_amount': Decimal('22275.00'), 'base_withholding': Decimal('987.50'), 'percentage': Decimal('0.12')},
    {'level_amount': Decimal('52525.00'), 'base_withholding': Decimal('4617.50'), 'percentage': Decimal('0.22')},
    {'level_amount': Decimal('97925.00'), 'base_withholding': Decimal('14605.50'), 'percentage': Decimal('0.24')},
    {'level_amount': Decimal('175700.00'), 'base_withholding': Decimal('33271.50'), 'percentage': Decimal('0.32')},
    {'level_amount': Decimal('219750.00'), 'base_withholding': Decimal('47367.50'), 'percentage': Decimal('0.35')},
    {'level_amount': Decimal('323425.00'), 'base_withholding': Decimal('83653.75'), 'percentage': Decimal('0.37')},
)


def get_tentative_withholding(adjusted_wage, filling_status, step2c_checked):
    if filling_status == SINGLE or filling_status == MARRIED_SEPARATELY:
        if step2c_checked:
            table = SINGLE_WITHHOLDING_DUAL_RATE
        else:
            table = SINGLE_WITHHOLDING_STANDARD_RATE
    elif filling_status == MARRIED_JOINTLY or filling_status == WIDOWER:
        if step2c_checked:
            table = MARRIED_WITHHOLDING_DUAL_RATE
        else:
            table = MARRIED_WITHHOLDING_STANDARD_RATE
    elif filling_status == HEAD:
        if step2c_checked:
            table = HOH_WITHHOLDING_DUAL_RATE
        else:
            table = HOH_WITHHOLDING_STANDARD_RATE
    else:
        raise ValueError('Invalid filling_status')
    ind = 0
    limit = len(table) - 1
    while ind < limit and adjusted_wage >= table[ind + 1].get('level_amount'):
        ind += 1
    total = round((adjusted_wage - table[ind].get('level_amount')) * table[ind].get('percentage'), 2) \
        + table[ind].get('base_withholding')
    return total
