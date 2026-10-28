"""Un Telegram de mentira detrás de la única puerta HTTP (`integraciones.pedir`).

Las pruebas del módulo 19 configuran un token y reemplazan la puerta por esto:
guarda cada llamada a la API y contesta como Telegram. Con `caido=True` contesta
como una red cortada, para probar que el aviso vuelve al correo.
"""

from unittest.mock import patch

from apps.core import integraciones

TOKEN = "123456:TOKEN-DE-PRUEBA"


class TelegramFalso:
    def __init__(self, *, caido=False, novedades=()):
        self.caido = caido
        self.novedades = list(novedades)
        self.llamadas = []

    def __call__(self, url, *, timeout, metodo="GET", cuerpo=None, cabeceras=None, archivos=None):
        if "api.telegram.org" not in url:
            return integraciones.Respuesta(motivo=integraciones.SIN_CONEXION)
        metodo_api = url.rsplit("/", 1)[-1]
        self.llamadas.append((metodo_api, {**(cuerpo or {}), **(archivos or {})}))
        if self.caido:
            return integraciones.Respuesta(motivo=integraciones.SIN_CONEXION)
        resultado = {
            "sendMessage": {"message_id": len(self.llamadas)},
            "sendPhoto": {"message_id": len(self.llamadas)},
            "getMe": {"username": "longbox_prueba_bot"},
            "getUpdates": self.novedades,
        }.get(metodo_api, True)
        if metodo_api == "getUpdates":
            self.novedades = []
        return integraciones.Respuesta(datos={"ok": True, "result": resultado})

    def mensajes(self, chat_id=None):
        return [
            cuerpo
            for metodo, cuerpo in self.llamadas
            if metodo == "sendMessage" and (chat_id is None or cuerpo.get("chat_id") == chat_id)
        ]

    def textos(self, chat_id=None):
        return [m["text"] for m in self.mensajes(chat_id)]

    def fotos(self, chat_id=None):
        return [
            cuerpo
            for metodo, cuerpo in self.llamadas
            if metodo == "sendPhoto" and (chat_id is None or cuerpo.get("chat_id") == chat_id)
        ]

    def salidas(self, chat_id=None):
        """Lo que vio el chat, mensajes y epígrafes de fotos, en orden."""
        return [
            cuerpo.get("text") or cuerpo.get("caption", "")
            for metodo, cuerpo in self.llamadas
            if metodo in ("sendMessage", "sendPhoto")
            and (chat_id is None or cuerpo.get("chat_id") == chat_id)
        ]


def telegram_falso(**kwargs):
    falso = TelegramFalso(**kwargs)
    return falso, patch.object(integraciones, "pedir", side_effect=falso)
