> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `00` Últimos cambios antes del cierre

**Estado del plan:** Propuesto · **Fecha:** 2026-11-07

Cuatro pedidos del responsable antes de pasar a documentar:

- **A.** Cuando el modelo de lenguaje falla seguido, el sistema **propone** pasar a un modelo de
  respaldo; no cambia solo.
- **B.** Una sola pantalla para la llegada de mercadería: hoy la llegada de una pre-venta y la de un
  pedido a proveedor se cargan en dos paneles distintos.
- **C.** El paso a paso para poner en marcha MercadoPago.
- **D.** Si sobra tiempo, el ingreso con Google.

**Ninguno tiene ficha ni contrato en el documento.** A y D agregan operaciones nuevas; B cambia dónde
ocurre una operación que ya existe (`CO-013`) y la junta con otra que todavía no tiene código (la
llegada de un pedido, `NUEVO-CU-03` en el [inventario](../sincronizacion/INVENTARIO.md)). Por
`CLAUDE.md`, los códigos los asigna el responsable: abajo van con rótulo provisorio (sección 7).

---

## 1. Qué cubre

| Parte | Caso de uso | Contratos | Escritura | Consulta |
| --- | --- | --- | --- | --- |
| A | `CU-CFG-LLM` (flujo alternativo nuevo) y `CU-CFG-PAR` (el modelo de respaldo) | `CO-130` extendido; `NUEVO-CO-26 proponerCambioDeModelo` (sistema), `NUEVO-CO-27 confirmarCambioDeModelo` | 2 | 0 |
| B | `CU-ALT-TRA` pasos 4 a 7 y `NUEVO-CU-03` (llegada de un pedido, `CU-RST-LLE` en el repositorio), en un solo flujo | `CO-013` (sin cambio de efecto); `NUEVO-CO-04` (la llegada de un pedido) | 1 (la confirmación unificada) | 1 (la pantalla) |
| C | `CU-TDA-CMP`, `CU-TDA-INV`, `CU-STK-DES` (ya construidos) | `CO-088`, `CO-089`, `CO-091` (sin cambio) | — | — |
| D | `CU-AUT-INI` y `CU-CLI-ALT` (flujos alternativos nuevos) | `NUEVO-CO-28 iniciarSesionConGoogle`, `NUEVO-CO-29 registrarClienteConGoogle` | 2 | 0 |

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué se hace con él |
| --- | --- | --- |
| `ConfiguracionSistema` | Sí | **A**: gana el perfil de respaldo del modelo (modo, dirección, modelo, credencial) y el contador de fallas seguidas con la fecha del último pedido de cambio |
| `PreferenciaAviso` | Sí | **A**: un tipo de aviso nuevo, «Modelo de lenguaje», por correo y Telegram por defecto |
| `RegistroAuditoria` | Sí | **A**: `cambio_de_modelo` y `cambio_de_modelo_propuesto`. **D**: `inicio_sesion_google` y `registro_cliente_google` |
| `PedidoProveedor`, `LineaPedidoProveedor` | Sí | **B**: sólo se leen y se confirman como hoy |
| `ProductoEditorial` (Pre-venta) | Sí | **B**: lo mismo que hoy con `CO-013` |
| `Usuario` | Sí | **D**: gana el identificador de Google (`sub`), único y opcional |

**B no agrega conceptos ni migraciones.** Es una pantalla y un servicio que reemplazan a dos.

---

## 3. Ambigüedades detectadas

### A · El modelo de respaldo

