from odoo import models, fields, api
import json

class HpBankWizard(models.TransientModel):
    _name = 'hp.bank.wizard'
    _description = 'Wizard to add bank to system parameter'

    bank_name = fields.Char(string="Bank Name", required=True)
    bank_account = fields.Char(string="Bank Account", required=True)
    bank_holder_name = fields.Char(string="Bank Holder Name", required=True)
    type = fields.Selection([
        ('personal', 'personal'),
        ('company', 'company'),
    ], string="Bank Type", required=True, default='personal')
    active = fields.Boolean(string="Active", default=True)

    def action_add_bank(self):
        param_obj = self.env['ir.config_parameter'].sudo()
        param_value = param_obj.get_param('hp_bank')
        banks = []

        if param_value:
            try:
                banks = json.loads(param_value)
            except Exception:
                banks = []

        updated = False
        for bank in banks:
            if bank.get('bank_account') == self.bank_account:
                # Update nếu có rồi
                bank['bank_name'] = self.bank_name
                bank['bank_holder_name'] = self.bank_holder_name
                bank['type'] = self.type
                bank['active'] = self.active
                updated = True
                break

        if not updated:
            # Thêm mới
            banks.append({
                'bank_name': self.bank_name,
                'bank_account': self.bank_account,
                'bank_holder_name': self.bank_holder_name,
                'type': self.type,
                'active': self.active,
            })

        param_obj.set_param('hp_bank', json.dumps(banks))
