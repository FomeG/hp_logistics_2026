from pkg_resources import require

from odoo import models, fields
from odoo.addons.hp_components.models import constants

class CsPreAlert(models.Model):
    _name = 'cs.pre.alert'
    _description = 'Pre Alert'
    _inherit = ['cs.order.detail']

    agent_id = fields.Many2one(
        'res.partner'
    )

    receiver_email = fields.Char()
    state = fields.Selection(
        constants.PreAlertState.SELECT_OPTIONS,
        required=True,
        default=constants.PreAlertState.DRAFT,
    )
    is_auto_send = fields.Boolean(
        required=True,
        string='Auto Send',
        default=False
    )
    sent_date = fields.Datetime(
        required=True,
    )