| # | Dónde | Las lecturas | Recomendación |
| --- | --- | --- | --- |
| A1 | Qué es «el otro modelo» | (a) **Un segundo perfil completo en Parámetros** (modo, dirección, modelo, credencial), y el cambio intercambia activo y respaldo · (b) Cambiar sólo el modo local ↔ remoto y que el Administrador escriba los datos en ese momento | **(a)**. Con (b), el pedido de cambio llega cuando no hay nada listo para usar. Intercambiar permite volver por el mismo camino |
| A2 | Qué cuenta como «falla constante» | (a) **3 fallas seguidas de conexión o de rechazo del proveedor** (sin servicio, credencial, cuota, límite) · (b) Cualquier falla, incluida la respuesta ilegible · (c) Un porcentaje en una ventana de tiempo | **(a)**. Una respuesta ilegible dice que el modelo funciona y el prompt no; cambiar de modelo no la arregla. Un acierto pone el contador en cero. El 3 como valor fijo, no parámetro |
| A3 | Por dónde llega la solicitud | (a) **Aviso por los canales del Administrador** (correo y Telegram), con enlace a una pantalla de confirmación y, en Telegram, un botón «Cambiar al respaldo» que pide confirmar · (b) Sólo un cartel en el panel | **(a)**, más el cartel en la pantalla de diagnóstico mientras la solicitud siga abierta |
| A4 | Cada cuánto se vuelve a pedir | (a) **Una vez por racha**: no se repite hasta que haya un acierto o se haga el cambio · (b) Cada N fallas | **(a)** |
| A5 | Si el respaldo no está configurado | (a) **El aviso dice que el modelo falla y que no hay respaldo**, sin botón · (b) No se avisa | **(a)** |
| A6 | Antes de cambiar | (a) **La confirmación prueba primero el respaldo** (la comprobación de disponibilidad de `CU-CFG-LLM`) y, si tampoco responde, no cambia y lo dice · (b) Cambia sin probar | **(a)** |

### B · Una sola pantalla de llegadas

| # | Dónde | Las lecturas | Recomendación |
| --- | --- | --- | --- |
| B1 | Cómo se agrupa lo que se espera | (a) Por pedido, como «Pedidos por llegar» · (b) Por fecha y editorial, como «Pre-ventas por llegar» · (c) **Por proveedor y fecha estimada**: una caja que llega de un proveedor, que puede abarcar más de un pedido | **(c)**. Es lo que entra por la puerta. Cada línea sigue diciendo de qué pedido es, y el calendario del mes se conserva |
| B2 | Qué muestra cada línea | — | Producto, pedido, pedida / confirmada / recibida, y **si es pre-venta**: reservas, cupo y si está demorada. Es lo que hoy se pierde entre los dos paneles |
| B3 | Un faltante (una línea en cero) | (a) **Como `CU-ALT-TRA` A1**: si es una pre-venta con reservas y su fecha ya pasó, se demora; si no, la línea sigue abierta · (b) Como «Pedidos por llegar»: la línea sigue abierta siempre | **(a)**: es lo que dice la ficha. La revisión lo muestra antes de confirmar, como hoy |
| B4 | Una pre-venta **sin pedido registrado** | (a) **Aparece en su grupo marcada «sin pedido»**, se carga igual (`CO-013` directo) y la revisión ofrece crear el pedido a mano · (b) No aparece hasta que tenga pedido | **(a)**. Con (b), una pre-venta sin pedido no tendría dónde llegar |
| B5 | Dónde vive | (a) **Proveedores → «Por llegar»**; las direcciones viejas de las dos pantallas redirigen ahí · (b) Dos entradas en el menú hacia la misma pantalla | **(a)**. El bloque del panel, el calendario, la demora de varios tomos (B-01-022) y el cierre de una línea sin recibir pasan a esta pantalla |
| B6 | Qué caso de uso la declara | (a) **Uno solo, «Registrar la llegada de mercadería»** (`NUEVO-CU-03`), y `CU-ALT-TRA` queda con la vigilancia (avisos y escalado) e invoca a éste en su paso 4 · (b) Se reescribe `CU-ALT-TRA` y la llegada de un pedido queda como alternativo | **(a)**: la llegada deja de ser propiedad de la pre-venta. Va a la bitácora como decisión del responsable |

### D · Ingreso con Google

