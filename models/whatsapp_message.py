# -*- coding: utf-8 -*-
import time
import random  # para la elección aleatoria
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    @api.model
    def message_post(self, *args, **kwargs):
        is_wa = (self.channel_type == "whatsapp")                   # ¿canal WA?
        is_inbound = bool(kwargs.get("whatsapp_inbound_msg_uid"))   # ¿mensaje entrante del webhook?
        parent_id = kwargs.get("parent_id")

        # 1) Dejar que Odoo cree el mail.message y haga lo estándar
        message = super().message_post(*args, **kwargs)

        # 2) Solo actuar si es WhatsApp entrante
        if not (is_wa and is_inbound):
            return message

        # 3) Contar inbound en este canal
        inbound_count = self.env['whatsapp.message'].sudo().search_count([
            ('mail_message_id.model', '=', 'discuss.channel'),
            ('mail_message_id.res_id', '=', self.id),
            ('message_type', '=', 'inbound'),
        ])

        # 4) Solo al primer inbound
        if inbound_count == 1:
            partner = self.whatsapp_partner_id  # contacto del número entrante
            if not partner:
                return message

            # 4.1) Buscar candidatos a vendedores: todos los usuarios internos activos
            users = self.env['res.users'].sudo().search([
                ('active', '=', True),
                ('share', '=', False),   # descarta usuarios portal/externos
            ])
            if not users:
                raise UserError(_("No hay usuarios internos disponibles para asignar como vendedor."))

            # 4.2) Elegir un vendedor al azar
            user = random.choice(users)

            # 4.3) Asignar vendedor al partner si no tenía
            if not partner.user_id:
                partner.user_id = user.id

            # 4.4) Agregar al vendedor como miembro del canal
            seller_partner = user.partner_id
            has_member = any(m.partner_id.id == seller_partner.id for m in self.channel_member_ids)
            if not has_member:
                self.env['discuss.channel.member'].sudo().create({
                    'partner_id': seller_partner.id,
                    'channel_id': self.id,
                })

            # 4.5) Delay y respuesta automática
            time.sleep(2)  # simular espera humana

            super(DiscussChannel, self).message_post(
                body=_("Hola %(name)s, gracias por escribir. Te atiende %(seller)s ✅",
                        name=(partner.name or "allí"), seller=user.name),
                message_type="whatsapp_message",
                parent_id=(message.id or parent_id),
                subtype_xmlid="mail.mt_comment",
            )

        return message
