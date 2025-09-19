from odoo import models, fields, api
import json

class HpBankWizard(models.TransientModel):
    _name = 'hp.bank.wizard'
    _description = 'Wizard to add bank to system parameter'

    bank_name = fields.Char(string="Bank Name", required=True)
    bank_account = fields.Char(string="Bank Account", required=True)
    bank_holder_name = fields.Char(string="Bank Holder Name", required=True)

    def action_add_bank(self):
        param_obj = self.env['ir.config_parameter'].sudo()
        param_value = param_obj.get_param('hp_bank')
        banks = []

        if param_value:
            try:
                banks = json.loads(param_value)
            except Exception:
                banks = []

        # Check if bank already exists (optional)
        exists = any(b.get('bank_name') == self.bank_name and
                     b.get('bank_account') == self.bank_account for b in banks)
        if exists:
            return

        # Add new bank
        banks.append({
            'bank_name': self.bank_name,
            'bank_account': self.bank_account,
            'bank_holder_name': self.bank_holder_name
        })

        param_obj.set_param('hp_bank', json.dumps(banks))
