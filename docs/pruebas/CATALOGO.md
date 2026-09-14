> **Tipo: Fotografía.** Tomada el 2026-09-14 de una corrida real de la suite, no de memoria.
> Caduca con la próxima prueba que se escriba. **Se reemplaza entera, no se actualiza por partes.**

# Catálogo de pruebas, prueba por prueba

Inventario de las **1132 funciones de prueba** del repositorio, que la corrida expande en **1310 casos ejecutados**. De cada una: qué hace, a qué módulo pertenece, de qué tipo es, qué garantía ofrece, qué necesita recibir para poder correr y si cumple.

El método con que se escribe una prueba está en [`ESPECIFICACION.md`](ESPECIFICACION.md) y los umbrales en `CLAUDE.md`. Esta foto no los repite: sólo mide.

---

## Resumen

| Módulo | Archivos | Funciones | Casos ejecutados | Cumplen | No cumplen |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cuentas y acceso (`apps/accounts`) | 20 | 273 | 322 | 273 | 0 |
| Catálogo (`apps/catalog`) | 17 | 491 | 567 | 491 | 0 |
| Núcleo (`apps/core`) | 11 | 111 | 130 | 111 | 0 |
| Proveedores (`apps/suppliers`) | 13 | 257 | 291 | 257 | 0 |
| **Total** | **61** | **1132** | **1310** | **1132** | **0** |

---

## La naturaleza de las pruebas

Tres ejes independientes. Cada prueba tiene un valor en cada uno, y la columna **Tipo de prueba** de las tablas los escribe en este orden: *nivel · enfoque · propósito*.

### Eje 1 — Nivel: hasta dónde llega

| Nivel | Qué es | Cómo se reconoce acá | Funciones |
| --- | --- | --- | ---: |
| **Unitaria** | Ejercita una pieza aislada del framework —una función, un cálculo, una normalización— sin base de datos ni servidor. Es la más barata y la única que puede permitirse ser exhaustiva. | No pide ninguna fixture que arrastre `db` ni `client`. | 109 |
| **Integración** | Ejercita varias piezas juntas contra la base real: modelo, servicio, restricciones, migraciones aplicadas. No entra por HTTP. | Arrastra `db` —por fixture o por `pytestmark`— pero no `client`. | 279 |
| **Sistema** | Recorre el camino completo del actor: URL, enrutador, permisos, formulario, servicio, base y plantilla. Es la única que detecta que un paso quedó inalcanzable aunque su lógica esté bien. | Arrastra el `client` de Django, directo o vía `client_admin`. | 744 |

### Eje 2 — Enfoque: cuánto sabe de lo que prueba

| Enfoque | Qué es | Cómo se reconoce acá | Funciones |
| --- | --- | --- | ---: |
| **Caja negra** | Entra por la interfaz y mira sólo lo que sale. No sabe cómo está hecho por dentro, así que sobrevive a que se reescriba la implementación. | Afirma sobre el valor devuelto o sobre la respuesta HTTP, sin consultar la base ni sustituir nada. | 613 |
| **Caja gris** | Entra por la interfaz pública, como la negra, pero además verifica el estado interno que quedó. Es la forma natural de la prueba de contrato: la postcondición habla de instancias y atributos, no de pantallas. | Consulta la base después de operar (`.objects.`, `refresh_from_db`) sin sustituir nada. | 473 |
| **Caja blanca** | Conoce la estructura interna y la manipula: sustituye una dependencia, fuerza una rama que desde afuera no se alcanza, espía una llamada. Es la que hace falta para el catálogo de fallas de un servicio externo, y la que se rompe al refactorizar. | Usa `patch`, `monkeypatch` o un doble de prueba. | 46 |

### Eje 3 — Propósito: qué clase de defecto busca

| Propósito | Qué busca | Cómo se reconoce acá | Funciones |
| --- | --- | --- | ---: |
| **Funcional** | Que el camino previsto haga lo que el caso de uso promete. | Es el caso por defecto: ninguna de las señales de abajo. | 880 |
| **Validación** | Que la entrada inválida se rechace, y que se rechace en el servidor y no sólo en el formulario. | El nombre habla de rechazo, o de un valor inválido, vacío o roto. | 135 |
| **Control de acceso** | Que la operación no la pueda ejercer quien no debe, por su dirección real y con el rol equivocado. | El nombre lleva `acceso`, `solo_el_` o `sin_permiso`, o el cuerpo espera un 403. | 40 |
| **Frontera** | Qué pasa cuando el sistema externo se comporta mal: no responde, responde tarde, responde basura, o responde con la forma correcta y el contenido inventado. | El cuerpo nombra la puerta HTTP, la casilla de correo, el modelo de lenguaje o la cotización. | 56 |
| **Idempotencia** | Que repetir la misma operación con la misma entrada no duplique nada. | El nombre habla de hacerlo dos veces, de reprocesar o de no duplicar. | 21 |
| **Concurrencia** | Que dos operaciones sobre el mismo dato dejen uno de los dos estados válidos y nunca un tercero. | Usa `transactional_db`, hilos o un bloqueo de registro. | 0 |

La fila de concurrencia está en cero y no es un descuido de la medición: el código toma `select_for_update()` en tres lugares —`apps/accounts/services.py` y dos veces en `apps/catalog/revisiones.py`— y ninguna prueba de la suite provoca la carrera sobre ellos. Ninguna usa `transactional_db` ni hilos.

### Cruce de los dos primeros ejes

| Nivel \ Enfoque | Caja negra | Caja gris | Caja blanca | Total |
| --- | ---: | ---: | ---: | ---: |
| **Unitaria** | 97 | 0 | 12 | **109** |
| **Integración** | 152 | 94 | 33 | **279** |
| **Sistema** | 364 | 379 | 1 | **744** |
| **Total** | **613** | **473** | **46** | **1132** |

### Y la capa que declara el proyecto

`ESPECIFICACION.md` usa un vocabulario propio, que no es el de arriba y conviene no confundir: la capa dice **qué garantía le aporta la prueba al documento de análisis**, no cómo está construida. Es la columna *Qué ofrece*.

| Qué ofrece | Funciones |
| --- | ---: |
| Pantalla (HTTP) | 659 |
| Base de datos | 277 |
| Unidad | 109 |
| Contrato | 84 |
| Acceso | 3 |

---

## Cómo se leyó cada columna

| Columna | De dónde sale |
| --- | --- |
| **Prueba** | El nombre de la función, tal cual está en el archivo. |
| **Qué hace** | Su docstring cuando la tiene; si no, el propio nombre de la prueba, que en este repositorio ya describe el efecto esperado. |
| **Tipo de prueba** | *Nivel · enfoque · propósito*, los tres ejes de arriba. Se deduce de las fixtures que la prueba arrastra y de lo que hace su cuerpo. |
| **Qué ofrece** | La capa del proyecto. `Contrato CO-NNN` cuando el nombre lleva el código del contrato; `Acceso`, `Flujo` o `Frontera` cuando lleva el prefijo de su capa; en el resto se infiere de lo que la prueba pide: `Pantalla (HTTP)`, `Base de datos` o `Unidad`. |
| **Qué recibe** | Las fixtures que declara en su firma y los casos de `parametrize`. Toda prueba recibe además la fixture automática `sin_red`, que corta la salida HTTP: no se repite en cada fila. |
| **Cumple** | El resultado de la corrida del 2026-09-14. `xfail` marca las que se declaran como fallo esperado y por eso cuentan como cumplidas. |

---

## Índice de archivos

**Cuentas y acceso** — `apps/accounts`

