from odoo import models, fields, api
from odoo.tools import config
import boto3
import os
import ast


class IrAttachmentInherit(models.Model):
    _inherit = 'ir.attachment'

    booking_id = fields.Many2one(
        comodel_name='freight.purchase.booking',
        string='Booking',
        help='Booking this document belongs to'
    )
    document_type = fields.Selection([
        ('booking_file', 'Booking File'),
        ('bl_draft', 'B/L Draft'),
        ('bl_final', 'B/L Final'),
        ('invoice', 'Invoice'),
        ('co', 'Certificate of Origin'),
        ('other', 'Other')
    ], string='Document Type')
    department = fields.Char(string="Department",compute='_compute_department')
    s3_path = fields.Char(string="S3 Path", readonly=False, store=True)

    @api.depends('res_model')
    def _compute_department(self):
        mapping = {
            'freight.purchase.booking': 'Pricing',
        }
        for rec in self:
            rec.department = mapping.get(rec.res_model, '')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('booking_id'):
                vals.setdefault('res_model', 'freight.purchase.booking')
                vals.setdefault('res_id', vals['booking_id'])
        return super().create(vals_list)

    @api.model
    def sync_document_to_s3(self):
        try:
            config_param = self.env['ir.config_parameter']
            models_list = config_param.get_param('model.list')
            model_list = ast.literal_eval(models_list) if models else []
            if not model_list:
                _logger.warning("No models found in config parameter 'model.list'.")
                return
            aws_access_key_id = config.get('s3.access.key.id')
            aws_secret_access_key = config.get('s3.secret.access.key')
            s3_bucket = config.get('s3.bucket')
            region_name = config.get('s3.region.name')
            s3 = boto3.client('s3',
                              aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key,
                              region_name=region_name
                              )
            attachments = self.env['ir.attachment'].search([
                ('res_model', 'in', model_list),
                ('type', '=', 'binary'),
                ('store_fname', '!=', False),
                ('s3_path','=', False)
            ])
            files_path_odoo = []
            filestore_path = config.filestore(self.env.cr.dbname)
            for attachment in attachments:
                filename = attachment.name
                ext = os.path.splitext(filename)[1]
                s3_key = f"hp_document/{attachment.store_fname}.{ext}"
                s3_path_aws = f"https://{s3_bucket}.s3.{region_name}.amazonaws.com/{s3_key}"
                file_path = os.path.join(filestore_path, attachment.store_fname)
                s3.upload_file(file_path, s3_bucket, s3_key)
                attachment.write({'s3_path': s3_path_aws})
                files_path_odoo.append(file_path)
            self._remove_filestore_path(files_path_odoo)
        except Exception as e:
            _logger.exception(f"Get error sync_document_to_s3: {e}")

    def _remove_filestore_path(self,files_path_odoo):
        for file_path in files_path_odoo:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                _logger.warning(f"Get error when remove file {file_path}: {e}")