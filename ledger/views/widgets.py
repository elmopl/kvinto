from django import forms

class LedgerWidget(forms.Widget):
    class Media:
        js = (
            'js/ledger_widgets.js',
        )
        css = {
            'all': ('css/ledger_widgets.css',),
        }


