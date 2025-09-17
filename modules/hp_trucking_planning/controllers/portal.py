# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _, fields
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.portal import CustomerPortal


class TruckingPortal(CustomerPortal):

    @http.route(['/my/trip/<int:trip_id>'], type='http', auth="public", website=True)
    def portal_trip_page(
        self,
        trip_id,
        report_type=None,
        access_token=None,
        message=False,
        download=False,
        **kw
    ):
        try:
            trip_sudo = self._document_check_access('trucking_planning.trip', trip_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            # Only try to render PDF if the report action exists
            report_action = request.env.ref('hp_trucking_planning.action_report_trip_order', raise_if_not_found=False)
            if report_action:
                return self._show_report(
                    model=trip_sudo,
                    report_type=report_type,
                    report_ref='hp_trucking_planning.action_report_trip_order',
                    download=download,
                )
            # If missing, fall through to regular page render

        if request.env.user.share and access_token:
            # If a public/portal user accesses the trip with the access token
            # Log a note on the chatter.
            today = fields.Date.today().isoformat()
            session_obj_date = request.session.get('view_trip_%s' % trip_sudo.id)
            if session_obj_date != today:
                # store the date as a string in the session to allow serialization
                request.session['view_trip_%s' % trip_sudo.id] = today
                # The "Trip viewed by customer" log note is an information
                # dedicated to the staff and shouldn't be translated in the customer/website lang
                context = {'lang': request.env.user.partner_id.lang or request.env.company.partner_id.lang}
                author = trip_sudo.client_id if request.env.user._is_public() else request.env.user.partner_id
                msg = _('Trip viewed by customer %s', author.name)
                del context
                trip_sudo.message_post(
                    author_id=author.id,
                    body=msg,
                    message_type="notification",
                    subtype_xmlid="mail.mt_note",
                )

        backend_url = f'/odoo/action-{trip_sudo._get_portal_return_action().id}/{trip_sudo.id}'
        values = {
            'trip_order': trip_sudo,
            'message': message,
            'report_type': 'html',
            'backend_url': backend_url,
            'res_company': request.env.company,  # Use current user's company
            'has_pdf_report': bool(request.env.ref('hp_trucking_planning.action_report_trip_order', raise_if_not_found=False)),
        }

        return request.render("hp_trucking_planning.portal_trip_template", values) 