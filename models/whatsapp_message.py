# -*- coding: utf-8 -*-
import time                                 # delay corto “humano”
import random                               # elección aleatoria de vendedor
from odoo import api, fields, models, _     # API Odoo
from odoo.exceptions import UserError       # errores claros al usuario

class DiscussChannel(models.Model):         # extendemos discuss.channel
    _inherit = "discuss.channel"             # herencia del modelo base

    @api.model
    def message_post(self, *args, **kwargs):                           # interceptamos message_post
        is_wa = (self.channel_type == "whatsapp")                      # ¿canal WhatsApp?
        is_inbound = bool(kwargs.get("whatsapp_inbound_msg_uid"))      # ¿mensaje entrante del webhook?
        parent_id = kwargs.get("parent_id")                            # parent explícito si vino

        message = super().message_post(*args, **kwargs)                # dejar que Odoo cree mail.message

        if not (is_wa and is_inbound):                                 # si no es WA entrante, nada extra
            return message                                             # devolver y salir

        inbound_count = self.env['whatsapp.message'].sudo().search_count([  # contar entrantes en este canal
            ('mail_message_id.model', '=', 'discuss.channel'),         # limitar al canal
            ('mail_message_id.res_id', '=', self.id),                  # id del canal
            ('message_type', '=', 'inbound'),                          # solo inbound
        ])

        if inbound_count == 1:                                         # actuar solo en el primer inbound
            partner = self.whatsapp_partner_id                          # contacto detectado/creado por WA
            if not partner:                                            # si no hay partner, nada que hacer
                return message                                         # devolver y salir

            # ---------------------------
            # 1) Elegir VENDEDOR aleatorio
            # ---------------------------
            users = self.env['res.users'].sudo().search([              # buscar usuarios internos activos
                ('active', '=', True),                                 # activos
                ('share', '=', False),                                 # no portal
            ])
            if not users:                                              # si no hay candidatos
                raise UserError(_("No hay usuarios internos disponibles para asignar como vendedor."))  # error

            user = random.choice(users)                                 # elegir 1 al azar

            # -----------------------------------------
            # 2) Asignar vendedor al PARTNER (si falta)
            # -----------------------------------------
            if not partner.user_id:                                     # si el contacto no tiene vendedor
                partner.user_id = user.id                               # asignar vendedor

            # ---------------------------------------------------
            # 3) Agregar vendedor como MIEMBRO del canal (Discuss)
            # ---------------------------------------------------
            seller_partner = user.partner_id                            # partner vinculado al usuario
            has_member = any(m.partner_id.id == seller_partner.id for m in self.channel_member_ids)  # ya está?
            if not has_member:                                          # si no está, crearlo
                self.env['discuss.channel.member'].sudo().create({
                    'partner_id': seller_partner.id,                    # partner del usuario
                    'channel_id': self.id,                              # este canal
                })

            # ------------------------------------------
            # 4) Crear LEAD en CRM asignado a user/partner
            # ------------------------------------------
            # evitar duplicados “recientes”: buscar lead abierto del mismo partner
            existing_lead = self.env['crm.lead'].sudo().search([        # buscar lead vivo
                ('partner_id', '=', partner.id),                        # mismo contacto
                ('type', 'in', ['lead', 'opportunity']),                # lead u oportunidad
                ('active', '=', True),                                  # activo
                ('probability', '<', 100),                              # no ganado
            ], limit=1, order='id desc')

            if existing_lead:                                           # si ya hay uno abierto, no duplicar
                lead = existing_lead                                    # usar el existente
            else:
                # intentar obtener equipo del usuario si existe el campo
                team_id = getattr(user, 'sale_team_id', False) and user.sale_team_id.id or False  # team si hay
                # armar datos del lead
                lead_vals = {
                    'name': _("WhatsApp de %(name)s", name=(partner.name or self.whatsapp_number or 'Contacto WA')),  # título
                    'partner_id': partner.id,                            # contacto
                    'contact_name': partner.name or False,               # nombre
                    'mobile': partner.mobile or (f"+{self.whatsapp_number}" if self.whatsapp_number else False),  # móvil
                    'phone': partner.phone or False,                     # teléfono fijo si tiene
                    'email_from': partner.email or False,                # email si existe
                    'user_id': user.id,                                  # vendedor asignado
                    'team_id': team_id,                                  # equipo (si aplica)
                    'type': 'opportunity',                               # lo dejamos como oportunidad
                    'description': _("Creado automáticamente desde el primer mensaje de WhatsApp."),  # descripción
                }
                # opcional: tag “WhatsApp” para identificar origen
                tag_model = self.env['crm.tag'].sudo()                   # modelo de etiquetas
                wa_tag = tag_model.search([('name', '=', 'WhatsApp')], limit=1) or tag_model.create({'name': 'WhatsApp'})  # crear si no existe
                lead_vals['tag_ids'] = [(6, 0, [wa_tag.id])]             # setear etiqueta
                lead = self.env['crm.lead'].sudo().create(lead_vals)     # crear lead

                # log de vínculo mutuo canal <-> lead (texto y link)
                self.message_post(                                       # post en canal
                    body=_("Se creó un lead en CRM: <b>%(lead)s</b>", lead=lead.display_name),
                    message_type='comment',                              # comentario
                    subtype_xmlid='mail.mt_note',                        # nota
                )
                lead.message_post(                                       # post en lead
                    body=_("Canal de WhatsApp asociado: <b>%(name)s</b>", name=self.display_name),
                    message_type='comment',
                    subtype_xmlid='mail.mt_note',
                )

            # -------------------------------------------
            # 5) Autorrespuesta con 2 s avisando vendedor
            # -------------------------------------------
            time.sleep(2)                                               # delay humano
            super(DiscussChannel, self).message_post(                   # enviar por flujo nativo WA
                body=_("Hola %(name)s, gracias por escribir. Te atiende %(seller)s ✅",
                        name=(partner.name or "allí"), seller=user.name),  # texto con vendedor
                message_type="whatsapp_message",                        # WA saliente
                parent_id=(message.id or parent_id),                    # responder al entrante
                subtype_xmlid="mail.mt_comment",                        # subtipo estándar
            )

        return message                                                  # devolver el entrante
