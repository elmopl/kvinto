from ..models import Account
from ..models import Statement
from ..models import StatementRow
from datetime import date
from datetime import datetime
from django import forms
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from . import statement_parsers as parsers
import mimetypes
import os

PARSERS = {
    'HSBC PDF': parsers.parse_hsbc_pdf,
    'HSBC CSV': parsers.parse_hsbc_csv,
    'Starling CSV': parsers.parse_starling_csv,
}

class DateInput(forms.DateInput):
    input_type = 'date'

class UploadStatementForm(forms.Form):
    def __init__(self, accounts, parsers):
        super(UploadStatementForm, self).__init__()
        accounts = sorted(accounts, key=lambda v: v[1])
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
    positions = positions.order_by('-transaction_date')
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
            accounts=((acc.id, acc.full_name) for acc in accounts),
            parsers=((p, p) for p in PARSERS),
        )
    }
    return render(request, 'statements.html', context)
