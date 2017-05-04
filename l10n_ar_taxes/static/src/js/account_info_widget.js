odoo.define('account.invoice.info', function (require) {
"use strict";

var core = require('web.core');
var form_common = require('web.form_common');
var formats = require('web.formats');
var Model = require('web.Model');

var QWeb = core.qweb;

var ShowAmountInfoWidget = form_common.AbstractField.extend({
    render_value: function() {
        var self = this;
        var info = JSON.parse(this.get('value'));
        var invoice_id = info.invoice_id;
        if (info !== false) {
            _.each(info.content, function(k,v){
                k.index = v;
                k.amount = formats.format_value(k.amount, {type: "float", digits: k.digits});
                if (k.date){
                    k.date = formats.format_value(k.date, {type: "date"});
                }
            });
            this.$el.html(QWeb.render('ShowAmountInfo', {
                'title': info.title
            }));
            _.each(this.$('.js_amount_info'), function(k, v){
                var options = {
                    'content': QWeb.render('AmountPopOver', {
                            'amount_to_tax': info.content[v].amount_to_tax,
                            'amount_not_taxable': info.content[v].amount_not_taxable,
                            'amount_exempt': info.content[v].amount_exempt,
                            'currency': info.content[v].currency,
                            'position': info.content[v].position,
                            }),
                    'html': true,
                    'placement': 'left',
                    'title': 'Informacion de importes',
                    'trigger': 'focus',
                    'delay': { "show": 0, "hide": 100 },
                };
                $(k).popover(options);
            });
        }
        else {
            this.$el.html('');
        }
    },
});

core.form_widget_registry.add('amountinfo', ShowAmountInfoWidget);

});