from odoo import models, api

class HpDocumentService(models.AbstractModel):
    _name = 'hp.document.service'
    _description = 'Document Service Library'

    @api.model
    def create_document(self, name, document_type, datas, filename=None, **kwargs):
        vals = {
            'name': name,
            'document_type': document_type,
            'datas': datas,  # base64-encoded file
            'filename': filename or name,
            'uploaded_by': self.env.user.id,
        }
        vals.update(kwargs)
        return self.env['ir.attachment'].create(vals)

    @api.model
    def get_booking_documents(self, booking_id, document_type=None):
        domain = [('booking_id', '=', booking_id)]
        if document_type:
            domain.append(('document_type', '=', document_type))
        return self.env['ir.attachment'].search(domain)