| # | Dónde | Las lecturas | Recomendación |
| --- | --- | --- | --- |
| D1 | Quién puede | (a) **Sólo Clientes** · (b) También el personal | **(a)**. Las cuentas del personal las da de alta el Administrador con su activación (`CU-USR-ALT`); un ingreso por Google para ellas abre una puerta que I-12 y el bloqueo por intentos no cubren |
| D2 | Un correo que ya tiene cuenta | (a) **Se vincula a esa cuenta** si Google lo da por verificado (I-10: un correo, una cuenta) · (b) Se rechaza | **(a)**. Si la cuenta es del personal, se rechaza (D1). Sólo una cuenta **Activa** entra (I-11) |
| D3 | Un correo sin cuenta | (a) **Registro con un paso**: Google da nombre y correo; se pide aceptar la política de privacidad y la cuenta nace Activa · (b) Se rechaza y se manda al registro común | **(a)**. El domicilio y el teléfono son opcionales hoy, así que no hace falta pedirlos |
| D4 | Contraseña | Una cuenta creada con Google no tiene contraseña | Puede crearla con «Recuperar contraseña». **La baja de cuenta (`CU-CLI-BAJ`) pide la contraseña**: sin contraseña, primero hay que crearla. Hay que decidir si eso alcanza |

---

## 4. Orden de construcción

| # | Parte | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | **B** · Llegadas unificadas | — | Es la que más afecta la operación diaria y la demostración |
| 2 | **A** · Modelo de respaldo | — | Chica y aislada: `core/llm.py`, Parámetros, avisos |
| 3 | **C** · MercadoPago | Tus credenciales y la URL pública | El código está; lo que falta es configuración (sección 8). Un ajuste chico si las pruebas lo piden |
| 4 | **D** · Google | Tu cliente OAuth | Sólo si sobra tiempo |

Cada parte cierra con sus pruebas (la del rol equivocado por la dirección real incluida), su entrada
de bitácora y las siete puertas.

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| Dos administradores confirman la misma llegada a la vez | B | El bloqueo de fila sobre el pedido y el producto que ya tienen `registrar_llegada` y `_ingresar`; la prueba de concurrencia de los dos caminos se mantiene |
| Romper lo que hoy funciona en dos pantallas | B | Las pruebas de `CO-013` y de la llegada de un pedido siguen pasando contra el servicio nuevo; las direcciones viejas redirigen |
| Que el contador de fallas se cuente mal con dos procesos a la vez (el reloj por minuto y una pantalla) | A | Incremento en la base con `F()`, no en memoria |
| La credencial del respaldo a la vista | A | Igual que la activa: se guarda y la pantalla sólo muestra los últimos caracteres |
| Google por fuera de la puerta HTTP única | D | **No se usa ninguna biblioteca que haga sus propias llamadas** (como django-allauth): el intercambio del código y la validación del token van por `core.integraciones.pedir`, así las pruebas lo cortan como al resto |
| Falsificar la vuelta de Google | D | `state` y `nonce` en la sesión; el token se valida (emisor, audiencia, vencimiento, `email_verified`) antes de tocar ninguna cuenta |

---

## 6. Fuera de alcance

- **El cambio automático del modelo**: se pidió como solicitud, y así queda.
- **Más de un respaldo**, o elegir entre varios: un activo y un respaldo.
- **Reembolsos en pesos por la API** de MercadoPago: siguen descartados (`DEUDA.md`, recorte); el
  reembolso automático del último ejemplar (`CO-089` E3) sí existe.
- **Validar la firma del aviso de MercadoPago** (`x-signature`): el sistema no le cree al aviso,
  vuelve a pedir el pago a la API con su credencial. Se puede sumar si el tutor lo pide.
- **Otros proveedores de ingreso** (Facebook, Apple) y **el ingreso del personal con Google**.

---

## 7. Rótulos provisorios

Para la tabla de rótulos del [inventario](../sincronizacion/INVENTARIO.md), sección especial 3:

| Rótulo | Qué es |
| --- | --- |
| `NUEVO-CO-26` | `proponerCambioDeModelo`: el sistema, tras la tercera falla seguida |
| `NUEVO-CO-27` | `confirmarCambioDeModelo`: el Administrador, desde la web o el chat |
| `NUEVO-CO-28` | `iniciarSesionConGoogle` |
| `NUEVO-CO-29` | `registrarClienteConGoogle` |
| `NUEVO-CU-03` | Pasa a ser «Registrar la llegada de mercadería» (B6) |

