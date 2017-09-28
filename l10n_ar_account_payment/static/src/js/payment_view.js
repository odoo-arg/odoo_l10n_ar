openerp.payment = function (instance){
    var QWeb = openerp.web.qweb;
    _t = instance.web._t;
    var self = this;
    openerp.web.ListView.include({
    load_list: function() {
        console.log('intentando load listear');
        this._super();
        console.log('no loadlistie nada');
        console.log(this.$buttons)
        if (this.$buttons) {
            this.$buttons.find('.oe_new_button').off().click(this.proxy('return_payment_imputation')) ;
            console.log('Save & Close button method call...');
        }
    },
    return_payment_imputation: function () {
        console.log('CORRIENDO FUNCION')
        this.do_action({
            type: "ir.actions.act_window",
            name: "Seleccionar pagos a imputar",
            res_model: "account.payment",
            views: [[false,'form']],
            target: 'current',
            view_type : 'form',
            view_mode : 'form',

            flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
        });
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
}
});
}
