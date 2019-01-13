import csv
import itertools
from collections import namedtuple
from datetime import datetime
import logging
import subprocess
import tempfile

ParsedRow = namedtuple('ParsedRow', ('date', 'billed', 'amount', 'name'))

def increment_month(date):
    if date.month == 12:
        return date.replace(year=date.year+1, month=1, day=1)
    else:
        return date.replace(month=date.month+1, day=1)

def parse_amount(text):
    try:
        return int(text.replace('.', '').replace(',', ''))
    except Exception as exc:
        raise Exception('Could not parse `{}`: {}'.format(text, exc))

def parse_hsbc_pdf(file_obj):
    out = tempfile.NamedTemporaryFile()
    with tempfile.NamedTemporaryFile() as err:
        p = subprocess.Popen(
            ('pdftotext', '-layout', '-enc', 'UTF-8', '-', out.name),
            stdin=subprocess.PIPE,
            stdout=out,
            stderr=err,
        )
        p.stdin.write(file_obj.read())
        p.stdin.close()
        p.wait()

        err.seek(0)

        if p.returncode != 0:
            raise Exception(err.read().decode('utf-8'))

    with out as data:
        lines = data.read().decode('utf-8').splitlines()
        rows = itertools.dropwhile(
            lambda line: 'Statement Date' not in line,
            lines
        )
        rows = itertools.takewhile(
            lambda line: 'Summary Of Interest On This Statement' not in line,
            rows
        ) 

        statement_info = next(rows)
        statement_date = datetime.strptime(' '.join(statement_info.split()[2:5]), '%d %B %Y').date()

        parsed = []
        for row in rows:
            row = row.strip()
            if not row:
                continue

            parts = row.split()
            try:
                billed = datetime.strptime(' '.join(parts[0:3]), '%d %b %y').date()
                date = datetime.strptime(' '.join(parts[3:6]), '%d %b %y').date()
            except ValueError as exc:
                logging.warning(str(exc))
                continue

            name = ' '.join(parts[6:-1])

            amount = parts[-1]
            if amount[-2:] == 'CR':
                amount = parse_amount(amount[:-2])
            else:
                amount = -parse_amount(amount)

            parsed.append(ParsedRow(
                billed=billed,
                date=date,
                name=name,
                amount=amount
            ))

    return statement_date, parsed

def parse_hsbc_csv(file_obj):
    data = csv.reader(file_obj.read().decode('utf-8').splitlines())
    data = iter(data)
    assert next(data) == ['date', 'description', 'amount', 'balance']
    opening_row = next(data)
    assert opening_row[1] == 'Opening balance this month'
    assert opening_row[2] == 'null'
    opening_balance = parse_amount(opening_row[3])

    parsed = []
    current_balance = opening_balance
    rows = list(data)
    prev_billed = None
    for row in rows[:-1]:
        billed = datetime.strptime(row[0], '%Y-%m-%d').date()
        amount = parse_amount(row[2])
        name = row[1]
        balance = row[3]
        if billed != prev_billed and prev_billed is not None:
            assert current_balance == last_seen_balance, (current_balance, last_seen_balance)
        prev_billed = billed

        if balance != 'null':
            last_seen_balance = parse_amount(balance)

        current_balance += amount

        parsed.append(ParsedRow(
            billed = billed,
            date = billed,
            name = name, 
            amount = amount,
        ))

    closing_row = rows[-1]
    assert closing_row[1] == 'Closing balance this month'
    assert closing_row[2] == 'null'
    closing_date = datetime.strptime(closing_row[0], '%Y-%m-%d').date()

    return closing_date, parsed

def parse_starling_csv(file_obj):
    data = csv.reader(file_obj.read().decode('utf-8').splitlines())
    data = iter(data)
    columns = next(data)
    assert columns == ["Date", "Counter Party", "Reference", "Type", "Amount (GBP)", "Balance (GBP)"]

    rows = (dict(zip(columns, row)) for row in data)

    row = next(rows)
    assert row['Counter Party'] == 'Opening Balance', row
    current_balance = parse_amount(row['Balance (GBP)'])
    parsed = []
    statement_date = None
    for row in rows:
        if all(v == '' for v in row.values()):
            break
        amount = parse_amount(row['Amount (GBP)'])
        current_balance += amount
        billed = datetime.strptime(row['Date'], "%d/%m/%Y").date()
        statement_date = billed
        assert current_balance == parse_amount(row['Balance (GBP)'])
        name = '{} - {}'.format(row['Counter Party'], row['Reference'])

        parsed.append(ParsedRow(
            billed = billed,
            date = billed,
            name = name, 
            amount = amount,
        ))

    statement_date = increment_month(statement_date.replace(day=1))

    return statement_date, parsed

