from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("""
        SELECT id
        FROM mail_template
        WHERE model = 'hr.applicant' AND name::text ILIKE %s
        LIMIT 1
    """, ['%Recruitment: Application Acknowledgement%'])
    record = cr.fetchone()
    if not record:
        return

    template = env['mail.template'].browse(record[0])
    if template:
        template.write({
            'subject': 'Thank you for applying for the position {{ object.job_id.name }}',
            'body_html': """
                <p>Hello <t t-out="object.partner_name"/> 👋</p>
                <p>Thank you for your interest and application to our company.</p>
                <p>The recruitment department will review and contact you as soon as possible.</p>
                <br/>
                <p>Best regards,<br/>Human Resources Department</p>
            """,
        })