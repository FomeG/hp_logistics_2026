from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import unicodedata
import re


class UniqueNormalizedNameMixin(models.AbstractModel):
    _name = 'unique.normalized.name.mixin'
    _description = 'Mixin for normalized name uniqueness'

    normalized_name = fields.Char(
        string='Normalized Name',
        index=True,
        readonly=True,
        help='Automatically computed normalized version of the name for duplicate checking'
    )

    _sql_constraints = [
        ('unique_normalized_name', 'unique(normalized_name)', 'A record with this name already exists.'),
    ]

    @staticmethod
    def _normalize_text(text):
        if not text:
            return ''
        text = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8')
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        return text

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' in vals:
                if not vals.get('name'):
                    raise ValidationError(_('Name is required'))
                vals['normalized_name'] = self._normalize_text(vals['name'])
        return super().create(vals_list)

    def write(self, vals):
        if 'name' in vals:
            if not vals.get('name'):
                raise ValidationError(_('Name cannot be empty'))
            vals['normalized_name'] = self._normalize_text(vals['name'])
        return super().write(vals)

    @api.constrains('normalized_name')
    def _check_duplicate_name(self):
        for rec in self:
            if not rec.normalized_name:
                continue
            duplicates = self.search([
                ('id', '!=', rec.id),
                ('normalized_name', '=', rec.normalized_name)
            ], limit=1)
            if duplicates:
                raise ValidationError(_(
                    'A record with this name already exists (ID: %s: %s)',
                    duplicates[0].id, duplicates[0].display_name
                ))