> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `00` Revisión integral antes del cierre

**Estado del plan:** Aprobado el 2026-11-07, con las recomendaciones de §3; en la ambigüedad 4, el responsable decidió bloquear · **Fecha:** 2026-11-07

La última revisión de punta a punta antes de la documentación final: flujos que se cruzan entre
módulos (como el de pre-ventas y pedidos al proveedor, ya resuelto en B-05-017), seguridad, pagos,
pantallas y rendimiento. Este plan no agrega casos de uso: corrige lo construido para que cumpla
los contratos que ya existen. Cada hallazgo dice **qué se vio, cómo se comprobó y qué se propone**.

---

## 1. Qué cubre

Lo que se revisó, y con qué método.

| Frente | Cómo se revisó |
| --- | --- |
| Control de acceso | Las 206 rutas, como anónimo, Cliente y Cajero, por su dirección real |
| Seguridad | XSS (Markdown de la FAQ, salida del modelo en Telegram), SQL, CSRF, redirecciones `volver`, subidas de archivos, ajustes de producción, puertos de la VM, webhook del bot |
| Pagos | Adaptador de MercadoPago, idempotencia, control de monto, cobros abandonados, reembolsos; prueba temporal de cada camino |
| Stock y estados | Cada camino que sube o baja stock, contra `al_agotarse`, `al_subir_stock` y los estados terminales |
| Puntos | Canje en la tienda, en el mostrador y débito manual, contra lo comprometido por cobros pendientes |
| Pantallas | 71 pantallas a 500 px (desborde horizontal), consola de JavaScript, íconos y clases CSS |
| Rendimiento | Consultas por pantalla en 18 pantallas clave, con 1 y con muchos datos (sin N+1) |
| Operación | Registros de la VM de los últimos 14 días, temporizadores y respaldos |

Las tablas de abajo listan **los hallazgos**. Lo que se revisó y está bien figura en §7, para que
quede constancia de que se miró.

### 1.1 Hallazgos que cuestan dinero

| # | Hallazgo | Evidencia | Contrato | Propuesta |
| --- | --- | --- | --- | --- |
| **R-01** | **Un pago aprobado después de un rechazo se cobra y no genera pedido ni reembolso.** En Checkout Pro, después de una tarjeta rechazada el comprador sigue en la página de MercadoPago y reintenta con otra; cada intento es un pago con la misma `external_reference`. El primer aviso deja el cobro en Rechazado y el segundo, aprobado, se descarta por «ya resuelto». | `compra.registrar_rechazo` (`apps/tienda/compra.py:455`) cierra el cobro; `registrar_resultado` (`:490`) devuelve sin hacer nada si no está Pendiente, y `_reembolso_tardio` sólo mira los Descartados. **Prueba temporal:** rechazo → aprobado deja el cobro en `rechazado`, 0 pedidos y 0 reembolsos. | `CO-089` E2 y E3 | Ver ambigüedad 1. |
| **R-02** | **Un invitado puede terminar con una pre-venta.** Si mientras paga se vende la última unidad y hay un pedido al proveedor en camino, `al_agotarse` abre la pre-venta; al aprobarse el pago, `_materializar` acepta la línea en Pre-venta. El invitado no tiene cuenta: si la editorial cancela, `cancelar_preventa` saltea su reembolso (`cliente.usuario is None`), y no puede decidir sobre una demora. | `apps/tienda/compra.py:598` admite `PRE_VENTA` sin mirar `cobro.usuario_id`; `apps/pedidos/preventa.py:895` saltea a quien no tiene usuario. | `CO-181` (precondición: el invitado no compra pre-ventas) | En `_materializar`, si el cobro es de invitado y una línea quedó en Pre-venta: `FalloDeMaterializacion` → reembolso (E3), con un mensaje que lo explique. |
| **R-03** | **Confirmar una llegada resucita un producto Cancelado por editorial o Descatalogado.** `registrar_llegada` escribe `estado=ACTIVO` en todo producto que no esté en Pre-venta. Y la línea del pedido al proveedor de un producto cancelado o descatalogado sigue figurando en «Por llegar». | `apps/suppliers/llegadas.py:244`. Los otros caminos que suben stock (devoluciones, vencimiento del stock en local, edición) sólo pasan de Agotado a Activo. | `CO-027` (Cancelado por editorial es terminal), `CO-034`/`CO-036` (salir de Descatalogado es una reactivación explícita) | La llegada suma el stock y sólo pasa a Activo desde Agotado o Activo; un producto terminal o descatalogado conserva su estado y la revisión de la llegada lo marca. Qué pasa con la línea abierta: ver ambigüedad 2. |
| **R-04** | **Un pago en efectivo (Rapipago, Pago Fácil) acreditado después de 24 horas se reembolsa.** La preferencia no tiene vencimiento: MercadoPago deja pagar el cupón días después, pero el temporizador descarta el cobro a las 24 h y `_reembolso_tardio` lo devuelve. No se pierde plata, pero el cliente pagó en una ventanilla y recibe un reembolso. | `MercadoPago.iniciar_cobro` (`apps/tienda/mercadopago.py:57`) no manda `expires` ni `date_of_expiration`; `compra.ABANDONO = 24 h`. | `CO-089`, plan 00 C3 | La preferencia vence a las 24 h (`expires`, `expiration_date_to`, `date_of_expiration`), alineada con `ABANDONO`. MercadoPago deja de ofrecer los medios que no se acreditan a tiempo. |

