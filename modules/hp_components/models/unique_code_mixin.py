from odoo import models, fields, api
from odoo.exceptions import ValidationError
import random
import string
import re

import logging
_logger = logging.getLogger(__name__)

class UniqueCodeMixin(models.AbstractModel):
    _name = 'unique.code.mixin'
    _description = 'Shared logic for models with unique code'
    _inherit = []
    code = fields.Char(
        string='Reference Code',
        required=True,
        index=True,
        copy=False,
        default='/',
        help="Unique identifier. Auto-generated if left blank."
    )

    _sql_constraints = [
        ('unique_code', 'unique(code)', 'The code must be unique.')
    ]

    @api.model
    def _generate_code_from_name(self, name, used_codes=None):
        if used_codes is None:
            used_codes = set()
        if not name:
            return '/'
        name = re.sub(r'[-–—]', ' ', name)
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        parts = clean_name.split()[:3]
        if len(parts) == 1:
            base_code = clean_name.upper()
        else:
            base_code = ''.join([w[0] for w in parts if w]).upper()[:6]
        code = base_code
        counter = 1
        while ( self.search_count([('code', '=', code)]) > 0 or code in used_codes ):
            code = f"{base_code}-{counter}"

            counter += 1
            if counter > 1000:
                suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                code = f"{base_code}-{suffix}"
                break
        return code

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [dict(vals) for vals in vals_list]
        used_codes = set()
        for vals in vals_list:
            if vals.get('code', '/') == '/' and 'name' in vals:
                vals['code'] = self._generate_code_from_name(vals['name'], used_codes)
                used_codes.add(vals['code'])
        return super().create(vals_list)

    @api.constrains('code')
    def _check_code_uniqueness(self):
        for record in self:
            if record.code == '/':
                raise ValidationError(f"Code cannot be empty!")
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]):
                raise ValidationError(f"Code {record.code} already exists!")

    @api.onchange('code')
    def _prevent_code_change(self):
        if self.code and self._origin.code and self.code != self._origin.code:
            raise ValidationError("Code cannot be changed once set.")