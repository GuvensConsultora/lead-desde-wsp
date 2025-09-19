# -*- coding: utf-8 -*-
import time                                   # para delay opcional corto
from odoo import api, fields, models          # API Odoo

class DiscussChannel(models.Model):           # extendemos discuss.channel
    _inherit = "discuss.channel"              # herencia del modelo base

    @api.model
    def message_post(self, *args, **kwargs):  # override del posteo de mensaje
        is_wa = (self.channel_type == "whatsapp")        # es canal WA
        is_inbound = bool(kwargs.get("whatsapp_inbound_msg_uid"))  # flag de entrante del webhook

        # guardamos parent_id si vino (vamos a responder en hilo al primero)
        parent_id = kwargs.get("parent_id")              # id padre (si existe)

        # 1) Postear el mensaje normalmente (crea mail.message y si es WA, registra whatsapp.message)
        message = super(DiscussChannel, self).message_post(*args, **kwargs)  # deja que core haga lo suyo

        # 2) Si NO es WhatsApp o NO es entrante, no hacemos nada extra
        if not (is_wa and is_inbound):                   # solo nos interesa el primer inbound WA
            return message                               # devolver mensaje tal cual

        # 3) Contar cuántos inbound WA existen en este canal (después del super ya existe el actual)
        WaMsg = self.env["whatsapp.message"].sudo()      # modelo whatsapp.message
        inbound_count = WaMsg.search_count([             # contamos inbound asociados a este canal
            ("mail_message_id.model", "=", "discuss.channel"),  # mensajes del canal
            ("mail_message_id.res_id", "=", self.id),    # este canal
            ("message_type", "=", "inbound"),            # solo entrantes
        ])

        # 4) Si este es el PRIMER inbound (contacto nuevo), disparamos auto-respuesta
        if inbound_count == 1:                           # primer mensaje del contacto en este canal
            ICP = self.env["ir.config_parameter"].sudo() # parámetros del sistema
            # texto configurable; default razonable con nombre si lo tenemos
            partner_name = (self.whatsapp_partner_id.name or "allí")  # nombre del contacto
            default_body = f"Hola {partner_name}, gracias por escribir. En breve te respondemos por acá ✅"  # texto por defecto
            reply_body = ICP.get_param("wh_auto_reply.first_text", default_body)   # permite cambiar por Ajustes

            # delay configurable en segundos (opcional). Ej: setear 2 para “dos segunditos”.
            delay = int(ICP.get_param("wh_auto_reply.delay_seconds", "0") or 0)    # lee delay o 0
            if delay > 0:                                  # si hay delay configurado
                time.sleep(min(delay, 5))                  # dormimos un toque (cap a 5s por salud del worker)

            # 5) Respondemos por WhatsApp (saliente). Usamos message_type='whatsapp_message'
            #    Esto hará que core cree whatsapp.message 'outbound' y llame _send_message() automáticamente.
            #    Además, colgamos la respuesta del entrante con parent_id para mantener el hilo prolijo.
            self.message_post(                             # posteamos nuevo mensaje
                body=reply_body,                           # el texto de auto-respuesta
                message_type="whatsapp_message",           # tipo WA saliente
                parent_id=(message.id or parent_id),       # respondemos al mensaje entrante
                subtype_xmlid="mail.mt_comment",           # subtipo estándar
            )

        # 6) Devolver el mensaje entrante que creó el core
        return message                                    # fin del override
