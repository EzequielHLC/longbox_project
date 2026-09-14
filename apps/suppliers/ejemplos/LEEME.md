# Correos de ejemplo

Tres `.eml` para probar la cola sin una casilla de correo, generados con
`apps/suppliers/tests/correos_de_ejemplo.py`. Reproducen lo que mandan los
proveedores nacionales: HTML con una tabla por producto y las portadas
embebidas en formato WebP.

| Archivo | Qué prueba |
|---|---|
| `novedades-marzo.eml` | El caso normal: tres productos con ISBN, portada, volumen, formato y PVP. Trae además un logo embebido que **no** es una portada y una tabla de maquetado envolviendo la de datos. |
| `demora-berserk.eml` | Un aviso de demora. Entra a la cola igual: es la razón por la que la cola existe. |
| `remitente-desconocido.eml` | No entra (E1 de CU-ALT-NOV). |

Para cargarlos, con un proveedor activo cuyo correo comercial sea
`novedades@ivrea.test` y con el procesamiento de novedades habilitado:

```powershell
python manage.py ingerir_correos apps\suppliers\ejemplos
```

Después se resuelven desde **Proveedores → Correos recibidos**.
