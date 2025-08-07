from odoo import models, api

class WhatsAppMessage(models.Model):
    _inherit = 'whatsapp.message'

    @api.model
    def create(self, vals):
        message = super().create(vals)

        if message.direction == 'inbound' and message.phone:
            partner = self.env['res.partner'].search([
                ('mobile', '=', message.phone)
            ], limit=1)

            if not partner:
                partner = self.env['res.partner'].create({
                    'name': f"WhatsApp {message.phone}",
                    'mobile': message.phone,
                })

            active_lead = self.env['crm.lead'].search([
                ('partner_id', '=', partner.id),
                ('active', '=', True),
                ('stage_id.is_won', '=', False),
                ('stage_id.is_lost', '=', False)
            ], limit=1)

            if not active_lead:
                self.env['crm.lead'].create({
                    'name': f"Nuevo lead desde WhatsApp ({message.phone})",
                    'partner_id': partner.id,
                    'contact_name': partner.name,
                    'mobile': partner.mobile,
                    'type': 'opportunity',
                    'description': message.body or '',
                })

        return message