**Decisión que necesito:** si autorizás estos nombres provisorios para construir, como hiciste con el
módulo 19 (B-19-001), o si asignás los códigos antes.

---

## 8. MercadoPago, paso a paso

El adaptador (`apps/tienda/mercadopago.py`) ya crea la preferencia, lee el pago desde la API cuando
llega el aviso (no le cree al aviso) y reembolsa. Lo que falta es **tuyo**: una cuenta, una
credencial y una dirección pública.

**Lo que necesito de vos** está marcado con ▶.

1. ▶ **Entrá a** <https://www.mercadopago.com.ar/developers> con tu cuenta de Mercado Pago (la
   personal sirve) y en **«Tus integraciones» → «Crear aplicación»**: nombre «Longbox», producto
   **Checkout Pro**, «pagos online».
2. ▶ En la aplicación, **«Credenciales» → «Credenciales de prueba»**: copiá el **Access Token**. La
   documentación actual dice que alcanzan las credenciales de prueba de la aplicación y que **no hace
   falta una cuenta de prueba compradora**: se paga desde una ventana de incógnito sin iniciar
   sesión. Pasame el token por el `.env`, **no por el chat**.
3. ▶ En el `.env` de la VM:
   - `MERCADOPAGO_ACCESS_TOKEN=` el token del paso 2.
   - `URL_PUBLICA=https://…` la dirección pública de la VM. **Mercado Pago no acepta `localhost` ni
     `127.0.0.1`** en las direcciones de vuelta: sin una dirección pública el pago se hace pero el
     Cliente no vuelve solo a la tienda, y el aviso no llega.
4. ▶ En **Parámetros → Compra online → Pasarela**, elegí **MercadoPago** (hoy está en la de prueba).
5. **Yo** verifico que la dirección del aviso (`/tienda/compra/aviso/mercadopago/`) responda desde
   afuera por HTTPS, y hago una compra con estas tarjetas de prueba (las publica Mercado Pago):

   | Tarjeta | Número | Código | Vence |
   | --- | --- | --- | --- |
   | Visa crédito | 4509 9535 6623 3704 | 123 | 11/30 |
   | Mastercard crédito | 5031 7557 3453 0604 | 123 | 11/30 |

   En «Nombre del titular» va el resultado que se quiere: **APRO** (aprobado, DNI 12345678),
   **OTHE** (rechazado), **CONT** (pendiente), **FUND** (fondos insuficientes).
6. **Yo** recorro los cuatro casos contra la API real: aprobado, rechazado, pendiente que se aprueba
   después, y el último ejemplar pagado por dos a la vez (debe reembolsarse el segundo, `CO-089` E3).
7. **Un punto que la documentación no deja claro:** si con credenciales de prueba hay que mandar al
   comprador a `init_point` (lo que hace hoy el sistema) o a `sandbox_init_point`. Lo resuelvo en la
   primera compra: si la página de pago rechaza la tarjeta de prueba, el adaptador pasa a usar
   `sandbox_init_point` con credenciales de prueba. Es un cambio de una línea, con su prueba.
8. **Para cobrar de verdad** (no hace falta para la demostración): «Credenciales de producción» →
   «Activar credenciales», con el rubro y la URL del sitio, y reemplazar el token. Producción exige
   HTTPS, que la VM ya tiene.

---

## 9. Lo que necesito para empezar

1. **La aprobación del plan**, con las recomendaciones o con lo que cambies de las ambigüedades A1 a
   A6, B1 a B6 y D1 a D4.
2. **Los códigos o la autorización** para construir con los rótulos de la sección 7.
3. Para A, **los datos del modelo de respaldo**: los cargás vos en Parámetros cuando esté la pantalla.
4. Para C, los pasos ▶ de la sección 8.
5. Para D, si llegamos: un proyecto en **Google Cloud Console** con la pantalla de consentimiento
   (externa, en modo prueba, con tu correo como usuario de prueba) y un **cliente OAuth «Aplicación
   web»** con la URI de redirección `https://<dirección pública>/cuentas/google/vuelta/`.
   `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` van en el `.env`.
