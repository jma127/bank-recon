#!/usr/bin/env python

import csv, datetime, decimal, re, sys

strip_chars = set(['$', ','])
type_counts = {}

def moneyfmt(value, places=2, curr='', sep=',', dp='.',  # From Python Decimal class documentation
             pos='', neg='-', trailneg=''):
    """Convert Decimal to a money formatted string.

    places:  required number of places after the decimal point
    curr:    optional currency symbol before the sign (may be blank)
    sep:     optional grouping separator (comma, period, space, or blank)
    dp:      decimal point indicator (comma or period)
             only specify as blank when places is zero
    pos:     optional sign for positive numbers: '+', space or blank
    neg:     optional sign for negative numbers: '-', '(', space or blank
    trailneg:optional trailing minus indicator:  '-', ')', space or blank

    >>> d = Decimal('-1234567.8901')
    >>> moneyfmt(d, curr='$')
    '-$1,234,567.89'
    >>> moneyfmt(d, places=0, sep='.', dp='', neg='', trailneg='-')
    '1.234.568-'
    >>> moneyfmt(d, curr='$', neg='(', trailneg=')')
    '($1,234,567.89)'
    >>> moneyfmt(Decimal(123456789), sep=' ')
    '123 456 789.00'
    >>> moneyfmt(Decimal('-0.02'), neg='<', trailneg='>')
    '<0.02>'

    """
    q = decimal.Decimal(10) ** -places      # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    digits = map(str, digits)
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        build(next() if digits else '0')
    build(dp)
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    return ''.join(reversed(result))

def fmt_amt(amt):
    return moneyfmt(amt, sep='', places=max(2, -amt.as_tuple().exponent))

def keys_to_lower(dic):
    lower_dict = {}
    for key, val in dic.iteritems():
        lower_dict[key.strip().lower()] = val
    return lower_dict

def parse_amt(amtstr):
    amtstr = amtstr.strip()
    noparen = amtstr.strip('()')
    amt = decimal.Decimal(''.join(['' if c in strip_chars else c for c in noparen])) * (1 if noparen == amtstr else -1)
    if amt.as_tuple().exponent < -8:
        raise Exception("Something's probably wrong -- you have am amount with more than 8 decimal places.")
    return amt

def print_msg(msg, level='INFO'):
    global type_counts
    if level in type_counts:
        type_counts[level] += 1
    else:
        type_counts[level] = 1
    print '[{:<5}] {}'.format(level, msg)
    

class Transaction:
    def __init__(self, **kwargs):
        entry = keys_to_lower(kwargs)
        try:
            self.amount = parse_amt(entry['amount'])
        except:
            print_msg('Unable to parse transaction amount from entry {}.'.format(entry), 'ERROR')
            raise 
        try:
            self.date = None
            if 'date' in entry:
                self.date = datetime.datetime.strptime(entry['date'], '%m/%d/%Y')
        except:
            print_msg('Unable to parse transaction date from entry {}.'.format(entry), 'ERROR')
            raise
        try:
            self.balance = None
            if entry.get('balance', '').strip():
                self.balance = parse_amt(entry['balance'])
        except:
            print_msg('Unable to parse balance remaining from entry {}.'.format(entry), 'ERROR')
            raise
        self.info = entry
        self.pending = entry.get('description', '').strip().lower().endswith('(pending)') or not entry.get('balance', '').strip()

    def __repr__(self):
        return ('[Pending] ' if self.pending else '') + ', '.join(['{}: {}'.format(key, val if val else 'None') for key, val in self.info.iteritems()])

def get_delta(transactions):
    prev_bal = None
    delta = decimal.Decimal(0)
    for trans in transactions:
        delta += trans.amount
        if prev_bal and trans.balance and prev_bal + trans.amount != trans.balance:
            print_msg('transaction [{}] is NOT consistent with previous balance of {}.'.format(trans, fmt_amt(prev_bal)), 'ERROR')
        prev_bal = trans.balance
    return delta

def main():
    decimal.getcontext().prec = 30  # should be enough precision, LMK if you become a yotta-aire
    statement_reader = csv.DictReader(sys.stdin)
    transactions = []
    for entry in statement_reader:
        trans = Transaction(**entry)
        if trans.pending:
            print_msg('Skipping pending transaction [{}].'.format(trans), 'WARN')
        else:
            transactions.append(trans)
    if not transactions:
        print_msg('No transactions entered.', 'ERROR')
        return
    transactions.sort(key=lambda transaction: transaction.date)
    change = get_delta(transactions)
    print_msg('Total change in balance should be {}.'.format(change), 'INFO')
    try:
        starting_balance = transactions[0].balance - transactions[0].amount
        ending_balance = transactions[-1].balance
        if starting_balance + change == ending_balance:
            print_msg('Starting and ending balances are consistent with transaction history.', 'GOOD')
        else:
            print_msg('Starting and ending balances are NOT consistent with transaction history: calcuated balance change of {}, actual change of {}.'.format(ending_balance - starting_balance, change), 'ERROR')
    except:
        print_msg('Unable to reconcile starting and ending balances (maybe the balance column was not provided?).', 'WARN')
    global type_counts
    print '{} errors, {} warnings.'.format(type_counts.get('ERROR', 0), type_counts.get('WARN', 0))

if __name__ == '__main__':
    main()