### 1.2 Flujos que se cruzan

| # | Hallazgo | Evidencia | Contrato | Propuesta |
| --- | --- | --- | --- | --- |
| **R-05** | **Dos caminos dejan el stock en 0 sin abrir la pre-venta.** La compra online y la venta de mostrador llaman a `llegadas.al_agotarse`, que abre la pre-venta si hay un pedido al proveedor en camino. El cambio por garantía y la edición manual del stock no lo llaman. | `apps/devoluciones/servicios.py:663` (pasa a Agotado sin `al_agotarse`); `apps/catalog/views.py:1588` (deja Activo con stock 0). | `CO-100`, `CO-030` · B-05-001 | Las dos llaman a `al_agotarse` al quedar en 0, como `compra.py` y `ventas/ticket.py`; la edición deja además el producto en Agotado, como los demás caminos. |
| **R-06** | **El canje en la tienda y en el mostrador no descuenta lo comprometido.** El débito manual usa `debitable()` (saldo menos lo que un cobro pendiente va a debitar); `aplicar_canje` y la venta de mostrador usan `saldo()`. Un cliente con un pago en curso puede gastar los mismos puntos en el local, y el pago online falla después y se reembolsa. | `apps/tienda/compra.py:328`, `apps/ventas/ticket.py:296`; `apps/puntos/servicios.py:199`. | `CO-103`, B-10-005 | Los dos caminos verifican contra `puntos.debitable()`, con el mensaje de E2 diciendo cuánto está comprometido. |
| **R-07** | **Los correos al cliente se pierden si falla el servidor SMTP.** El 28/10 falló Gmail durante unas tres horas: al menos 25 correos (confirmaciones y cambios de estado de pedidos) se perdieron sin reintento. Sólo el pedido al proveedor reintenta. | Registros de la VM: 25 líneas `[correo] Falló el envío por smtp.gmail.com: Connection unexpectedly closed` entre las 06:21 y las 09:36; 10 *tracebacks* en `pedidos/avisos.py`, `pedidos/servicios.py` y `compra._avisar_confirmacion`. | Sin contrato que lo regule | Ver ambigüedad 3. |

### 1.3 Seguridad

| # | Hallazgo | Evidencia | Propuesta |
| --- | --- | --- | --- |
| **R-08** | **El restablecimiento de contraseña no tiene límite.** Cualquiera puede pedir restablecimientos en serie para un correo ajeno y usar el sistema para inundarlo; además, cada pedido gasta cupo del SMTP. | `PasswordResetView` de Django sin envoltura (`apps/accounts/urls.py:17`). El ingreso sí bloquea por intentos. | Tope por correo y por IP (p. ej., 3 por hora), con la misma respuesta de siempre para no revelar si la cuenta existe. |
| **R-09** | **Dos pantallas buscan el objeto antes de mirar el rol.** Un Cliente obtiene 404 si el registro no existe y 403 si existe: revela qué claves hay. | `PrecioModificarView.dispatch` (`apps/catalog/views_precios.py:94`) y `EtiquetasDeGrupoView.dispatch` (`apps/catalog/views_catalogos.py:438`). | Buscar el objeto después de la verificación de rol (en `get`/`post` o después de `super().dispatch`). |
| **R-10** | **«Retirar» un artículo que no existe da error 500.** | `servicios.retirar` usa `.get(pk=…)` (`apps/almacen/servicios.py:519`). | 404 por `get_object_or_404`, como el resto de las fichas. |

### 1.4 Pantallas

