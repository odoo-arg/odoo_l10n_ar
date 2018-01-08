odoo.define('l10n_ar_payment_imputation.create_payment_wizard', function(require){

    var ListView = require('web.ListView');

    ListView.include({
        render_buttons: function() {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.$buttons.find('#payment_imputation').click(this.proxy('create_imputation'));
            }
        },

        create_imputation: function () {
            if (this.getParent().action.context.default_payment_type != 'transfer'){
                this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: 'payment.imputation.wizard',
                    views: [[false, 'form']],
                    target: 'new',
                    context: this.getParent().action.context
                });
            }else{
                this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: 'account.payment',
                    views: [[false, 'form']],
                    context: this.getParent().action.context
                });
            }
        }
    });
});