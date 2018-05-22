from ..models import Account
from ..models import Statement
from ..models import StatementRow
from collections import namedtuple
from datetime import date
from datetime import datetime
from django import forms
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
import csv
import itertools
import logging
import mimetypes
import os
import subprocess
import tempfile

# Create your views here.
ParsedRow = namedtuple('ParsedRow', ('date', 'billed', 'amount', 'name'))

def parse_amount(text):
    try:
        return int(text.replace('.', ''))
    except Exception as exc:
        raise Exception('Could not parse `{}`: {}'.format(text, exc))

def prase_hsbc_pdf_row(text):
    text = text.strip()

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

    return None, parsed

PARSERS = {
    'HSBC PDF': parse_hsbc_pdf,
    'HSBC CSV': parse_hsbc_csv,
}

class DateInput(forms.DateInput):
    input_type = 'date'

class UploadStatementForm(forms.Form):
    def __init__(self, accounts, parsers):
        super(UploadStatementForm, self).__init__()
        self.fields['account'] = forms.ChoiceField(choices=accounts)
        self.fields['parser'] = forms.ChoiceField(choices=parsers)
        self.fields['date'] = forms.DateField(widget=DateInput())
        self.fields['statement_file'] = forms.FileField()

def accounts(request):
    return HttpResponse('test')

def download(request, statement_id):
    statement = Statement.objects.get(id=statement_id)
    src = statement.source
    response = HttpResponse(
        src,
        content_type=mimetypes.guess_type(src.path)[0],
    )
    response['Content-Disposition'] = 'inline;filename={}'.format(os.path.basename(src.name))
    return response

def show(request, statement_id):
    statement = Statement.objects.get(id=statement_id)
    context = {
        'statement': statement,
        'rows': statement.rows.order_by('transaction_date'),
    }
    return render(request, 'statement.html', context)

def _show_positions(request, start_date, end_date):
    positions = StatementRow.objects
    positions = positions.prefetch_related('statement').prefetch_related('statement__account').prefetch_related('transfer')
    positions = positions.filter(transaction_date__range = (start_date, end_date))
    positions = positions.order_by('transaction_date')
    print(positions.query)
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'positions': positions,
    }
    return render(request, 'statement_positions.html', context)

def show_year_positions(request, year):
    return _show_positions(request, date(year, 1, 1), date(year+1, 1, 1))

def show_positions(request, year, month, day, end_year, end_month, end_day):
    start_date = date(year, month, day)
    end_date = date(end_year, end_month, end_day)
    return _show_positions(request, start_date, end_date)

def destroy(request, statement_id):
    statement = Statement.objects.get(id=statement_id)
    statement.delete()
    return redirect('list_statements')

@transaction.atomic
def upload(request):
    statement_date = datetime.strptime(request.POST['date'], '%Y-%m-%d').date()
    statement = Statement(
        source = request.FILES['statement_file'],
        account = Account.objects.get(id=request.POST['account']),
        date = statement_date,
    )

    parse = PARSERS[request.POST['parser']]
    parsed_date, rows = parse(request.FILES['statement_file'])

    if parsed_date is not None:
        assert parsed_date == statement_date, (statement_date, parsed_date)

    statement.save()

    for row in rows:
        StatementRow(
            statement = statement,
            name = row.name,
            amount = row.amount,
            billing_date = row.billed,
            transaction_date = row.date,
        ).save()

    return redirect('view_statement', statement_id=statement.id)

def statements_list(request):
    statements = Statement.objects.order_by('date')
    accounts = Account.objects.order_by('name')
    context = {
        'statements': statements,
        'upload_statement_form': UploadStatementForm(
            accounts=((acc.id, acc.name) for acc in accounts),
            parsers=((p, p) for p in PARSERS),
        )
    }
    return render(request, 'statements.html', context)