| # | Hallazgo | Evidencia | Propuesta |
| --- | --- | --- | --- |
| **R-11** | **Las fechas aparecen vacías al editar una oferta y en Reportes.** Con `LANGUAGE_CODE = "es-ar"`, un `DateInput(type="date")` sin `format` se pinta como `01/11/2026`, y el navegador sólo acepta `2026-11-01`: lo descarta y muestra el campo vacío. En la oferta las dos fechas son obligatorias y hay que volver a cargarlas; en Reportes se pierde el período por omisión. | Consola de Chrome en `reportes:generar`: «The specified value "01/11/2026" does not conform to the required format». Formulario renderizado: `<input type="date" value="01/11/2026">`. Afecta `forms_ofertas.py:33,37`, `reportes/forms.py:16,17`, `catalog/forms.py:223` y `suppliers/views_pedidos.py:441`. | `format="%Y-%m-%d"`, como ya hacen `almacen/views.py` y el borrador (`catalog/forms.py:2250`). Una prueba que recorre todos los formularios y falla si queda un `type="date"` sin formato ISO. |
| **R-12** | **«Por llegar» se desborda en el celular.** Un nombre de proveedor largo ensancha la página a 760 px en una ventana de 500. | Barrido de 71 pantallas: es la única que desborda. `.calendario-lista__llegadas` es `display: grid` sin columna acotada. | `grid-template-columns: minmax(0, 1fr)` y `min-width: 0` en `.calendario__llegada`. |
| **R-13** | **La fecha de llegada se edita como texto en la ficha del producto** y con el selector de fecha en todos los demás lados. Funciona, pero es la única. | `ProductoEditorialForm` hereda el `DateInput` de texto del modelo. | El mismo widget con `type="date"` y formato ISO. |

### 1.5 Rendimiento

| # | Hallazgo | Evidencia | Propuesta |
| --- | --- | --- | --- |
| **R-14** | **El pedido a mano carga el catálogo entero en un `datalist`.** Con 300 productos no se nota; con 3000 la página pesa varios cientos de KB. | `catalog/busqueda.opciones_para_pedir()` en `pedido_nuevo.html`. | Sin cambio ahora: el autocompletado ya busca en el servidor (`buscar_para_pedir`). Va a `docs/DEUDA.md` como límite de escala. |

**Total:** 13 arreglos (R-01 a R-13) y 1 deuda registrada (R-14).

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `CobroEnCurso` | Sí | Lo modifica: un rechazo deja de cerrarlo (R-01, según la ambigüedad 1) |
| `Pedido`, `LineaPedido` | Sí | Sólo se dejan de crear en el caso de R-02 |
| `Producto.estado` | Sí | La llegada respeta los estados terminales (R-03); dos caminos más pasan a Agotado (R-05) |
| `LineaPedidoProveedor` | Sí | Según la ambigüedad 2, se cierra al cancelar o descatalogar |
| `LotePuntos` | Sí | Sólo se lee: cambia contra qué se verifica el canje (R-06) |
| Correo pendiente | **No** | Sólo si la ambigüedad 3 se resuelve con una cola: es el único concepto nuevo, y trae migración |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | `CO-089` E2 (R-01) | **(a)** Un rechazo de la pasarela no cierra el cobro: se audita el intento y el cobro sigue Pendiente hasta que llegue un aprobado o lo descarte el temporizador a las 24 h. La pantalla de resultado dice «rechazado, podés reintentar». / **(b)** El rechazo cierra el cobro como hoy, y un aprobado posterior sobre un cobro Rechazado se reembolsa, como el que llega después del abandono. | Una decisión del responsable. **Recomiendo (a):** es lo que hace Checkout Pro y el cliente que reintentó con otra tarjeta recibe su pedido. Con (b) se le cobra y se le devuelve. En los dos casos se agrega la prueba `test_CO089_…` del camino rechazo → aprobado. |
| 2 | `CO-027` y `CO-034` (R-03) | Al cancelar una pre-venta o descatalogar un producto con un pedido al proveedor abierto: **(a)** su línea se cierra sola como «sin recibir», con el motivo «Cancelado por editorial» o «Descatalogado», y deja de figurar en «Por llegar». / **(b)** La línea sigue abierta: si la mercadería llega igual, entra al stock sin cambiar el estado del producto. | Una decisión del responsable. **Recomiendo (a)**, y aun así aplicar el arreglo de R-03 en la llegada: una caja que llega de todos modos se puede cargar sin resucitar el producto. Las dos lecturas agregan una postcondición a contratos existentes: va a la bitácora como agregado. |
| 3 | Sin contrato (R-07) | **(a)** Reintento simple: tres intentos con espera creciente dentro del mismo hilo de segundo plano, y si fallan los tres, un aviso al Administrador. Sin migración. / **(b)** Una cola de correos pendientes que el reloj de la VM reintenta cada minuto. Sobrevive a un reinicio, pero es un concepto nuevo. | Una decisión del responsable. **Recomiendo (a)** a esta altura: cubre una caída de minutos como la del 28/10, que es lo que se vio. (b) cambia el alcance y queda en `docs/DEUDA.md`. |
| 4 | Pedido a mano (pregunta abierta del pedido por nombre) | Un producto sin proveedor identificable **(a)** se acepta, como hoy, o **(b)** se bloquea hasta asignarle uno. | Sigue pendiente de la respuesta del responsable; no bloquea nada de este plan. |