| Archivo | Qué cubre | Tipo predominante | Funciones | Casos |
| --- | --- | --- | ---: | ---: |
| [`test_activacion_cuenta.py`](#test_activacion_cuentapy) | CU-USR-ALT, del lado del usuario nuevo: activar la cuenta y elegir contraseña. | Sistema · caja negra (5 de 9) | 9 | 9 |
| [`test_admin.py`](#test_adminpy) | El rol se administra desde el admin de Django hasta que exista el CU-USR-MOD. | Sistema · caja negra (2 de 3) | 3 | 3 |
| [`test_alta_usuario.py`](#test_alta_usuariopy) | CU-USR-ALT — Dar de Alta Usuario del Sistema. | Sistema · caja gris (7 de 13) | 13 | 14 |
| [`test_baja_usuario.py`](#test_baja_usuariopy) | CU-USR-BAJ — Dar de Baja Usuario del Sistema. | Sistema · caja gris (10 de 11) | 11 | 11 |
| [`test_bloqueo_intentos.py`](#test_bloqueo_intentospy) | CU-AUT-INI, excepción: 5 intentos fallidos consecutivos bloquean el acceso. | Sistema · caja gris (4 de 8) | 8 | 8 |
| [`test_contratos_12_autenticacion.py`](#test_contratos_12_autenticacionpy) | Pruebas de contrato del Módulo 12 — Autenticación (CO-114 a CO-119, CO-196) | Sistema · caja gris (21 de 35) | 35 | 37 |
| [`test_contratos_13_gestion_de_usuarios.py`](#test_contratos_13_gestion_de_usuariospy) | Pruebas de contrato del Módulo 13 — Gestión de Usuarios (CO-120 a CO-125, CO-197 a CO-202) | Sistema · caja gris (39 de 52) | 52 | 57 |
| [`test_correos.py`](#test_correospy) | Los enlaces con token tienen que llegar enteros al correo | Sistema · caja negra (4 de 4) | 4 | 4 |
| [`test_eliminar_pendiente.py`](#test_eliminar_pendientepy) | Eliminación de una cuenta que nunca se activó | Sistema · caja gris (7 de 7) | 7 | 8 |
| [`test_listado_clientes.py`](#test_listado_clientespy) | Consulta de cuentas de Cliente desde el backoffice (solo lectura). | Sistema · caja negra (11 de 11) | 11 | 14 |
| [`test_listado_usuarios.py`](#test_listado_usuariospy) | Buscador y filtros de la tabla de usuarios del sistema. | Sistema · caja negra (12 de 12) | 12 | 14 |
| [`test_login.py`](#test_loginpy) | CU-AUT-INI — Iniciar Sesión. | Sistema · caja negra (7 de 8) | 8 | 10 |
| [`test_logout.py`](#test_logoutpy) | CU-AUT-FIN — Cerrar Sesión. | Sistema · caja negra (2 de 4) | 4 | 4 |
| [`test_models.py`](#test_modelspy) | El modelo de usuario: las garantías que la base sostiene por su cuenta | Integración · caja gris (4 de 4) | 4 | 4 |
| [`test_modificacion_usuario.py`](#test_modificacion_usuariopy) | CU-USR-MOD — Modificar Usuario del Sistema. | Sistema · caja gris (9 de 15) | 15 | 15 |
| [`test_pantallas_backoffice.py`](#test_pantallas_backofficepy) | Chequeos de las pantallas del Módulo 13 que no son de lógica de negocio. | Sistema · caja negra (1 de 1) | 1 | 1 |
| [`test_reactivacion_usuario.py`](#test_reactivacion_usuariopy) | Reactivación y congelamiento de una cuenta dada de baja | Sistema · caja gris (10 de 12) | 12 | 12 |
| [`test_recuperar_contrasena.py`](#test_recuperar_contrasenapy) | CU-AUT-REC — Recuperar Contraseña. | Sistema · caja negra (6 de 12) | 12 | 12 |
| [`test_registro_cliente.py`](#test_registro_clientepy) | CU-CLI-ALT — Registrar Cuenta de Cliente. | Sistema · caja gris (30 de 47) | 47 | 80 |
| [`test_sesion.py`](#test_sesionpy) | CU-AUT-INI, comportamiento adicional: expiración por inactividad y renovación. | Sistema · caja negra (5 de 5) | 5 | 5 |

**Catálogo** — `apps/catalog`

| Archivo | Qué cubre | Tipo predominante | Funciones | Casos |
| --- | --- | --- | ---: | ---: |
| [`test_alta_lote_importado.py`](#test_alta_lote_importadopy) | Alta de lote de material editorial importado. | Sistema · caja gris (19 de 21) | 21 | 24 |
| [`test_alta_lote_nacional.py`](#test_alta_lote_nacionalpy) | Alta de lote de material editorial nacional. | Sistema · caja gris (35 de 41) | 41 | 42 |
| [`test_alta_no_editorial.py`](#test_alta_no_editorialpy) | CU-CAT-ALT — Registrar Alta de Producto No Editorial | Sistema · caja gris (18 de 26) | 26 | 30 |
| [`test_asistencias_de_carga.py`](#test_asistencias_de_cargapy) | Las ayudas que la pantalla de carga pide al servidor mientras se escribe | Sistema · caja gris (7 de 13) | 13 | 17 |
| [`test_baja_producto.py`](#test_baja_productopy) | CU-CAT-BAJ — Dar de Baja Producto (Editorial o No Editorial), y la reactivación | Sistema · caja gris (14 de 24) | 24 | 26 |
| [`test_borradores.py`](#test_borradorespy) | La generación de borradores desde una extracción (CU-ALT-NOV pasos 5, 6, 7 y 9) | Integración · caja negra (29 de 39) | 39 | 39 |
| [`test_edicion_producto.py`](#test_edicion_productopy) | CU-CAT-EDI — Editar Producto (Editorial o No Editorial) | Sistema · caja gris (21 de 29) | 29 | 29 |
| [`test_inventario.py`](#test_inventariopy) | Inventario y ficha de producto: la contraparte de lectura del alta | Sistema · caja negra (41 de 46) | 46 | 48 |
| [`test_isbn.py`](#test_isbnpy) | El ISBN: normalización, dígito verificador y detección de duplicados | Unitaria · caja negra (7 de 20) | 20 | 30 |
| [`test_jerarquia_de_producto.py`](#test_jerarquia_de_productopy) | La jerarquía de producto: identidad, rubro y las garantías de la base | Integración · caja negra (27 de 33) | 33 | 33 |
| [`test_nombres_de_catalogo.py`](#test_nombres_de_catalogopy) | Los catálogos que se identifican por su nombre no distinguen mayúsculas | Integración · caja gris (5 de 9) | 9 | 36 |
| [`test_pantalla_etiquetas.py`](#test_pantalla_etiquetaspy) | La pantalla de etiquetas, que salió de Parámetros globales | Sistema · caja negra (12 de 13) | 13 | 13 |
| [`test_pantalla_revision.py`](#test_pantalla_revisionpy) | Las pantallas de la revisión de borradores (CU-ALT-REV) | Sistema · caja gris (19 de 34) | 34 | 35 |
| [`test_parametros.py`](#test_parametrospy) | Parámetros globales: clasificación del catálogo, precios y configuración. | Sistema · caja gris (25 de 56) | 56 | 66 |
| [`test_precios.py`](#test_preciospy) | RF-10 — la aritmética del precio importado | Unitaria · caja negra (12 de 12) | 12 | 16 |
| [`test_revision_borradores.py`](#test_revision_borradorespy) | Revisar y confirmar borradores (CU-ALT-REV), del lado de las reglas | Integración · caja gris (20 de 39) | 39 | 39 |
| [`test_validaciones.py`](#test_validacionespy) | Entradas mal puestas en la carga de lotes | Sistema · caja negra (19 de 36) | 36 | 44 |

**Núcleo** — `apps/core`

| Archivo | Qué cubre | Tipo predominante | Funciones | Casos |
| --- | --- | --- | ---: | ---: |
| [`test_auditoria.py`](#test_auditoriapy) | El registro de auditoría: lo que queda escrito y lo que no se puede reescribir | Integración · caja negra (2 de 4) | 4 | 4 |
| [`test_componentes.py`](#test_componentespy) | Los controles de formulario del modo operativo están todos vestidos | Sistema · caja negra (8 de 13) | 13 | 17 |
| [`test_configuracion_del_modelo.py`](#test_configuracion_del_modelopy) | La configuración del modelo de lenguaje, y el diagnóstico de sus fallos | Integración · caja blanca (11 de 18) | 18 | 18 |
| [`test_consola.py`](#test_consolapy) | La salida de consola en ASCII | Unitaria · caja negra (4 de 4) | 4 | 8 |
| [`test_cotizaciones.py`](#test_cotizacionespy) | Cotización del peso frente a las monedas con las que se importa. | Unitaria · caja negra (13 de 18) | 18 | 21 |
| [`test_georef.py`](#test_georefpy) | Integración con georef-ar-api: caché, respaldo y degradación. | Unitaria · caja negra (8 de 14) | 14 | 14 |
| [`test_paises.py`](#test_paisespy) | Catálogo de códigos telefónicos de país. | Unitaria · caja negra (7 de 9) | 9 | 9 |
| [`test_panel.py`](#test_panelpy) | Tablero de entrada del Administrador y menú lateral del backoffice. | Sistema · caja negra (8 de 8) | 8 | 9 |
| [`test_permisos_por_rol.py`](#test_permisos_por_rolpy) | RNF-03: el control de acceso por rol se valida siempre del lado del servidor. | Sistema · caja negra (3 de 3) | 3 | 10 |
| [`test_plantillas.py`](#test_plantillaspy) | Reglas que tienen que cumplir todas las plantillas del proyecto. | Unitaria · caja negra (2 de 3) | 3 | 3 |
| [`test_respaldo.py`](#test_respaldopy) | El comando de respaldo de la base | Integración · caja blanca (17 de 17) | 17 | 17 |

**Proveedores** — `apps/suppliers`

| Archivo | Qué cubre | Tipo predominante | Funciones | Casos |
| --- | --- | --- | ---: | ---: |
| [`test_alta_proveedor.py`](#test_alta_proveedorpy) | CU-PRV-ALT — Registrar Proveedor Editorial | Sistema · caja gris (14 de 16) | 16 | 18 |
| [`test_baja_proveedor.py`](#test_baja_proveedorpy) | CU-PRV-BAJ — Dar de Baja Proveedor Editorial, y la reactivación que lo revierte | Sistema · caja gris (13 de 16) | 16 | 18 |
| [`test_borradores_del_correo.py`](#test_borradores_del_correopy) | El pipeline entero: de un `.eml` en la cola a borradores con su portada | Integración · caja gris (11 de 15) | 15 | 15 |
| [`test_cola_de_correos.py`](#test_cola_de_correospy) | La cola de aprobación: ingesta, pantallas y descarte | Sistema · caja negra (10 de 26) | 26 | 27 |
| [`test_comando_extraer.py`](#test_comando_extraerpy) | El comando `extraer_novedades`: la puerta por la que hoy corre el pipeline | Integración · caja negra (7 de 11) | 11 | 11 |
| [`test_consulta_proveedores.py`](#test_consulta_proveedorespy) | CU-PRV-CON — Consultar Proveedores: el listado y la ficha | Sistema · caja negra (17 de 18) | 18 | 21 |
| [`test_diagnostico_llm.py`](#test_diagnostico_llmpy) | La pantalla de diagnóstico del modelo de lenguaje | Sistema · caja negra (31 de 35) | 35 | 36 |
| [`test_edicion_proveedor.py`](#test_edicion_proveedorpy) | CU-PRV-EDI — Editar Proveedor Editorial | Sistema · caja gris (8 de 11) | 11 | 12 |
| [`test_extraccion.py`](#test_extraccionpy) | La extracción del modelo: el prompt, la validación y lo que se guarda | Integración · caja negra (37 de 44) | 44 | 61 |
| [`test_lectura_de_correos.py`](#test_lectura_de_correospy) | Lectura de un correo de novedades: de bytes MIME a texto parseable | Unitaria · caja negra (22 de 22) | 22 | 25 |
| [`test_muestras.py`](#test_muestraspy) | El generador de contenido de muestra para el banco de pruebas | Unitaria · caja negra (17 de 17) | 17 | 19 |
| [`test_pipeline_de_novedades.py`](#test_pipeline_de_novedadespy) | Lo que el proveedor le aporta al procesamiento automático de CU-ALT-NOV | Sistema · caja negra (9 de 17) | 17 | 17 |
| [`test_remitentes.py`](#test_remitentespy) | El filtro de remitentes válidos: lo que este módulo le aporta a CU-ALT-NOV | Integración · caja gris (8 de 9) | 9 | 11 |

---

## Cuentas y acceso — `apps/accounts`

### `test_activacion_cuenta.py`

> CU-USR-ALT, del lado del usuario nuevo: activar la cuenta y elegir contraseña.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 4; Sistema · caja gris · funcional — 2; Sistema · caja gris · validación — 2; Sistema · caja negra · idempotencia — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_activar_la_cuenta_la_deja_activa_y_con_contrasena` | Activar la cuenta la deja activa y con contrasena | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_al_terminar_se_ofrece_iniciar_sesion` | Al terminar se ofrece iniciar sesion | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_despues_de_activar_la_cuenta_puede_iniciar_sesion` | Despues de activar la cuenta puede iniciar sesion | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_una_cuenta_pendiente_no_puede_iniciar_sesion` | Una cuenta pendiente no puede iniciar sesion | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_enlace_vale_48_horas` | El enlace vale 48 horas | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_enlace_vencido_es_rechazado` | El enlace vencido es rechazado | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_enlace_no_se_puede_usar_dos_veces` | El enlace no se puede usar dos veces | Sistema · caja negra · idempotencia | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_una_contrasena_debil_no_activa_la_cuenta` | Una contrasena debil no activa la cuenta | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_activacion_queda_registrada_en_auditoria` | La activacion queda registrada en auditoria | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |

### `test_admin.py`

> El rol se administra desde el admin de Django hasta que exista el CU-USR-MOD.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 2; Sistema · caja gris · funcional — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_formulario_de_usuario_incluye_el_campo_rol` | El formulario de usuario incluye el campo rol | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `superusuario` | Cumple |
| `test_el_rol_se_puede_cambiar_desde_la_lista` | El rol se puede cambiar desde la lista | Sistema · caja gris · funcional | Pantalla (HTTP) | `client`, `superusuario` | Cumple |
| `test_el_log_de_auditoria_no_se_puede_editar_ni_borrar_desde_el_admin` | El log de auditoria no se puede editar ni borrar desde el admin | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `superusuario` | Cumple |

### `test_alta_usuario.py`

> CU-USR-ALT — Dar de Alta Usuario del Sistema.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · validación — 5; Sistema · caja negra · funcional — 4; Sistema · caja negra · validación — 1; Sistema · caja gris · funcional — 1; Sistema · caja gris · control de acceso — 1; Sistema · caja negra · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_alta_deja_la_cuenta_pendiente_de_activacion` | El alta deja la cuenta pendiente de activacion | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_genera_un_token_de_activacion_utilizable` | El alta genera un token de activacion utilizable | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_cuenta_nueva_no_tiene_contrasena_utilizable` | La cuenta nueva no tiene contrasena utilizable | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_avisa_por_correo_al_usuario_nuevo` | El alta avisa por correo al usuario nuevo | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_queda_registrada_en_auditoria_con_el_rol` | El alta queda registrada en auditoria con el rol | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |
| `test_un_correo_ya_usado_por_una_cuenta_activa_es_rechazado` | Un correo ya usado por una cuenta activa es rechazado | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_correo_ya_usado_por_una_cuenta_pendiente_es_rechazado` | Un correo ya usado por una cuenta pendiente es rechazado | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_campo_obligatorio_vacio_no_crea_la_cuenta` | Un campo obligatorio vacio no crea la cuenta | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_formulario_no_ofrece_cliente_como_rol` | El formulario no ofrece cliente como rol | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_post_con_rol_cliente_es_rechazado` | La restricción del rol es del servidor, no del `select` del navegador. | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_solo_el_administrador_accede_al_alta` | Solo el administrador accede al alta | Sistema · caja gris · control de acceso | Pantalla (HTTP) | `client`; `rol_sin_permiso` — 2 casos | Cumple |
| `test_la_lista_de_usuarios_no_filtra_datos_a_otros_roles` | 403 sin datos parciales: el cajero no ve ni un pedazo de la tabla. | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client`, `cajero` | Cumple |
| `test_la_lista_muestra_solo_cuentas_de_personal` | La lista muestra solo cuentas de personal | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `cliente`, `cajero` | Cumple |

### `test_baja_usuario.py`

> CU-USR-BAJ — Dar de Baja Usuario del Sistema.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 8; Sistema · caja gris · validación — 1; Sistema · caja negra · funcional — 1; Sistema · caja gris · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_la_pantalla_pide_confirmacion_explicita` | La pantalla pide confirmacion explicita | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `cajero` | Cumple |
| `test_la_baja_cambia_el_estado_e_invalida_las_sesiones` | La baja cambia el estado e invalida las sesiones | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `cajero` | Cumple |
| `test_la_baja_es_logica_y_no_borra_la_cuenta` | La baja es logica y no borra la cuenta | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `cajero` | Cumple |
| `test_un_usuario_dado_de_baja_no_puede_volver_a_iniciar_sesion` | Un usuario dado de baja no puede volver a iniciar sesion | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `cajero` | Cumple |
| `test_no_se_puede_dar_de_baja_al_unico_administrador_activo` | No se puede dar de baja al unico administrador activo | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |
| `test_se_puede_dar_de_baja_un_administrador_si_queda_otro_activo` | Se puede dar de baja un administrador si queda otro activo | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |
| `test_darse_de_baja_a_uno_mismo_cierra_la_propia_sesion` | Darse de baja a uno mismo cierra la propia sesion | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |
| `test_la_baja_queda_registrada_en_auditoria` | La baja queda registrada en auditoria | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `cajero`, `administrador` | Cumple |
| `test_el_historial_del_usuario_dado_de_baja_sigue_consultable` | La baja no dispara borrado ni anonimización en cascada. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `cajero` | Cumple |
| `test_no_se_puede_dar_de_baja_una_cuenta_que_no_esta_activa` | No se puede dar de baja una cuenta que no esta activa | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_solo_el_administrador_puede_dar_de_baja` | Solo el administrador puede dar de baja | Sistema · caja gris · control de acceso | Pantalla (HTTP) | `client`, `cajero` | Cumple |

### `test_bloqueo_intentos.py`

> CU-AUT-INI, excepción: 5 intentos fallidos consecutivos bloquean el acceso.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 4; Sistema · caja negra · funcional — 2; Sistema · caja negra · validación — 1; Integración · caja negra · funcional — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_quinto_intento_fallido_bloquea_el_acceso` | Quinto intento fallido bloquea el acceso | Sistema · caja gris · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_el_bloqueo_rechaza_incluso_la_contrasena_correcta` | El bloqueo rechaza incluso la contrasena correcta | Sistema · caja negra · validación | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_el_bloqueo_avisa_al_correo_registrado_y_queda_auditado` | El bloqueo avisa al correo registrado y queda auditado | Sistema · caja gris · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_el_bloqueo_se_levanta_al_pasar_la_ventana_de_tiempo` | El bloqueo se levanta al pasar la ventana de tiempo | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cliente`, `settings` | Cumple |
| `test_los_intentos_de_otra_ip_no_bloquean_la_cuenta` | El bloqueo es por dispositivo: un tercero no puede dejar afuera al titular. | Integración · caja negra · funcional | Base de datos | `cliente` | Cumple |
| `test_un_login_exitoso_corta_la_racha_de_intentos` | Un login exitoso corta la racha de intentos | Sistema · caja gris · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_tambien_se_cuentan_los_intentos_contra_correos_inexistentes` | Si solo contáramos cuentas reales, la diferencia revelaría cuáles existen. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_una_cuenta_inactiva_con_clave_correcta_no_suma_intentos` | Una cuenta inactiva con clave correcta no suma intentos | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |

### `test_contratos_12_autenticacion.py`

> Pruebas de contrato del Módulo 12 — Autenticación (CO-114 a CO-119, CO-196). Se escriben desde el contrato, no desde la implementación: cada prueba transcribe una postcondición declarada y afirma sus dos mitades —el valor anterior y el posterior— según el apartado 3 de `docs/pruebas/ESPECIFICACION.md`. **Dos postcondiciones de este módulo no se pueden afirmar como están declaradas.** CO-117…

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 16; Sistema · caja negra · funcional — 11; Sistema · caja gris · validación — 5; Sistema · caja negra · validación — 1; Integración · caja negra · funcional — 1; Integración · caja negra · validación — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_CO114_credenciales_validas_establecen_sesion_con_el_nivel_del_rol` | Postcondición: se estableció una sesión con el nivel de permisos del rol. | Sistema · caja negra · funcional | Contrato CO-114 | `client`; `rol`, `destino` — 3 casos | Cumple |
| `test_CO114_la_sesion_nace_con_expiracion_por_inactividad` | Postcondición: «un token con expiración por inactividad». La mitad que el contrato declara y acá **no** se afirma es «según ConfiguracionSistema»: el plazo vive hoy en `settings`, no en esa entidad. Ver `bitacora/12-autenticacion.md`,… | Sistema · caja negra · funcional | Contrato CO-114 | `client`, `cliente` | Cumple |
| `test_CO114_credenciales_validas_registran_el_inicio_en_auditoria` | Postcondición: se creó una entrada con acción «Inicio de sesión», actor y momento. | Sistema · caja gris · funcional | Contrato CO-114 | `client`, `cliente` | Cumple |
| `test_CO114_credenciales_invalidas_crean_un_intento_fallido` | Postcondición (a): se creó if : IntentoFallido. Y (c): sus tres atributos. | Sistema · caja gris · validación | Contrato CO-114 | `client`, `cliente` | Cumple |
| `test_CO114_el_intento_fallido_guarda_el_correo_tal_como_se_escribio` | Postcondición (c): «if.correo tecleado quedó con el valor tal como se escribió». | Sistema · caja gris · funcional | Contrato CO-114 | `client`, `cliente` | Cumple |
| `test_CO114_se_registra_el_intento_aunque_la_cuenta_no_exista` | Notas del contrato: se registra «exista o no una cuenta con ese valor». | Sistema · caja gris · funcional | Contrato CO-114 | `client` | Cumple |
| `test_CO114_el_quinto_intento_registra_el_bloqueo_en_auditoria` | Postcondición: «si los intentos dentro de la ventana alcanzaron cinco». | Sistema · caja gris · funcional | Contrato CO-114 | `client`, `cliente` | Cumple |
| `test_CO114_bloqueado_no_entra_ni_con_la_contrasena_correcta` | Excepción E1: «se bloquea el acceso por el período parametrizado». | Sistema · caja negra · funcional | Contrato CO-114 | `client`, `cliente` | Cumple |
| `test_CO114_el_bloqueo_se_levanta_solo_al_salir_los_intentos_de_la_ventana` | Notas: «el bloqueo se levanta solo cuando los intentos salen de la ventana». | Sistema · caja negra · funcional | Contrato CO-114 | `client`, `cliente` | Cumple |
| `test_CO114_cuenta_inactiva_no_obtiene_sesion` | Excepción E2: cuenta en estado Inactivo, «sin otorgar sesión». | Sistema · caja negra · funcional | Contrato CO-114 | `client` | Cumple |
| `test_CO114_cuenta_inactiva_no_deja_rastro_de_inicio_en_auditoria` | Postcondición negativa: la rama de credenciales válidas no corrió. | Sistema · caja gris · funcional | Contrato CO-114 | `client` | Cumple |
| `test_CO115_extender_renueva_el_plazo_de_inactividad` | Postcondición: «el plazo de expiración por inactividad del token quedó renovado». | Sistema · caja negra · funcional | Contrato CO-115 | `client`, `cliente` | Cumple |
| `test_CO115_sobre_una_sesion_vencida_la_extension_no_procede` | Excepción: «si la sesión ya expiró, la extensión no procede». | Sistema · caja negra · funcional | Contrato CO-115 | `client`, `cliente` | Cumple |
| `test_CO116_cerrar_sesion_invalida_el_token_del_dispositivo_actual` | Postcondición: «el token de sesión del dispositivo actual quedó invalidado». | Sistema · caja negra · validación | Contrato CO-116 | `client`, `cliente` | Cumple |
| `test_CO116_cerrar_sesion_no_afecta_las_sesiones_de_otros_dispositivos` | Postcondición negativa explícita: «las sesiones en otros dispositivos no fueron afectadas». Es la que distingue CO-116 de CO-118 y de CO-123, y la que ninguna prueba del camino feliz mira. | Integración · caja negra · funcional | Contrato CO-116 | `cliente` | Cumple |
| `test_CO116_cerrar_sesion_registra_el_cierre_en_auditoria` | Postcondición: entrada con acción «Cierre de sesión», actor y timestamp. | Sistema · caja gris · funcional | Contrato CO-116 | `client`, `cliente` | Cumple |
| `test_CO117_una_cuenta_activa_recibe_el_enlace_en_su_direccion` | Postcondición (a): «sólo si el correo corresponde a una cuenta Activa […] el enlace se envió a esa dirección». | Sistema · caja negra · funcional | Contrato CO-117 | `client`, `cliente` | Cumple |
| `test_CO117_un_correo_sin_cuenta_no_produce_ninguna_postcondicion` | Postcondición: «si el correo no corresponde a ninguna cuenta activa: ninguna postcondición». | Sistema · caja gris · funcional | Contrato CO-117 | `client` | Cumple |
| `test_CO117_la_respuesta_es_identica_exista_o_no_la_cuenta` | Notas: «la respuesta es idéntica exista o no una cuenta con el correo consultado». | Sistema · caja negra · funcional | Contrato CO-117 | `client`, `cliente` | Cumple |
| `test_CO117_una_cuenta_inactiva_no_recibe_enlace` | Postcondición (a): la condición es «una cuenta Activa». | Sistema · caja negra · funcional | Contrato CO-117 | `client` | Cumple |
| `test_CO118_la_credencial_pasa_del_hash_anterior_al_nuevo` | Postcondición (c): «u.credencial pasó del hash anterior al nuevo». | Sistema · caja gris · funcional | Contrato CO-118 | `client`, `cliente` | Cumple |
| `test_CO118_la_contrasena_anterior_queda_invalidada` | Postcondición (c): «la contraseña anterior quedó invalidada». | Sistema · caja gris · validación | Contrato CO-118 | `client`, `cliente` | Cumple |
| `test_CO118_el_token_queda_consumido_efecto_observable` | Postcondición (c): «tr.estado pasó de Vigente a Consumido». `TokenRecuperacion` no existe como tabla —es `<<planificado>>`—, así que no hay estado que leer. Lo observable es que el mismo enlace deja de servir para una segunda vez. | Sistema · caja gris · funcional | Contrato CO-118 | `client`, `cliente` | Cumple |
| `test_CO118_invalida_las_sesiones_en_todos_los_dispositivos` | Postcondición: «todas las sesiones activas del usuario, en cualquier dispositivo, quedaron invalidadas». Es la diferencia con CO-116. | Integración · caja negra · validación | Contrato CO-118 | `cliente` | Cumple |
| `test_CO118_registra_el_cambio_de_contrasena_en_auditoria` | Postcondición: entrada con acción «Cambio de contraseña». | Sistema · caja gris · funcional | Contrato CO-118 | `client`, `cliente` | Cumple |
| `test_CO118_con_contrasenas_que_no_coinciden_el_enlace_no_se_consume` | Excepción E2: «el token no se consume y el usuario puede corregir sin necesidad de uno nuevo». | Sistema · caja gris · funcional | Contrato CO-118 | `client`, `cliente` | Cumple |
| `test_CO118_un_enlace_vencido_no_cambia_la_credencial` | Excepción E1: token vencido. Lo que se afirma es qué quedó en el sistema. | Sistema · caja gris · funcional | Contrato CO-118 | `client`, `cliente` | Cumple |
| `test_CO119_la_cuenta_pasa_de_pendiente_de_activacion_a_activo` | Postcondición (c): «u.estado pasó de Pendiente de activación a Activo». | Sistema · caja gris · validación | Contrato CO-119 | `client`, `pendiente` | Cumple |
| `test_CO119_la_credencial_pasa_de_nula_al_hash_de_la_elegida` | Postcondición (c): «u.credencial pasó de nula al hash con sal única». | Sistema · caja gris · funcional | Contrato CO-119 | `client`, `pendiente` | Cumple |
| `test_CO119_el_enlace_no_admite_un_segundo_uso_efecto_observable` | Postcondición (c): «EnlaceActivacion.estado pasó de Vigente a Consumido». `EnlaceActivacion` es `<<planificado>>` y no existe como tabla. Lo observable es que el mismo enlace no sirve una segunda vez para fijar otra contraseña. | Sistema · caja gris · funcional | Contrato CO-119 | `client`, `pendiente` | Cumple |
| `test_CO119_registra_la_activacion_en_auditoria` | Postcondición: entrada con acción «Activación de cuenta». | Sistema · caja gris · validación | Contrato CO-119 | `client`, `pendiente` | Cumple |
| `test_CO119_un_enlace_vencido_deja_la_cuenta_pendiente` | Excepción E1: enlace vencido. Qué quedó en el sistema después del fallo. | Sistema · caja gris · funcional | Contrato CO-119 | `client`, `pendiente` | Cumple |
| `test_CO119_una_contrasena_rechazada_no_consume_el_enlace` | Excepción E3: «el enlace no se consume por un intento fallido». | Sistema · caja gris · validación | Contrato CO-119 | `client`, `pendiente` | Cumple |
| `test_CO196_abrir_el_enlace_no_modifica_el_estado_del_sistema` | Postcondición: «ninguna. La operación no modifica el estado del sistema». Suena trivial y no lo es: es lo que detecta que alguien le puso un efecto a una consulta. | Sistema · caja gris · funcional | Contrato CO-196 | `client`, `pendiente` | Cumple |
| `test_CO196_no_exige_sesion_iniciada` | Precondición: «ninguna de sesión: el enlace es la credencial». | Sistema · caja negra · funcional | Contrato CO-196 | `client`, `pendiente` | Cumple |

### `test_contratos_13_gestion_de_usuarios.py`

> Pruebas de contrato del Módulo 13 — Gestión de Usuarios (CO-120 a CO-125, CO-197 a CO-202). Incluye CO-156 `cancelarOperacion` en sus tres puntos de este módulo: CU-USR-BAJ A1, CU-USR-REA A1 y CU-USR-ELI A1. Se escriben desde el contrato. Igual que en el módulo 12, `EnlaceActivacion` es un concepto `<<planificado>>` del modelo de dominio y no existe como tabla: las postcondiciones que declaran su…

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 31; Sistema · caja negra · funcional — 9; Sistema · caja gris · validación — 6; Sistema · caja negra · validación — 3; Sistema · caja gris · control de acceso — 2; Sistema · caja negra · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_CO120_se_creo_la_cuenta_en_pendiente_de_activacion` | Postcondición (a) y (c): «se creó u : Usuario», «u.estado quedó en Pendiente». | Sistema · caja gris · validación | Contrato CO-120 | `client_admin` | Cumple |
| `test_CO120_el_rol_queda_con_el_valor_declarado` | Postcondición (c): «u.rol con el valor declarado (Cajero o Administrador)». | Sistema · caja gris · funcional | Contrato CO-120 | `client_admin` | Cumple |
| `test_CO120_el_correo_queda_normalizado` | Postcondición (c): «u.correo normalizado». | Sistema · caja gris · funcional | Contrato CO-120 | `client_admin` | Cumple |
| `test_CO120_la_cuenta_nace_sin_credencial_utilizable` | Postcondición (c): «u.credencial nula». Django no guarda nulo sino un hash que ninguna contraseña satisface; lo verificable es que no hay credencial con la que entrar, que es lo que el contrato protege en sus Notas: «la establece su… | Sistema · caja negra · funcional | Contrato CO-120 | `client_admin`, `pendiente` | Cumple |
| `test_CO120_se_envio_el_enlace_al_correo_del_nuevo_usuario_efecto_observable` | Postcondición (a)(b)(c): «se creó ea : EnlaceActivacion», «ea → u», «el enlace se envió». | Sistema · caja negra · funcional | Contrato CO-120 | `client_admin` | Cumple |
| `test_CO120_registra_el_alta_en_auditoria_con_el_rol_asignado` | Postcondición: entrada «Alta de usuario del sistema» con actor, momento y rol asignado. | Sistema · caja gris · funcional | Contrato CO-120 | `client_admin`, `administrador` | Cumple |
| `test_CO120_un_correo_de_cuenta_activa_no_crea_la_cuenta` | Excepción E2: «el correo ya pertenece a una cuenta Activa o Pendiente […] no se crea». | Sistema · caja gris · funcional | Contrato CO-120 | `client_admin`, `cajero_activo` | Cumple |
| `test_CO120_un_correo_de_cuenta_pendiente_no_crea_la_cuenta` | Excepción E2, la otra mitad: también bloquea contra una cuenta Pendiente. | Sistema · caja gris · funcional | Contrato CO-120 | `client_admin`, `pendiente` | Cumple |
| `test_CO121_los_atributos_pasan_de_su_valor_anterior_al_declarado` | Postcondición (c): «los atributos modificados pasaron de sus valores anteriores a los declarados». | Sistema · caja gris · funcional | Contrato CO-121 | `client_admin`, `cajero_activo` | Cumple |
| `test_CO121_la_ultima_modificacion_queda_con_el_instante` | Postcondición (c): «u.última modificación quedó con el instante». | Sistema · caja gris · funcional | Contrato CO-121 | `client_admin`, `cajero_activo` | Cumple |
| `test_CO121_cambiar_el_rol_invalida_la_sesion_del_usuario_modificado` | Postcondición: «si se modificó el rol: el token de sesión activo del usuario modificado quedó invalidado de forma inmediata, forzando un re-login con los nuevos permisos». | Sistema · caja negra · validación | Contrato CO-121 | `client_admin`, `cajero_activo` | Cumple |
| `test_CO121_sin_cambiar_el_rol_la_sesion_del_usuario_sigue_viva` | Postcondición negativa: la invalidación está condicionada a «si se modificó el rol». | Sistema · caja negra · funcional | Contrato CO-121 | `client_admin`, `cajero_activo` | Cumple |
| `test_CO121_registra_los_valores_anterior_y_nuevo_de_cada_campo` | Postcondición: entrada con «los valores anteriores y nuevos de cada campo modificado». | Sistema · caja gris · funcional | Contrato CO-121 | `client_admin`, `cajero_activo` | Cumple |
| `test_CO121_no_se_puede_quitar_el_rol_al_ultimo_administrador` | Excepción E1: «la operación se cancela sin efecto» (I-12). | Sistema · caja gris · funcional | Contrato CO-121 | `client_admin`, `administrador` | Cumple |
| `test_CO121_un_correo_que_ya_es_de_otra_cuenta_no_actualiza` | Excepción E2: «se informa el conflicto y no se actualiza». | Sistema · caja gris · funcional | Contrato CO-121 | `client_admin`, `cajero_activo` | Cumple |
| `test_CO121_una_cuenta_inactiva_no_admite_modificacion` | Excepción E3: «se bloquea el acceso al formulario y se ofrece la acción de reactivación». | Sistema · caja negra · funcional | Contrato CO-121 | `client_admin`, `dado_de_baja` | Cumple |
| `test_CO121_una_cuenta_inactiva_no_cambia_aunque_se_envie_el_formulario` | Excepción E3, la mitad que importa: la restricción vive en el servidor, no en la pantalla. | Sistema · caja gris · funcional | Contrato CO-121 | `client_admin`, `dado_de_baja` | Cumple |
| `test_CO122_se_reenvia_un_enlace_nuevo_efecto_observable` | Postcondición (a): «se creó un EnlaceActivacion nuevo». «El correo fue reenviado». | Sistema · caja negra · funcional | Contrato CO-122 | `client_admin`, `pendiente` | Cumple |
| `test_CO122_el_enlace_anterior_deja_de_admitir_uso_efecto_observable` | Postcondición (c): «el EnlaceActivacion anterior pasó a estado Vencido y no admite uso». | Sistema · caja gris · funcional | Contrato CO-122 | `client_admin`, `pendiente` | Cumple |
| `test_CO122_registra_el_reenvio_en_auditoria` | Postcondición: entrada «Reenvío del enlace de activación» con actor y momento. | Sistema · caja gris · funcional | Contrato CO-122 | `client_admin`, `pendiente` | Cumple |
| `test_CO123_el_estado_pasa_de_activo_a_inactivo` | Postcondición (c): «u.estado pasó de Activo a Inactivo». | Sistema · caja gris · funcional | Contrato CO-123 | `client_admin`, `cajero_activo` | Cumple |
| `test_CO123_la_cuenta_no_puede_volver_a_iniciar_sesion` | Postcondición (c): «el usuario no puede volver a iniciar sesión» (I-11). | Sistema · caja negra · funcional | Contrato CO-123 | `client_admin`, `cajero_activo` | Cumple |
| `test_CO123_invalida_los_tokens_de_todos_los_dispositivos` | Postcondición: «todos sus tokens de sesión, en cualquier dispositivo, quedaron invalidados de forma inmediata». | Sistema · caja negra · validación | Contrato CO-123 | `client_admin`, `cajero_activo` | Cumple |
| `test_CO123_el_historial_del_usuario_se_conserva_integro` | Postcondición negativa explícita: «el historial de operaciones registradas por ese usuario se conservó íntegro en el log». | Sistema · caja gris · funcional | Contrato CO-123 | `client_admin`, `cajero_activo` | Cumple |
| `test_CO123_registra_la_baja_en_auditoria` | Postcondición: entrada «Baja de usuario del sistema» con actor y momento. | Sistema · caja gris · funcional | Contrato CO-123 | `client_admin`, `cajero_activo` | Cumple |
| `test_CO123_no_se_puede_dar_de_baja_al_ultimo_administrador` | Excepción E1: se bloquea (I-12). | Sistema · caja gris · funcional | Contrato CO-123 | `client_admin`, `administrador` | Cumple |
| `test_CO124_el_estado_pasa_de_inactivo_a_pendiente_de_activacion` | Postcondición (c): «u.estado pasó de Inactivo a Pendiente de activación (no a Activo)». | Sistema · caja gris · validación | Contrato CO-124 | `client_admin`, `dado_de_baja` | Cumple |
| `test_CO124_la_credencial_anterior_queda_invalidada` | Postcondición (c): «u.credencial quedó invalidada». Las Notas dicen por qué: «entre la baja y la reincorporación pudo pasar cualquier cosa con esa credencial, y el sistema no tiene forma de saberlo». | Sistema · caja gris · validación | Contrato CO-124 | `client_admin`, `dado_de_baja` | Cumple |
| `test_CO124_se_envia_un_enlace_de_activacion_efecto_observable` | Postcondición (a): «se creó un EnlaceActivacion con vigencia de 48 horas, enviado al correo de la cuenta». | Sistema · caja negra · validación | Contrato CO-124 | `client_admin`, `dado_de_baja` | Cumple |
| `test_CO124_el_historial_del_usuario_se_conserva_integro` | Postcondición: «el historial de operaciones del usuario en el log se conservó íntegro». | Sistema · caja gris · funcional | Contrato CO-124 | `client_admin`, `dado_de_baja` | Cumple |
| `test_CO124_registra_la_reactivacion_en_auditoria` | Postcondición: entrada «Reactivación de usuario del sistema» con actor y momento. | Sistema · caja gris · validación | Contrato CO-124 | `client_admin`, `dado_de_baja` | Cumple |
| `test_CO124_el_rol_queda_con_el_valor_declarado` | Postcondición (c): «u.rol quedó con el valor declarado». Las Notas explican para qué: «el rol se elige acá y queda registrado junto con la reactivación, en lugar de restaurarse el que tenía. Es lo que impide dejar preparado un cambio de… | Sistema · caja gris · funcional | Contrato CO-124 | `client_admin`, `dado_de_baja` | Cumple (xfail esperado) |
| `test_CO124_la_auditoria_incluye_el_rol_asignado` | Postcondición: entrada «Reactivación de usuario del sistema» […] «incluyendo el rol asignado». | Sistema · caja gris · funcional | Contrato CO-124 | `client_admin`, `dado_de_baja` | Cumple (xfail esperado) |
| `test_CO199_la_pantalla_permite_modificar_el_rol_antes_de_confirmar` | Responsabilidad de CO-199: «presentar el rol con el que quedará reactivada, permitiendo modificarlo antes de confirmar». | Sistema · caja negra · funcional | Contrato CO-199 | `client_admin`, `dado_de_baja` | Cumple (xfail esperado) |
| `test_CO125_la_auditoria_se_escribe_antes_de_eliminar_el_registro` | Postcondición, en el orden que «es parte del contrato»: primero la entrada, después la eliminación física. Lo verificable del orden es su consecuencia: la entrada sobrevive al registro que la originó y sigue diciendo de quién era la cuenta. | Sistema · caja gris · funcional | Contrato CO-125 | `client_admin`, `pendiente` | Cumple |
| `test_CO125_se_elimino_fisicamente_la_instancia` | Postcondición (a): «se eliminó físicamente la instancia u : Usuario del sistema». | Sistema · caja gris · funcional | Contrato CO-125 | `client_admin`, `pendiente` | Cumple |
| `test_CO125_el_correo_queda_disponible_para_un_alta_nueva` | Postcondición: «el correo quedó disponible para un alta nueva (I-10 deja de bloquearlo)». | Sistema · caja gris · funcional | Contrato CO-125 | `client_admin`, `pendiente` | Cumple |
| `test_CO125_el_enlace_pendiente_queda_invalidado_efecto_observable` | Postcondición (c): «el EnlaceActivacion pendiente quedó invalidado». | Sistema · caja gris · validación | Contrato CO-125 | `client_admin`, `pendiente` | Cumple |
| `test_CO125_una_cuenta_activa_no_se_elimina` | Excepción E2: «la cuenta está en estado Activo o Inactivo: la operación no se ofrece». Se ejerce por la dirección real: que la pantalla no ofrezca el botón no alcanza. | Sistema · caja gris · funcional | Contrato CO-125 | `client_admin`, `cajero_activo` | Cumple |
| `test_CO125_una_cuenta_inactiva_no_se_elimina` | Excepción E2, la otra mitad del estado. | Sistema · caja gris · funcional | Contrato CO-125 | `client_admin`, `dado_de_baja` | Cumple |
| `test_CO125_una_pendiente_que_ya_inicio_sesion_no_se_elimina` | Excepción E1 y Notas: «no alcanza con estar Pendiente: una cuenta reactivada por CO-124 también lo está, y ésa sí tiene historial». | Sistema · caja gris · funcional | Contrato CO-125 | `client_admin`, `dado_de_baja` | Cumple |
| `test_CO156_abandonar_antes_de_confirmar_no_cambia_nada` | Postcondición: «ninguna. El objeto sobre el que se operaba conserva todos sus atributos, asociaciones y estado. No se genera entrada de auditoría». | Sistema · caja gris · funcional | Contrato CO-156 | `client_admin`, `request`; `url_de`, `fixture` — 3 casos | Cumple |
| `test_CO197_abrir_la_edicion_no_modifica_el_estado` | CO-197. Postcondición: ninguna. | Sistema · caja gris · funcional | Contrato CO-197 | `client_admin`, `cajero_activo` | Cumple |
| `test_CO198_solicitar_la_baja_no_modifica_el_estado` | CO-198. Postcondición: ninguna. | Sistema · caja gris · funcional | Contrato CO-198 | `client_admin`, `cajero_activo` | Cumple |
| `test_CO198_no_se_ofrece_sobre_el_ultimo_administrador` | CO-198, excepción E1: «última cuenta Administrador activa: se bloquea» (I-12). El sistema no queda expuesto —CO-123 sí rechaza la baja, y esa prueba pasa—; lo que falla es que la operación se ofrece. Es el principio que CO-202 enuncia: «la… | Sistema · caja negra · funcional | Contrato CO-198 | `client_admin`, `administrador` | Cumple (xfail esperado) |
| `test_CO199_solicitar_la_reactivacion_no_modifica_el_estado` | CO-199. Postcondición: ninguna. | Sistema · caja gris · validación | Contrato CO-199 | `client_admin`, `dado_de_baja` | Cumple |
| `test_CO200_solicitar_la_eliminacion_no_modifica_el_estado` | CO-200. Postcondición: ninguna. | Sistema · caja gris · funcional | Contrato CO-200 | `client_admin`, `pendiente` | Cumple |
| `test_CO201_el_listado_presenta_nombre_correo_rol_y_estado` | CO-201. Responsabilidad: «listar nombre, correo, rol y estado de cada cuenta». | Sistema · caja negra · funcional | Contrato CO-201 | `client_admin`, `cajero_activo` | Cumple |
| `test_CO201_el_listado_no_modifica_el_estado` | CO-201. Postcondición: ninguna. | Sistema · caja gris · funcional | Contrato CO-201 | `client_admin`, `cajero_activo` | Cumple |
| `test_acceso_CO201_el_listado_de_personal_es_solo_del_administrador` | Precondición de CO-201: «rol Administrador validado en el servidor» (RNF-03). Por la dirección real y con el rol equivocado, no llamando a la vista. | Sistema · caja negra · control de acceso | Acceso | `client`; `rol` — 2 casos | Cumple |
| `test_acceso_CO123_la_baja_de_usuario_es_solo_del_administrador` | Precondición de CO-123: la operación es del Administrador. Se ejerce el POST real. | Sistema · caja gris · control de acceso | Acceso | `client`, `cajero_activo`; `rol` — 2 casos | Cumple |
| `test_acceso_CO125_la_eliminacion_es_solo_del_administrador` | Precondición de CO-125: la operación es del Administrador. Se ejerce el POST real. | Sistema · caja gris · control de acceso | Acceso | `client`, `pendiente`; `rol` — 2 casos | Cumple |

### `test_correos.py`

> Los enlaces con token tienen que llegar enteros al correo. Estos tests miran el mensaje MIME que sale, no el cuerpo que armamos nosotros. La diferencia es exactamente el agujero por el que se coló el bug: `correo.body` siempre está entero, pero el enlace se partía en dos al codificar el mensaje, y el destinatario recibía un token incompleto que el sistema rechazaba.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 3; Sistema · caja negra · validación — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_enlace_de_activacion_llega_entero` | El enlace de activacion llega entero | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_enlace_de_recuperacion_llega_entero` | El enlace de recuperacion llega entero | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_los_acentos_llegan_legibles` | Sin codificar, el cuerpo se lee tal cual: importa porque en desarrollo el correo se lee crudo en la consola del `runserver`. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_ninguna_linea_del_cuerpo_queda_partida` | Ninguna linea del cuerpo queda partida | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |

### `test_eliminar_pendiente.py`

> Eliminación de una cuenta que nunca se activó. Agregado al CU, documentado en `/docs/modulos/gestion_usuarios.md`: sin esto, una cuenta cargada con el correo equivocado queda pendiente para siempre y ese correo bloqueado, porque el CU-USR-BAJ exige estado Activo para dar de baja.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 6; Sistema · caja gris · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_la_pantalla_pide_confirmacion_explicita` | La pantalla pide confirmacion explicita | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_eliminar_una_cuenta_pendiente_la_borra` | Eliminar una cuenta pendiente la borra | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_eliminar_libera_el_correo_para_darlo_de_alta_de_nuevo` | Es el motivo por el que existe esta operación. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_una_cuenta_que_alguna_vez_se_uso_no_se_elimina` | Una cuenta que alguna vez se uso no se elimina | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`; `estado` — 2 casos | Cumple |
| `test_la_auditoria_sobrevive_al_borrado_con_el_correo` | La auditoria sobrevive al borrado con el correo | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |
| `test_el_registro_del_alta_tambien_sigue_consultable` | El registro del alta tambien sigue consultable | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_solo_el_administrador_puede_eliminar` | Solo el administrador puede eliminar | Sistema · caja gris · control de acceso | Pantalla (HTTP) | `client`, `client_admin`, `cajero` | Cumple |

### `test_listado_clientes.py`

> Consulta de cuentas de Cliente desde el backoffice (solo lectura).

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 10; Sistema · caja negra · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_la_pantalla_lista_solo_cuentas_de_cliente` | La pantalla lista solo cuentas de cliente | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `clientela` | Cumple |
| `test_la_tabla_no_ofrece_acciones_sobre_las_cuentas` | Es de consulta: dar de baja un Cliente es el CU-CLI-BAJ, todavía sin documentar. Se mira el fragmento de la tabla y no la pantalla entera: la cáscara del backoffice trae las clases de los botones definidas en su CSS, así que buscarlas en… | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `clientela` | Cumple |
| `test_muestra_el_telefono_armado_y_la_direccion` | Muestra el telefono armado y la direccion | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_avisa_cuando_una_cuenta_no_tiene_consentimiento_registrado` | Una cuenta sin fecha de aceptación no salió del registro público. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `clientela` | Cumple |
| `test_el_buscador_encuentra_por_nombre_correo_y_telefono` | El buscador encuentra por nombre correo y telefono | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `clientela`; `termino` — 3 casos | Cumple |
| `test_el_filtro_por_provincia` | El filtro por provincia | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `clientela` | Cumple |
| `test_el_filtro_por_estado` | El filtro por estado | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `clientela` | Cumple |
| `test_una_provincia_inventada_en_la_url_se_ignora` | Un valor cualquiera en la query string no filtra de más ni rompe. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `clientela` | Cumple |
| `test_el_pedido_parcial_devuelve_solo_la_tabla` | El pedido parcial devuelve solo la tabla | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `clientela` | Cumple |
| `test_solo_el_administrador_consulta_los_clientes` | RNF-03: el control es del servidor, no de que el menú no muestre el enlace. | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client`; `rol_sin_permiso` — 2 casos | Cumple |
| `test_sin_sesion_redirige_al_login` | Sin sesion redirige al login | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |

### `test_listado_usuarios.py`

> Buscador y filtros de la tabla de usuarios del sistema.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 10; Sistema · caja negra · validación — 1; Sistema · caja negra · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_la_busqueda_filtra_por_nombre` | La busqueda filtra por nombre | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `personal` | Cumple |
| `test_la_busqueda_filtra_por_correo` | La busqueda filtra por correo | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `personal` | Cumple |
| `test_el_filtro_de_rol_deja_solo_ese_rol` | El filtro de rol deja solo ese rol | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `personal` | Cumple |
| `test_el_filtro_de_estado_deja_solo_ese_estado` | El filtro de estado deja solo ese estado | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `personal` | Cumple |
| `test_los_filtros_se_combinan_con_la_busqueda` | Los filtros se combinan con la busqueda | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `personal` | Cumple |
| `test_un_filtro_con_un_valor_invalido_se_ignora` | Un parámetro pisado a mano en la URL no filtra de más ni rompe la vista. | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin`, `personal`; `filtro`, `valor` — 3 casos | Cumple |
| `test_sin_resultados_se_explica_en_la_voz_del_sistema` | Sin resultados se explica en la voz del sistema | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `personal` | Cumple |
| `test_se_informa_cuantos_resultados_hay` | Se informa cuantos resultados hay | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `personal` | Cumple |
| `test_la_fila_del_propio_usuario_esta_marcada` | El Administrador se ve a sí mismo en la tabla: conviene que lo sepa. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `administrador`, `personal` | Cumple |
| `test_los_filtros_siguen_siendo_selects_de_verdad` | El desplegable propio es una mejora sobre el `select`, no un reemplazo. Si el HTML dejara de traer los `select`, la pantalla dejaría de funcionar sin JavaScript y los filtros no viajarían en el envío del formulario. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_pedido_parcial_devuelve_solo_la_tabla` | Es lo que consume el buscador en vivo: el fragmento, no la pantalla. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `personal` | Cumple |
| `test_el_pedido_parcial_tambien_exige_ser_administrador` | El pedido parcial tambien exige ser administrador | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client`, `cajero` | Cumple |

### `test_login.py`

> CU-AUT-INI — Iniciar Sesión.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 7; Sistema · caja gris · funcional — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_login_exitoso_crea_sesion_y_redirige_segun_rol` | Login exitoso crea sesion y redirige segun rol | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`; `rol`, `destino` — 3 casos | Cumple |
| `test_login_exitoso_registra_el_inicio_en_auditoria` | Login exitoso registra el inicio en auditoria | Sistema · caja gris · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_login_acepta_el_correo_sin_distinguir_mayusculas` | Login acepta el correo sin distinguir mayusculas | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_contrasena_incorrecta_no_crea_sesion_y_muestra_mensaje_generico` | Contrasena incorrecta no crea sesion y muestra mensaje generico | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_correo_inexistente_devuelve_exactamente_el_mismo_mensaje` | No debe poder distinguirse "no existe la cuenta" de "erraste la clave". | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_cuenta_inactiva_no_crea_sesion` | Cuenta inactiva no crea sesion | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_cuenta_inactiva_no_se_revela_a_quien_no_sabe_la_contrasena` | Sin la contraseña correcta, una cuenta inactiva responde como cualquier otra. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_usuario_con_sesion_activa_no_ve_la_pantalla_de_login` | Precondición del CU: no tiene una sesión vigente en el dispositivo. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |

### `test_logout.py`

> CU-AUT-FIN — Cerrar Sesión.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · validación — 1; Integración · caja negra · funcional — 1; Sistema · caja gris · funcional — 1; Sistema · caja negra · funcional — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_logout_invalida_la_sesion_actual` | Logout invalida la sesion actual | Sistema · caja negra · validación | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_logout_no_afecta_las_sesiones_de_otros_dispositivos` | Logout no afecta las sesiones de otros dispositivos | Integración · caja negra · funcional | Base de datos | `cliente` | Cumple |
| `test_logout_queda_registrado_en_auditoria` | Logout queda registrado en auditoria | Sistema · caja gris · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_logout_no_acepta_get` | Un GET no puede desloguear: evita que un enlace externo cierre la sesión. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |

### `test_models.py`

> El modelo de usuario: las garantías que la base sostiene por su cuenta. Se prueban acá y no en los tests de las pantallas porque son invariantes del modelo: valen para el alta desde el backoffice, para el registro de un cliente y para cualquier `create()` que se escriba mañana en un comando.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Integración · caja gris · funcional — 4.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_crear_usuario_con_rol_por_defecto` | Crear usuario con rol por defecto | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_la_contrasena_se_guarda_hasheada` | La contrasena se guarda hasheada | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_correo_se_normaliza_a_minusculas` | El correo se normaliza a minusculas | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_no_permite_dos_cuentas_con_el_mismo_correo` | No permite dos cuentas con el mismo correo | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |

### `test_modificacion_usuario.py`

> CU-USR-MOD — Modificar Usuario del Sistema.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 6; Sistema · caja negra · funcional — 5; Sistema · caja gris · validación — 2; Sistema · caja negra · validación — 1; Sistema · caja gris · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_formulario_precarga_los_datos_actuales` | El formulario precarga los datos actuales | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `cajero` | Cumple |
| `test_modificar_datos_sin_tocar_el_rol_no_invalida_la_sesion` | Modificar datos sin tocar el rol no invalida la sesion | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `cajero` | Cumple |
| `test_modificar_el_rol_invalida_la_sesion_del_usuario` | Modificar el rol invalida la sesion del usuario | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `cajero` | Cumple |
| `test_modificar_el_rol_no_toca_las_sesiones_de_los_demas` | Modificar el rol no toca las sesiones de los demas | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `cajero`, `cliente` | Cumple |
| `test_no_se_le_puede_quitar_el_rol_al_unico_administrador_activo` | No se le puede quitar el rol al unico administrador activo | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |
| `test_se_le_puede_quitar_el_rol_si_queda_otro_administrador_activo` | Se le puede quitar el rol si queda otro administrador activo | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_cambiarse_el_rol_a_uno_mismo_cierra_la_propia_sesion` | La sesión invalidada puede ser la del propio Administrador que edita. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |
| `test_un_correo_ya_usado_por_otra_cuenta_no_actualiza_nada` | Un correo ya usado por otra cuenta no actualiza nada | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `cajero` | Cumple |
| `test_conservar_el_propio_correo_no_es_un_conflicto` | Conservar el propio correo no es un conflicto | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `cajero` | Cumple |
| `test_la_auditoria_registra_valores_anteriores_y_nuevos` | La auditoria registra valores anteriores y nuevos | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `cajero` | Cumple |
| `test_guardar_sin_cambios_no_ensucia_la_auditoria` | Guardar sin cambios no ensucia la auditoria | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `cajero` | Cumple |
| `test_regenerar_el_enlace_de_activacion_invalida_el_anterior` | Regenerar el enlace de activacion invalida el anterior | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_regenerar_el_enlace_queda_en_auditoria` | Regenerar el enlace queda en auditoria | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_no_se_regenera_el_enlace_de_una_cuenta_ya_activa` | No se regenera el enlace de una cuenta ya activa | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `cajero` | Cumple |
| `test_solo_el_administrador_puede_editar` | Solo el administrador puede editar | Sistema · caja gris · control de acceso | Pantalla (HTTP) | `client`, `cajero` | Cumple |

### `test_pantallas_backoffice.py`

> Chequeos de las pantallas del Módulo 13 que no son de lógica de negocio.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_ninguna_pantalla_filtra_comentarios_del_template` | `{# ... #}` solo comenta una línea: si ocupa más, Django lo imprime. Es un error fácil de reintroducir y que solo se ve abriendo la pantalla, así que queda cubierto acá. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `cajero` | Cumple |

### `test_reactivacion_usuario.py`

> Reactivación y congelamiento de una cuenta dada de baja. Agregados al CU, documentados en `/docs/modulos/gestion_usuarios.md`.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 7; Sistema · caja gris · validación — 2; Sistema · caja negra · funcional — 2; Sistema · caja gris · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_la_pantalla_pide_confirmacion_explicita` | La pantalla pide confirmacion explicita | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `dado_de_baja` | Cumple |
| `test_reactivar_deja_la_cuenta_pendiente_y_manda_enlace` | Reactivar deja la cuenta pendiente y manda enlace | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `dado_de_baja` | Cumple |
| `test_reactivar_invalida_la_contrasena_anterior` | El acceso no vuelve con la credencial vieja: hay que elegir una nueva. | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `dado_de_baja` | Cumple |
| `test_una_cuenta_reactivada_no_puede_entrar_hasta_usar_el_enlace` | Una cuenta reactivada no puede entrar hasta usar el enlace | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `dado_de_baja` | Cumple |
| `test_la_cuenta_reactivada_conserva_su_rol_y_su_historial` | La cuenta reactivada conserva su rol y su historial | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `dado_de_baja` | Cumple |
| `test_la_reactivacion_queda_en_auditoria` | La reactivacion queda en auditoria | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `dado_de_baja`, `administrador` | Cumple |
| `test_no_se_reactiva_una_cuenta_que_no_esta_de_baja` | No se reactiva una cuenta que no esta de baja | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `cajero` | Cumple |
| `test_solo_el_administrador_puede_reactivar` | Solo el administrador puede reactivar | Sistema · caja gris · control de acceso | Pantalla (HTTP) | `client`, `cajero`, `dado_de_baja` | Cumple |
| `test_no_se_puede_abrir_la_edicion_de_una_cuenta_de_baja` | No se puede abrir la edicion de una cuenta de baja | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `dado_de_baja` | Cumple |
| `test_un_post_directo_tampoco_modifica_una_cuenta_de_baja` | RNF-03: esconder el botón no es una restricción; el chequeo va en la vista. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `dado_de_baja` | Cumple |
| `test_la_tabla_ofrece_reactivar_y_no_editar` | La tabla ofrece reactivar y no editar | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `dado_de_baja` | Cumple |
| `test_una_cuenta_reactivada_no_se_puede_eliminar` | Quedó Pendiente, pero tiene historial: el borrado físico no corresponde. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `dado_de_baja` | Cumple |

### `test_recuperar_contrasena.py`

> CU-AUT-REC — Recuperar Contraseña.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 6; Sistema · caja gris · funcional — 3; Sistema · caja gris · validación — 2; Integración · caja negra · validación — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_correo_existente_e_inexistente_devuelven_el_mismo_mensaje` | Correo existente e inexistente devuelven el mismo mensaje | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_solo_se_envia_correo_a_una_cuenta_real` | Solo se envia correo a una cuenta real | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_una_cuenta_inactiva_no_recibe_enlace` | Una cuenta inactiva no recibe enlace | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_el_correo_incluye_un_enlace_utilizable` | El correo incluye un enlace utilizable | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_un_token_valido_permite_cambiar_la_contrasena` | Un token valido permite cambiar la contrasena | Sistema · caja gris · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_un_token_expirado_es_rechazado` | Un token expirado es rechazado | Sistema · caja gris · validación | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_un_token_vigente_a_los_29_minutos_sigue_sirviendo` | Un token vigente a los 29 minutos sigue sirviendo | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_un_token_ya_usado_no_puede_reutilizarse` | Un token ya usado no puede reutilizarse | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_contrasenas_que_no_coinciden_no_cambian_nada_y_no_queman_el_token` | Contrasenas que no coinciden no cambian nada y no queman el token | Sistema · caja gris · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_contrasena_debil_es_rechazada_con_el_motivo` | Contrasena debil es rechazada con el motivo | Sistema · caja gris · validación | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_el_cambio_invalida_todas_las_sesiones_activas` | El cambio invalida todas las sesiones activas | Integración · caja negra · validación | Base de datos | `cliente` | Cumple |
| `test_el_cambio_queda_registrado_en_auditoria` | El cambio queda registrado en auditoria | Sistema · caja gris · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |

### `test_registro_cliente.py`

> CU-CLI-ALT — Registrar Cuenta de Cliente.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 17; Sistema · caja gris · validación — 12; Sistema · caja negra · funcional — 10; Sistema · caja negra · validación — 6; Sistema · caja gris · idempotencia — 1; Sistema · caja negra · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_registro_crea_una_cuenta_de_cliente_activa` | El registro crea una cuenta de cliente activa | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_la_contrasena_se_guarda_hasheada` | RNF-04: en la base no puede quedar la contraseña en texto plano. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_el_registro_inicia_sesion_automaticamente` | El registro inicia sesion automaticamente | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_el_registro_envia_el_correo_de_bienvenida` | El registro envia el correo de bienvenida | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_el_registro_queda_en_el_log_de_auditoria` | El registro queda en el log de auditoria | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_el_inicio_de_sesion_automatico_tambien_se_audita` | El `login()` de la vista pasa por la misma signal que el CU-AUT-INI. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_los_datos_opcionales_se_guardan` | Los datos opcionales se guardan | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_los_datos_opcionales_pueden_quedar_vacios` | Los datos opcionales pueden quedar vacios | Sistema · caja gris · validación | Pantalla (HTTP) | `client` | Cumple |
| `test_la_aceptacion_de_la_politica_queda_persistida` | La aceptacion de la politica queda persistida | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_sin_aceptar_la_politica_no_se_crea_la_cuenta` | Sin aceptar la politica no se crea la cuenta | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_un_correo_ya_registrado_es_rechazado_y_ofrece_recuperar_la_contrasena` | Un correo ya registrado es rechazado y ofrece recuperar la contrasena | Sistema · caja gris · validación | Pantalla (HTTP) | `client` | Cumple |
| `test_el_correo_repetido_se_detecta_aunque_cambie_la_capitalizacion` | El modelo normaliza a minúsculas: "Lucia@" y "lucia@" son la misma cuenta. | Sistema · caja gris · idempotencia | Pantalla (HTTP) | `client` | Cumple |
| `test_contrasenas_distintas_conservan_los_datos_ya_ingresados` | Contrasenas distintas conservan los datos ya ingresados | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_una_contrasena_que_no_cumple_los_requisitos_minimos_es_rechazada` | Los requisitos los ponen los `AUTH_PASSWORD_VALIDATORS`, no reglas propias. | Sistema · caja gris · validación | Pantalla (HTTP) | `client` | Cumple |
| `test_un_campo_obligatorio_vacio_no_crea_la_cuenta` | Un campo obligatorio vacio no crea la cuenta | Sistema · caja gris · validación | Pantalla (HTTP) | `client` | Cumple |
| `test_un_nombre_de_menos_de_tres_letras_es_rechazado` | Se cuentan letras, no caracteres: "A.B" tiene tres pero no es un nombre. | Sistema · caja gris · validación | Pantalla (HTTP) | `client`; `nombre` — 4 casos | Cumple |
| `test_un_nombre_con_caracteres_especiales_es_rechazado` | Un nombre con caracteres especiales es rechazado | Sistema · caja gris · validación | Pantalla (HTTP) | `client`; `nombre` — 6 casos | Cumple |
| `test_los_nombres_reales_se_aceptan` | La validación no puede dejar afuera apellidos que existen de verdad. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client`; `nombre` — 6 casos | Cumple |
| `test_los_espacios_de_mas_se_limpian_antes_de_validar` | Los espacios de mas se limpian antes de validar | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_el_pais_viene_predeterminado_en_argentina` | El pais viene predeterminado en argentina | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_los_codigos_de_pais_salen_del_catalogo_externo` | No hay una lista escrita a mano: viene del servicio (o de su respaldo). | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_un_codigo_de_pais_fuera_del_catalogo_es_rechazado` | Un codigo de pais fuera del catalogo es rechazado | Sistema · caja negra · validación | Pantalla (HTTP) | `client` | Cumple |
| `test_un_numero_de_telefono_invalido_es_rechazado` | El caso que motivó desarmar el teléfono: un "-1" no es un teléfono. | Sistema · caja gris · validación | Pantalla (HTTP) | `client`; `numero` — 6 casos | Cumple |
| `test_un_codigo_de_area_invalido_es_rechazado` | Un codigo de area invalido es rechazado | Sistema · caja negra · validación | Pantalla (HTTP) | `client`; `area` — 4 casos | Cumple |
| `test_un_codigo_de_pais_invalido_es_rechazado` | Un codigo de pais invalido es rechazado | Sistema · caja negra · validación | Pantalla (HTTP) | `client`; `pais` — 4 casos | Cumple |
| `test_el_telefono_se_normaliza_en_vez_de_rechazarse` | El telefono se normaliza en vez de rechazarse | Sistema · caja gris · validación | Pantalla (HTTP) | `client`; `area_tipeada`, `numero_tipeado` — 4 casos | Cumple |
| `test_un_numero_sin_codigo_de_area_es_rechazado` | Medio teléfono no se puede discar: o van las dos partes o ninguna. | Sistema · caja negra · validación | Pantalla (HTTP) | `client` | Cumple |
| `test_un_codigo_de_area_sin_numero_es_rechazado` | Un codigo de area sin numero es rechazado | Sistema · caja negra · validación | Pantalla (HTTP) | `client` | Cumple |
| `test_el_pais_vacio_vuelve_al_predeterminado` | El pais vacio vuelve al predeterminado | Sistema · caja gris · validación | Pantalla (HTTP) | `client` | Cumple |
| `test_la_direccion_completa_se_guarda_con_todos_sus_campos` | La direccion completa se guarda con todos sus campos | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_una_direccion_incompleta_es_rechazada` | Sin calle, localidad, código postal o provincia no se puede despachar nada. | Sistema · caja gris · validación | Pantalla (HTTP) | `client`; `faltante` — 4 casos | Cumple |
| `test_los_campos_accesorios_solos_tampoco_alcanzan` | Un depto sin dirección no es una dirección. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_un_codigo_postal_invalido_es_rechazado` | Un codigo postal invalido es rechazado | Sistema · caja negra · validación | Pantalla (HTTP) | `client`; `codigo` — 4 casos | Cumple |
| `test_el_codigo_postal_se_guarda_en_mayusculas` | El codigo postal se guarda en mayusculas | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_una_provincia_inventada_es_rechazada` | El desplegable no es la restricción: el servidor valida contra el catálogo. | Sistema · caja gris · validación | Pantalla (HTTP) | `client` | Cumple |
| `test_la_provincia_arranca_sin_elegir` | La provincia arranca sin elegir | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_las_provincias_del_formulario_salen_del_catalogo_oficial` | No hay una lista escrita a mano: viene de georef (o de su respaldo). | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_el_registro_funciona_aunque_la_api_de_provincias_este_caida` | La fixture `sin_red` ya simula la caída: esto verifica que no bloquea. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_un_cpa_de_otra_provincia_es_rechazado` | La N de N3300ABC es de Misiones: con Corrientes elegida, algo está mal. | Sistema · caja gris · validación | Pantalla (HTTP) | `client` | Cumple |
| `test_el_codigo_postal_de_cuatro_digitos_no_se_contradice` | Sin letra no declara provincia, así que no hay nada que cruzar. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_un_cpa_que_coincide_con_la_provincia_pasa` | Un cpa que coincide con la provincia pasa | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_un_campo_con_error_queda_marcado_para_el_lector_de_pantalla` | El borde rojo no existe para quien no ve la pantalla. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_un_campo_sin_error_no_lleva_la_marca` | Un campo sin error no lleva la marca | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_el_formulario_es_de_acceso_publico` | El formulario es de acceso publico | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client` | Cumple |
| `test_quien_ya_tiene_sesion_no_vuelve_al_registro` | Precondición del CU: el registro es para quien no tiene sesión previa. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |
| `test_el_rol_no_se_puede_elegir_desde_el_formulario` | El rol lo fija el servidor: un POST con `rol` no puede escalar permisos. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_el_estado_no_se_puede_elegir_desde_el_formulario` | El estado no se puede elegir desde el formulario | Sistema · caja gris · funcional | Pantalla (HTTP) | `client` | Cumple |

### `test_sesion.py`

> CU-AUT-INI, comportamiento adicional: expiración por inactividad y renovación.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 5.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_login_avisa_cuando_se_llega_por_sesion_expirada` | El login avisa cuando se llega por sesion expirada | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_el_login_normal_no_muestra_el_aviso_de_expiracion` | El login normal no muestra el aviso de expiracion | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_renovar_extiende_la_sesion_del_usuario_autenticado` | Renovar extiende la sesion del usuario autenticado | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cliente`, `settings` | Cumple |
| `test_renovar_sin_sesion_redirige_al_login` | Renovar sin sesion redirige al login | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_renovar_no_acepta_get` | Renovar no acepta get | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cliente` | Cumple |


## Catálogo — `apps/catalog`

### `test_alta_lote_importado.py`

> Alta de lote de material editorial importado.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 16; Sistema · caja gris · validación — 3; Sistema · caja negra · funcional — 2.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_cre_y_el_margen_quedan_congelados_en_el_lote` | Postcondición del CU: la auditoría tiene que poder decir con qué números se fijaron estos precios, y los dos cambian con el tiempo. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |
| `test_el_precio_final_sale_de_la_formula_de_rf_10` | `C × (1 + R) × (1 + M)` = 1000 × 1,1 × 1,4 = 1540. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |
| `test_el_cre_del_lote_se_aplica_a_todos_los_items` | El cre del lote se aplica a todos los items | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |
| `test_el_costo_en_origen_es_obligatorio` | El costo en origen es obligatorio | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |
| `test_la_calculadora_de_envio_es_obligatoria` | Sin los dos totales no hay CRE, y sin CRE no hay precio. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `editorial`, `tipo` | Cumple |
| `test_editar_el_precio_final_sin_confirmar_muestra_la_advertencia` | El CU pide que el Administrador confirme. El chequeo va del lado del servidor: un cartel de JavaScript esquivado no debería poder romper el vínculo con el margen global. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |
| `test_editar_el_precio_final_confirmado_marca_precio_manual` | Editar el precio final confirmado marca precio manual | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |
| `test_el_precio_base_no_cambia_al_editar_el_precio_final` | RF-10: el precio base se almacena siempre y nunca se deriva del final. Es lo que permite recalcular ante un cambio de margen sin volver a pedir los datos del lote. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |
| `test_confirmar_el_precio_calculado_no_lo_marca_como_manual` | Escribir el mismo número que calculó el sistema no es editarlo. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |
| `test_un_lote_sin_ediciones_deja_todos_los_productos_alcanzables_por_la_propagacion` | Para que el recálculo de CU-PVP-MAR los alcance a todos por defecto. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |
| `test_la_cotizacion_convierte_el_costo_en_origen_a_pesos` | La cotizacion convierte el costo en origen a pesos | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |
| `test_un_lote_en_pesos_se_guarda_con_cotizacion_uno` | Se guarda el 1 en vez de dejarlo en nulo: así el cálculo de cualquier ítem se reconstruye igual, con conversión o sin ella. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |
| `test_una_moneda_fuera_del_catalogo_es_rechazada` | El negocio importa en tres monedas y el desplegable ofrece esas tres. El chequeo vive en el servidor: el desplegable de la pantalla no es una restricción, es una comodidad. | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `editorial`; `moneda` — 4 casos | Cumple |
| `test_una_moneda_extranjera_sin_cotizacion_es_rechazada` | Una moneda extranjera sin cotizacion es rechazada | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |
| `test_una_cotizacion_sobre_un_lote_en_pesos_es_rechazada` | Se rechaza en vez de ignorarla: descartar en silencio un número que alguien escribió es la forma más rápida de que un precio salga mal sin que nadie se entere. | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |
| `test_la_pantalla_ofrece_la_cotizacion_de_referencia` | La sugerencia se ofrece; el que decide es el Administrador. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |
| `test_el_estado_sigue_la_misma_logica_que_cu_01` | El estado sigue la misma logica que cu 01 | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |
| `test_un_duplicado_se_excluye_y_el_resto_se_registra` | Un duplicado se excluye y el resto se registra | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `editorial`, `tipo` | Cumple |
| `test_dos_importados_sin_formato_del_mismo_tomo_chocan_entre_si` | En SQL dos nulos no son iguales, así que sin el `Coalesce` de la restricción el mismo tomo entraría dos veces sin que nada lo impida. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `editorial`, `tipo` | Cumple |
| `test_la_auditoria_conserva_el_cre_y_el_margen_usados` | La auditoria conserva el cre y el margen usados | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |
| `test_el_resumen_muestra_el_desglose_del_lote` | El resumen muestra el desglose del lote | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `editorial` | Cumple |

### `test_alta_lote_nacional.py`

> Alta de lote de material editorial nacional.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 34; Sistema · caja negra · funcional — 5; Sistema · caja blanca · funcional — 1; Sistema · caja gris · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_los_items_heredan_la_clasificacion_y_el_precio_de_la_cabecera` | Los items heredan la clasificacion y el precio de la cabecera | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_con_la_cabecera_puesta_manda_la_cabecera_aunque_el_item_declare_otra_cosa` | El ítem llega bloqueado en la pantalla, y el servidor sostiene la regla. Un `select` deshabilitado no se envía, pero nada impide mandar el campo a mano: si el servidor no ignorara ese valor, el bloqueo de la pantalla sería decorativo. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_item_desbloqueado_declara_su_propia_clasificacion` | Un item desbloqueado declara su propia clasificacion | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_desbloquear_un_item_convierte_el_lote_en_mixto` | La cabecera deja de describir al lote, así que se la vacía. Dejarla puesta haría que el resumen y la auditoría dijeran que todo el lote es de una editorial cuando no lo es. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_item_puede_sobrescribir_el_precio_sin_desbloquear_nada` | El precio y el estado siempre se pueden pisar por ítem: lo que el bloqueo protege es la clasificación, no los valores del alta. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_el_precio_editado_a_mano_queda_excluido_de_la_propagacion` | Sin la marca, un cambio de la tabla de precios le pisaría después una decisión que alguien tomó a propósito. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_el_producto_queda_vinculado_a_su_combinacion_de_la_tabla` | El precio de un nacional es un vínculo, no una foto (RF-11). | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_en_un_lote_mixto_cada_item_declara_sus_propios_datos` | En un lote mixto cada item declara sus propios datos | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_en_un_lote_mixto_falta_la_editorial_del_item` | En un lote mixto falta la editorial del item | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_en_un_lote_mixto_falta_el_tipo_del_item` | En un lote mixto falta el tipo del item | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_sin_precio_de_referencia_el_alta_pide_el_precio_a_mano` | Que la combinación no esté en la tabla no bloquea el alta: solo obliga a escribir el precio. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_formato_es_obligatorio_para_un_tipo_que_lo_usa` | El formato es obligatorio para un tipo que lo usa | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_tipo_que_no_usa_formato_no_lo_pide_ni_lo_guarda` | Un artbook no se clasifica por tamaño: si viene un formato, se descarta. Se descarta y no se rechaza porque la pantalla esconde el campo al cambiar de tipo y el valor puede haber quedado de la selección anterior. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_comic_se_da_de_alta_sin_declarar_ninguna_etiqueta` | Las etiquetas describen, no identifican: un tomo sin ninguna es un producto completo, solo más difícil de encontrar. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_las_etiquetas_de_la_cabecera_las_heredan_todos_los_items` | Es el motivo por el que viven en la cabecera: veinte tomos de la misma serie comparten franquicia y género igual que comparten editorial. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_la_cabecera_dibuja_las_etiquetas_agrupadas` | Si el campo no llega a la pantalla, el formulario lo acepta igual pero nadie puede usarlo: es el tipo de hueco que solo se ve mirando el HTML. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_item_puede_sumar_etiquetas_propias` | Un item puede sumar etiquetas propias | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_declarar_la_misma_etiqueta_arriba_y_abajo_no_la_duplica` | Declarar la misma etiqueta arriba y abajo no la duplica | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_una_etiqueta_desactivada_no_se_puede_elegir` | Una etiqueta desactivada no se puede elegir | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_item_se_puede_marcar_como_solo_para_adultos` | No es una etiqueta: cambia lo que el sistema hace con el producto, así que es un campo y la tienda va a preguntar por él, no por una cadena. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_por_defecto_un_producto_no_es_solo_para_adultos` | Por defecto un producto no es solo para adultos | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_el_precio_depende_de_los_tres_campos` | La misma editorial y el mismo tipo, en dos tamaños, valen distinto. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_con_fecha_de_llegada_el_producto_nace_en_pre_venta` | Con fecha de llegada el producto nace en pre venta | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_sin_fecha_de_llegada_el_producto_nace_activo` | Sin fecha de llegada el producto nace activo | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_el_item_puede_sobrescribir_el_estado_de_la_cabecera` | El item puede sobrescribir el estado de la cabecera | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_item_duplicado_se_excluye_y_los_demas_se_crean` | Un duplicado no es un fallo del lote, es una exclusión esperada. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_el_duplicado_se_detecta_sin_distinguir_mayusculas` | El duplicado se detecta sin distinguir mayusculas | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_el_mismo_tomo_en_otro_formato_no_es_duplicado` | Dos ediciones del mismo tomo son dos productos: distinto precio, distinto stock y las dos pueden estar en la góndola al mismo tiempo. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_una_editorial_distinta_no_es_duplicado` | Una editorial distinta no es duplicado | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_resumen_informa_la_colision_con_enlace_a_la_ficha` | El resumen informa la colision con enlace a la ficha | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_la_confirmacion_genera_una_unica_entrada_de_auditoria` | Una entrada consolidada por lote, no una por ítem. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `administrador`, `referencia` | Cumple |
| `test_la_auditoria_apunta_al_lote_y_no_a_una_cuenta` | La auditoria apunta al lote y no a una cuenta | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_fallo_tecnico_no_deja_productos_a_medio_crear` | RNF-06: la creación del lote es atómica. | Sistema · caja blanca · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_item_sin_stock_declarado_nace_en_cero` | El sistema no inventa unidades que nadie contó. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_el_stock_declarado_se_respeta` | El stock declarado se respeta | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_sin_portada_el_producto_queda_marcado_como_imagen_pendiente` | Sin portada el producto queda marcado como imagen pendiente | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_item_sin_titulo_no_se_registra` | Un item sin titulo no se registra | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_lote_sin_ningun_item_no_se_guarda` | Un lote sin ningun item no se guarda | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_lote_de_un_solo_item_es_valido` | Un lote de un solo item es valido | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_solo_el_administrador_da_de_alta_lotes` | Solo el administrador da de alta lotes | Sistema · caja gris · control de acceso | Pantalla (HTTP) | `client`, `referencia`; `rol_sin_permiso` — 2 casos | Cumple |
| `test_sin_sesion_el_alta_redirige_al_login` | Sin sesion el alta redirige al login | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |

### `test_alta_no_editorial.py`

> CU-CAT-ALT — Registrar Alta de Producto No Editorial. Es el alta del rubro secundario del negocio: TCG, figuras, merchandising e insumos. De a uno y no por lote, a diferencia del alta editorial — cinco artículos no editoriales no comparten nada entre sí. Lo que más se prueba acá es el duplicado, porque es donde este CU se aparta de la fuente. CU-CAT-ALT E2 lo trata como **bloqueo**: "el producto…

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 15; Sistema · caja negra · funcional — 8; Sistema · caja gris · validación — 2; Sistema · caja gris · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_alta_crea_el_producto` | El alta crea el producto | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_nace_activo_y_con_su_codigo` | CU-CAT-ALT asigna exclusivamente Activo, y todo producto nace identificado. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_el_codigo_escrito_a_mano_se_respeta` | CU-CAT-ALT paso 3 lista el "código de producto interno" entre los opcionales. Nuestro campo es el mismo, híbrido: se escribe o se genera. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_los_opcionales_se_guardan` | Los opcionales se guardan | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_la_marca_es_opcional` | Es el caso que reescribió el modelo: hay merch genérico y no oficial. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_la_imagen_no_bloquea_el_alta` | CU-CAT-ALT paso 2 la lista entre los obligatorios; se unifica con A5 de `alta_editorial.md`, donde la portada tampoco bloquea. Es el mismo campo del mismo modelo y la misma pantalla de inventario. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_los_obligatorios_bloquean_el_alta` | E1: se resaltan, el formulario permanece abierto y no se registra nada. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `categoria`; `faltante` — 4 casos | Cumple |
| `test_el_formulario_conserva_lo_ya_escrito` | E1 lo pide explícitamente: no se reinicia vacío. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_una_categoria_editorial_se_rechaza` | El recorte del desplegable es comodidad; la validación es del servidor. | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_formulario_no_ofrece_el_estado` | No hay campo que mandar: el sistema asigna Activo. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_un_precio_desmesurado_se_rechaza` | Un precio desmesurado se rechaza | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_el_duplicado_no_se_registra_sin_confirmar` | El duplicado no se registra sin confirmar | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_el_duplicado_se_informa_con_enlace_a_la_ficha_existente` | E2 pide el enlace, no solo el aviso: sin él hay que ir a buscarlo a mano. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_confirmando_el_duplicado_el_alta_procede` | Dos llaveros de Naruto de proveedores distintos son dos productos. Con la clave dura, el Administrador tendría que inventarle un nombre al segundo. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_los_dos_duplicados_tienen_códigos_distintos` | Es lo que hace posible convivir: la identidad nunca fue el nombre. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_el_mismo_nombre_en_otra_categoria_no_es_duplicado` | La clave del CU es nombre **+ categoría**: un llavero y una carta con el mismo nombre no chocan. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_la_confirmacion_no_se_ofrece_cuando_no_hay_choque` | Ofrecerla siempre la volvería un clic automático, que es lo mismo que no tenerla — el mismo motivo por el que la confirmación de cambio de correo no aparece en el alta de proveedor. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_el_duplicado_ignora_mayusculas_y_espacios` | El duplicado ignora mayusculas y espacios | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_la_consulta_encuentra_el_choque_exacto` | La consulta encuentra el choque exacto | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_la_consulta_avisa_de_parecidos_en_otras_categorias` | Que exista en Merchandising es información útil aunque se lo esté cargando en TCG: puede ser el aviso de que la categoría es la equivocada. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_la_consulta_no_devuelve_nada_con_un_nombre_muy_corto` | Con una letra, todo el catálogo es un parecido. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_la_consulta_no_valida_nada` | Se puede esquivar, ignorar o no llegar nunca: el duplicado se informa igual al guardar. Por eso el control vive en el formulario. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `categoria` | Cumple |
| `test_el_alta_queda_auditada` | La postcondición pide fecha, hora y datos del producto creado. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `categoria`, `administrador` | Cumple |
| `test_el_alta_es_exclusiva_del_administrador` | El Cajero consulta el inventario (CU-CAT-INV) pero no da de alta nada. | Sistema · caja gris · control de acceso | Pantalla (HTTP) | `client`, `categoria`; `rol` — 2 casos | Cumple |
| `test_el_inventario_enlaza_el_alta` | El inventario enlaza el alta | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_sin_categorias_activas_la_pantalla_lo_dice` | Sin ninguna, el desplegable aparecería vacío y sin explicar por qué. Las cuatro categorías de CU-CAT-ALT vienen sembradas por la migración, así que para llegar a este caso hay que desactivarlas — que es exactamente lo que podría pasar en… | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |

### `test_asistencias_de_carga.py`

> Las ayudas que la pantalla de carga pide al servidor mientras se escribe. Son dos: la consulta del precio de referencia —que es lo que hace que el precio se pre-complete al elegir la clasificación— y el alta de editorial sin abandonar el lote. Las dos existen para no perder lo escrito: mandar a otra pantalla a quien tiene medio lote cargado termina en un lote cargado mal "para no volver a…

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 4; Sistema · caja negra · funcional — 3; Sistema · caja negra · control de acceso — 2; Sistema · caja negra · validación — 1; Sistema · caja gris · idempotencia — 1; Sistema · caja gris · validación — 1; Sistema · caja gris · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_devuelve_el_precio_de_la_combinacion` | Devuelve el precio de la combinacion | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_una_combinacion_sin_precio_devuelve_nulo` | Una combinacion sin precio devuelve nulo | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_cambiar_solo_el_formato_cambia_el_precio` | Es la razón de ser de la consulta: el tamaño es lo que fija el precio. | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_parametro_invalido_no_rompe_la_consulta` | Un parametro invalido no rompe la consulta | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin`; `basura` — 4 casos | Cumple |
| `test_la_consulta_de_precios_no_se_abre_sin_ser_administrador` | La consulta de precios no se abre sin ser administrador | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client`, `cajero` | Cumple |
| `test_crea_la_editorial_y_devuelve_su_identificador` | Crea la editorial y devuelve su identificador | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_rapida_normaliza_igual_que_la_pantalla_completa` | Los dos caminos crean lo mismo, así que usan el mismo formulario: si tuvieran reglas distintas, el atajo sería la puerta para meter duplicados. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_rapida_rechaza_una_editorial_repetida` | El alta rapida rechaza una editorial repetida | Sistema · caja gris · idempotencia | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_rapida_rechaza_un_nombre_vacio` | El alta rapida rechaza un nombre vacio | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_rapida_queda_auditada` | El alta rapida queda auditada | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |
| `test_la_editorial_nueva_se_puede_usar_enseguida` | Sin esto el atajo no serviría de nada: habría que recargar la pantalla y perder el lote a medio escribir. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_rapida_es_solo_del_administrador` | El alta rapida es solo del administrador | Sistema · caja gris · control de acceso | Pantalla (HTTP) | `client`; `rol_sin_permiso` — 2 casos | Cumple |
| `test_la_pantalla_recibe_las_banderas_de_cada_tipo` | Qué muestra cada tipo viaja como dato y no escrito en el JavaScript: es la misma bandera —y la misma lista de formatos— que lee el servidor, así los dos lados no pueden discrepar. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |

### `test_baja_producto.py`

> CU-CAT-BAJ — Dar de Baja Producto (Editorial o No Editorial), y la reactivación. La fuente da solo la descripción resumida. De ella salen las tres reglas que concentran estos tests: - **La baja es lógica.** La postcondición pide conservar el producto en el inventario interno y en el historial de ventas, así que nunca hay un `DELETE`. - **El informe de impacto va antes de la confirmación.** El CU…

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 12; Sistema · caja negra · funcional — 8; Sistema · caja gris · validación — 2; Integración · caja negra · funcional — 1; Sistema · caja negra · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_la_pantalla_muestra_las_cuatro_categorias` | Las cuatro se declaran aunque ninguna se pueda calcular: agregar cada una después es llenar un hueco y no rediseñar la pantalla. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_lo_que_no_se_puede_calcular_se_dice` | Un cero se leería como "no afecta a nadie". | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_informe_trae_el_stock_y_el_estado` | No son categorías del CU. Van porque son lo único verificable hoy, y sin ellos la decisión se tomaría sin ningún dato del producto. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_hoy_ninguna_categoria_se_puede_determinar` | Hoy ninguna categoria se puede determinar | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_ver_el_informe_no_da_de_baja` | El GET es el informe, no la acción. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_baja_descataloga_el_producto` | La baja descataloga el producto | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_baja_no_borra_nada` | La postcondición pide conservarlo en el inventario y en el historial. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_tambien_se_da_de_baja_un_articulo_no_editorial` | Tambien se da de baja un articulo no editorial | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_producto_en_pre_venta_se_puede_dar_de_baja` | Un producto en pre venta se puede dar de baja | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_baja_queda_registrada` | La baja queda registrada | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |
| `test_una_segunda_baja_no_registra_de_nuevo` | El clásico doble envío. La precondición se vuelve a chequear del lado del servidor y no solo escondiendo el botón. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_titulo_cancelado_por_editorial_no_admite_la_baja` | Es un estado terminal: un tomo cancelado no llega nunca y no se reactiva. Descatalogarlo lo movería a un estado del que sí se vuelve, borrando la única marca de que ese tomo no existe. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_pantalla_lo_dice_antes_de_ofrecer_el_boton` | La pantalla lo dice antes de ofrecer el boton | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_reactivacion_devuelve_el_producto_al_catalogo` | La reactivacion devuelve el producto al catalogo | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_vuelve_con_la_misma_identidad` | Volver a cargarlo no sería equivalente: el código es único e inmutable, así que el producto reingresaría con otra identidad y sin su historial. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_vuelve_a_activo_y_no_al_estado_anterior` | Un producto que estaba en Pre-venta cuando se lo dio de baja lleva meses fuera del catálogo, y su fecha de llegada ya no describe nada. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_reactivacion_queda_registrada` | La reactivacion queda registrada | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_reactivar_algo_que_ya_esta_activo_no_hace_nada` | Reactivar algo que ya esta activo no hace nada | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_ciclo_completo_conserva_el_historial` | Es lo que la baja lógica se propuso conservar: las dos entradas apuntan al mismo producto y la ficha las muestra juntas. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_ofrece_editar_y_dar_de_baja` | La ficha ofrece editar y dar de baja | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_de_un_descatalogado_ofrece_reactivar_y_no_dar_de_baja` | La ficha de un descatalogado ofrece reactivar y no dar de baja | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_del_cajero_no_ofrece_ninguna_accion` | CU-CAT-INV paso 6 se la reserva al Administrador. No se esconde con CSS: no se dibuja, que es lo único que cuenta. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_el_cajero_no_da_de_baja_ni_reactiva` | El cajero no da de baja ni reactiva | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client`; `ruta` — 2 casos | Cumple |
| `test_sin_sesion_redirige_al_login` | Sin sesion redirige al login | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`; `ruta` — 2 casos | Cumple |

### `test_borradores.py`

> La generación de borradores desde una extracción (CU-ALT-NOV pasos 5, 6, 7 y 9). Es el punto del pipeline donde lo que el modelo propuso se cruza contra el catálogo real, y donde se decide qué llega a la cola de revisión de CU-ALT-REV y qué se descarta antes. **Ninguno de estos tests llama al modelo:** se trabaja sobre la extracción ya guardada, que es exactamente como funciona en producción —…

**Tipos en este archivo:** Integración · caja negra · funcional — 27; Integración · caja gris · funcional — 10; Integración · caja negra · idempotencia — 2.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_un_producto_anunciado_se_convierte_en_borrador` | Un producto anunciado se convierte en borrador | Integración · caja gris · funcional | Base de datos | `correo`, `editorial`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_el_borrador_hereda_la_editorial_y_el_rubro_del_proveedor` | El correo no los trae y el modelo no los inventa: los aporta la ficha del proveedor (A7). Sin esto todos los borradores nacerían bloqueados. | Integración · caja negra · funcional | Base de datos | `correo`, `editorial`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_el_stock_inicial_sale_de_la_configuracion` | Es el único stock del sistema que nace con un número que nadie contó, y por eso el de las altas manuales es cero y este no (A3). | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_el_borrador_guarda_de_que_correo_y_proveedor_salio` | El borrador guarda de que correo y proveedor salio | Integración · caja negra · funcional | Base de datos | `correo`, `proveedor`; base de datos (`django_db`) | Cumple |
| `test_un_producto_que_ya_esta_en_el_catalogo_se_omite` | Un producto que ya esta en el catalogo se omite | Integración · caja negra · funcional | Base de datos | `correo`, `editorial`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_el_duplicado_se_detecta_por_isbn_aunque_el_titulo_este_escrito_distinto` | Es justamente lo que la tupla no atrapa: el mismo tomo anunciado como "Berserk edición deluxe vol. 5" en vez de "Berserk Deluxe 5" (A19). | Integración · caja negra · funcional | Base de datos | `correo`, `editorial`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_el_duplicado_se_detecta_por_la_tupla_cuando_no_hay_isbn` | El duplicado se detecta por la tupla cuando no hay isbn | Integración · caja negra · funcional | Base de datos | `correo`, `editorial`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_un_duplicado_no_frena_a_los_demas_productos_del_correo` | Una exclusión esperada no es un fallo transaccional: es la misma regla con la que un duplicado no aborta el alta en lote de CU-ALT-NAC. | Integración · caja negra · funcional | Base de datos | `correo`, `editorial`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_dos_filas_con_el_mismo_isbn_generan_un_solo_borrador` | Son el mismo tomo aunque les hayan escrito el título distinto. | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_se_omite_el_segundo_repetido_y_no_los_dos` | Marcar los dos obligaría a adivinar cuál había que conservar. | Integración · caja negra · idempotencia | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_dos_filas_sin_isbn_y_con_la_misma_tupla_tambien_se_detectan` | Dos filas sin isbn y con la misma tupla tambien se detectan | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_dos_tomos_distintos_de_la_misma_serie_no_son_repetidos` | Comparar solo el título rechazaría el tomo 6 porque ya está el 5. | Integración · caja negra · idempotencia | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_un_producto_sin_titulo_no_llega_a_la_cola` | Un borrador sin título solo se podría rechazar: no hay con qué buscarlo ni con qué mostrarlo. | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_una_fecha_futura_deja_el_borrador_en_pre_venta` | Una fecha futura deja el borrador en pre venta | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_sin_fecha_el_borrador_nace_activo` | Sin fecha el borrador nace activo | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_una_fecha_ya_pasada_no_se_conserva` | Si el material ya llegó, el producto va Activo y sin fecha (A10). Arrastrarla dejaría un activo con fecha de llegada del mes pasado, que no significa nada y ensucia la vigilancia de pre-ventas de CU-ALT-TRA. | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_la_fecha_propia_de_una_fila_pisa_al_periodo_del_correo` | La fecha propia de una fila pisa al periodo del correo | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_una_pre_venta_siempre_tiene_fecha` | A10: sin fecha no se puede vigilar, y el producto quedaría en pre-venta para siempre, invisible para el ciclo que debería sacarlo de ahí. | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_el_formato_anunciado_se_resuelve_contra_el_catalogo` | El formato anunciado se resuelve contra el catalogo | Integración · caja negra · funcional | Base de datos | `correo`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_un_formato_que_no_existe_se_descarta_con_su_reparo` | Un formato que no existe se descarta con su reparo | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_un_formato_que_no_se_ofrece_para_ese_tipo_se_descarta` | A20: un formato enviado a mano que no aplique se rechaza. Que venga del modelo en vez de del navegador no lo hace más confiable. | Integración · caja negra · funcional | Base de datos | `correo`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_en_un_tipo_que_no_usa_formato_no_se_busca_ninguno` | En un artbook el tamaño no fija el precio, así que no hay nada que resolver y tampoco nada que reparar. | Integración · caja negra · funcional | Base de datos | `correo`, `proveedor`; base de datos (`django_db`) | Cumple |
| `test_un_producto_sin_precio_genera_un_borrador_incompleto` | CU-ALT-NOV: los que el modelo identificó pero no pudo completar generan borradores incompletos, y van a la **misma** cola que los demás. | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_el_fallo_parcial_deja_completos_e_incompletos_en_la_misma_cola` | El fallo parcial deja completos e incompletos en la misma cola | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_un_proveedor_sin_editorial_deja_los_borradores_bloqueados` | Una distribuidora trae varias editoriales y el correo no dice cuál: esos borradores sí hay que completarlos a mano, y el estado lo dice. | Integración · caja negra · funcional | Base de datos | `correo`, `proveedor`; base de datos (`django_db`) | Cumple |
| `test_la_confianza_se_guarda_campo_por_campo` | CU-ALT-REV depende de esa granularidad para decidir qué es confirmable en lote: un único nivel global no alcanzaría. | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_una_confianza_baja_nace_sin_revisar` | Es la acción afirmativa que CU-ALT-REV paso 3 exige antes de confirmar. | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_una_confianza_alta_no_exige_revision` | Una confianza alta no exige revision | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_un_nivel_inventado_se_guarda_como_bajo` | Al alza sería peor: un valor raro leído como "alta" haría que un dato dudoso se confirme en lote sin que nadie lo mire. | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_los_reparos_del_producto_viajan_al_borrador` | Los reparos del producto viajan al borrador | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_un_reparo_del_correo_entero_se_copia_a_cada_borrador` | La cola de CU-ALT-REV se mira de a un borrador por vez: un reparo que solo viviera en el correo no lo vería nadie desde ahí. | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_regenerar_reemplaza_los_borradores_abiertos_en_vez_de_duplicarlos` | Regenerar reemplaza los borradores abiertos en vez de duplicarlos | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_regenerar_conserva_los_ya_resueltos` | Son historia: volver a proponerlos sería reabrir una decisión tomada. | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_la_generacion_deja_una_sola_entrada_de_auditoria` | Consolidada por correo, no una por borrador: lo que se quiere reconstruir después es qué produjo este correo, y treinta filas lo esconderían. | Integración · caja gris · funcional | Base de datos | `correo`, `editorial`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_la_auditoria_apunta_al_correo_y_dice_con_que_prompt_se_extrajo` | La auditoria apunta al correo y dice con que prompt se extrajo | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_la_auditoria_registra_al_administrador_cuando_lo_hay` | La auditoria registra al administrador cuando lo hay | Integración · caja gris · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_la_fecha_heredada_del_periodo_no_lleva_confianza` | Salió corriendo el pipeline contra el modelo de verdad, y es grave. Una fila de novedades casi nunca trae fecha propia —el período lo anuncia el correo entero—, así que el modelo declara "baja" correctamente sobre esa celda vacía. Si esa… | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_la_fecha_propia_de_una_fila_si_lleva_confianza` | Ahí sí hay un juicio del modelo que registrar: leyó una celda y dudó. | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_sin_ninguna_fecha_tampoco_se_guarda_confianza_de_fecha` | Un borrador Activo sin fecha no tiene nada que revisar sobre ella: la fecha ni siquiera es bloqueante ahí. | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |

### `test_edicion_producto.py`

> CU-CAT-EDI — Editar Producto (Editorial o No Editorial). La fuente da solo la descripción resumida de este CU: no hay flujo numerado ni excepciones. Lo que se prueba acá sale de ahí y de las decisiones que documenta `catalogo.md`. Tres cosas concentran casi todos los tests, porque son donde el CU se puede romper en silencio: - **El duplicado al editar.** Cambiar el título o el volumen puede…

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 18; Sistema · caja negra · funcional — 6; Sistema · caja gris · validación — 2; Sistema · caja gris · idempotencia — 1; Sistema · caja negra · validación — 1; Sistema · caja negra · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_se_edita_un_tomo` | Se edita un tomo | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_se_edita_un_articulo_no_editorial` | Se edita un articulo no editorial | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_pantalla_de_cada_rubro_ofrece_sus_campos` | Una vista y dos formularios: el tomo pide volumen y el artículo, marca. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_guardar_sin_cambios_no_registra_nada` | No es un error, pero tampoco una modificación: el historial no miente. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_codigo_no_se_puede_cambiar` | Es la identidad del producto y el modelo la declara inmutable. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_estado_no_se_puede_cambiar_desde_la_edicion` | Descatalogar tiene que pasar por el informe de impacto de CU-CAT-BAJ. Un `select` que no se dibuja no impide mandar el valor a mano, así que lo que cuenta es que el servidor lo ignore. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_editar_sin_tocar_la_identidad_no_es_un_duplicado` | El caso que rompería una búsqueda que no se excluya a sí misma: sin esto ningún producto se podría guardar dos veces. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_choque_con_otro_tomo_se_informa` | El choque con otro tomo se informa | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_choque_editorial_no_se_puede_confirmar` | Las dos políticas de duplicado son opuestas, y es correcto. En el rubro editorial la unicidad de una edición la sostiene la base (`producto_editorial_unico_por_clave`), así que **no hay confirmación posible**: la fila no entra de ninguna… | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_choque_no_editorial_si_se_puede_confirmar` | El otro rubro no tiene restricción de base y su duplicado es una advertencia: dos llaveros de Naruto pueden ser dos productos (corrección 21). | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_isbn_repetido_se_detecta` | El ISBN identifica una edición: dos filas con el mismo son la misma. | Sistema · caja gris · idempotencia | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_isbn_con_el_digito_mal_se_rechaza` | Se verifica la aritmética, no una consulta externa. Un dígito mal copiado no falla de forma ruidosa: pasa a identificar algo que no existe. | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_articulo_no_editorial_tambien_se_excluye_a_si_mismo` | El articulo no editorial tambien se excluye a si mismo | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_cambiar_el_precio_exige_confirmacion` | El cartel avisa; el que exige es el servidor. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_confirmado_el_precio_cambia_y_queda_marcado` | Confirmado el precio cambia y queda marcado | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_sin_tocar_el_precio_no_se_pide_nada` | Sin tocar el precio no se pide nada | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_precio_ya_manual_no_vuelve_a_pedir_confirmacion` | No hay vínculo que romper. Volver a preguntar enseña a tildar sin leer. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_precio_desmesurado_se_rechaza` | El precio desmesurado se rechaza | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_modificacion_queda_registrada` | La modificacion queda registrada | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |
| `test_el_registro_guarda_el_par_anterior_y_nuevo` | Solo el estado final no permite reconstruir nada. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_registro_nombra_los_campos_del_rubro` | La marca solo existe en un rubro y el volumen solo en el otro. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_producto_descatalogado_se_edita` | A diferencia de una cuenta de usuario, que se congela al darse de baja: un producto de baja no habilita nada, y mantener sus datos al día es lo que permite reactivarlo. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_pantalla_avisa_que_esta_fuera_del_catalogo` | La pantalla avisa que esta fuera del catalogo | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_cajero_no_edita` | CU-CAT-INV le abre la consulta al Cajero; editar sigue siendo del Administrador. | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client` | Cumple |
| `test_sin_sesion_redirige_al_login` | Sin sesion redirige al login | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_el_tomo_no_ofrece_categorias_del_otro_rubro` | El tomo no ofrece categorias del otro rubro | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_las_etiquetas_se_pueden_cambiar` | Las etiquetas se pueden cambiar | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_tipo_ajeno_al_rubro_se_rechaza` | El recorte del desplegable es comodidad; la validación es del servidor. | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_los_dos_rubros_llegan_a_su_propia_ficha` | La vista baja a la instancia de la hija, que es sobre la que trabaja su formulario. Sin eso, un artículo no editorial se editaría con el formulario del otro rubro. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |

### `test_inventario.py`

> Inventario y ficha de producto: la contraparte de lectura del alta. No son un CU: existen porque E1 exige enlazar a la ficha del producto con el que se chocó, y porque después de cargar un lote hay que poder ver que quedó cargado. Editar y dar de baja son CU-CAT-EDI y CU-CAT-BAJ (Módulo 02).

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 35; Integración · caja negra · funcional — 5; Sistema · caja negra · control de acceso — 3; Sistema · caja negra · validación — 3.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_inventario_lista_los_productos_cargados` | El inventario lista los productos cargados | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_buscador_filtra_por_titulo` | El buscador filtra por titulo | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_los_filtros_ignoran_un_valor_inventado` | Un valor arbitrario en la query string no rompe ni filtra de más. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_filtro_de_estado_funciona` | El filtro de estado funciona | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_filtro_de_etiqueta_funciona` | Las etiquetas no identifican un producto, pero son la forma natural de recortar el catálogo: "todo lo de Marvel" cruza editoriales y tipos, y ninguno de los otros filtros junta eso. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_desplegable_de_etiquetas_solo_ofrece_las_que_filtran_algo` | Es el único eje que puede no aplicarle a ningún producto —ninguna es obligatoria—, así que una etiqueta sin productos ocuparía lugar en el desplegable sin filtrar nada. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_producto_puede_tener_varias_etiquetas` | Es el defecto que la franquicia no podía expresar: Marvel publica cómics de Star Wars, o sea Marvel **y** Star Wars. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_agrupa_las_etiquetas_por_su_grupo` | Sin el grupo, la ficha mostraría "Marvel, Shonen, Edición limitada" como una bolsa. Es el mismo motivo por el que la tienda las necesita agrupadas. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_parcial_devuelve_solo_el_fragmento_de_la_tabla` | El parcial devuelve solo el fragmento de la tabla | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_muestra_los_datos_del_producto` | La ficha muestra los datos del producto | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_marca_la_portada_pendiente` | La ficha marca la portada pendiente | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_de_un_importado_muestra_la_composicion_del_precio` | La ficha de un importado muestra la composicion del precio | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_avisa_cuando_el_precio_es_manual` | La ficha avisa cuando el precio es manual | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_inventario_avisa_cuando_esta_vacio` | El inventario avisa cuando esta vacio | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_avisa_si_falta_configurar_editoriales` | Sin editoriales no se puede dar de alta nada, y la pantalla lo dice. Los tipos vienen sembrados con la instalación; las editoriales las carga el negocio, así que son lo primero que puede faltar. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_con_editoriales_cargadas_no_aparece_el_aviso` | Con editoriales cargadas no aparece el aviso | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_inventario_no_filtra_datos_al_cliente` | 403 sin datos parciales, igual que la tabla de usuarios. **El Cajero sí entra**, y este test dejó de incluirlo en agosto 2026: es actor declarado de CU-CAT-INV y recibía un 403 porque estas pantallas nacieron dentro de Alta Editorial, que… | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client` | Cumple |
| `test_el_cajero_puede_consultar_el_inventario` | CU-CAT-INV lo declara actor: verifica disponibilidad para responder consultas de mostrador. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cajero` | Cumple |
| `test_el_cajero_puede_abrir_la_ficha` | El cajero puede abrir la ficha | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cajero` | Cumple |
| `test_la_ficha_no_se_abre_para_un_cliente` | La ficha no se abre para un cliente | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client` | Cumple |
| `test_las_dos_pantallas_de_alta_se_dibujan_enteras` | Humo: las dos cargan con sus ítems vacíos y con el molde del `<template>`. El molde usa `empty_form`, que se arma por un camino distinto del de los ítems normales: si le faltara un argumento, la pantalla reventaría recién al abrirla y no… | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`; `pantalla` — 2 casos | Cumple |
| `test_cada_item_ofrece_quitarlo_y_duplicarlo` | Contrato con el script de la pantalla: los `data-` son lo que busca. Duplicar existe porque cargar los doce tomos de una serie es el caso normal y es donde más se tipea de más. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_molde_de_items_nuevos_trae_los_mismos_campos_que_los_dibujados` | El ítem que se agrega desde el navegador sale del `empty_form`. Se arma por un camino distinto del de los ítems normales: si le faltara un campo, el ítem agregado se guardaría incompleto y nadie lo notaría. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_de_importados_muestra_la_calculadora_de_envio` | El alta de importados muestra la calculadora de envio | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_de_nacionales_no_muestra_la_calculadora_de_envio` | El alta de nacionales no muestra la calculadora de envio | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_menu_del_administrador_ofrece_el_catalogo` | El menu del administrador ofrece el catalogo | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_no_se_pueden_cargar_dos_productos_con_la_misma_tupla` | La restricción de la base es la que realmente garantiza la unicidad: dos altas simultáneas pasarían las dos validaciones de formulario. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_restriccion_tambien_alcanza_a_los_productos_sin_formato` | En SQL dos nulos no son iguales: sin el `Coalesce` de la restricción, dos importados del mismo tomo entrarían los dos sin que nada lo impida. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`; `sin_formato` — 2 casos | Cumple |
| `test_un_producto_nuevo_no_nace_demorado` | Un producto nuevo no nace demorado | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_indicador_convive_con_pre_venta_y_no_la_reemplaza` | "Demorado" no es un estado: como estado habría que elegir entre perder el "Pre-venta" o inventar un "Pre-venta demorado". | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_producto_activo_no_figura_demorado_aunque_quede_la_bandera` | Leer la bandera sola mostraría "Demorado" en el catálogo sobre algo que ya está en la góndola. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_la_fecha_estimada_pisa_a_la_programada` | Para que la ficha y las notificaciones digan lo mismo sin que cada una elija por su cuenta cuál de las dos mostrar. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_sin_fecha_estimada_vale_la_programada` | Demorado sin fecha nueva es el flujo A1 del CU y un caso normal: el proveedor muchas veces avisa que se atrasa sin saber para cuándo. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_la_vista_por_defecto_muestra_solo_los_activos` | Paso 2: "todos los productos en estado Activo". Un inventario que abre mostrando también lo descatalogado obliga a filtrar antes de poder leerlo. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_estado_vacio_explicito_muestra_todos` | No es lo mismo que no mandar el parámetro: sin él se aplica el valor por defecto. Es la única forma de ver lo descatalogado. | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_los_descatalogados_llevan_su_etiqueta` | Paso 4: se presentan con una etiqueta visual diferenciada. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_orden_por_defecto_es_alfabetico` | Lo pide el paso 2. Antes ordenaba por fecha de alta descendente, que es lo que sirve después de cargar un lote y no lo que pide el CU. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_orden_por_lo_ultimo_cargado_sigue_disponible` | Cambiar el orden por defecto no puede romper el uso que le da Alta Editorial: después de cargar un lote se quiere ver lo recién cargado. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_orden_inventado_cae_en_el_por_defecto` | Un valor de la query string no puede romper la pantalla. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_filtro_de_stock_separa_lo_que_hay_de_lo_que_no` | Es el filtro que más usa el Cajero: la pregunta del mostrador es "¿lo tenés?", no "¿en qué estado está?". | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_sin_filtro_de_stock_se_ven_los_dos` | Sin filtro de stock se ven los dos | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_catalogo_vacio_se_distingue_del_filtro_sin_resultados` | Se rompió al darle un valor por defecto al estado: con un filtro siempre puesto, un catálogo vacío se anunciaba como "ningún resultado", que manda a buscar un problema donde no lo hay. | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_administrador_ve_el_historial_de_modificaciones` | El administrador ve el historial de modificaciones | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_cajero_no_ve_la_informacion_interna` | No se esconde con CSS: no se dibuja. Es lo único que cuenta cuando lo que se protege es información y no una acción. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`, `cajero` | Cumple |
| `test_la_ficha_no_inventa_las_cifras_que_no_puede_calcular` | Un cero acá se leería como "nadie lo tiene reservado", que es la conclusión equivocada para decidir una baja. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_historial_sale_del_log_de_auditoria` | Sale del log genérico, que desde A8 tiene un índice sobre `(objetivo_tipo, objetivo_pk)` puesto exactamente para esta consulta. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |

### `test_isbn.py`

> El ISBN: normalización, dígito verificador y detección de duplicados. La primera mitad no toca la base —igual que `test_precios.py`— porque la aritmética del verificador se prueba mejor con una tabla de casos que con un formulario de por medio.

**Tipos en este archivo:** Unitaria · caja negra · funcional — 4; Integración · caja negra · funcional — 4; Sistema · caja gris · funcional — 4; Unitaria · caja negra · validación — 3; Sistema · caja negra · funcional — 2; Unitaria · caja blanca · frontera — 1; Integración · caja gris · funcional — 1; Sistema · caja gris · validación — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_se_guarda_sin_guiones_ni_espacios` | Se normaliza al guardar y no solo al comparar: si no, el mismo ISBN escrito de dos formas serían dos productos para cualquier consulta que se olvide de normalizar, y la restricción de la base es una de esas. | Unitaria · caja negra · funcional | Unidad | `escrito` — 4 casos | Cumple |
| `test_la_x_final_va_en_mayuscula` | Es un dígito que vale diez, no una letra: en minúscula rompería la comparación exacta. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_un_valor_vacio_se_normaliza_a_cadena_vacia` | Un valor vacio se normaliza a cadena vacia | Unitaria · caja negra · validación | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_un_isbn_bien_formado_pasa` | Un isbn bien formado pasa | Unitaria · caja negra · funcional | Unidad | `valido` — 4 casos | Cumple |
| `test_un_digito_cambiado_se_detecta` | Es el caso que justifica verificar: un ISBN mal copiado no falla de forma ruidosa, pasa a identificar un producto que no existe y el chequeo de duplicados deja de encontrar el que sí. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_un_largo_que_no_es_de_isbn_se_rechaza` | Un largo que no es de isbn se rechaza | Unitaria · caja negra · validación | Unidad | `largo_raro` — 3 casos | Cumple |
| `test_las_letras_donde_no_van_se_rechazan` | Las letras donde no van se rechazan | Unitaria · caja negra · validación | Unidad | `con_letras` — 3 casos | Cumple |
| `test_verificar_no_consulta_nada_externo` | La fixture corta la red. Que esto pase confirma que la verificación es aritmética y no una consulta a una base de ISBN — que es justamente lo que RF-05 excluye del alcance del proyecto. | Unitaria · caja blanca · frontera | Unidad | `sin_red` | Cumple |
| `test_dos_productos_no_pueden_compartir_isbn` | Dos productos no pueden compartir isbn | Integración · caja negra · funcional | Base de datos | base de datos (`django_db`) | Cumple |
| `test_muchos_productos_pueden_no_tener_isbn` | La restricción es parcial a propósito: el "sin ISBN" se representa con la cadena vacía, y una unicidad común los haría chocar a todos entre sí. | Integración · caja gris · funcional | Base de datos | base de datos (`django_db`) | Cumple |
| `test_el_isbn_encuentra_el_duplicado_aunque_el_titulo_este_escrito_distinto` | Es lo que la tupla no atrapa, y el motivo por el que el ISBN va primero: el mismo tomo anunciado con otro nombre sigue siendo el mismo tomo. | Integración · caja negra · funcional | Base de datos | base de datos (`django_db`) | Cumple |
| `test_sin_isbn_se_cae_a_la_tupla_de_siempre` | Sin isbn se cae a la tupla de siempre | Integración · caja negra · funcional | Base de datos | base de datos (`django_db`) | Cumple |
| `test_un_isbn_que_no_esta_no_impide_encontrar_por_la_tupla` | Un producto viejo cargado sin ISBN puede ser el mismo tomo que uno nuevo que sí lo trae: si el ISBN no encuentra nada, todavía hay que mirar la tupla. | Integración · caja negra · funcional | Base de datos | base de datos (`django_db`) | Cumple |
| `test_el_alta_guarda_el_isbn_normalizado` | El alta guarda el isbn normalizado | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia`; base de datos (`django_db`) | Cumple |
| `test_un_isbn_invalido_frena_el_item` | Un isbn invalido frena el item | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `referencia`; base de datos (`django_db`) | Cumple |
| `test_el_isbn_es_opcional` | No todo producto tiene uno, y exigirlo trabaría el alta de todo el material que no responde a estándares editoriales (RF-05). | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia`; base de datos (`django_db`) | Cumple |
| `test_un_item_con_isbn_ya_cargado_se_excluye_del_lote` | E1 de CU-ALT-NAC con el criterio nuevo: el duplicado se excluye e informa, y los demás ítems del lote se cargan igual. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia`; base de datos (`django_db`) | Cumple |
| `test_dos_items_con_el_mismo_isbn_en_el_mismo_envio_se_marcan` | A11 con el criterio nuevo: se marca el segundo, y se detecta aunque los títulos estén escritos distinto. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `referencia`; base de datos (`django_db`) | Cumple |
| `test_la_ficha_muestra_el_isbn` | La ficha muestra el isbn | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`; base de datos (`django_db`) | Cumple |
| `test_dos_ediciones_del_mismo_tomo_tienen_isbn_distinto` | Es la razón por la que el ISBN resuelve lo que A13 resolvía con esfuerzo: el B6 y el Deluxe del mismo volumen son dos ediciones y dos ISBN. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`; base de datos (`django_db`) | Cumple |

### `test_jerarquia_de_producto.py`

> La jerarquía de producto: identidad, rubro y las garantías de la base. Todo lo de acá salió de una pregunta que estaba mal contestada en el modelo: **qué identifica a un producto**. La respuesta vieja mezclaba dos cosas —la identidad de la fila y la detección de duplicados— y por eso `marca` no podía ser opcional: en cuanto un dato descriptivo entra en la clave, todo producto que no lo tenga se…

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Integración · caja negra · funcional — 27; Integración · caja gris · funcional — 5; Integración · caja gris · validación — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_un_producto_nace_con_codigo_aunque_nadie_se_lo_de` | Es la identidad de la fila: no puede faltar nunca. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_codigo_del_no_editorial_lleva_su_propio_prefijo` | El prefijo es seguro porque el rubro de una fila no cambia: una fila no salta de una tabla hija a la otra. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_codigo_escrito_a_mano_se_respeta` | Híbrido a propósito: la comiquería ya tiene una nomenclatura en sus planillas y el sistema no tiene por qué pisarla. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_dos_productos_no_pueden_compartir_codigo` | Dos productos no pueden compartir codigo | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_codigo_no_se_regenera_al_volver_a_guardar` | Si cambiara, dejaría de servir para lo único que sirve: identificar. | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_los_codigos_generados_no_se_repiten_entre_rubros` | Se derivan de la clave primaria, que es compartida por la jerarquía, así que el prefijo es lo único que los separa. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_dos_tomos_con_la_misma_tupla_chocan_en_la_base` | La restricción vieja abarcaba dos tablas y se perdió con la jerarquía. `clave_edicion` la recupera copiando a la hija los dos campos del padre. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_la_clave_ignora_mayusculas_y_espacios_de_mas` | Quien carga "Batman " un martes y "batman" el jueves está cargando el mismo tomo. Es el mismo `Lower()` de la restricción vieja. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_dos_importados_sin_formato_tambien_chocan` | A13: en SQL dos nulos no son iguales, así que sin el cero de relleno dos importados sin formato —que es lo normal— no chocarían nunca entre sí. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_la_misma_obra_de_dos_editoriales_son_dos_productos` | Es el caso que ordenó todo el modelo: la edición de Ivrea y la de Norma son la misma obra y **dos productos distintos**. Cambian la traducción, los modismos y el papel, y al cliente le importa. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_origen_no_entra_en_la_identidad` | `origen` es **cómo se forma el precio**, no qué es la cosa. Si entrara en la clave, el mismo tomo comprado por otro canal entraría dos veces. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_la_clave_se_recalcula_al_cambiar_un_campo_de_la_tupla` | La clave se recalcula al cambiar un campo de la tupla | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_codigo_de_barras_existe_en_los_dos_rubros` | **Un ISBN-13 es un EAN-13.** Los prefijos 978 y 979 son "Bookland", el país ficticio que GS1 reservó para libros dentro del sistema EAN, y el dígito verificador usa los mismos pesos alternados. Decir que solo el material no editorial tiene… | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_codigo_de_barras_es_opcional` | El merch genérico no lo trae, y el material editorial de fondo puede tener un ISBN-10, que no es un EAN válido. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_dos_productos_no_pueden_compartir_codigo_de_barras` | Igual que el ISBN y por el mismo motivo: son identificadores del mundo, y dos productos con el mismo número son el mismo producto. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_choque_de_codigo_de_barras_cruza_los_rubros` | Es consecuencia de que la restricción viva en la entidad general, y es lo correcto: el número identifica la cosa, no el rubro en el que la guardamos. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_varios_productos_sin_codigo_de_barras_conviven` | La restricción es parcial: si no lo fuera, todos los que no lo tienen chocarían entre sí por compartir la cadena vacía. | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_isbn_no_se_copia_al_codigo_de_barras` | Se decidió **no** derivarlo: son el mismo número, pero mientras no haya lector la utilidad no está definida y sería lógica que nada ejercita. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_la_marca_es_opcional` | Es el caso que rompió el modelo viejo: hay merch genérico y no oficial. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_dos_articulos_del_mismo_nombre_y_categoria_pueden_convivir` | CU-CAT-ALT E2 lo trata como bloqueo y el catálogo real no lo tolera: dos llaveros de Naruto de proveedores distintos son dos productos. Se informa como advertencia, no se impide (corrección 21). | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_tomo_no_acepta_una_categoria_no_editorial` | Un tomo no acepta una categoria no editorial | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_articulo_no_acepta_un_tipo_editorial` | Un articulo no acepta un tipo editorial | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_material_no_editorial_no_admite_pre_venta` | CU-CAT-ALT lo dice en sus comentarios, y se valida en el modelo y no escondiendo la opción en la pantalla. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_usa_formato_no_sirve_como_discriminador_de_rubro` | El atajo que parece obvio y no lo es: Artbook, Novela ligera y Libro son editoriales y ya tienen `usa_formato` en falso. Son dos preguntas distintas. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_especifico_devuelve_la_hija_desde_el_padre` | La herencia con tabla por hija no baja sola: sin esto el inventario no puede leer `volumen` ni `marca`. | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_especifico_sobre_una_hija_se_devuelve_a_si_misma` | Especifico sobre una hija se devuelve a si misma | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_inventario_devuelve_los_dos_rubros_en_una_sola_consulta` | Es lo que la herencia con tabla propia hace posible y las clases abstractas no: CU-CAT-INV pide un listado único sobre los dos rubros. | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_discriminador_lo_escribe_el_modelo` | Que lo complete quien crea el objeto sería pedirle que repita algo que el propio tipo ya dice. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_precio_es_el_base_redondeado_en_los_dos_rubros` | La invariante que justifica que `precio_base` esté siempre presente. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_no_se_puede_guardar_un_producto_sin_rubro` | No hay productos sueltos: todos son de un rubro o del otro. `Producto` tiene tabla propia porque la necesita —el inventario único y las claves foráneas de los módulos que vienen— pero eso no lo vuelve instanciable. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_guardar_por_la_entidad_general_tambien_se_rechaza` | Protege de paso la clave de edición: guardar por la general no la recalcula, porque no toca la tabla de la especialización. Antes era una condición documentada; ahora es una regla. | Integración · caja gris · validación | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_las_dos_especializaciones_se_guardan_sin_problema` | Las dos especializaciones se guardan sin problema | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_alta_fallida_no_deja_una_fila_sin_codigo` | Las dos escrituras del código van en una transacción: el código se deriva de la clave primaria, así que hay que insertar para calcularlo, y sin la transacción hay un instante en el que la fila existe sin código. | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |

### `test_nombres_de_catalogo.py`

> Los catálogos que se identifican por su nombre no distinguen mayúsculas. Es la regla que evita que en seis meses convivan "Ivrea", "ivrea " e "IVREA" como tres registros distintos con los productos repartidos entre los tres. Estaba escrita, pero solo aplicada en tres de los cinco catálogos: `Tipo` y `Formato` quedaron afuera, y son justamente los dos que **deciden** —el tipo entra en la clave de…

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Integración · caja gris · funcional — 4; Integración · caja gris · validación — 1; Integración · caja negra · funcional — 1; Sistema · caja gris · funcional — 1; Sistema · caja gris · validación — 1; Sistema · caja gris · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_mismo_nombre_en_otra_caja_se_rechaza` | El mismo nombre en otra caja se rechaza | Integración · caja gris · validación | Base de datos | `modelo`, `formulario`, `extra`, `_` — 4 casos | Cumple |
| `test_el_aviso_nombra_al_registro_existente` | Sin el nombre tal como está guardado, hay que ir a buscarlo a la lista. | Integración · caja gris · funcional | Base de datos | `modelo`, `formulario`, `extra`, `_` — 4 casos | Cumple |
| `test_los_espacios_de_mas_se_normalizan` | Los espacios de mas se normalizan | Integración · caja negra · funcional | Base de datos | `modelo`, `formulario`, `extra`, `_` — 4 casos | Cumple |
| `test_editarse_a_si_mismo_no_es_un_duplicado` | Guardar un registro sin tocarle el nombre tiene que seguir andando: el choque se busca contra los demás, no contra uno mismo. | Integración · caja gris · funcional | Base de datos | `modelo`, `formulario`, `extra`, `_` — 4 casos | Cumple |
| `test_se_le_puede_corregir_la_capitalizacion` | El caso que rompería una comparación ingenua contra sí mismo: cambiar "zeta de prueba" por "Zeta de prueba" es la misma fila, no un duplicado. | Integración · caja gris · funcional | Base de datos | `modelo`, `formulario`, `extra`, `_` — 4 casos | Cumple |
| `test_la_restriccion_esta_en_la_base` | Sin esto la regla vale solo para quien pase por el formulario, y un `create()` en un comando o en un import la esquiva sin avisar. | Integración · caja gris · funcional | Base de datos | `modelo`, `_f`, `extra`, `_` — 4 casos | Cumple |
| `test_la_pantalla_de_edicion_abre` | La pantalla de edicion abre | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`; `ruta`, `modelo`, `extra` — 4 casos | Cumple |
| `test_la_edicion_rechaza_el_choque_con_otro` | La edicion rechaza el choque con otro | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`; `ruta`, `modelo`, `extra` — 4 casos | Cumple |
| `test_solo_el_administrador_edita` | Solo el administrador edita | Sistema · caja gris · control de acceso | Pantalla (HTTP) | `client`; `ruta`, `modelo`, `extra` — 4 casos | Cumple |

### `test_pantalla_etiquetas.py`

> La pantalla de etiquetas, que salió de Parámetros globales. Se separó por una razón de escala, no de prolijidad: los otros catálogos de parámetros son cerrados y chicos —nueve tipos, siete formatos, un puñado de editoriales— y se tocan una vez por semestre. Las etiquetas son el único catálogo abierto: crecen con cada franquicia, género y colección nueva. Un catálogo que crece necesita buscador, y…

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 10; Sistema · caja negra · control de acceso — 2; Sistema · caja gris · funcional — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_lista_las_etiquetas_agrupadas` | Agrupadas porque es como se piensan y como se eligen: nadie busca "una etiqueta", busca una franquicia o un género. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_muestra_cuantos_productos_usan_cada_etiqueta` | Es el dato que decide si una etiqueta se puede desactivar sin romper nada. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_cada_etiqueta_enlaza_a_su_edicion` | Cada etiqueta enlaza a su edicion | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_grupo_inactivo_se_marca` | Desactivarlo saca del alta a todas sus etiquetas, así que tiene que verse. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_sin_grupos_avisa_que_no_se_puede_cargar_ninguna` | Toda etiqueta pertenece a un grupo. Enterarse en el formulario, con el nombre ya escrito, es tarde. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_buscador_filtra` | El buscador filtra | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_grupo_sin_coincidencias_no_se_dibuja` | Con el buscador escrito, una lista de encabezados vacíos es ruido que hay que saltear para llegar al único resultado. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_sin_coincidencias_lo_dice` | Sin coincidencias lo dice | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_buscador_en_vivo_devuelve_solo_el_fragmento` | `?parcial=1` reemplaza la zona de resultados sin recargar la pantalla. | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_cajero_no_administra_etiquetas` | El cajero no administra etiquetas | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client` | Cumple |
| `test_sin_sesion_redirige_al_login` | Sin sesion redirige al login | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_el_alta_de_etiqueta_vuelve_a_esta_pantalla` | El alta de etiqueta vuelve a esta pantalla | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_de_grupo_vuelve_a_esta_pantalla` | El alta de grupo vuelve a esta pantalla | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |

### `test_pantalla_revision.py`

> Las pantallas de la revisión de borradores (CU-ALT-REV). Las reglas se prueban en `test_revision_borradores.py`. Acá está lo que solo existe en la pantalla: que la cola diferencie visualmente lo que el CU pide diferenciar, que la acción afirmativa sobre cada campo de confianza baja **se valide en el servidor** y no escondiendo un botón (RNF-03), y que las exclusiones de la confirmación en lote se…

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 15; Sistema · caja negra · funcional — 14; Sistema · caja gris · validación — 3; Sistema · caja negra · validación — 1; Sistema · caja gris · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_la_cola_lista_los_borradores_pendientes` | La cola lista los borradores pendientes | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_la_cola_vacia_lo_dice_y_apunta_a_donde_se_generan` | Sin borradores pendientes: informa y no presenta nada (excepción del CU). | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_la_cola_distingue_incompletos_de_confianza_baja` | No son lo mismo y no se arreglan igual: al incompleto le falta un dato, al dudoso hay que mirarle uno que ya está. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_solo_se_puede_seleccionar_lo_que_el_lote_va_a_confirmar` | Ofrecer la casilla en un incompleto sería invitar a un clic que termina en una advertencia. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_la_cola_no_muestra_una_sesion_hasta_que_haya_una_accion` | La cola no muestra una sesion hasta que haya una accion | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_el_buscador_filtra_por_titulo` | El buscador filtra por titulo | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_la_ficha_muestra_los_reparos_del_borrador` | La ficha muestra los reparos del borrador | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_guardar_sin_confirmar_deja_el_borrador_en_la_cola` | Guardar sin confirmar deja el borrador en la cola | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_confirmar_desde_la_ficha_crea_el_producto` | Confirmar desde la ficha crea el producto | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_el_titulo_editado_es_el_que_llega_al_producto` | El titulo editado es el que llega al producto | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_un_isbn_mal_escrito_a_mano_se_rechaza` | El pipeline ya lo verifica al extraer, pero acá lo escribe una persona: es exactamente el momento del error de transcripción (A19). | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_una_pre_venta_sin_fecha_no_se_puede_guardar` | Una pre venta sin fecha no se puede guardar | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_rechazar_sin_motivo_no_descarta_nada` | Rechazar sin motivo no descarta nada | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_rechazar_con_motivo_descarta_el_borrador` | Rechazar con motivo descarta el borrador | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_un_borrador_ya_resuelto_no_se_vuelve_a_resolver` | El doble envío del formulario es el caso normal, no el raro. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `correo`, `administrador` | Cumple |
| `test_la_ficha_de_un_borrador_resuelto_no_ofrece_acciones` | La ficha de un borrador resuelto no ofrece acciones | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_la_ficha_pide_la_casilla_por_cada_campo_de_confianza_baja` | La ficha pide la casilla por cada campo de confianza baja | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_confirmar_sin_revisar_la_confianza_baja_se_bloquea` | Se valida en el servidor y no escondiendo el botón: un POST armado a mano confirmaría igual un dato que nadie miró (RNF-03). | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_confirmar_marcando_la_casilla_funciona` | Confirmar marcando la casilla funciona | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_revisar_un_campo_y_no_el_otro_sigue_bloqueando` | La acción es por campo, no un "revisé este borrador" genérico. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_la_marca_de_revisado_se_puede_retirar` | Dejar la marca puesta haría que un dato vuelto a poner en duda siguiera contando como mirado. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_el_lote_confirma_los_seleccionados` | El lote confirma los seleccionados | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_el_lote_informa_lo_que_excluyo` | Se informa la exclusión: sin eso, el borrador que quedó afuera desaparecería de la vista sin explicación. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_el_lote_sin_seleccion_no_hace_nada` | El lote sin seleccion no hace nada | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_cerrar_manda_el_pedido_y_lo_informa` | Cerrar manda el pedido y lo informa | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_cerrar_sin_sesion_en_curso_lo_dice` | Cerrar sin sesion en curso lo dice | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_cerrar_una_sesion_de_solo_rechazos_no_manda_pedidos` | Cerrar una sesion de solo rechazos no manda pedidos | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_la_cola_muestra_la_sesion_en_curso` | La cola muestra la sesion en curso | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo`, `administrador` | Cumple |
| `test_las_pantallas_son_solo_del_administrador` | Las pantallas son solo del administrador | Sistema · caja gris · control de acceso | Pantalla (HTTP) | `client`, `correo`; `rol` — 2 casos | Cumple |
| `test_el_menu_enlaza_la_revision` | El menu enlaza la revision | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_confirmar_desde_la_pantalla_deja_al_producto_atado_a_su_proveedor` | Confirmar desde la pantalla deja al producto atado a su proveedor | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `correo`, `proveedor` | Cumple |
| `test_la_ficha_avisa_si_el_producto_ya_esta_en_el_catalogo` | Salió de correr el pipeline sobre dos correos que anunciaban los mismos tomos: los borradores del segundo quedaban en la cola sin ninguna marca, y la única forma de enterarse era apretar «confirmar» y recibir el rechazo. Es la misma… | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_un_borrador_sin_duplicado_no_lleva_ese_aviso` | Un borrador sin duplicado no lleva ese aviso | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_la_ficha_de_un_confirmado_no_se_avisa_a_si_misma` | El "duplicado" de un borrador confirmado sería el producto que él mismo creó, y avisarlo sería absurdo. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |

### `test_parametros.py`

> Parámetros globales: clasificación del catálogo, precios y configuración.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 20; Integración · caja gris · funcional — 10; Sistema · caja negra · funcional — 9; Sistema · caja negra · validación — 7; Sistema · caja negra · control de acceso — 3; Sistema · caja gris · validación — 3; Sistema · caja gris · idempotencia — 2; Integración · caja negra · funcional — 1; Sistema · caja negra · idempotencia — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_sistema_arranca_con_tipos_y_formatos_cargados` | Sin al menos un tipo no se puede dar de alta ningún producto: una instalación nueva no puede quedar trabada esperando que alguien adivine qué cargar primero. | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_los_tipos_con_grilla_de_tamanos_usan_formato` | Los tipos con grilla de tamanos usan formato | Integración · caja gris · funcional | Base de datos | `nombre` — 2 casos | Cumple |
| `test_los_tipos_sin_grilla_de_tamanos_no_usan_formato` | Los tipos sin grilla de tamanos no usan formato | Integración · caja gris · funcional | Base de datos | `nombre` — 3 casos | Cumple |
| `test_el_sistema_arranca_con_los_grupos_de_etiqueta_sembrados` | No pretenden ser la taxonomía completa: existen para que la pantalla no arranque vacía y el primer producto se pueda describir sin inventar los ejes desde cero. | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_hay_grupos_para_el_rubro_no_editorial` | Los sembrados originalmente describen material editorial, y la pantalla de una figura ofrecía cuatro ejes y ninguno aplicable: una figura no tiene demografía ni género literario, y etiquetarla igual ensucia los filtros. | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_franquicia_sirve_para_los_dos_rubros` | Es el único eje compartido, y por eso no se duplicó: una figura de Marvel y un cómic de Marvel comparten franquicia. | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_la_pantalla_muestra_los_catalogos` | Se administran acá y no desde el admin de Django: es la pantalla que tiene el diseño del sistema y la que usa el personal. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_las_etiquetas_se_administran_en_su_propia_pantalla` | Salieron de acá porque son el único catálogo abierto de los seis. Queda el acceso y el resumen de grupos, no la lista entera. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_tabla_de_precios_se_puede_filtrar_por_editorial` | La tabla de precios se puede filtrar por editorial | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_se_avisa_cuando_una_editorial_no_tiene_precios` | Se avisa cuando una editorial no tiene precios | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_solo_el_administrador_ve_los_parametros` | Solo el administrador ve los parametros | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client`; `rol_sin_permiso` — 2 casos | Cumple |
| `test_la_configuracion_nace_con_los_valores_de_settings` | Estrenar la pantalla no puede cambiar ningún cálculo. | Integración · caja gris · funcional | Base de datos | `settings` | Cumple |
| `test_no_puede_haber_dos_configuraciones` | Si hubiera dos nadie sabría cuál rige, y el precio de los importados dependería de cuál se leyó primero. El intento falla de forma ruidosa, y así tiene que ser: quedarse callado y guardar la segunda dejaría el sistema con dos verdades… | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_la_configuracion_no_se_borra` | La configuracion no se borra | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_guardar_el_margen_lo_deja_vigente_y_auditado` | Guardar el margen lo deja vigente y auditado | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |
| `test_un_margen_escrito_como_porcentaje_es_rechazado` | 40 en vez de 0,40 es el error más fácil de cometer, y multiplicaría por cuarenta el precio de todos los importados. | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_margen_negativo_es_rechazado` | Un margen negativo es rechazado | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_stock_por_defecto_absurdo_es_rechazado` | Un stock por defecto absurdo es rechazado | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_se_puede_dar_de_alta_una_editorial` | Se puede dar de alta una editorial | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_nombre_de_la_editorial_se_normaliza` | Sin esto, en seis meses conviven tres editoriales con el mismo nombre y los productos quedan repartidos entre las tres. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_una_editorial_repetida_es_rechazada` | Una editorial repetida es rechazada | Sistema · caja gris · idempotencia | Pantalla (HTTP) | `client_admin`; `repetido` — 3 casos | Cumple |
| `test_se_puede_dar_de_alta_un_tipo_con_su_bandera` | `usa_formato` es la única que quedó: es la que gobierna una restricción real, porque el formato entra en la tabla de precios. La de franquicia se fue con ella — las etiquetas aplican a todo tipo de material, así que la bandera habría… | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_se_puede_editar_un_formato` | Se puede editar un formato | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_de_un_parametro_queda_auditada` | El alta de un parametro queda auditada | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |
| `test_se_puede_cargar_un_precio_de_referencia` | Se puede cargar un precio de referencia | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_no_se_puede_repetir_la_misma_combinacion` | No se puede repetir la misma combinacion | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_tabla_no_ofrece_tipos_que_no_usan_formato` | Un artbook no tiene con qué completar la clave: su precio va a mano. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_precio_negativo_es_rechazado` | Un precio negativo es rechazado | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_eliminar_un_precio_no_toca_los_productos_ya_cargados` | El producto guarda su precio: lo que se pierde es el pre-completado. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_baja_de_un_precio_pide_confirmacion` | La baja de un precio pide confirmacion | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_las_altas_de_parametros_son_solo_del_administrador` | Las altas de parametros son solo del administrador | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client`, `cajero`; `pantalla` — 4 casos | Cumple |
| `test_se_puede_dar_de_alta_una_etiqueta` | Se puede dar de alta una etiqueta | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_nombre_de_la_etiqueta_se_normaliza` | El nombre de la etiqueta se normaliza | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_una_etiqueta_repetida_en_el_mismo_grupo_es_rechazada` | La comparación ignora mayúsculas: es la misma etiqueta escrita distinto. | Sistema · caja gris · idempotencia | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_mismo_nombre_en_otro_grupo_si_se_puede` | La unicidad es por grupo: "Terror" puede ser un género y también el nombre de una colección, y son dos etiquetas distintas. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_una_etiqueta_de_una_letra_es_rechazada` | Una sola letra no describe nada y casi siempre es un enter de más. | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_una_etiqueta_sin_grupo_es_rechazada` | El grupo es lo que la hace filtrable: sin él no se sabe en qué faceta de la tienda tendría que aparecer. | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_de_etiqueta_queda_auditada` | El alta de etiqueta queda auditada | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_se_puede_dar_de_alta_un_grupo_de_etiquetas` | Se puede dar de alta un grupo de etiquetas | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_grupo_repetido_es_rechazado` | Un grupo repetido es rechazado | Sistema · caja negra · idempotencia | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_solo_el_administrador_administra_etiquetas` | Solo el administrador administra etiquetas | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client`; `rol_sin_permiso` — 2 casos | Cumple |
| `test_un_formato_sin_tipos_declarados_es_universal` | El vacío significa "en todos" y no "en ninguno": olvidarse de declararlos deja el comportamiento anterior a que el campo existiera, no un formato invisible. | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_formato_con_tipos_declarados_solo_aplica_a_esos` | Un formato con tipos declarados solo aplica a esos | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_alta_solo_ofrece_los_formatos_del_tipo_elegido` | Es lo que baja el desplegable de quince opciones a las que aplican, en la pantalla que más campos pide. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_precio_de_referencia_con_un_formato_que_no_aplica_es_rechazado` | Una fila para una combinación imposible es una fila muerta: no va a coincidir nunca con ningún producto y confunde a quien la lea. | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_se_puede_cambiar_a_un_proveedor_remoto` | Se puede cambiar a un proveedor remoto | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_proveedor_remoto_sin_clave_se_rechaza` | Sin clave no va a contestar nunca, y el fallo aparecería recién en la pantalla de diagnóstico. Se avisa donde se puede arreglar. Se vacía primero la que trae la semilla del entorno: el formulario solo exige que **haya** una, y juzgar si… | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_proveedor_remoto_sin_modelo_se_rechaza` | Los proveedores hospedan cientos: sin nombrarlo devuelven un error que cuesta interpretar. | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_dejar_la_clave_vacia_no_la_borra` | El campo llega vacío siempre, así que un vacío significa "no la cambies" y no "borrala". Sin esto, ajustar el timeout dejaría el sistema sin clave. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_clave_nunca_se_dibuja_entera` | La pantalla no puede ser un lugar del que copiar el secreto. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_clave_no_entra_en_la_auditoria` | El log es inmutable y consultable: un secreto que pasa por ahí queda ahí para siempre. Se registra **que** cambió, que es lo que hace falta saber. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_cambio_de_modelo_queda_auditado` | El cambio de modelo queda auditado | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_guardar_el_modelo_no_toca_el_margen` | Son dos formularios porque se tocan por motivos distintos: un error en uno no puede borrar lo escrito en el otro. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_una_direccion_sin_la_ruta_de_la_api_se_rechaza` | Pegar la dirección base del servidor es el error más natural acá, y el formulario lo aceptaba: quedaba una configuración que no puede funcionar y el diagnóstico decía "no parece una API compatible", que es verdad pero no dice qué corregir. | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_direccion_completa_se_acepta_en_los_dos_modos` | La direccion completa se acepta en los dos modos | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_barra_final_de_mas_no_molesta` | La barra final de mas no molesta | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |

### `test_precios.py`

> RF-10 — la aritmética del precio importado. Son los únicos tests del módulo que no tocan la base: la fórmula es una función pura y probarla sola permite recorrer muchos casos sin armar un lote cada vez.

**Tipos en este archivo:** Unitaria · caja negra · funcional — 12.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_cre_es_el_cociente_entre_el_envio_y_la_compra` | El cre es el cociente entre el envio y la compra | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_cre_se_guarda_con_seis_decimales` | Es un factor que multiplica a todos los ítems: redondearlo a dos arrastraría el error del cociente a cada precio del lote. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_un_valor_de_compra_en_cero_da_un_cre_de_cero` | No hay contra qué prorratear el envío. No es un error que deba explotar. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_la_formula_encadena_costo_cre_y_margen` | `precio_final = C × (1 + R) × (1 + M)`, la condición de verificación de RF-10. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_casos_de_la_formula` | Casos de la formula | Unitaria · caja negra · funcional | Unidad | `costo`, `cre`, `margen`, `base_esperada`, `final_esperado` — 3 casos | Cumple |
| `test_el_precio_base_conserva_centavos` | Es el valor que se persiste para recalcular en CU-PVP-MAR: redondearlo al peso metería el error del redondeo dentro de cada recálculo futuro. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_precio_final_se_redondea_al_peso` | El precio final se redondea al peso | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_medio_peso_redondea_para_arriba` | El medio peso redondea para arriba | Unitaria · caja negra · funcional | Unidad | `valor`, `esperado` — 3 casos | Cumple |
| `test_sin_cotizacion_el_importe_ya_esta_en_pesos` | Sin cotizacion el importe ya esta en pesos | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_la_cotizacion_convierte_el_costo_en_origen_a_pesos` | Agregado a la fuente: el CU habla de 'costo base en origen' sin decir en qué moneda. Con cotización declarada, el sistema convierte. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_desglose_convierte_antes_de_aplicar_el_cre` | El desglose convierte antes de aplicar el cre | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_recalculo_de_cu_13_sale_del_precio_base_almacenado` | Ante un margen nuevo, el precio final se recalcula sin los datos del lote. Es la mitad de la condición de verificación de RF-10, y lo que justifica que `precio_base` se persista. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |

### `test_revision_borradores.py`

> Revisar y confirmar borradores (CU-ALT-REV), del lado de las reglas. La pantalla se prueba aparte; acá está lo que tiene que valer aunque se la invoque desde un comando o desde una tarea de fondo. Lo que se pone a prueba es la línea que sostiene todo el pipeline: **el modelo propone, la persona aplica**. Ningún camino de este archivo puede terminar con un producto en el catálogo sin una acción…

**Tipos en este archivo:** Integración · caja gris · funcional — 14; Integración · caja negra · funcional — 14; Integración · caja gris · validación — 5; Integración · caja blanca · frontera — 4; Integración · caja gris · idempotencia — 1; Integración · caja blanca · funcional — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_confirmar_crea_el_producto` | Confirmar crea el producto | Integración · caja gris · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_el_producto_nace_atado_al_proveedor_que_lo_anuncio` | Es la única vía por la que ese dato se llena: las altas manuales no lo piden (A4 de proveedores). | Integración · caja negra · funcional | Base de datos | `correo`, `administrador`, `proveedor`; base de datos (`django_db`) | Cumple |
| `test_el_borrador_queda_confirmado_y_apunta_a_su_producto` | El borrador queda confirmado y apunta a su producto | Integración · caja gris · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_una_pre_venta_conserva_su_fecha` | Una pre venta conserva su fecha | Integración · caja negra · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_el_precio_se_redondea_al_peso` | A1: el precio final es el número que se cobra, y en una comiquería no se cobran centavos. El base conserva los centavos para poder recalcular. | Integración · caja negra · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_un_precio_que_coincide_con_la_tabla_no_queda_manual` | Un precio que coincide con la tabla no queda manual | Integración · caja negra · funcional | Base de datos | `correo`, `administrador`, `editorial`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_un_precio_distinto_del_de_la_tabla_queda_manual` | A4: si el precio confirmado no es el de la tabla, alguien lo decidió a propósito y la propagación de CU-PVP-MAR no debe pisárselo. | Integración · caja negra · funcional | Base de datos | `correo`, `administrador`, `editorial`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_sin_fila_en_la_tabla_la_marca_no_aplica` | No hay de dónde propagarle, así que no se lo marca como manual. | Integración · caja negra · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_un_bloqueante_vacio_impide_confirmar` | Un bloqueante vacio impide confirmar | Integración · caja gris · validación | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_una_pre_venta_sin_fecha_no_se_puede_confirmar` | Bloqueante condicional del CU, y A10: sin fecha quedaría en pre-venta para siempre, invisible para el ciclo que debería sacarla de ahí. | Integración · caja negra · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_el_mismo_borrador_sin_fecha_se_confirma_si_nace_activo` | La fecha es bloqueante **solo** si el borrador quedaría en Pre-venta. | Integración · caja negra · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_un_producto_que_se_cargo_mientras_tanto_bloquea_la_confirmacion` | Entre que el borrador se generó y que alguien lo confirma pueden pasar días: la comprobación del pipeline caducó y hay que rehacerla. | Integración · caja negra · funcional | Base de datos | `correo`, `administrador`, `editorial`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_confirmar_dos_veces_no_duplica_el_producto` | La segunda confirmación encuentra el borrador ya resuelto y se retira. | Integración · caja gris · idempotencia | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_el_lote_confirma_todos_los_que_estan_en_condiciones` | El lote confirma todos los que estan en condiciones | Integración · caja gris · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_el_lote_excluye_la_confianza_baja_sin_bloquear_al_resto` | Es la excepción central del CU: se informa la exclusión y el borrador permanece en cola para revisión individual. | Integración · caja gris · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_una_confianza_baja_ya_revisada_no_excluye_del_lote` | La acción afirmativa del paso 3 es lo que la desbloquea. | Integración · caja gris · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_la_confianza_media_no_excluye_del_lote` | El CU habla de confianza **baja**: la media no traba nada. | Integración · caja gris · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_un_borrador_de_confianza_baja_si_se_puede_confirmar_de_a_uno` | La pantalla exige la acción afirmativa antes de dejar apretar el botón; el servicio no la vuelve a exigir en el camino individual. | Integración · caja gris · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_rechazar_exige_motivo` | Rechazar exige motivo | Integración · caja gris · validación | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_rechazar_persiste_el_motivo_y_lo_audita` | Rechazar persiste el motivo y lo audita | Integración · caja gris · validación | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_rechazar_no_crea_ningun_producto` | Rechazar no crea ningun producto | Integración · caja gris · validación | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_mirar_la_cola_no_abre_una_sesion` | Se crea con la primera acción: abrirla al entrar llenaría la tabla de tandas vacías cada vez que alguien pasa a ver qué hay. | Integración · caja gris · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_la_primera_confirmacion_abre_la_sesion` | La primera confirmacion abre la sesion | Integración · caja negra · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_las_acciones_siguientes_reusan_la_misma_sesion` | Las acciones siguientes reusan la misma sesion | Integración · caja gris · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_dos_revisores_tienen_sesiones_distintas` | Mezclarlas haría que el pedido consolidado de uno se lleve los productos del otro. | Integración · caja gris · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_cerrar_manda_un_correo_por_proveedor` | Cerrar manda un correo por proveedor | Integración · caja gris · funcional | Base de datos | `correo`, `administrador`, `editorial`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_cada_correo_lleva_solo_los_productos_de_su_proveedor` | Cada correo lleva solo los productos de su proveedor | Integración · caja gris · funcional | Base de datos | `correo`, `administrador`, `editorial`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_el_pedido_lleva_las_cantidades_de_stock_solicitadas` | El pedido lleva las cantidades de stock solicitadas | Integración · caja negra · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_una_sesion_sin_confirmaciones_no_manda_ningun_correo` | Solo rechazos: la sesión queda registrada, pero un correo vacío sería peor que no mandarlo. | Integración · caja gris · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_dos_sesiones_el_mismo_dia_son_dos_correos_separados` | No reabre pedidos de sesiones anteriores: son dos decisiones distintas y el proveedor tiene que poder tratarlas como tales. | Integración · caja negra · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_el_envio_se_reintenta_tres_veces` | El envio se reintenta tres veces | Integración · caja blanca · frontera | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_un_envio_fallido_no_revierte_los_productos` | El alta y el pedido son operaciones separadas: un correo que no salió no puede deshacer productos que ya están en el catálogo. | Integración · caja blanca · frontera | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_el_fallo_queda_registrado_con_el_proveedor` | El CU pide notificar indicando **cuál** proveedor falló: sin el nombre el aviso no sirve para ir a mandarlo a mano. | Integración · caja blanca · frontera | Base de datos | `correo`, `administrador`, `proveedor`; base de datos (`django_db`) | Cumple |
| `test_un_proveedor_caido_no_frena_al_resto` | Un proveedor caido no frena al resto | Integración · caja blanca · frontera | Base de datos | `correo`, `administrador`, `editorial`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_cada_confirmacion_deja_su_entrada` | "Qué pasó en esta tanda" la contesta la sesión; "de dónde salió este producto" solo la contesta esta entrada. | Integración · caja gris · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_el_cierre_registra_confirmados_rechazados_y_pendientes` | El cierre registra confirmados rechazados y pendientes | Integración · caja gris · validación | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_el_stock_por_defecto_de_la_configuracion_llega_al_producto` | El stock por defecto de la configuracion llega al producto | Integración · caja negra · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_una_carrera_contra_la_base_se_trata_como_duplicado` | La restricción de la base es la que **realmente** garantiza la unicidad. Dos confirmaciones simultáneas del mismo tomo pueden pasar las dos el chequeo previo y chocar recién al insertar. Eso no es un error del sistema: es un duplicado, y… | Integración · caja blanca · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |
| `test_un_proveedor_sin_productos_confirmados_no_recibe_correo` | Nada que pedir no es un fallo: es una sesión donde ese proveedor no aportó ningún producto. | Integración · caja negra · funcional | Base de datos | `correo`, `administrador`; base de datos (`django_db`) | Cumple |

### `test_validaciones.py`

> Entradas mal puestas en la carga de lotes. La pantalla también valida, pero lo que se prueba acá es el servidor: cada uno de estos envíos se puede armar con las herramientas del navegador abiertas, sin pasar por ningún control del JavaScript. Si una regla no está en este archivo, en la práctica no existe.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · validación — 15; Sistema · caja gris · validación — 9; Sistema · caja gris · funcional — 7; Sistema · caja negra · funcional — 2; Sistema · caja negra · idempotencia — 2; Sistema · caja gris · idempotencia — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_un_valor_negativo_en_el_item_es_rechazado` | Un valor negativo en el item es rechazado | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `referencia`; `campo` — 2 casos | Cumple |
| `test_un_volumen_negativo_es_rechazado` | Un volumen negativo es rechazado | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_costo_en_origen_negativo_es_rechazado` | Un costo en origen negativo es rechazado | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_total_negativo_del_lote_es_rechazado` | Un total negativo del lote es rechazado | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`; `campo` — 2 casos | Cumple |
| `test_una_cotizacion_negativa_es_rechazada` | Una cotizacion negativa es rechazada | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_precio_en_cero_es_rechazado` | Un producto de precio cero no es una promoción, es un cero de menos. | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_valor_de_compra_en_cero_es_rechazado` | Es el divisor del CRE: sin él no hay contra qué prorratear el envío. | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_envio_en_cero_es_valido` | Hay proveedores que bonifican el envío: el CRE da cero y el precio base termina siendo el costo. Es un caso legítimo, no un error. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_stock_en_cero_es_valido` | Un stock en cero es valido | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_volumen_absurdo_es_rechazado` | Un volumen absurdo es rechazado | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_stock_absurdo_es_rechazado` | Un stock absurdo es rechazado | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_precio_absurdo_es_rechazado` | Un precio absurdo es rechazado | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_precio_que_no_es_un_numero_es_rechazado` | Un precio que no es un numero es rechazado | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `referencia`; `basura` — 5 casos | Cumple |
| `test_un_volumen_que_no_es_entero_es_rechazado` | Un volumen que no es entero es rechazado | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin`, `referencia`; `basura` — 3 casos | Cumple |
| `test_un_titulo_de_una_sola_letra_es_rechazado` | Un titulo de una sola letra es rechazado | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_titulo_de_solo_espacios_es_rechazado` | Django recorta los extremos, así que el campo queda vacío y obligatorio. | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_los_espacios_de_mas_del_titulo_se_normalizan` | Sin esto, "Akira vol" y "Akira vol" serían dos productos distintos para cualquiera que compare sin normalizar. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_estado_inventado_es_rechazado` | El alta ofrece dos estados; los otros tres son consecuencia de algo posterior y no se pueden elegir desde acá. | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_formato_inexistente_es_rechazado` | Un formato inexistente es rechazado | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_tipo_inexistente_es_rechazado` | Un tipo inexistente es rechazado | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_una_editorial_inexistente_es_rechazada` | Una editorial inexistente es rechazada | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_una_editorial_inactiva_no_se_puede_elegir` | Una editorial dada de baja no se ofrece, y tampoco se acepta si alguien manda su identificador a mano. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_una_fecha_de_llegada_pasada_es_rechazada_en_el_item` | Una fecha de llegada pasada es rechazada en el item | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_una_fecha_de_llegada_pasada_es_rechazada_en_la_cabecera` | Una fecha de llegada pasada es rechazada en la cabecera | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_la_fecha_de_hoy_se_acepta` | El lote que llega hoy es el caso más común de todos. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_una_fecha_invalida_es_rechazada` | Una fecha invalida es rechazada | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_pre_venta_sin_fecha_es_rechazada` | El ciclo que transiciona las pre-ventas busca por fecha de llegada: una pre-venta sin fecha no se puede vigilar y quedaría colgada para siempre. | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_pre_venta_con_fecha_de_la_cabecera_se_acepta` | Pre venta con fecha de la cabecera se acepta | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_dos_items_identicos_en_el_mismo_lote_se_marcan` | Distinto del duplicado contra el catálogo: este todavía se puede corregir sin perder nada, y avisarlo al guardar sería tarde. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_el_repetido_se_detecta_sin_distinguir_mayusculas` | El repetido se detecta sin distinguir mayusculas | Sistema · caja negra · idempotencia | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_el_primero_de_los_repetidos_no_se_marca` | Solo se señala el que sobra: marcar los dos obligaría a adivinar cuál de los dos había que borrar. | Sistema · caja negra · idempotencia | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_dos_volumenes_distintos_no_son_repetidos` | Dos volumenes distintos no son repetidos | Sistema · caja gris · idempotencia | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_contador_de_items_manipulado_no_rompe_la_pantalla` | El formulario de gestión viaja en el HTML y se puede editar a mano. Django lo trata como dato no confiable y devuelve un formulario inválido; lo que no puede pasar es que la pantalla explote con un 500. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_envio_sin_formulario_de_gestion_no_rompe_la_pantalla` | Un envio sin formulario de gestion no rompe la pantalla | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_los_items_vacios_se_descartan_sin_dar_error` | La pantalla arranca con tres ítems en blanco: los que no se toquen no tienen por qué reclamar campos obligatorios. | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |
| `test_un_archivo_que_no_es_imagen_es_rechazado` | Un archivo que no es imagen es rechazado | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin`, `referencia` | Cumple |


## Núcleo — `apps/core`

### `test_auditoria.py`

> El registro de auditoría: lo que queda escrito y lo que no se puede reescribir. `RegistroAuditoria` apunta a su objetivo con una clave genérica y no con una foránea a `Usuario`, porque los módulos que vinieron después auditan lotes, borradores y sesiones de revisión. El correo del objetivo queda desnormalizado para el caso que la clave genérica no cubre: la cuenta que se elimina.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Integración · caja negra · funcional — 2; Integración · caja gris · funcional — 2.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_registrar_completa_el_correo_del_actor` | Registrar completa el correo del actor | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_una_entrada_de_auditoria_no_se_puede_modificar` | Una entrada de auditoria no se puede modificar | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_una_entrada_de_auditoria_no_se_puede_borrar` | Una entrada de auditoria no se puede borrar | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_la_traza_sobrevive_a_la_baja_del_usuario` | La traza sobrevive a la baja del usuario | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |

### `test_componentes.py`

> Los controles de formulario del modo operativo están todos vestidos. Este archivo existe por un error concreto: la cáscara del backoffice estilaba `input[type="text"]`, `email` y `password`, y nada más. El día que una pantalla usó un número, una fecha y un área de texto, los tres salieron con el estilo claro de la cáscara base —letra blanca sobre fondo blanco— y el problema se descubrió mirando…

**Tipos en este archivo:** Sistema · caja negra · funcional — 8; Unitaria · caja negra · funcional — 5.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_archivo_de_campos_cubre_algo` | Si la lectura del archivo dejara de encontrar selectores, el test de abajo pasaría solo y no probaría nada. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_ninguna_pantalla_operativa_dibuja_un_control_sin_estilo` | Ninguna pantalla operativa dibuja un control sin estilo | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`; base de datos (`django_db`); `pantalla` — 3 casos | Cumple |
| `test_la_pantalla_de_alta_usa_los_tipos_que_habian_quedado_sin_estilo` | El caso que originó el problema: número, fecha y área de texto. Si alguna vez dejaran de aparecer en esta pantalla, el test de arriba seguiría en verde sin estar mirando nada. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`; base de datos (`django_db`) | Cumple |
| `test_el_area_de_texto_tambien_esta_cubierta` | El area de texto tambien esta cubierta | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`; base de datos (`django_db`) | Cumple |
| `test_las_pantallas_operativas_traen_los_componentes_propios` | El desplegable y el selector de archivo se arman con JavaScript. Si la cáscara dejara de incluirlos, los controles nativos del sistema operativo aparecerían en medio del sistema sin que nada fallara. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`; base de datos (`django_db`); `pantalla` — 3 casos | Cumple |
| `test_los_campos_obligatorios_se_marcan_solos` | El asterisco sale de `field.required`, no de un dato escrito a mano. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`; base de datos (`django_db`) | Cumple |
| `test_las_pantallas_de_producto_dibujan_el_campo_de_portada` | Las pantallas de producto dibujan el campo de portada | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`; base de datos (`django_db`) | Cumple |
| `test_el_selector_de_etiquetas_dibuja_el_select_real` | Lo que viaja en el POST es el `<select multiple>`: el buscador con fichas se arma encima. Sin el control real, el campo no envia nada. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`; base de datos (`django_db`) | Cumple |
| `test_el_desplegable_propio_no_toca_los_multiples` | Ese componente elige **un** valor y cerrarse al elegirlo es la mitad de lo que hace. Aplicado a un multiple, lo esconde y lo rompe. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`; base de datos (`django_db`) | Cumple |
| `test_los_cuatro_niveles_estan_definidos` | Los cuatro niveles estan definidos | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_paralelogramo_vive_solo_donde_hay_filas` | Es el nivel 3 y su presencia comunica algo concreto. Repartido por toda la pantalla deja de comunicarlo y solo carga el diseno. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_ninguna_pantalla_repite_el_boton_principal` | Uno por pantalla. La excepcion son los dos caminos de igual peso, y ahi el segundo va en la variante fria, que se cuenta aparte. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_boton_de_texto_lleva_su_copia_para_el_barrido` | El color entra con una copia recortada encima del texto. Si `data-texto` no coincide con la etiqueta, al pasar el mouse aparece otra palabra. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |

### `test_configuracion_del_modelo.py`

> La configuración del modelo de lenguaje, y el diagnóstico de sus fallos. Todo esto salió de una restricción del proyecto que no es técnica: **el sistema se demuestra desplegado**, y el modelo local corre en una máquina de escritorio que no viaja. Sin poder apuntar a un proveedor remoto desde una pantalla, la mitad del sistema no se puede mostrar fuera de esa máquina. Y apuntar a un proveedor…

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Integración · caja blanca · frontera — 11; Integración · caja negra · funcional — 5; Integración · caja negra · frontera — 2.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_una_respuesta_buena_trae_los_datos` | Una respuesta buena trae los datos | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_sin_conexion_se_distingue_de_un_rechazo` | Sin conexion se distingue de un rechazo | Integración · caja negra · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_rechazo_conserva_el_codigo` | Es lo que antes se perdía: el servidor **contestó**, y contestó que no. | Integración · caja negra · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_cuerpo_del_error_se_conserva` | Los proveedores explican ahí por qué rechazaron, y sin leerlo el diagnóstico se queda en el número. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_una_respuesta_que_no_es_json_se_distingue` | Pasa cuando la dirección apunta a algo que no es la API que se cree: es un problema de configuración, no de red. | Integración · caja blanca · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_los_catalogos_siguen_recibiendo_json_o_nada` | `pedir_json` descarta el diagnóstico a propósito: un catálogo tiene respaldo local y hace lo mismo sea cual sea el motivo. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_pedido_usa_la_configuracion_guardada` | Cambiar de proveedor desde la pantalla tiene que surtir efecto sin reiniciar el servidor: para eso existe la pantalla. | Integración · caja blanca · frontera | Base de datos | `settings` | Cumple |
| `test_sin_clave_no_se_manda_la_cabecera` | Un servidor local no la pide, y algunos rechazan el pedido si llega vacía. | Integración · caja blanca · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_chequeo_de_estado_manda_la_credencial` | Antes iba sin ella, y contra un proveedor que la exige en el catálogo de modelos la pantalla informaba "caído" con el servicio vivo. | Integración · caja blanca · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_una_clave_vencida_no_se_reporta_como_servicio_caido` | Es el fallo más probable con un proveedor remoto, y el que peor se diagnostica desde un mensaje genérico. | Integración · caja blanca · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_sin_credito_se_dice_con_todas_las_letras` | Sin credito se dice con todas las letras | Integración · caja blanca · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_limite_de_pedidos_se_explica` | 429 es lo habitual con los modelos gratuitos, y sin traducirlo la pantalla muestra un número. | Integración · caja blanca · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_modelo_inexistente_muestra_el_motivo_del_proveedor` | Mensaje real de OpenRouter al pedirle un identificador que no existe. | Integración · caja blanca · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_una_extraccion_rechazada_no_se_confunde_con_el_servicio_caido` | Una extraccion rechazada no se confunde con el servicio caido | Integración · caja blanca · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_error_del_proveedor_con_codigo_200_se_reconoce` | Pasa con los modelos gratuitos hospedados: la pasarela contesta bien y el fallo es del modelo de arriba. Mensaje real de OpenRouter. | Integración · caja blanca · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_la_clave_se_muestra_enmascarada` | La clave se muestra enmascarada | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_sin_clave_no_hay_nada_que_enmascarar` | Sin clave no hay nada que enmascarar | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_la_direccion_del_catalogo_se_deduce_de_la_del_chat` | Funciona igual con LM Studio que con un proveedor remoto, porque `/v1/` es parte de la convención de la API que los dos implementan. | Integración · caja blanca · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |

### `test_consola.py`

> La salida de consola en ASCII. Existe por un modo de falla concreto en Windows: la consola corre en cp1252, y un comando que imprima un carácter fuera de ese juego muere con `UnicodeEncodeError` **después** de haber hecho el trabajo — la base quedó escrita y la salida no alcanzó a decir cuánto se procesó. Los textos propios del proyecto ya se escriben en ASCII. El problema son los ajenos: el…

**Tipos en este archivo:** Unitaria · caja negra · funcional — 3; Unitaria · caja negra · validación — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_los_diacriticos_se_sacan_conservando_la_lectura` | Se descompone y se quitan las tildes en vez de reemplazar la letra entera: "Tankobon" se lee, "T?nk?bon" no. | Unitaria · caja negra · funcional | Unidad | `original`, `esperado` — 4 casos | Cumple |
| `test_lo_que_no_tiene_equivalente_se_reemplaza_sin_romper` | Un kanji no se puede transcribir. Perder ese carácter es peor que el original pero infinitamente mejor que perder el resto de la salida. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_resultado_siempre_se_puede_escribir_en_la_consola` | La garantía que el módulo entero existe para dar. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_un_valor_vacio_no_rompe` | Un asunto ausente es normal; que el comando explote por eso, no. | Unitaria · caja negra · validación | Unidad | `vacio` — 2 casos | Cumple |

### `test_cotizaciones.py`

> Cotización del peso frente a las monedas con las que se importa.

**Tipos en este archivo:** Unitaria · caja negra · frontera — 13; Unitaria · caja blanca · frontera — 5.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_dolar_sale_directo_de_la_paridad_contra_el_peso` | El dolar sale directo de la paridad contra el peso | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_euro_y_el_yen_salen_por_paridad_cruzada` | 1500 pesos por dólar y 0,8 euros por dólar dan 1875 pesos por euro. | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_solo_se_ofrecen_las_tres_monedas_del_negocio` | El servicio devuelve 160 monedas; el desplegable ofrece tres. | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_peso_vale_un_peso_sin_consultar_nada` | La moneda local no depende de que ningún servicio esté en línea. | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_una_respuesta_sin_exito_se_trata_como_caida` | Una respuesta sin exito se trata como caida | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_una_respuesta_sin_la_paridad_del_peso_no_sirve` | Una respuesta sin la paridad del peso no sirve | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_una_paridad_rota_no_genera_una_cotizacion` | Un cero o un negativo no son un dato: son una respuesta rota. Dejarlos pasar pondría el precio de todo un lote importado en cero. | Unitaria · caja negra · frontera | Unidad | `valor` — 4 casos | Cumple |
| `test_una_moneda_rota_se_descarta_sin_tirar_abajo_las_otras` | Una moneda rota se descarta sin tirar abajo las otras | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_la_segunda_consulta_sale_de_la_cache` | La segunda consulta sale de la cache | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_si_la_api_no_responde_se_usa_el_respaldo_local` | Si la api no responde se usa el respaldo local | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_respaldo_versionado_tiene_las_tres_monedas_y_su_fecha` | El respaldo versionado tiene las tres monedas y su fecha | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_una_cotizacion_de_hace_meses_se_marca_como_desactualizada` | El aviso existe porque un tipo de cambio viejo no es como una provincia vieja: usarlo sin mirarlo deja mal el precio de todo el lote. | Unitaria · caja blanca · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_una_cotizacion_de_hoy_no_se_marca_como_desactualizada` | Una cotizacion de hoy no se marca como desactualizada | Unitaria · caja blanca · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_sin_ninguna_cotizacion_se_considera_desactualizada` | Ante la duda, se avisa: es preferible una revisión de más que un precio calculado con un dato que nadie sabe de cuándo es. | Unitaria · caja blanca · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_resumen_para_la_pantalla_trae_todo_masticado` | El resumen para la pantalla trae todo masticado | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_comando_reescribe_el_respaldo` | El comando reescribe el respaldo | Unitaria · caja blanca · frontera | Unidad | `tmp_path` | Cumple |
| `test_el_comando_no_pisa_el_respaldo_si_la_api_falla` | El comando no pisa el respaldo si la api falla | Unitaria · caja blanca · frontera | Unidad | `tmp_path` | Cumple |
| `test_las_cabeceras_de_las_integraciones_son_ascii` | Un valor de cabecera HTTP viaja en ASCII. Con tildes, Cloudflare —que está delante de buena parte de las APIs públicas— contesta 403, y el error llega como un rechazo genérico que no dice nada de la causa. Este test es el recordatorio de… | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |

### `test_georef.py`

> Integración con georef-ar-api: caché, respaldo y degradación.

**Tipos en este archivo:** Unitaria · caja negra · frontera — 8; Unitaria · caja blanca · frontera — 4; Sistema · caja negra · funcional — 2.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_las_provincias_salen_de_la_api_ordenadas` | Las provincias salen de la api ordenadas | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_la_segunda_consulta_sale_de_la_cache` | No se castiga a un servicio público gratuito con una consulta por visita. | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_si_la_api_no_responde_se_usa_el_respaldo_local` | El registro no puede depender de que un tercero esté en línea. | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_respaldo_se_cachea_por_menos_tiempo_que_la_api` | Si el servicio vuelve enseguida, no seguimos un día con la foto vieja. | Unitaria · caja blanca · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_un_error_de_red_no_se_propaga` | `pedir_json` traga la excepción: la pantalla tiene que renderizar igual. | Unitaria · caja blanca · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_respaldo_versionado_tiene_las_veinticuatro_jurisdicciones` | El respaldo versionado tiene las veinticuatro jurisdicciones | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_las_localidades_se_devuelven_sin_repetir_y_ordenadas` | Las localidades se devuelven sin repetir y ordenadas | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_sin_provincia_no_se_consulta_la_api` | Sin provincia no se consulta la api | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_si_la_api_no_responde_las_localidades_quedan_vacias` | Se pierde la sugerencia, no la posibilidad de escribir la localidad. | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_la_cache_de_localidades_es_por_provincia` | La cache de localidades es por provincia | Unitaria · caja negra · frontera | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_endpoint_de_localidades_es_publico` | El registro es público (CU-CLI-ALT): pedir localidades no puede exigir sesión. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_el_endpoint_sin_provincia_devuelve_lista_vacia` | El endpoint sin provincia devuelve lista vacia | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |
| `test_el_comando_reescribe_el_respaldo` | El comando reescribe el respaldo | Unitaria · caja blanca · frontera | Unidad | `tmp_path` | Cumple |
| `test_el_comando_no_pisa_el_respaldo_si_la_api_falla` | Un respaldo vacío es peor que uno viejo: deja el formulario sin provincias. | Unitaria · caja blanca · frontera | Unidad | `tmp_path` | Cumple |

### `test_paises.py`

> Catálogo de códigos telefónicos de país.

**Tipos en este archivo:** Unitaria · caja negra · funcional — 7; Unitaria · caja blanca · funcional — 2.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_los_paises_salen_de_la_api_ordenados_por_nombre` | Los paises salen de la api ordenados por nombre | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_una_fila_sin_codigo_se_descarta_sin_romper_el_resto` | Una fila sin codigo se descarta sin romper el resto | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_codigo_se_recorta_al_primer_grupo_de_digitos` | "+1 684" es Estados Unidos con un área adentro: el país es "+1". | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_una_respuesta_con_error_se_trata_como_caida` | Una respuesta con error se trata como caida | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_la_segunda_consulta_sale_de_la_cache` | La segunda consulta sale de la cache | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_si_la_api_no_responde_se_usa_el_respaldo_local` | Si la api no responde se usa el respaldo local | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_todos_los_codigos_del_respaldo_entran_en_el_campo` | `Usuario.telefono_pais` tiene `max_length=4`: "+999" es el tope. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_comando_reescribe_el_respaldo` | El comando reescribe el respaldo | Unitaria · caja blanca · funcional | Unidad | `tmp_path` | Cumple |
| `test_el_comando_no_pisa_el_respaldo_si_la_api_falla` | El comando no pisa el respaldo si la api falla | Unitaria · caja blanca · funcional | Unidad | `tmp_path` | Cumple |

### `test_panel.py`

> Tablero de entrada del Administrador y menú lateral del backoffice.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 7; Sistema · caja negra · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_las_cifras_cuentan_cada_estado_por_separado` | Las cifras cuentan cada estado por separado | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_muestra_la_actividad_reciente_del_log` | Muestra la actividad reciente del log | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |
| `test_la_actividad_se_recorta_a_las_ultimas_doce_entradas` | La actividad se recorta a las ultimas doce entradas | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |
| `test_los_bloqueos_del_dia_se_muestran` | Los bloqueos del dia se muestran | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_sin_bloqueos_el_contador_esta_en_cero` | Sin bloqueos el contador esta en cero | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_solo_el_administrador_entra_al_panel` | Solo el administrador entra al panel | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client`; `rol_sin_permiso` — 2 casos | Cumple |
| `test_el_menu_lateral_enlaza_las_secciones_disponibles` | El menu lateral enlaza las secciones disponibles | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_menu_marca_la_pantalla_en_la_que_se_esta` | El menu marca la pantalla en la que se esta | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |

### `test_permisos_por_rol.py`

> RNF-03: el control de acceso por rol se valida siempre del lado del servidor.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 2; Sistema · caja negra · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_cada_rol_entra_a_su_propia_seccion` | Cada rol entra a su propia seccion | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`; `rol` — 3 casos | Cumple |
| `test_un_rol_que_no_corresponde_recibe_403` | Un request directo con el rol equivocado corta en 403, sin datos parciales. | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client`; `rol`, `url_ajena` — 4 casos | Cumple |
| `test_sin_sesion_redirige_al_login` | Sin sesion redirige al login | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`; `url` — 3 casos | Cumple |

### `test_plantillas.py`

> Reglas que tienen que cumplir todas las plantillas del proyecto.

**Tipos en este archivo:** Unitaria · caja negra · funcional — 2; Sistema · caja negra · funcional — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_hay_plantillas_para_revisar` | Si el recorrido dejara de encontrar archivos, el test de abajo pasaría solo. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_ninguna_plantilla_usa_comentarios_de_varias_lineas` | Ninguna plantilla usa comentarios de varias lineas | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_las_pantallas_publicas_se_renderizan_sin_sesion` | Humo: las tres pantallas públicas cargan enteras para un visitante. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client`; base de datos (`django_db`) | Cumple |

### `test_respaldo.py`

> El comando de respaldo de la base. `pg_dump` no se llama de verdad acá. No es por velocidad: el ejecutable puede no estar en la máquina que corre los tests —en el CI la base es un contenedor y el cliente no viene instalado— y un test que dependa de eso falla por el entorno y no por el código. Lo que se prueba es la lógica que rodea al volcado, que es donde están las decisiones: - que un respaldo…

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Integración · caja blanca · funcional — 15; Integración · caja blanca · validación — 2.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_deja_un_respaldo_con_la_fecha_en_el_nombre` | Deja un respaldo con la fecha en el nombre | Integración · caja blanca · funcional | Base de datos | `tmp_path`, `volcado_falso` | Cumple |
| `test_crea_la_carpeta_si_no_existe` | Una tarea programada corre sin nadie mirando: si el destino no existe, tiene que crearlo y no fallar. | Integración · caja blanca · funcional | Base de datos | `tmp_path`, `volcado_falso` | Cumple |
| `test_el_formato_es_el_propio_de_postgresql` | `custom` viene comprimido y permite restaurar una tabla sola; un `.sql` plano no permite ni lo uno ni lo otro. | Integración · caja blanca · funcional | Base de datos | `tmp_path`, `volcado_falso` | Cumple |
| `test_no_espera_una_contrasena_por_teclado` | Sin `--no-password`, un respaldo mal configurado no falla: se cuelga esperando a alguien que en una tarea programada no está. | Integración · caja blanca · funcional | Base de datos | `tmp_path`, `volcado_falso` | Cumple |
| `test_la_contrasena_no_va_en_los_argumentos` | Los argumentos de un proceso los lee cualquiera que liste procesos. | Integración · caja blanca · funcional | Base de datos | `tmp_path`, `volcado_falso` | Cumple |
| `test_la_contrasena_va_por_el_entorno` | La contrasena va por el entorno | Integración · caja blanca · funcional | Base de datos | `tmp_path`, `volcado_falso` | Cumple |
| `test_un_respaldo_ilegible_se_descarta` | `pg_dump` puede terminar en 0 y dejar el archivo truncado. Contarlo como bueno es peor que no tenerlo: se descubre el día que hace falta. | Integración · caja blanca · funcional | Base de datos | `tmp_path`, `herramientas` | Cumple |
| `test_si_pg_dump_falla_no_queda_un_archivo_a_medias` | Si pg dump falla no queda un archivo a medias | Integración · caja blanca · funcional | Base de datos | `tmp_path`, `herramientas` | Cumple |
| `test_un_pg_dump_mas_viejo_que_el_servidor_se_rechaza` | Se niega a volcar y el mensaje aparece justo cuando hace falta el respaldo. Mejor enterarse acá, que dice qué actualizar. | Integración · caja blanca · validación | Base de datos | `tmp_path`, `herramientas` | Cumple |
| `test_sin_pg_restore_no_se_respalda` | Sin con qué verificar, el comando no genera nada: un respaldo sin verificar es la mitad del trabajo y toda la falsa tranquilidad. | Integración · caja blanca · funcional | Base de datos | `tmp_path` | Cumple |
| `test_conserva_los_mas_nuevos_y_borra_el_resto` | Conserva los mas nuevos y borra el resto | Integración · caja blanca · funcional | Base de datos | `tmp_path`, `volcado_falso` | Cumple |
| `test_conservar_cero_no_borra_nada` | Conservar cero no borra nada | Integración · caja blanca · funcional | Base de datos | `tmp_path`, `volcado_falso` | Cumple |
| `test_no_toca_lo_que_no_genero` | Borrar por antigüedad archivos ajenos es la peor forma de fallar que tiene un limpiador, y la carpeta puede tener cualquier cosa. | Integración · caja blanca · funcional | Base de datos | `tmp_path`, `volcado_falso` | Cumple |
| `test_verificar_solo_no_genera_un_respaldo_nuevo` | Verificar solo no genera un respaldo nuevo | Integración · caja blanca · funcional | Base de datos | `tmp_path`, `volcado_falso` | Cumple |
| `test_verificar_solo_avisa_si_alguno_esta_roto` | Verificar solo avisa si alguno esta roto | Integración · caja blanca · validación | Base de datos | `tmp_path`, `herramientas` | Cumple |
| `test_verificar_solo_con_la_carpeta_vacia_no_es_un_error` | Es el estado del primer día, y una tarea programada que devuelve error ese día manda a buscar un problema que no existe. | Integración · caja blanca · funcional | Base de datos | `tmp_path`, `herramientas` | Cumple |
| `test_la_salida_es_ascii` | La consola de Windows corre en cp1252: un acento la hace reventar con el trabajo ya hecho y sin decir cuánto se procesó. | Integración · caja blanca · funcional | Base de datos | `tmp_path`, `volcado_falso`, `capsys` | Cumple |


## Proveedores — `apps/suppliers`

### `test_alta_proveedor.py`

> CU-PRV-ALT — Registrar Proveedor Editorial. Lo que se prueba acá no es un CRUD: es que el alta deje bien puesta la única cosa que este módulo le aporta al resto del sistema, que es el filtro de remitentes válidos del procesamiento automático de CU-ALT-NOV.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 8; Sistema · caja gris · idempotencia — 4; Sistema · caja negra · funcional — 2; Sistema · caja gris · validación — 1; Sistema · caja gris · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_alta_deja_el_proveedor_activo` | Postcondición del CU: queda registrado con estado Activo. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_correo_queda_habilitado_como_remitente_valido` | La otra postcondición, y la que le da sentido al módulo entero. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_los_campos_opcionales_no_traban_el_alta` | E1 solo se dispara con los obligatorios: nombre de contacto, teléfono y notas pueden quedar vacíos. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_los_campos_opcionales_se_guardan_cuando_vienen` | Los campos opcionales se guardan cuando vienen | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_falta_un_campo_obligatorio_y_no_procede` | E1: se resaltan los faltantes y el formulario permanece abierto. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`; `faltante` — 2 casos | Cumple |
| `test_una_razon_social_repetida_es_rechazada` | Una razon social repetida es rechazada | Sistema · caja gris · idempotencia | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_correo_repetido_es_rechazado` | Un correo repetido es rechazado | Sistema · caja gris · idempotencia | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_conflicto_se_informa_con_enlace_a_la_ficha_existente` | E2 lo pide explícitamente: sin el enlace, el aviso obligaría a salir a buscar el proveedor a mano. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_razon_social_repetida_se_detecta_sin_distinguir_mayusculas` | "Editorial Ivrea" y "EDITORIAL IVREA" son el mismo proveedor escrito distinto: con dos filas habría dos agendas del mismo interlocutor. | Sistema · caja gris · idempotencia | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_correo_repetido_se_detecta_sin_distinguir_mayusculas` | El correo repetido se detecta sin distinguir mayusculas | Sistema · caja gris · idempotencia | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_una_razon_social_de_una_letra_es_rechazada` | Una sola letra no distingue a nadie y casi siempre es un enter de más. | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_razon_social_se_normaliza` | La razon social se normaliza | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_correo_se_guarda_en_minuscula` | Es la clave con la que CU-ALT-NOV reconoce un remitente: normalizarlo al guardar hace que la búsqueda del pipeline y la pantalla digan lo mismo. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_queda_auditada` | El alta queda auditada | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |
| `test_solo_el_administrador_da_de_alta_proveedores` | Solo el administrador da de alta proveedores | Sistema · caja gris · control de acceso | Pantalla (HTTP) | `client`; `rol_sin_permiso` — 2 casos | Cumple |
| `test_sin_sesion_el_alta_redirige_al_login` | Sin sesion el alta redirige al login | Sistema · caja negra · funcional | Pantalla (HTTP) | `client` | Cumple |

### `test_baja_proveedor.py`

> CU-PRV-BAJ — Dar de Baja Proveedor Editorial, y la reactivación que lo revierte. La baja tiene dos mitades que conviene no confundir: el **informe de impacto** (pasos 2 y 3, lo que el Administrador lee antes de decidir) y el **efecto** (paso 5, sacar el correo del filtro de remitentes sin perder el historial).

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 10; Sistema · caja negra · funcional — 3; Sistema · caja gris · control de acceso — 2; Sistema · caja gris · idempotencia — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_informe_cuenta_los_productos_vinculados` | El informe cuenta los productos vinculados | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_sin_impacto_el_informe_lo_dice_explicitamente` | A1: si no hay impacto, el informe lo indica en vez de mostrarse vacío. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_informe_no_afirma_que_no_hay_propuestas_de_restock` | El módulo de Restock no existe todavía. Decir "0 propuestas afectadas" sería mentir sobre un dato que el propio CU considera parte de la decisión; la pantalla dice que no se puede determinar. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_mirar_el_informe_no_da_de_baja_nada` | A2: el Administrador puede revisar el impacto y no confirmar. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_baja_deja_el_proveedor_inactivo` | La baja deja el proveedor inactivo | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_baja_saca_el_correo_del_filtro_de_remitentes` | Es la postcondición que le da sentido a la baja: el pipeline de CU-ALT-NOV deja de procesar sus mensajes. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_los_productos_conservan_la_referencia_al_proveedor` | La baja es lógica: el CU pide expresamente que el historial sobreviva. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_baja_queda_auditada_con_el_impacto` | La baja queda auditada con el impacto | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `administrador` | Cumple |
| `test_dar_de_baja_dos_veces_no_registra_dos_bajas` | El doble envío del formulario es el caso normal, no el raro. | Sistema · caja gris · idempotencia | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_reactivar_devuelve_el_correo_al_filtro_de_remitentes` | Reactivar devuelve el correo al filtro de remitentes | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_reactivar_conserva_los_datos_y_el_historial` | Reactivar conserva los datos y el historial | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_reactivar_queda_auditado` | Reactivar queda auditado | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_reactivar_uno_ya_activo_no_hace_nada` | Reactivar uno ya activo no hace nada | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_baja_no_bloquea_la_razon_social_para_siempre` | Es el motivo por el que la reactivación existe: la razón social y el correo son únicos *en cualquier estado*, así que sin vuelta atrás un proveedor dado de baja se bloquearía a sí mismo. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_solo_el_administrador_da_de_baja` | Solo el administrador da de baja | Sistema · caja gris · control de acceso | Pantalla (HTTP) | `client`; `rol_sin_permiso` — 2 casos | Cumple |
| `test_solo_el_administrador_reactiva` | Solo el administrador reactiva | Sistema · caja gris · control de acceso | Pantalla (HTTP) | `client`; `rol_sin_permiso` — 2 casos | Cumple |

### `test_borradores_del_correo.py`

> El pipeline entero: de un `.eml` en la cola a borradores con su portada. Los tests de `apps/catalog/tests/test_borradores.py` prueban las reglas sobre una extracción escrita a mano. Estos prueban lo otro: que el correo real —con su tabla de maquetado, su logo embebido y sus portadas con `Content-ID`— llegue hasta el borrador sin perder nada en el camino. Es el paso 7 de CU-ALT-NOV y es donde más…

**Tipos en este archivo:** Integración · caja gris · funcional — 10; Sistema · caja negra · funcional — 4; Integración · caja gris · idempotencia — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_procesar_un_correo_de_la_cola_deja_sus_borradores` | Procesar un correo de la cola deja sus borradores | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_un_correo_que_no_es_de_novedades_no_genera_borradores` | Es lo que justifica que la cola exista: por la casilla del proveedor llegan facturas y saludos, y ninguno tiene que ensuciar la revisión. | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_si_el_modelo_no_contesta_no_se_genera_ningun_borrador` | Un fallo del servicio no puede dejar medio borrador cargado. | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_la_portada_embebida_termina_como_archivo_del_borrador` | No se descarga de ninguna URL: ya vino adentro del correo (corrección 16). | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_el_borrador_conserva_el_identificador_de_su_portada` | Es lo que permite volver a sacarla del archivo original si algo sale mal, sin tener que adivinar cuál era. | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_una_portada_inventada_deja_el_borrador_sin_imagen_y_con_su_reparo` | La extracción ya descarta el identificador que no existe entre las partes del correo; acá se verifica que eso llegue hasta el borrador. | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_un_producto_sin_portada_no_interrumpe_al_resto` | CU-ALT-NOV: la portada que falta no corta el procesamiento del correo. | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_el_logo_del_encabezado_no_se_confunde_con_una_portada` | El correo de ejemplo trae un logo embebido que **no** es tapa de nada. Si las portadas se correlacionaran por orden, correría todo un lugar. | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_sin_archivo_guardado_los_borradores_salen_igual_sin_portada` | El archivo es el respaldo, no una precondición: si faltara, la revisión sigue siendo posible y la portada se adjunta a mano. | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_el_periodo_anunciado_llega_hasta_la_fecha_del_borrador` | El periodo anunciado llega hasta la fecha del borrador | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_reprocesar_un_correo_no_duplica_sus_borradores` | Ajustar el prompt y volver a correr es el caso normal, no el raro. | Integración · caja gris · idempotencia | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_la_ficha_muestra_los_borradores_generados` | Van junto al contenido del que salieron: un borrador con el precio del tomo siguiente solo se nota teniendo las dos cosas a la vista. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo`; base de datos (`django_db`) | Cumple |
| `test_la_ficha_marca_los_borradores_incompletos` | La ficha marca los borradores incompletos | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo`; base de datos (`django_db`) | Cumple |
| `test_la_ficha_ya_no_dice_que_falta_el_extractor` | Decía que el procesamiento se habilitaba "cuando esté el extractor conectado", y el extractor existe desde que el pipeline genera borradores. Lo que falta es el botón, y falta por RNF-02, que es otra cosa. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo`; base de datos (`django_db`) | Cumple |
| `test_un_correo_sin_procesar_no_muestra_la_seccion_de_borradores` | Una sección vacía se leería como "no generó nada", que es distinto de "todavía no se procesó". | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo`; base de datos (`django_db`) | Cumple |

### `test_cola_de_correos.py`

> La cola de aprobación: ingesta, pantallas y descarte. Es la pieza que **no está en la fuente**. CU-ALT-NOV describe un ciclo que parsea todo lo que encuentre de un remitente registrado; acá el correo llega, se archiva y espera una decisión. Ver la corrección 11 de `docs/correcciones-fuente.md`.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 10; Integración · caja negra · funcional — 5; Sistema · caja gris · funcional — 5; Integración · caja gris · funcional — 4; Integración · caja gris · idempotencia — 1; Sistema · caja gris · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_un_correo_de_un_proveedor_habilitado_entra_a_la_cola` | Un correo de un proveedor habilitado entra a la cola | Integración · caja negra · funcional | Base de datos | `ivrea` | Cumple |
| `test_el_correo_queda_archivado_entero` | CU-ALT-NOV pide archivar el original como respaldo. Además es lo que permite volver a extraer el contenido si la extracción mejora, sin depender de que el correo siga en la casilla. | Integración · caja negra · funcional | Base de datos | `ivrea` | Cumple |
| `test_se_guarda_el_contenido_extraido_y_el_resumen_de_las_portadas` | El contenido se guarda y no se recalcula al leer: es exactamente lo que se le va a mandar al modelo, y tenerlo escrito hace que el paso siguiente sea reproducible. | Integración · caja negra · funcional | Base de datos | `ivrea` | Cumple |
| `test_un_remitente_no_registrado_no_genera_nada` | E1 de CU-ALT-NOV: se loguea y el ciclo sigue con el mensaje siguiente. No levanta: un correo raro no puede tumbar la lectura de la casilla entera. | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_proveedor_dado_de_baja_no_alimenta_la_cola` | Un proveedor dado de baja no alimenta la cola | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_proveedor_con_el_procesamiento_apagado_tampoco` | Es el efecto práctico del interruptor de A6: le seguís comprando, pero su casilla no entra al pipeline. | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_mismo_correo_dos_veces_no_se_duplica` | Un ciclo que se ejecuta dos veces —porque se reintentó, o porque el mensaje quedó sin marcar en la casilla— no puede encolar dos filas. | Integración · caja gris · idempotencia | Base de datos | `ivrea` | Cumple |
| `test_reingerir_no_pisa_un_correo_ya_resuelto` | Si lo pisara, un correo ya descartado volvería a la cola en cada pasada. | Integración · caja gris · funcional | Base de datos | `ivrea`, `administrador` | Cumple |
| `test_un_correo_sin_identificador_no_entra` | Sin `Message-ID` no hay clave de idempotencia, y cada pasada lo volvería a encolar. Se descarta en vez de inventarle uno: un identificador fabricado daría distinto en cada lectura y el efecto sería el mismo duplicado. | Integración · caja gris · funcional | Base de datos | `ivrea` | Cumple |
| `test_un_aviso_de_demora_entra_igual_a_la_cola` | No se procesa distinto todavía, pero entra: es la razón de ser de la cola de aprobación —por la casilla del proveedor no llegan solo novedades—. | Integración · caja negra · funcional | Base de datos | `ivrea` | Cumple |
| `test_la_cola_lista_los_correos` | La cola lista los correos | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `ivrea` | Cumple |
| `test_la_cola_cuenta_los_pendientes` | La cola cuenta los pendientes | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `ivrea` | Cumple |
| `test_la_cola_vacia_no_es_un_error` | Es el resultado normal de un ciclo sin novedades, que el propio CU-ALT-NOV contempla en E6. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_buscador_de_la_cola_filtra` | El buscador de la cola filtra | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `ivrea` | Cumple |
| `test_la_ficha_muestra_el_contenido_extraido` | Es lo que permite darse cuenta de que la extracción salió mal antes de gastar un solo ciclo del modelo. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `ivrea` | Cumple |
| `test_la_ficha_muestra_las_portadas_embebidas` | La ficha muestra las portadas embebidas | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `ivrea` | Cumple |
| `test_la_ficha_muestra_que_va_a_heredar_el_borrador` | Si el proveedor tiene la editorial equivocada, todo lo que salga de este correo va a nacer mal: hay que poder verlo antes de aprobar. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `ivrea` | Cumple |
| `test_descartar_lo_saca_de_la_cola` | Descartar lo saca de la cola | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `ivrea`, `administrador` | Cumple |
| `test_el_motivo_del_descarte_es_obligatorio` | Mismo criterio que el rechazo de un borrador en CU-ALT-REV: una cola llena de descartes sin explicación no sirve para entender nada después. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `ivrea` | Cumple |
| `test_un_motivo_de_una_letra_no_alcanza` | Un motivo de una letra no alcanza | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `ivrea` | Cumple |
| `test_el_descarte_queda_auditado` | El descarte queda auditado | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `ivrea`, `administrador` | Cumple |
| `test_un_correo_ya_resuelto_no_se_vuelve_a_resolver` | El doble envío del formulario es el caso normal, no el raro. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `ivrea`, `administrador` | Cumple |
| `test_la_ficha_de_un_resuelto_no_ofrece_descartarlo` | La ficha de un resuelto no ofrece descartarlo | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `ivrea`, `administrador` | Cumple |
| `test_el_get_de_la_ficha_no_resuelve_nada` | El get de la ficha no resuelve nada | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin`, `ivrea` | Cumple |
| `test_la_cola_es_solo_del_administrador` | La cola es solo del administrador | Sistema · caja gris · control de acceso | Pantalla (HTTP) | `client`, `ivrea`; `rol_sin_permiso` — 2 casos | Cumple |
| `test_el_menu_enlaza_la_cola` | El menu enlaza la cola | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |

### `test_comando_extraer.py`

> El comando `extraer_novedades`: la puerta por la que hoy corre el pipeline. Mientras no exista el ejecutor en segundo plano, esta es la **única** forma de procesar un correo de la cola, así que romperlo deja el pipeline sin entrada. Y es además el lugar donde se ve si funcionó: la diferencia entre "entendió cinco" y "generó tres" es lo que dice si el modelo está leyendo bien o si el catálogo ya…

**Tipos en este archivo:** Integración · caja negra · funcional — 7; Integración · caja gris · funcional — 4.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_sin_argumentos_no_procesa_nada` | El modelo corre local y cada pasada son minutos de GPU: un comando que procese todo por omisión es la forma más rápida de gastar una tarde. | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_un_correo_inexistente_lo_dice_en_vez_de_callarse` | Un correo inexistente lo dice en vez de callarse | Integración · caja negra · funcional | Base de datos | `db` | Cumple |
| `test_procesa_el_correo_que_se_le_nombra` | Procesa el correo que se le nombra | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_con_pendientes_recorre_la_cola` | Con pendientes recorre la cola | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_una_cola_vacia_lo_informa` | Una cola vacia lo informa | Integración · caja negra · funcional | Base de datos | `db` | Cumple |
| `test_informa_por_separado_lo_entendido_y_lo_generado` | Es la diferencia que dice si el pipeline está funcionando o si el catálogo ya tenía todo. | Integración · caja negra · funcional | Base de datos | `correo`, `editorial`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_enumera_lo_omitido_con_su_motivo` | Enumera lo omitido con su motivo | Integración · caja negra · funcional | Base de datos | `correo`, `editorial`, `tipo`; base de datos (`django_db`) | Cumple |
| `test_informa_los_reparos_del_modelo` | Informa los reparos del modelo | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_un_correo_que_no_era_de_novedades_lo_aclara` | Sin esta línea, cero borradores se leería como un fallo del pipeline. | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_si_el_modelo_esta_caido_lo_dice_y_no_genera_nada` | Si el modelo esta caido lo dice y no genera nada | Integración · caja gris · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |
| `test_la_salida_es_ascii_aunque_el_correo_traiga_de_todo` | El asunto, el título y los motivos vienen del proveedor y del modelo: pueden traer kanji, tildes o comillas angulares. La consola corre en cp1252 y reventaría con el trabajo ya hecho. | Integración · caja negra · funcional | Base de datos | `correo`; base de datos (`django_db`) | Cumple |

### `test_consulta_proveedores.py`

> CU-PRV-CON — Consultar Proveedores: el listado y la ficha. Es solo lectura y el CU es explícito en que **no genera entrada de auditoría**. Ese último punto también se prueba: consultar no es operar, y un log que registrara cada consulta enterraría las operaciones reales.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 14; Sistema · caja negra · control de acceso — 3; Sistema · caja gris · funcional — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_listado_muestra_los_proveedores` | El listado muestra los proveedores | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_listado_sale_ordenado_alfabeticamente` | CU-PRV-CON paso 2: la vista por defecto es alfabética. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_cada_fila_trae_la_cantidad_de_productos_vinculados` | Lo pide el paso 2, y se anota en la consulta: contarlo por fila serían tantas consultas extra como proveedores haya. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_buscador_encuentra_por_los_tres_campos` | Paso 3: búsqueda por texto libre. El nombre de contacto se suma a los dos que nombra el CU porque es por donde se busca cuando lo que se recuerda es con quién se habló, no cómo se llama la empresa. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`; `campo` — 3 casos | Cumple |
| `test_el_filtro_de_estado_funciona` | El filtro de estado funciona | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_estado_inventado_se_ignora` | Un valor arbitrario en la query string no rompe ni filtra de más. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_parcial_devuelve_solo_el_fragmento_de_la_tabla` | El parcial devuelve solo el fragmento de la tabla | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_sin_proveedores_ofrece_el_acceso_directo_al_alta` | E2 del CU: la vista vacía informa y ofrece el camino a CU-PRV-ALT. | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_filtro_sin_resultados_ofrece_limpiarlo` | E1 del CU. Es un mensaje distinto del de "no hay ninguno" porque es un problema distinto: acá sí hay proveedores, solo que no estos. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_consultar_no_genera_entrada_de_auditoria` | Postcondición explícita del CU: solo lectura. Se miran las acciones del módulo y no el log entero porque abrir la sesión del Administrador ya deja su propia entrada, que no tiene nada que ver con esto. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_muestra_los_datos_de_contacto` | La ficha muestra los datos de contacto | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_lista_los_productos_vinculados` | La ficha lista los productos vinculados | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_dice_si_el_correo_se_reconoce_como_remitente` | Es la consecuencia práctica del estado, y no se deduce sola de la palabra "Inactivo". | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_encadena_las_acciones_del_modulo` | CU-PRV-CON paso 5: desde la ficha se inician CU-PRV-EDI y CU-PRV-BAJ. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_de_un_inactivo_ofrece_reactivar_y_no_dar_de_baja` | La ficha de un inactivo ofrece reactivar y no dar de baja | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_avisa_que_falta_el_historial_de_restock` | El paso 4 del CU lo pide, pero el módulo de Restock no existe. Se dice en vez de mostrar una tabla vacía, que se leería como "nunca se le pidió nada". | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_listado_no_filtra_datos_a_otros_roles` | El listado no filtra datos a otros roles | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client`; `rol_sin_permiso` — 2 casos | Cumple |
| `test_el_menu_del_administrador_enlaza_proveedores` | El menu del administrador enlaza proveedores | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |

### `test_diagnostico_llm.py`

> La pantalla de diagnóstico del modelo de lenguaje. No corresponde a ningún caso de uso: es una herramienta de operación. Existe porque el pipeline depende de un servicio que corre **afuera de Django** y que se apaga sin avisar — sin ella, la única forma de enterarse es que un correo quede fallido con un mensaje genérico. Como todo lo demás, no llama al modelo de verdad: se parchea…

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 28; Integración · caja negra · frontera — 3; Integración · caja negra · funcional — 1; Sistema · caja negra · validación — 1; Sistema · caja negra · frontera — 1; Sistema · caja negra · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_muestra_el_servicio_en_linea_con_sus_modelos` | Muestra el servicio en linea con sus modelos | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_muestra_el_servicio_caido_cuando_no_responde` | `pedir` devuelve `None` sin conexión. La pantalla tiene que decirlo, no quedarse en blanco: es la pregunta que se viene a responder. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_estado_se_consulta_con_un_timeout_corto` | No con el del modelo. Generar puede tardar minutos y está bien, pero preguntar si está vivo tiene que contestar enseguida: con el timeout largo, la pantalla contra un servicio caído quedaría cargando cinco minutos. | Integración · caja negra · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_catalogo_de_modelos_se_deduce_de_la_direccion_del_chat` | Se deduce en vez de pedir otra variable de entorno: son del mismo servidor, y configurar las dos es una oportunidad más de que queden apuntando a lugares distintos. | Integración · caja negra · frontera | Base de datos | `settings` | Cumple |
| `test_una_direccion_que_no_parece_esa_api_lo_dice` | Una direccion que no parece esa api lo dice | Integración · caja negra · frontera | Base de datos | `settings` | Cumple |
| `test_un_servicio_sin_modelos_cargados_se_distingue_de_uno_caido` | Responde, así que no está caído — pero no va a poder generar nada. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_muestra_con_que_esta_configurado` | Muestra con que esta configurado | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `settings` | Cumple |
| `test_la_muestra_viene_cargada_y_es_editable` | El valor de la pantalla no es correr una prueba fija sino poder pegar el contenido de un correo que salió mal y ver qué entiende. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_cada_carga_trae_una_muestra_distinta` | Mostrar siempre los mismos tres tomos deja la duda de si el modelo los está reconociendo en vez de leerlos. Con datos nuevos cada vez, lo que se ve es que lee. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_muestra_trae_un_isbn_corrupto_a_proposito` | Es la mitad interesante de la demostración: se ve que el sistema lo detecta, no solo que el modelo copia bien. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_probar_muestra_lo_que_el_modelo_entendio` | Probar muestra lo que el modelo entendio | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_prueba_declara_los_identificadores_de_portada_de_la_muestra` | Sin declararlos, la comprobación de portada inexistente no tendría contra qué comparar y la demostración mostraría una validación que no valida. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_los_reparos_se_muestran_en_pantalla` | Es lo que hace visible que el sistema le desconfía al modelo. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_muestra_el_prompt_que_recibe_el_modelo` | Con la versión, que es lo que vuelve comparable un resultado con otro. El prompt deja de ser algo que hay que creer y pasa a verse. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_muestra_la_respuesta_en_crudo` | Cuando algo sale raro es lo único que explica por qué. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_informa_cuanto_tardo` | Con un modelo local, la diferencia entre dos segundos y dos minutos decide si el pipeline necesita una cola de verdad. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_contenido_vacio_no_se_manda_al_modelo` | Gastar una pasada del modelo en una caja vacía es tirar minutos de GPU. | Sistema · caja negra · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_si_el_servicio_esta_caido_ni_se_intenta_la_extraccion` | Intentarla esperaría el timeout largo entero —minutos— para fallar por lo mismo que el chequeo de estado ya sabe. La pantalla que existe para avisar que el servicio no está no puede ser la que más tarda cuando no está. | Sistema · caja negra · frontera | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_una_respuesta_ilegible_se_distingue_del_servicio_caido` | Se arreglan en lugares distintos: uno es infraestructura, el otro es el prompt o el modelo elegido. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_pantalla_es_solo_del_administrador` | Deja ver la configuración del servicio y permite gastarle tiempo de cómputo: no es información ni una acción para cualquier rol. | Sistema · caja negra · control de acceso | Pantalla (HTTP) | `client`; `rol_sin_permiso` — 2 casos | Cumple |
| `test_el_menu_la_enlaza_dentro_de_proveedores` | El menu la enlaza dentro de proveedores | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_pantalla_muestra_el_periodo_que_copio_el_modelo` | La pantalla muestra el periodo que copio el modelo | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_pantalla_muestra_la_fecha_interpretada` | Son dos valores encadenados y hay que ver los dos: un período que el modelo leyó bien y el intérprete no entendió se arregla en otro lugar que uno que el modelo no encontró. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_periodo_ilegible_se_ve_en_la_pantalla` | Su efecto —todos los borradores naciendo Activos— es de los que no dan ningún síntoma, así que tiene que decirse acá. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_sin_periodo_la_pantalla_lo_dice_sin_alarmar` | No anunciar fecha es el caso normal, no un problema. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_pantalla_dice_con_que_estado_nacerian_los_borradores` | Es la consecuencia concreta del período, y es lo que se viene a mirar. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_periodo_pasado_deja_los_borradores_activos` | Un periodo pasado deja los borradores activos | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_pantalla_muestra_la_confianza_que_no_es_alta` | La pantalla muestra la confianza que no es alta | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_muestra_de_la_pantalla_anuncia_un_periodo_futuro` | Si anunciara una fecha pasada, el banco de pruebas nunca ejercitaría la rama de Pre-venta, que es de la que hay que desconfiar. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_solo_se_muestra_el_modelo_configurado` | Solo se muestra el modelo configurado | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_se_avisa_si_el_servidor_no_ofrece_el_modelo_configurado` | Adelanta el 404 más común —un identificador mal copiado— antes de gastar una corrida y recibirlo en medio de un procesamiento. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_con_el_modelo_disponible_se_dice_que_lo_ofrece` | Con el modelo disponible se dice que lo ofrece | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_sin_modelo_declarado_se_muestran_los_cargados` | Ahí sí la lista **es** la respuesta: es lo que el servidor va a contestar. Es el caso normal con un servidor local. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_total_de_modelos_se_dice_como_cifra` | La cifra sirve —confirma que la dirección apunta a la API que se cree—; la lista de nombres, no. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_modo_no_nombra_proveedores` | Los dos valores describen dónde corre el modelo; qué empresa lo hospeda es un dato de la dirección. Nombrar una en un desplegable la convierte en una recomendación que el proyecto no hace. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |

### `test_edicion_proveedor.py`

> CU-PRV-EDI — Editar Proveedor Editorial. El punto delicado no es guardar campos: es que cambiar el correo comercial **redirige el pipeline de CU-ALT-NOV**, y que esa consecuencia se confirme del lado del servidor y no solo con un cartel del navegador.

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja gris · funcional — 5; Sistema · caja negra · funcional — 3; Sistema · caja gris · validación — 2; Sistema · caja gris · control de acceso — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_se_editan_los_datos_de_contacto` | Se editan los datos de contacto | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_cambiar_el_correo_sin_confirmar_es_rechazado` | La advertencia del CU no es informativa: es una puerta. Si viviera solo en el JavaScript, una pestaña de herramientas abierta alcanzaría para sacar del filtro de remitentes el correo por el que entra todo el pipeline de novedades. | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_cambiar_el_correo_confirmado_redirige_el_pipeline` | Postcondición del CU: CU-ALT-NOV empieza a procesar el nuevo y deja de procesar el anterior a partir de la confirmación. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_editar_otros_campos_no_pide_confirmacion` | La confirmación es del cambio de correo, no de la edición: pedirla siempre la convertiría en un clic automático. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_no_ofrece_la_confirmacion_de_cambio_de_correo` | En un alta no hay correo anterior que invalidar. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_correo_de_otro_proveedor_es_rechazado` | E2: no se puede pisar el remitente de otro. Si se pudiera, qué proveedor "es" un mensaje dependería del orden de la consulta. | Sistema · caja gris · validación | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_guardar_sin_cambiar_el_correo_propio_no_choca_consigo_mismo` | Guardar sin cambiar el correo propio no choca consigo mismo | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_proveedor_inactivo_si_se_puede_editar` | La precondición de CU-PRV-EDI dice "cualquier estado", y acá no hay nada que congelar: un proveedor de baja no habilita nada mientras lo esté, porque el filtro de remitentes mira el estado antes que el correo. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_auditoria_guarda_los_valores_anteriores_y_nuevos` | El CU lo pide explícitamente: con solo el estado final no se puede reconstruir qué pasó. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_guardar_sin_cambios_no_genera_entrada_de_auditoria` | Un log lleno de entradas vacías esconde las que importan. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_solo_el_administrador_edita_proveedores` | Solo el administrador edita proveedores | Sistema · caja gris · control de acceso | Pantalla (HTTP) | `client`; `rol_sin_permiso` — 2 casos | Cumple |

### `test_extraccion.py`

> La extracción del modelo: el prompt, la validación y lo que se guarda. **Ninguno de estos tests llama al modelo de verdad.** Se parchea `integraciones.pedir`, que es la única puerta HTTP del proyecto y la misma que corta la fixture `sin_red`. Eso no es solo por velocidad: el modelo corre en `localhost`, así que un test que lo llamara andaría en la máquina del desarrollador —dando una falsa…

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Integración · caja negra · funcional — 32; Integración · caja gris · funcional — 5; Integración · caja negra · frontera — 4; Integración · caja negra · validación — 1; Integración · caja gris · idempotencia — 1; Sistema · caja negra · funcional — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_extrae_los_productos_de_un_correo_de_novedades` | Extrae los productos de un correo de novedades | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_resultado_dice_con_que_version_del_prompt_se_extrajo` | Un borrador de marzo y otro de junio no son comparables, y cuando algo salga raro la primera pregunta va a ser con cuál se hizo. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_esquema_le_exige_al_servidor_la_forma_de_la_respuesta` | Es la primera de las tres defensas: con el esquema declarado, el modelo **no puede** emitir algo que no encaje, y la validación deja de tener que ocuparse de la estructura. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_contenido_del_correo_va_separado_de_las_instrucciones` | Mezclarlos haría que el texto de un correo se pueda leer como una instrucción más. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_aviso_de_demora_no_produce_productos` | Si el modelo clasificó "demora" y devolvió productos igual, se ignoran: mezclar las dos cosas es el error que la clasificación viene a evitar. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_una_intencion_inventada_se_toma_como_otro` | Una intencion inventada se toma como otro | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_isbn_que_no_verifica_se_descarta_con_su_reparo` | Es la defensa que atrapa un ISBN alucinado. Guardarlo sería peor que no tenerlo: pasaría a identificar un producto que no existe, y el chequeo de duplicados dejaría de encontrar el que sí. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_isbn_con_guiones_se_normaliza` | Un isbn con guiones se normaliza | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_sin_isbn_no_hay_reparo` | No tenerlo es válido; inventarlo no. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_una_portada_que_no_esta_en_el_correo_se_ignora` | Sin esta comprobación, el borrador quedaría apuntando a una imagen que no existe y el fallo aparecería recién al intentar adjuntarla. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_marcador_completo_tambien_se_acepta` | El modelo a veces devuelve el marcador entero en vez del identificador. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_precio_se_lee_venga_como_venga` | El prompt lo pide limpio, pero llega con signo y separador de miles igual. En Argentina el separador de miles es el punto, así que se saca antes de interpretar — leerlo como decimal daría $24,90 en vez de $24.900. | Integración · caja negra · funcional | Base de datos | `escrito`, `esperado` — 4 casos | Cumple |
| `test_un_precio_ilegible_deja_el_producto_incompleto` | Un precio ilegible deja el producto incompleto | Integración · caja negra · funcional | Base de datos | `malo` — 3 casos | Cumple |
| `test_un_precio_en_cero_se_rechaza` | Un precio en cero se rechaza | Integración · caja negra · validación | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_volumen_se_lee_aunque_venga_con_texto` | El volumen se lee aunque venga con texto | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_volumen_ilegible_deja_su_reparo` | Un tomo único puede venir sin volumen; "primavera" es otra cosa. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_producto_sin_titulo_lo_dice` | Sin título no hay forma de identificarlo, ni siquiera para revisarlo a mano en la cola. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_resumen_cuenta_completos_incompletos_y_con_reparos` | Es lo que va al log de auditoría y a la salida del comando: sin eso, la única forma de saber cómo salió una pasada es abrir el correo. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_se_declara_el_modelo_cuando_esta_configurado` | Vacío significa "el que esté cargado", que es lo cómodo con LM Studio; contra un servicio remoto hay que nombrarlo. | Integración · caja negra · funcional | Base de datos | `settings` | Cumple |
| `test_una_confianza_inventada_se_toma_como_baja` | Al alza sería peor: un valor raro leído como "alta" haría que un dato dudoso se confirme en lote sin que nadie lo mire (CU-ALT-REV). | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_sin_confianza_declarada_no_rompe` | Sin confianza declarada no rompe | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_si_el_servicio_no_responde_no_se_extrae_nada` | `pedir` devuelve `None` cuando no hay conexión, y eso tiene que llegar como un motivo, no como una excepción: el ciclo sigue con el correo siguiente. | Integración · caja negra · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_una_respuesta_que_no_es_json_se_reporta_como_ilegible` | Pasa cuando el modelo envuelve el JSON en prosa. No se intenta rescatar con expresiones regulares: eso esconde un prompt que hay que arreglar. | Integración · caja negra · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_modelo_de_razonamiento_deja_la_respuesta_en_otro_campo` | Caso real, no hipotético: `qwen3.5` en LM Studio devolvió el JSON entero en `reasoning_content` con `content` vacío. La extracción era correcta —los tres productos estaban bien— y el pipeline la descartaba igual. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_si_vienen_los_dos_campos_manda_el_principal` | `reasoning_content` es el razonamiento, no la respuesta: solo se usa cuando no hay otra cosa. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_error_en_el_cuerpo_se_reporta_como_rechazo` | Antes salía como "respuesta ilegible" y mandaba a revisar el prompt, que estaba bien. Un cuerpo con `error` **es** un rechazo del proveedor: pasa con los modelos gratuitos hospedados, donde la pasarela contesta con código 200 y el fallo es… | Integración · caja negra · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_una_respuesta_sin_forma_no_rompe` | La respuesta viene de afuera: un servidor que conteste distinto no puede tumbar el ciclo con un `KeyError`. Sin `choices` y sin `error` no hay nada que interpretar, y eso sí es una respuesta ilegible. | Integración · caja negra · frontera | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_texto_crudo_se_conserva_aunque_no_se_haya_podido_leer` | Es lo único con lo que se puede entender por qué falló; sin él, ajustar el prompt es adivinar. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_una_extraccion_exitosa_deja_el_correo_procesado` | Una extraccion exitosa deja el correo procesado | Integración · caja gris · funcional | Base de datos | `correo` | Cumple |
| `test_un_correo_que_no_era_de_novedades_igual_queda_procesado` | Que resulte no ser de novedades es un resultado válido, no un fallo: es justamente lo que la clasificación viene a detectar. | Integración · caja gris · funcional | Base de datos | `correo` | Cumple |
| `test_si_el_servicio_esta_caido_el_correo_queda_fallido` | Si el servicio esta caido el correo queda fallido | Integración · caja gris · funcional | Base de datos | `correo` | Cumple |
| `test_el_motivo_distingue_el_servicio_caido_de_la_respuesta_ilegible` | Se arreglan en lugares distintos: uno es infraestructura, el otro es el prompt o el modelo elegido. | Integración · caja gris · funcional | Base de datos | `correo` | Cumple |
| `test_las_portadas_del_correo_se_usan_para_validar_la_extraccion` | El correo sabe qué imágenes trae, y eso es lo que permite descartar una inventada. Sin pasarlas, la comprobación no tendría contra qué comparar. | Integración · caja gris · funcional | Base de datos | `correo` | Cumple |
| `test_reprocesar_pisa_la_extraccion_anterior` | Ajustar el prompt y volver a correr tiene que dejar el resultado nuevo, no dos resultados conviviendo. | Integración · caja gris · idempotencia | Base de datos | `correo` | Cumple |
| `test_la_ficha_muestra_lo_que_entendio_el_modelo` | Es el paso siguiente de la misma idea que muestra el contenido extraído: cada etapa del pipeline se puede mirar antes de que la próxima gaste algo. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin`, `correo` | Cumple |
| `test_la_fecha_se_lee_venga_como_venga` | La fecha se lee venga como venga | Integración · caja negra · funcional | Base de datos | `escrito`, `esperado` — 7 casos | Cumple |
| `test_una_fecha_que_no_se_entiende_devuelve_nada` | Una fecha que no se entiende devuelve nada | Integración · caja negra · funcional | Base de datos | `escrito` — 7 casos | Cumple |
| `test_el_periodo_del_correo_se_interpreta` | El correo anuncia el período en la prosa de alrededor de la tabla, no en cada fila: es de ahí que los borradores heredan la fecha. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_correo_sin_periodo_no_deja_reparo` | No anunciar fecha es el caso normal, no un problema: esos borradores nacen Activos, que es exactamente lo que pide CU-ALT-NOV paso 6. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_periodo_ilegible_deja_su_reparo` | Sin esto, todos los borradores del correo nacerían Activos y no habría forma de saber por qué. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_la_fecha_propia_de_una_fila_pisa_al_periodo` | La fecha propia de una fila pisa al periodo | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_una_fecha_de_fila_ilegible_deja_reparo_en_ese_producto` | Una fecha de fila ilegible deja reparo en ese producto | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_periodo_de_un_correo_que_no_es_de_novedades_se_ignora` | Mezclar las dos cosas es el error que la clasificación viene a evitar. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_periodo_y_las_fechas_quedan_en_lo_que_se_guarda` | La ficha las muestra, y el generador de borradores las lee de acá. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |

### `test_lectura_de_correos.py`

> Lectura de un correo de novedades: de bytes MIME a texto parseable. No toca la base: `apps/suppliers/correos.py` no conoce Django. Lo que se prueba acá es lo que decide si el pipeline entiende o no lo que le llega, y son las dos correcciones que este módulo le hace a la fuente: que la tabla no se aplane (15) y que las portadas vienen embebidas y no por URL (16).

**Tipos en este archivo:** Unitaria · caja negra · funcional — 20; Unitaria · caja negra · validación — 2.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_el_remitente_sale_pelado_aunque_venga_con_nombre_de_fantasia` | Un `From` real llega como `"Novedades Ivrea" <novedades@ivrea.test>` y el matcheo del proveedor compara direcciones, no cadenas enteras. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_remitente_se_normaliza_a_minuscula` | La caja de una dirección no la distingue, y el proveedor se guarda en minúscula: comparar en crudo dejaría afuera mensajes legítimos. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_se_leen_asunto_identificador_y_fecha` | Se leen asunto identificador y fecha | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_un_correo_sin_identificador_lo_deja_vacio` | Sin `Message-ID` no hay forma de saber si un correo ya se leyó. Que salga vacío es lo que le permite al servicio descartarlo en vez de encolarlo de nuevo en cada pasada. | Unitaria · caja negra · validación | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_cada_producto_queda_en_una_fila_con_sus_columnas` | Es la corrección 15: aplanar a texto plano rompe la asociación fila-columna y el modelo empieza a atribuirle a un tomo el precio del siguiente. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_precio_queda_en_la_misma_fila_que_su_titulo` | El error que la corrección evita no da ningún síntoma: se descubre tres meses después mirando un precio raro. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_la_prosa_que_envuelve_la_tabla_no_se_pierde` | Las tablas vienen anidadas —el HTML de un correo maqueta con tablas— y ahí vive el período del envío, que es de donde los borradores van a heredar la fecha. Con una sola fila "actual", abrir la tabla interna pisaba la externa y esto… | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_una_fila_de_una_sola_celda_no_parece_un_producto` | El encabezado con el logo es maquetado, no datos. Marcarlo con barras lo haría parecer un producto de una sola columna. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_la_hoja_de_estilos_no_entra_al_contenido` | La hoja de estilos no entra al contenido | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_un_correo_de_prosa_se_lee_como_prosa` | Un aviso de demora no tiene tabla, y tiene que salir legible igual: es el otro tipo de correo que llega por la misma casilla. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_las_portadas_vienen_dentro_del_correo` | Es la corrección 16: CU-ALT-NOV supone una descarga por URL, y acá no hay nada que descargar. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_cada_imagen_queda_marcada_dentro_de_la_fila_de_su_producto` | Sin el marcador habría que correlacionar por orden, y el logo del encabezado corre todo un lugar. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_los_marcadores_coinciden_con_las_partes_del_correo` | Si no coincidieran, la resolución fallaría en silencio y el borrador quedaría con "Imagen pendiente" sin que nadie entienda por qué. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_identificador_se_compara_venga_como_venga` | El `src` del HTML puede venir codificado y la cabecera de la parte llega entre ángulos: sin normalizar los dos lados, el marcador nunca encontraría su imagen. | Unitaria · caja negra · funcional | Unidad | `escrito` — 4 casos | Cumple |
| `test_un_correo_sin_imagenes_se_lee_igual` | Un correo sin imagenes se lee igual | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_un_html_mal_cerrado_no_pierde_la_ultima_fila` | Los correos mal formados llegan, y perder el último producto en silencio es peor que fallar. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_un_cuerpo_vacio_no_rompe` | Un cuerpo vacio no rompe | Unitaria · caja negra · validación | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_una_fecha_ilegible_no_tumba_la_lectura` | La fecha es un dato de presentación; el orden de la cola lo da cuándo lo recibimos nosotros. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_una_imagen_por_enlace_tambien_deja_rastro_en_la_fila` | Las dos formas conviven en la práctica. Una imagen externa no se puede resolver contra ninguna parte del correo, pero si no dejara rastro la celda quedaría vacía y correría todas las columnas de esa fila. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_una_imagen_sin_origen_ni_descripcion_se_ignora` | Un espaciador de un pixel no es un dato: meterlo en la fila agregaría una columna que no existe. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_una_celda_sin_fila_no_pierde_su_texto` | HTML roto, pero el texto que traía se conserva igual. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_un_correo_solo_de_texto_plano_se_lee_igual` | Estos proveedores mandan HTML, pero un correo sin parte HTML no puede quedar sin contenido: se trata su texto como párrafos. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |

### `test_muestras.py`

> El generador de contenido de muestra para el banco de pruebas. **Lo que de verdad prueba este archivo** es que dos implementaciones del dígito de control del ISBN, escritas por vías distintas, coinciden. `isbn.py` recorre con pesos alternados; `muestras.py` suma el total y le agrega dos veces los impares. Que coincidan sobre cientos de valores es evidencia; si el generador usara la misma función,…

**Tipos en este archivo:** Unitaria · caja negra · funcional — 13; Unitaria · caja negra · validación — 4.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_todo_isbn_generado_lo_acepta_la_verificacion` | Quinientos valores, dos implementaciones independientes. Una diferencia en las ponderaciones aparecería acá aunque los cuatro ISBN reales de `test_isbn.py` sigan pasando. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_todo_isbn_roto_lo_rechaza_la_verificacion` | La otra mitad: que el generador de rotos genere rotos de verdad. Sin esto, la demostración podría estar mostrando un ISBN válido y diciendo que lo detectó. | Unitaria · caja negra · validación | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_roto_difiere_del_valido_en_un_solo_digito` | Es el error que se comete al transcribir, y el que la verificación tiene que atrapar. Un número completamente distinto no probaría lo mismo. | Unitaria · caja negra · validación | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_numeros_distintos_dan_isbn_distintos` | Si se repitieran, una muestra con varios productos chocaría contra la restricción de unicidad al confirmarlos. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_los_isbn_empiezan_como_uno_argentino` | 978 de Bookland más 987 de Argentina: que la muestra arranque bien hace que se parezca a lo que llega de verdad. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_la_muestra_tiene_la_forma_de_un_correo_extraido` | La muestra tiene la forma de un correo extraido | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_trae_las_trampas_de_un_correo_real` | Probar contra un correo ideal no prueba nada: el logo no es un producto y la fila de encabezado tampoco. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_exactamente_un_producto_trae_el_isbn_roto` | Ni ninguno —no se vería la validación— ni todos, que haría parecer que el modelo lee mal siempre. | Unitaria · caja negra · validación | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_cual_sale_roto_no_es_siempre_el_mismo` | Si fuera siempre el último, alcanzaría con mirar la última fila para saber qué va a pasar antes de correr la prueba. | Unitaria · caja negra · validación | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_declara_los_identificadores_de_portada_que_trae` | Sin ellos, la comprobación de portada inexistente no tendría contra qué comparar y la demostración mostraría una validación que no valida. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_la_misma_semilla_da_la_misma_muestra` | Un test que necesite una muestra conocida tiene que poder pedirla. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_sin_semilla_las_muestras_difieren` | Sin semilla las muestras difieren | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_se_puede_pedir_la_cantidad_de_productos` | Se puede pedir la cantidad de productos | Unitaria · caja negra · funcional | Unidad | `cantidad` — 3 casos | Cumple |
| `test_el_periodo_anunciado_es_futuro` | Con una fecha ya pasada, todos los borradores nacen Activos y el banco de pruebas nunca ejercita la rama de Pre-venta — que es la que tiene consecuencias: un producto que no llegó figurando disponible no da ningún síntoma hasta que alguien… | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_periodo_se_declara_y_coincide_con_el_texto` | La muestra dice qué debería salir de ella, para que verificarlo no obligue a volver a interpretar el texto acá — eso compararía la muestra consigo misma. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_periodo_varia_entre_muestras` | Mismo motivo que los títulos y los ISBN: un valor fijo deja la duda de si el modelo lo lee o lo reconoce de verlo siempre igual. | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |
| `test_el_vencimiento_de_pedidos_es_un_señuelo_sin_año` | Es una segunda fecha en la misma prosa, y el modelo tiene que copiar el período y no el vencimiento. Va sin año a propósito: si el modelo la eligiera igual, el intérprete la descarta y el reparo lo dice en pantalla en vez de quedar en… | Unitaria · caja negra · funcional | Unidad | nada: entradas literales en el cuerpo | Cumple |

### `test_pipeline_de_novedades.py`

> Lo que el proveedor le aporta al procesamiento automático de CU-ALT-NOV. Son tres campos y dos responsabilidades distintas: - `procesa_novedades` decide **si** sus correos entran al pipeline. Está separado del estado a propósito: la relación comercial puede estar viva y el procesamiento apagado igual. - `editorial` y `tipo_por_defecto` son la **cabecera de sus borradores**. Los correos de…

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Sistema · caja negra · funcional — 9; Sistema · caja gris · funcional — 4; Integración · caja gris · funcional — 2; Integración · caja negra · funcional — 2.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_un_proveedor_con_las_novedades_apagadas_no_es_remitente_valido` | El caso que justifica que el campo exista: le seguís comprando, pero sus correos no alimentan el pipeline. | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_apagarlo_no_lo_da_de_baja` | Son dos cosas distintas: el proveedor sigue activo para todo lo demás —pedidos de restock, contacto, historial—, solo que su casilla no se lee. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_con_novedades_habilitadas_pide_las_dos_condiciones` | Con novedades habilitadas pide las dos condiciones | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_alta_lo_deja_habilitado_por_defecto` | Postcondición de CU-PRV-ALT: el correo queda habilitado como remitente válido. Nadie tiene que acordarse de prenderlo. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_se_puede_dar_de_alta_con_el_procesamiento_apagado` | Sirve para registrar al proveedor primero y probar el parseo después. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_proveedor_declara_la_editorial_bajo_la_que_publica` | El proveedor declara la editorial bajo la que publica | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_sin_editorial_declarada_el_proveedor_trae_varias` | El vacío significa algo: distribuidora o servicio conjunto, y ahí sí la editorial se extrae de cada correo. Es el mismo criterio con el que una cabecera de lote sin editorial significa "lote mixto". | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_solo_se_ofrecen_editoriales_y_tipos_activos` | Vincular un proveedor a una editorial dada de baja dejaría sus borradores apuntando a algo que ya no aparece en ningún desplegable del alta. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_alta_ofrece_crear_la_editorial_sin_salir_de_la_pantalla` | Vincularlo a una editorial que todavía no existe es el caso normal la primera vez. Es el mismo atajo de la carga de lotes, y del otro lado el mismo formulario: no hay dos caminos con reglas distintas. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_apagar_el_procesamiento_queda_auditado` | Sin esto, "por qué de Ivrea no llega nada desde marzo" sería una pregunta sin respuesta: el pipeline deja de generar borradores en silencio. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_cambiar_la_editorial_queda_auditado_con_los_dos_valores` | Cambia bajo qué sello nacen todos los borradores siguientes. | Sistema · caja gris · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_distingue_los_dos_motivos_por_los_que_no_se_procesa` | "Activo" ya no alcanza para responder por qué de un proveedor no llega nada, y los dos motivos se arreglan en lugares distintos. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_muestra_la_cabecera_de_sus_borradores` | La ficha muestra la cabecera de sus borradores | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_la_ficha_de_una_distribuidora_lo_dice` | La ficha de una distribuidora lo dice | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_listado_marca_solo_al_activo_con_las_novedades_apagadas` | Es el único caso invisible: que un proveedor de baja no alimente el pipeline ya lo dice su estado, y que uno normal sí lo haga es lo esperable. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_un_proveedor_normal_no_lleva_ninguna_marca` | Un proveedor normal no lleva ninguna marca | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |
| `test_el_tablero_cuenta_aparte_los_que_alimentan_el_pipeline` | La diferencia entre "activos" y "alimentan" es justo el grupo que de otro modo quedaría invisible. | Sistema · caja negra · funcional | Pantalla (HTTP) | `client_admin` | Cumple |

### `test_remitentes.py`

> El filtro de remitentes válidos: lo que este módulo le aporta a CU-ALT-NOV. `Proveedor.objects.remitente_valido` es la única puerta por la que el pipeline de novedades decide si procesa un correo o lo saltea. Todavía no hay pipeline, pero la regla ya existe y se prueba sola: cuando CU-ALT-NOV se implemente, va a apoyarse en algo verificado en vez de inventarlo de nuevo dentro de una tarea de…

*Todo el archivo corre contra la base: lo marca `pytestmark = pytest.mark.django_db` en la cabecera, y por eso no se repite en cada fila.*

**Tipos en este archivo:** Integración · caja gris · funcional — 7; Integración · caja gris · validación — 1; Integración · caja negra · funcional — 1.

| Prueba | Qué hace | Tipo de prueba | Qué ofrece | Qué recibe | Cumple |
| --- | --- | --- | --- | --- | --- |
| `test_un_proveedor_activo_es_remitente_valido` | Un proveedor activo es remitente valido | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_proveedor_inactivo_no_lo_es` | Es el efecto de CU-PRV-BAJ: la baja saca el correo del filtro. | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_proveedor_con_el_procesamiento_apagado_tampoco` | La otra mitad del filtro: son dos condiciones, no una. | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_correo_desconocido_no_devuelve_nada` | E1 de CU-ALT-NOV: el remitente no registrado no se procesa. | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_la_busqueda_ignora_las_mayusculas` | Un encabezado de correo puede traer cualquier caja. Comparar en crudo dejaría afuera mensajes legítimos, y el modo en que fallaría —silencio, sin error— es el peor de todos. | Integración · caja gris · funcional | Base de datos | `escrito` — 2 casos | Cumple |
| `test_los_espacios_alrededor_no_estorban` | Los espacios alrededor no estorban | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_un_remitente_vacio_no_encuentra_nada` | Un correo sin remitente legible no puede caer por casualidad en el primer proveedor de la tabla. | Integración · caja gris · validación | Base de datos | `vacio` — 2 casos | Cumple |
| `test_activos_solo_devuelve_los_activos` | Activos solo devuelve los activos | Integración · caja gris · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |
| `test_el_proveedor_se_identifica_por_su_razon_social` | Es lo que se lee en el log de auditoría y en los desplegables. | Integración · caja negra · funcional | Base de datos | nada: entradas literales en el cuerpo | Cumple |

---

## Lo que la foto no cubre

- **No dice qué contrato quedó sin prueba.** Esta tabla se lee desde las pruebas hacia los contratos; el mapa inverso —contrato por contrato, cubierto o no— es `COBERTURA.md`, que todavía no existe.
- **No mide cobertura de líneas.** Ese porcentaje lo da `pytest --cov`, no este inventario.
- **Ni el *Tipo de prueba* ni el *Qué ofrece* están declarados por cada prueba: se deducen de su firma y de su cuerpo.** El nivel y el enfoque son mecánicos; el propósito se lee sobre todo del nombre, así que una prueba de validación cuyo nombre no hable de rechazo aparece acá como `funcional`.
- **Una prueba de contrato cuyo nombre no lleve el código `CO###` no figura como contrato**, sino como `Pantalla (HTTP)` o `Base de datos`.
- **No cubre las fixtures ni las factories** (`conftest.py`, `factories.py`, `helpers_*.py`, `correos_de_ejemplo.py`): son material de montaje, no pruebas.
- **Las migraciones sobre la base de desarrollo y la supervivencia de las restricciones no se ven acá**: son las dos verificaciones a mano que ninguna puerta cubre.

