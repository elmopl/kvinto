function LedgerTransactionForm(form)
{
    this.csrf_token = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    this.form = form;

    let widget = form.getElementsByClassName('ledger-transaction-widget')[0];
    this.transfers = new LedgerTransfersWidget(widget, this.csrf_token);

    document.getElementsByName('submit')[0].addEventListener('click', this.submit.bind(this));
}

LedgerTransactionForm.prototype.data = function()
{
    return {
        'id': parseInt(this._id_widget().value),
        'name': this._name_widget().value,
        'transfers': this.transfers.data(),
    };
}

LedgerTransactionForm.prototype.submit = function(evt)
{
    evt.preventDefault();
    let data = this.data();

    var xhr = new XMLHttpRequest();
    xhr.open('POST', this.form.action, true);
    xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
    xhr.setRequestHeader('X-CSRFToken', this.csrf_token);

    console.log(JSON.stringify(data));
  
    // send the collected data as JSON
    xhr.send(JSON.stringify(data));
  
    xhr.onloadend = function () {
        let info = JSON.parse(xhr.responseText);
        window.location.href = info.edit_url;
    };

    return false;
}

LedgerTransactionForm.prototype.add_transfer = function(data)
{
    this.transfers.add(data);
}

LedgerTransactionForm.prototype.set_name = function(name)
{
    this._name_widget().value = name;
}

LedgerTransactionForm.prototype.set_id = function(id)
{
    this._id_widget().value = id;
}

LedgerTransactionForm.prototype._name_widget = function()
{
    return this.form.querySelector('[name=name]');
}

LedgerTransactionForm.prototype._id_widget = function()
{
    return this.form.querySelector('[name=transaction_id]');
}

document.addEventListener('DOMContentLoaded', function(){
    let form = new LedgerTransactionForm(
        document.getElementsByTagName('form')[0]
    );

    console.log(JSON.stringify(initial_form_data));

    if (initial_form_data)
    {
        form.set_name(initial_form_data.name || '');
        form.set_id(initial_form_data.id || '');
        for (transfer of initial_form_data.transfers || [])
        {
            form.add_transfer(transfer);
        }
    }
});