---

## 4. Orden de construcción

Primero lo que cuesta dinero, después los flujos, la seguridad y las pantallas. Cada punto se
cierra con sus pruebas, se anota en la bitácora del módulo que toca y pasa las siete puertas.

| # | Arreglo | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | R-01 · aprobado después de un rechazo | Ambigüedad 1 | Es el único hallazgo que pierde plata del cliente sin rastro |
| 2 | R-02 · invitado con pre-venta | — | Mismo archivo y misma prueba de materialización |
| 3 | R-04 · vencimiento de la preferencia | R-01 | Mismo adaptador; se prueba con la puerta HTTP interceptada |
| 4 | R-03 · llegada y estados terminales | Ambigüedad 2 | Toca `CO-232`, recién construido |
| 5 | R-05 · `al_agotarse` en cambio y edición | — | Mismo patrón que B-05-001 |
| 6 | R-06 · canje contra lo comprometido | — | Una línea por camino y sus pruebas |
| 7 | R-07 · reintento de correos | Ambigüedad 3 | — |
| 8 | R-08 a R-10 · seguridad | — | Pruebas por la dirección real con el rol equivocado |
| 9 | R-11 a R-13 · pantallas | — | Se verifican con capturas, como el resto de la interfaz |

Las pruebas de contrato llevan su código: `test_CO089_un_aprobado_despues_de_un_rechazo_…`,
`test_CO181_…`, `test_CO232_la_llegada_no_reactiva_un_producto_cancelado`, `test_CO100_…`,
`test_CO103_…`.

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| Que un cobro siga Pendiente después de un rechazo y comprometa puntos 24 h (R-01 a) | `puntos.comprometidos` | Lo comprometido ya caduca con el abandono (B-10-005); una prueba lo verifica |
| Que los parámetros de vencimiento no los acepte la API de MercadoPago | R-04 | Se prueba en la VM con la cuenta de prueba, como se probó el pago |
| Que un reintento de correo duplique un aviso | R-07 | Sólo se reintenta lo que el servidor rechazó antes de aceptar el mensaje |
| Que el cambio de estado en la edición (R-05) dispare avisos de reposición de más | `catalog/views.py` | La prueba cubre subir y bajar el stock en la misma edición |

---

## 6. Fuera de alcance

- La autenticación con Google (parte D del plan de últimos cambios): sigue esperando las
  credenciales.
- Contracargos y reembolsos iniciados desde MercadoPago (`charged_back`, `refunded`): el sistema
  no los recibe. Va a `docs/DEUDA.md`.
- La cola de correos persistente, si la ambigüedad 3 se resuelve con (a).
- Que la compra de invitado diga si el correo tiene cuenta: está especificado (A1 de
  `CU-TDA-INV`, B-07-036) y se acepta como riesgo conocido.

---

## 7. Lo que se revisó y está bien

- **Acceso:** las 206 rutas devuelven 403 al rol equivocado, salvo R-09 y R-10.
- **Bot de Telegram:** el webhook compara el secreto en tiempo constante; cada respuesta y botón
  verifica que el chat sea de un Administrador activo, y los botones van firmados. La charla del
  modelo se escapa antes de mandarse como HTML y nunca ejecuta nada (regla 4).
- **Pagos:** el resultado se lee de la API, no del aviso; el monto se verifica; los avisos
  repetidos son idempotentes; la pasarela de prueba se restringe a `pasarela=prueba`.
- **Contenido:** el Markdown de la FAQ no admite HTML; las redirecciones `volver` se validan; las
  imágenes subidas se re-codifican y tienen tope de tamaño y cantidad; las evidencias de
  devolución se sirven por una vista con permiso.
- **Dinero:** no hay punto flotante en la aritmética; sólo en el transporte a MercadoPago y en
  porcentajes de pantalla.
- **VM:** Django escucha en 127.0.0.1 detrás de Caddy, PostgreSQL sólo local; el temporizador, el
  reloj y los respaldos corren. Los 403 por `Referer` de los registros son escaneos de bots
  (`/.git/config`).
- **Rendimiento:** la cantidad de consultas es constante con el volumen en las 18 pantallas
  medidas (de 14 a 37).
- **Interfaz:** los 57 íconos usados están definidos; no hay clases CSS sin definir; no hay errores
  de JavaScript en las 71 pantallas.
