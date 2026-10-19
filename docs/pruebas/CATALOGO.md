> **Tipo: Fotografía.** Tomada el 2026-10-19 de una corrida real de la suite.
> **Generado por `scripts/generar_catalogo.py`.** No lo edites: la próxima corrida lo pisa.

# Catálogo de pruebas

Qué pruebas hay, qué hace cada una y si pasa. Cómo se escriben está en
[`ESPECIFICACION.md`](ESPECIFICACION.md); qué contratos cubren, en [`COBERTURA.md`](COBERTURA.md);
qué casos de prueba verifican, en [`CASOS_DE_PRUEBA.md`](CASOS_DE_PRUEBA.md).

## Resumen

| | |
| --- | ---: |
| Archivos de prueba | 123 |
| Funciones de prueba | 2163 |
| Casos, contando cada valor de `parametrize` | 2472 |
| Pasan | 2163 |
| Fallan | 0 |
| Omitidas | 0 |
| No corrieron | 0 |
| Duración de la corrida | 187 s |
| Scripts de resistencia en `scripts/demo/` | 23 |

---

## Cuentas y acceso — `apps/accounts`

### `test_activacion_cuenta.py`

CU-USR-ALT, del lado del usuario nuevo: activar la cuenta y elegir contraseña.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_activar_la_cuenta_la_deja_activa_y_con_contrasena` | Activar la cuenta la deja activa y con contrasena | 1 | Pasa |
| `test_al_terminar_se_ofrece_iniciar_sesion` | Al terminar se ofrece iniciar sesion | 1 | Pasa |
| `test_despues_de_activar_la_cuenta_puede_iniciar_sesion` | Despues de activar la cuenta puede iniciar sesion | 1 | Pasa |
| `test_una_cuenta_pendiente_no_puede_iniciar_sesion` | Una cuenta pendiente no puede iniciar sesion | 1 | Pasa |
| `test_el_enlace_vale_48_horas` | El enlace vale 48 horas | 1 | Pasa |
| `test_el_enlace_vencido_es_rechazado` | El enlace vencido es rechazado | 1 | Pasa |
| `test_el_enlace_no_se_puede_usar_dos_veces` | El enlace no se puede usar dos veces | 1 | Pasa |
| `test_una_contrasena_debil_no_activa_la_cuenta` | Una contrasena debil no activa la cuenta | 1 | Pasa |
| `test_la_activacion_queda_registrada_en_auditoria` | La activacion queda registrada en auditoria | 1 | Pasa |

### `test_alta_usuario.py`

CU-USR-ALT — Dar de Alta Usuario del Sistema.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_alta_deja_la_cuenta_pendiente_de_activacion` | El alta deja la cuenta pendiente de activacion | 1 | Pasa |
| `test_el_alta_genera_un_token_de_activacion_utilizable` | El alta genera un token de activacion utilizable | 1 | Pasa |
| `test_la_cuenta_nueva_no_tiene_contrasena_utilizable` | La cuenta nueva no tiene contrasena utilizable | 1 | Pasa |
| `test_el_alta_avisa_por_correo_al_usuario_nuevo` | El alta avisa por correo al usuario nuevo | 1 | Pasa |
| `test_el_alta_queda_registrada_en_auditoria_con_el_rol` | El alta queda registrada en auditoria con el rol | 1 | Pasa |
| `test_un_correo_ya_usado_por_una_cuenta_activa_es_rechazado` | Un correo ya usado por una cuenta activa es rechazado | 1 | Pasa |
| `test_un_correo_ya_usado_por_una_cuenta_pendiente_es_rechazado` | Un correo ya usado por una cuenta pendiente es rechazado | 1 | Pasa |
| `test_un_campo_obligatorio_vacio_no_crea_la_cuenta` | Un campo obligatorio vacio no crea la cuenta | 1 | Pasa |
| `test_el_formulario_no_ofrece_cliente_como_rol` | El formulario no ofrece cliente como rol | 1 | Pasa |
| `test_un_post_con_rol_cliente_es_rechazado` | La restricción del rol es del servidor, no del `select` del navegador. | 1 | Pasa |
| `test_solo_el_administrador_accede_al_alta` | Solo el administrador accede al alta | 2 | Pasa |
| `test_la_lista_de_usuarios_no_filtra_datos_a_otros_roles` | 403 sin datos parciales: el cajero no ve ni un pedazo de la tabla. | 1 | Pasa |
| `test_la_lista_muestra_solo_cuentas_de_personal` | La lista muestra solo cuentas de personal | 1 | Pasa |

### `test_baja_usuario.py`

CU-USR-BAJ — Dar de Baja Usuario del Sistema.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_la_pantalla_pide_confirmacion_explicita` | La pantalla pide confirmacion explicita | 1 | Pasa |
| `test_la_baja_cambia_el_estado_e_invalida_las_sesiones` | La baja cambia el estado e invalida las sesiones | 1 | Pasa |
| `test_la_baja_es_logica_y_no_borra_la_cuenta` | La baja es logica y no borra la cuenta | 1 | Pasa |
| `test_un_usuario_dado_de_baja_no_puede_volver_a_iniciar_sesion` | Un usuario dado de baja no puede volver a iniciar sesion | 1 | Pasa |
| `test_no_se_puede_dar_de_baja_al_unico_administrador_activo` | No se puede dar de baja al unico administrador activo | 1 | Pasa |
| `test_se_puede_dar_de_baja_un_administrador_si_queda_otro_activo` | Se puede dar de baja un administrador si queda otro activo | 1 | Pasa |
| `test_darse_de_baja_a_uno_mismo_cierra_la_propia_sesion` | Darse de baja a uno mismo cierra la propia sesion | 1 | Pasa |
| `test_la_baja_queda_registrada_en_auditoria` | La baja queda registrada en auditoria | 1 | Pasa |
| `test_el_historial_del_usuario_dado_de_baja_sigue_consultable` | La baja no dispara borrado ni anonimización en cascada. | 1 | Pasa |
| `test_no_se_puede_dar_de_baja_una_cuenta_que_no_esta_activa` | No se puede dar de baja una cuenta que no esta activa | 1 | Pasa |
| `test_solo_el_administrador_puede_dar_de_baja` | Solo el administrador puede dar de baja | 1 | Pasa |

### `test_bloqueo_intentos.py`

CU-AUT-INI, excepción: 5 intentos fallidos consecutivos bloquean el acceso.

**Casos de prueba que ejecuta:** CP-13.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_quinto_intento_fallido_bloquea_el_acceso` | Quinto intento fallido bloquea el acceso | 1 | Pasa |
| `test_el_bloqueo_rechaza_incluso_la_contrasena_correcta` | El bloqueo rechaza incluso la contrasena correcta | 1 | Pasa |
| `test_el_bloqueo_avisa_al_correo_registrado_y_queda_auditado` | El bloqueo avisa al correo registrado y queda auditado | 1 | Pasa |
| `test_el_bloqueo_se_levanta_al_pasar_la_ventana_de_tiempo` | El bloqueo se levanta al pasar la ventana de tiempo | 1 | Pasa |
| `test_los_intentos_de_otra_ip_no_bloquean_la_cuenta` | El bloqueo es por dispositivo: un tercero no puede dejar afuera al titular. | 1 | Pasa |
| `test_un_login_exitoso_corta_la_racha_de_intentos` | Un login exitoso corta la racha de intentos | 1 | Pasa |
| `test_tambien_se_cuentan_los_intentos_contra_correos_inexistentes` | Si solo contáramos cuentas reales, la diferencia revelaría cuáles existen. | 1 | Pasa |
| `test_una_cuenta_inactiva_con_clave_correcta_no_suma_intentos` | Una cuenta inactiva con clave correcta no suma intentos | 1 | Pasa |

### `test_cierre_de_sesion_visible.py`

Todo rol con sesión tiene a la vista cómo cerrarla (CU-AUT-FIN).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_cliente_puede_cerrar_sesion_desde_la_tienda` | El cliente puede cerrar sesion desde la tienda | 1 | Pasa |
| `test_sin_sesion_la_tienda_ofrece_ingresar_y_no_salir` | Sin sesion la tienda ofrece ingresar y no salir | 1 | Pasa |
| `test_el_cajero_encuentra_cerrar_sesion_en_el_menu` | El cajero encuentra cerrar sesion en el menu | 1 | Pasa |
| `test_el_menu_del_cajero_no_ofrece_el_panel_del_administrador` | El Panel le respondería 403: el menú no ofrece caminos que no existen. | 1 | Pasa |
| `test_el_cajero_puede_abrir_el_inventario_que_le_ofrece_el_menu` | El cajero puede abrir el inventario que le ofrece el menu | 1 | Pasa |
| `test_el_administrador_tambien_tiene_la_salida_en_el_menu` | El administrador tambien tiene la salida en el menu | 1 | Pasa |

### `test_codigo_cliente.py`

El código de cliente (B-06-001): seis cifras, único, sólo para cuentas de Cliente.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_una_cuenta_de_cliente_nace_con_un_codigo_de_seis_cifras` | Una cuenta de cliente nace con un codigo de seis cifras | 1 | Pasa |
| `test_el_personal_no_tiene_codigo_de_cliente` | El personal no tiene codigo de cliente | 2 | Pasa |
| `test_el_codigo_no_cambia_al_volver_a_guardar` | El codigo no cambia al volver a guardar | 1 | Pasa |
| `test_la_base_no_admite_dos_cuentas_con_el_mismo_codigo` | La base no admite dos cuentas con el mismo codigo | 1 | Pasa |
| `test_el_cliente_ve_su_codigo_en_mi_cuenta` | El cliente ve su codigo en mi cuenta | 1 | Pasa |
| `test_el_administrador_busca_un_cliente_por_su_codigo` | El administrador busca un cliente por su codigo | 1 | Pasa |

### `test_concurrencia_ultimo_administrador.py`

I-12 bajo concurrencia real: dos Administradores se sacan el rol o se dan de baja a la vez.

**Casos de prueba que ejecuta:** CP-21.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO121_dos_administradores_que_se_sacan_el_rol_a_la_vez_dejan_uno` | CO121 dos administradores que se sacan el rol a la vez dejan uno | 1 | Pasa |
| `test_CO123_dos_administradores_que_se_dan_de_baja_a_la_vez_dejan_uno` | CO123 dos administradores que se dan de baja a la vez dejan uno | 1 | Pasa |
| `test_CO121_y_CO123_cruzados_dejan_uno` | Uno saca el rol y el otro da de baja, a la vez. | 1 | Pasa |

### `test_contratos_11_cuenta.py`

Pruebas de contrato de «Mi cuenta» (plan 11, segunda parte).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO192_muestra_los_pedidos_activos_del_cliente` | CO192 muestra los pedidos activos del cliente | 1 | Pasa |
| `test_CO192_el_historial_muestra_los_despachados` | CO192 el historial muestra los despachados | 1 | Pasa |
| `test_CO192_E1_sin_pedidos_activos_informa_y_las_demas_secciones_siguen` | CO192 E1 sin pedidos activos informa y las demas secciones siguen | 1 | Pasa |
| `test_CO192_la_seccion_stock_en_local_se_muestra` | Plan 18: la sección oculta por B-11-003 ya existe. | 1 | Pasa |
| `test_CO192_no_modifica_el_estado_del_sistema` | CO192 no modifica el estado del sistema | 1 | Pasa |
| `test_CO193_muestra_items_precios_estados_alcanzados_y_sus_fechas` | CO193 muestra items precios estados alcanzados y sus fechas | 1 | Pasa |
| `test_CO193_el_pedido_de_otro_cliente_responde_404` | CO193 el pedido de otro cliente responde 404 | 1 | Pasa |
| `test_CO193_un_pedido_activo_se_actualiza_solo_y_uno_despachado_no` | CO193 un pedido activo se actualiza solo y uno despachado no | 1 | Pasa |
| `test_CO193_no_modifica_el_estado_del_sistema` | CO193 no modifica el estado del sistema | 1 | Pasa |
| `test_CO108_c_los_atributos_modificados_pasan_a_los_declarados` | CO108 c los atributos modificados pasan a los declarados | 1 | Pasa |
| `test_CO108_queda_en_la_auditoria_con_el_actor` | CO108 queda en la auditoria con el actor | 1 | Pasa |
| `test_CO108_el_correo_no_se_cambia_desde_aca` | CO108 el correo no se cambia desde aca | 1 | Pasa |
| `test_CO108_una_direccion_incoherente_no_cambia_nada` | CO108 una direccion incoherente no cambia nada | 1 | Pasa |
| `test_CO108_guardar_sin_cambios_no_audita` | CO108 guardar sin cambios no audita | 1 | Pasa |
| `test_CO109_a_se_crea_un_token_de_cambio_de_correo` | CO109 a se crea un token de cambio de correo | 1 | Pasa |
| `test_CO109_el_correo_de_la_cuenta_no_cambia` | CO109 el correo de la cuenta no cambia | 1 | Pasa |
| `test_CO109_el_enlace_va_al_correo_nuevo` | CO109 el enlace va al correo nuevo | 1 | Pasa |
| `test_CO109_con_la_contrasena_equivocada_no_se_emite_nada` | CO109 con la contrasena equivocada no se emite nada | 1 | Pasa |
| `test_CO109_E1_un_correo_con_cuenta_se_rechaza_y_ofrece_recuperar` | CO109 E1 un correo con cuenta se rechaza y ofrece recuperar | 1 | Pasa |
| `test_CO109_un_pedido_nuevo_vence_el_anterior` | CO109 un pedido nuevo vence el anterior | 1 | Pasa |
| `test_CO110_abrir_el_enlace_no_cambia_nada` | CO110 abrir el enlace no cambia nada | 1 | Pasa |
| `test_CO110_c_el_correo_pasa_al_nuevo_y_el_token_queda_consumido` | CO110 c el correo pasa al nuevo y el token queda consumido | 1 | Pasa |
| `test_CO110_queda_en_la_auditoria` | CO110 queda en la auditoria | 1 | Pasa |
| `test_CO110_el_correo_anterior_recibe_un_aviso` | CO110 el correo anterior recibe un aviso | 1 | Pasa |
| `test_CO110_un_enlace_usado_no_sirve_dos_veces` | CO110 un enlace usado no sirve dos veces | 1 | Pasa |
| `test_CO110_un_enlace_vencido_no_sirve` | CO110 un enlace vencido no sirve | 1 | Pasa |
| `test_CO110_si_otra_cuenta_tomo_el_correo_en_el_medio_no_se_cambia` | CO110 si otra cuenta tomo el correo en el medio no se cambia | 1 | Pasa |
| `test_CO111_c_la_credencial_pasa_al_hash_nuevo` | CO111 c la credencial pasa al hash nuevo | 1 | Pasa |
| `test_CO111_la_sesion_actual_sigue_y_las_otras_se_cierran` | CO111 la sesion actual sigue y las otras se cierran | 1 | Pasa |
| `test_CO111_queda_en_la_auditoria` | CO111 queda en la auditoria | 1 | Pasa |
| `test_CO111_con_la_contrasena_actual_equivocada_no_cambia_nada` | CO111 con la contrasena actual equivocada no cambia nada | 1 | Pasa |
| `test_acceso_el_personal_recibe_403_en_mi_cuenta` | Acceso el personal recibe 403 en mi cuenta | 12 | Pasa |
| `test_acceso_sin_sesion_va_al_ingreso` | Acceso sin sesion va al ingreso | 1 | Pasa |
| `test_acceso_el_personal_no_cambia_sus_datos_por_aca` | Acceso el personal no cambia sus datos por aca | 1 | Pasa |

### `test_contratos_11_cuenta_de_cliente.py`

Pruebas de contrato del módulo 11 · Cuenta de Cliente (CU-CLI-CON).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO194_el_padron_lista_nombre_correo_estado_y_registro` | CO194 el padron lista nombre correo estado y registro | 1 | Pasa |
| `test_CO194_A1_sin_coincidencias_lo_informa` | CO194 A1 sin coincidencias lo informa | 1 | Pasa |
| `test_CO194_E1_por_la_direccion_real_con_otro_rol_se_deniega` | CO194 E1 por la direccion real con otro rol se deniega | 2 | Pasa |
| `test_CO194_E1_sin_sesion_no_se_ve_el_padron` | CO194 E1 sin sesion no se ve el padron | 1 | Pasa |
| `test_CO195_la_ficha_presenta_los_datos_que_declara_el_contrato` | CO195 la ficha presenta los datos que declara el contrato | 1 | Pasa |
| `test_CO195_la_ficha_no_ofrece_ninguna_modificacion` | «Sin acciones de modificación»: ni formularios ni enlaces a operaciones. | 1 | Pasa |
| `test_CO195_la_ficha_no_modifica_el_estado` | CO195 la ficha no modifica el estado | 1 | Pasa |
| `test_CO195_por_la_direccion_real_con_otro_rol_se_deniega` | CO195 por la direccion real con otro rol se deniega | 2 | Pasa |
| `test_CO195_una_cuenta_de_personal_no_tiene_ficha_de_cliente` | CO195 una cuenta de personal no tiene ficha de cliente | 1 | Pasa |

### `test_contratos_12_autenticacion.py`

Pruebas de contrato del Módulo 12 — Autenticación (CO-114 a CO-119, CO-196).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO114_credenciales_validas_establecen_sesion_con_el_nivel_del_rol` | Postcondición: se estableció una sesión con el nivel de permisos del rol. | 3 | Pasa |
| `test_CO114_la_sesion_nace_con_expiracion_por_inactividad` | Postcondición: «un token con expiración por inactividad». | 1 | Pasa |
| `test_CO114_credenciales_validas_registran_el_inicio_en_auditoria` | Postcondición: se creó una entrada con acción «Inicio de sesión», actor y momento. | 1 | Pasa |
| `test_CO114_credenciales_invalidas_crean_un_intento_fallido` | Postcondición (a): se creó if : IntentoFallido. | 1 | Pasa |
| `test_CO114_el_intento_fallido_guarda_el_correo_tal_como_se_escribio` | Postcondición (c): «if.correo tecleado quedó con el valor tal como se escribió». | 1 | Pasa |
| `test_CO114_se_registra_el_intento_aunque_la_cuenta_no_exista` | Notas del contrato: se registra «exista o no una cuenta con ese valor». | 1 | Pasa |
| `test_CO114_el_quinto_intento_registra_el_bloqueo_en_auditoria` | Postcondición: «si los intentos dentro de la ventana alcanzaron cinco». | 1 | Pasa |
| `test_CO114_bloqueado_no_entra_ni_con_la_contrasena_correcta` | Excepción E1: «se bloquea el acceso por el período parametrizado». | 1 | Pasa |
| `test_CO114_el_bloqueo_se_levanta_solo_al_salir_los_intentos_de_la_ventana` | Notas: «el bloqueo se levanta solo cuando los intentos salen de la ventana». | 1 | Pasa |
| `test_CO114_cuenta_inactiva_no_obtiene_sesion` | Excepción E2: cuenta en estado Inactivo, «sin otorgar sesión». | 1 | Pasa |
| `test_CO114_cuenta_inactiva_no_deja_rastro_de_inicio_en_auditoria` | Postcondición negativa: la rama de credenciales válidas no corrió. | 1 | Pasa |
| `test_CO115_extender_renueva_el_plazo_de_inactividad` | Postcondición: «el plazo de expiración por inactividad del token quedó renovado». | 1 | Pasa |
| `test_CO115_sobre_una_sesion_vencida_la_extension_no_procede` | Excepción: «si la sesión ya expiró, la extensión no procede». | 1 | Pasa |
| `test_CO116_cerrar_sesion_invalida_el_token_del_dispositivo_actual` | Postcondición: «el token de sesión del dispositivo actual quedó invalidado». | 1 | Pasa |
| `test_CO116_cerrar_sesion_no_afecta_las_sesiones_de_otros_dispositivos` | Postcondición negativa explícita: «las sesiones en otros dispositivos no fueron afectadas». | 1 | Pasa |
| `test_CO116_cerrar_sesion_registra_el_cierre_en_auditoria` | Postcondición: entrada con acción «Cierre de sesión», actor y timestamp. | 1 | Pasa |
| `test_CO117_una_cuenta_activa_recibe_el_enlace_en_su_direccion` | Postcondición (a): «sólo si el correo corresponde a una cuenta Activa […] el enlace se envió a esa dirección». | 1 | Pasa |
| `test_CO117_se_creo_el_token_de_recuperacion_asociado_a_la_cuenta` | Postcondición (a): «se creó tr : TokenRecuperacion con vigencia de 30 minutos, y se formó tr → Usuario». | 1 | Pasa |
| `test_CO117_un_correo_sin_cuenta_no_crea_ningun_token` | Postcondición: «si el correo no corresponde a ninguna cuenta activa: ninguna postcondición». | 1 | Pasa |
| `test_CO117_un_correo_sin_cuenta_no_produce_ninguna_postcondicion` | Postcondición: «si el correo no corresponde a ninguna cuenta activa: ninguna postcondición». | 1 | Pasa |
| `test_CO117_la_respuesta_es_identica_exista_o_no_la_cuenta` | Notas: «la respuesta es idéntica exista o no una cuenta con el correo consultado». | 1 | Pasa |
| `test_CO117_una_cuenta_inactiva_no_recibe_enlace` | Postcondición (a): la condición es «una cuenta Activa». | 1 | Pasa |
| `test_CO118_la_credencial_pasa_del_hash_anterior_al_nuevo` | Postcondición (c): «u.credencial pasó del hash anterior al nuevo». | 1 | Pasa |
| `test_CO118_la_contrasena_anterior_queda_invalidada` | Postcondición (c): «la contraseña anterior quedó invalidada». | 1 | Pasa |
| `test_CO118_el_token_pasa_de_vigente_a_consumido` | Postcondición (c): «tr.estado pasó de Vigente a Consumido». | 1 | Pasa |
| `test_CO118_el_token_consumido_no_admite_un_segundo_uso` | Postcondición (c), segunda mitad de la misma frase: consumido quiere decir que no sirve otra vez. | 1 | Pasa |
| `test_CO118_E2_una_contrasena_rechazada_no_consume_el_token` | Excepción E2: «el token no se consume y el usuario puede corregir sin necesidad de uno nuevo». | 1 | Pasa |
| `test_CO118_invalida_las_sesiones_en_todos_los_dispositivos` | Postcondición: «todas las sesiones activas del usuario, en cualquier dispositivo, quedaron invalidadas». | 1 | Pasa |
| `test_CO118_registra_el_cambio_de_contrasena_en_auditoria` | Postcondición: entrada con acción «Cambio de contraseña». | 1 | Pasa |
| `test_CO118_con_contrasenas_que_no_coinciden_el_enlace_no_se_consume` | Excepción E2: «el token no se consume y el usuario puede corregir sin necesidad de uno nuevo». | 1 | Pasa |
| `test_CO118_un_enlace_vencido_no_cambia_la_credencial` | Excepción E1: token vencido. | 1 | Pasa |
| `test_CO119_la_cuenta_pasa_de_pendiente_de_activacion_a_activo` | Postcondición (c): «u.estado pasó de Pendiente de activación a Activo». | 1 | Pasa |
| `test_CO119_la_credencial_pasa_de_nula_al_hash_de_la_elegida` | Postcondición (c): «u.credencial pasó de nula al hash con sal única». | 1 | Pasa |
| `test_CO119_el_enlace_pasa_de_vigente_a_consumido` | Postcondición (c): «EnlaceActivacion.estado pasó de Vigente a Consumido». | 1 | Pasa |
| `test_CO119_el_enlace_no_admite_un_segundo_uso` | Postcondición (c), segunda mitad: «no admite un segundo uso». | 1 | Pasa |
| `test_CO119_E1_un_enlace_vencido_se_distingue_de_uno_ya_usado` | Excepciones E1 y E2: «enlace vencido» y «enlace ya utilizado» dicen cosas distintas. | 1 | Pasa |
| `test_CO119_E3_una_contrasena_rechazada_no_consume_el_enlace` | Excepción E3: «el enlace no se consume por un intento fallido». | 1 | Pasa |
| `test_CO119_registra_la_activacion_en_auditoria` | Postcondición: entrada con acción «Activación de cuenta». | 1 | Pasa |
| `test_CO119_un_enlace_vencido_deja_la_cuenta_pendiente` | Excepción E1: enlace vencido. | 1 | Pasa |
| `test_CO119_una_contrasena_rechazada_no_consume_el_enlace` | Excepción E3: «el enlace no se consume por un intento fallido». | 1 | Pasa |
| `test_CO196_abrir_el_enlace_no_modifica_el_estado_del_sistema` | Postcondición: «ninguna. | 1 | Pasa |
| `test_CO196_no_exige_sesion_iniciada` | Precondición: «ninguna de sesión: el enlace es la credencial». | 1 | Pasa |

### `test_contratos_13_gestion_de_usuarios.py`

Pruebas de contrato del Módulo 13 — Gestión de Usuarios (CO-120 a CO-125, CO-197 a CO-202).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO120_se_creo_la_cuenta_en_pendiente_de_activacion` | Postcondición (a) y (c): «se creó u : Usuario», «u.estado quedó en Pendiente». | 1 | Pasa |
| `test_CO120_el_rol_queda_con_el_valor_declarado` | Postcondición (c): «u.rol con el valor declarado (Cajero o Administrador)». | 1 | Pasa |
| `test_CO120_el_correo_queda_normalizado` | Postcondición (c): «u.correo normalizado». | 1 | Pasa |
| `test_CO120_la_cuenta_nace_sin_credencial_utilizable` | Postcondición (c): «u.credencial nula». | 1 | Pasa |
| `test_CO120_se_creo_el_enlace_de_activacion_asociado_a_la_cuenta` | Postcondición (a) y (b): «se creó u : Usuario y ea : EnlaceActivacion», «se formó ea → u». | 1 | Pasa |
| `test_CO120_el_enlace_nace_vigente_y_con_48_horas` | Postcondición (c): «ea.vigencia quedó en 48 horas y ea.estado en Vigente». | 1 | Pasa |
| `test_CO120_se_envio_el_enlace_al_correo_del_nuevo_usuario` | Postcondición: «el enlace se envió al correo del nuevo usuario». | 1 | Pasa |
| `test_CO120_registra_el_alta_en_auditoria_con_el_rol_asignado` | Postcondición: entrada «Alta de usuario del sistema» con actor, momento y rol asignado. | 1 | Pasa |
| `test_CO120_un_correo_de_cuenta_activa_no_crea_la_cuenta` | Excepción E2: «el correo pertenece a otra cuenta, en cualquier estado […] no se crea». | 1 | Pasa |
| `test_CO120_un_correo_de_cuenta_pendiente_no_crea_la_cuenta` | Excepción E2, segundo estado: también bloquea contra una cuenta Pendiente. | 1 | Pasa |
| `test_CO120_un_correo_de_cuenta_inactiva_no_crea_la_cuenta` | Excepción E2, tercer estado: el correo de una cuenta Inactiva tampoco se libera. | 1 | Pasa |
| `test_CO121_los_atributos_pasan_de_su_valor_anterior_al_declarado` | Postcondición (c): «los atributos modificados pasaron de sus valores anteriores a los declarados». | 1 | Pasa |
| `test_CO121_la_ultima_modificacion_queda_con_el_instante` | Postcondición (c): «u.última modificación quedó con el instante». | 1 | Pasa |
| `test_CO121_cambiar_el_rol_invalida_la_sesion_del_usuario_modificado` | Postcondición: «si se modificó el rol: el token de sesión activo del usuario modificado quedó invalidado de forma inmediata, forzando un re-login con los nuevos permisos». | 1 | Pasa |
| `test_CO121_sin_cambiar_el_rol_la_sesion_del_usuario_sigue_viva` | Postcondición negativa: la invalidación está condicionada a «si se modificó el rol». | 1 | Pasa |
| `test_CO121_registra_los_valores_anterior_y_nuevo_de_cada_campo` | Postcondición: entrada con «los valores anteriores y nuevos de cada campo modificado». | 1 | Pasa |
| `test_CO121_no_se_puede_quitar_el_rol_al_ultimo_administrador` | Excepción E1: «la operación se cancela sin efecto» (I-12). | 1 | Pasa |
| `test_CO121_un_correo_que_ya_es_de_otra_cuenta_no_actualiza` | Excepción E2: «se informa el conflicto y no se actualiza». | 1 | Pasa |
| `test_CO121_una_cuenta_inactiva_no_admite_modificacion` | Excepción E3: «se bloquea el acceso al formulario y se ofrece la acción de reactivación». | 1 | Pasa |
| `test_CO121_una_cuenta_inactiva_no_cambia_aunque_se_envie_el_formulario` | Excepción E3, la mitad que importa: la restricción vive en el servidor, no en la pantalla. | 1 | Pasa |
| `test_CO122_se_creo_un_enlace_nuevo_con_vigencia_de_48_horas` | Postcondición (a): «se creó un EnlaceActivacion nuevo con vigencia de 48 horas». | 1 | Pasa |
| `test_CO122_el_correo_de_activacion_fue_reenviado` | Postcondición: «el correo de activación fue reenviado». | 1 | Pasa |
| `test_CO122_el_enlace_anterior_pasa_de_vigente_a_vencido` | Postcondición (c): «el EnlaceActivacion anterior pasó a estado Vencido». | 1 | Pasa |
| `test_CO122_el_enlace_anterior_deja_de_admitir_uso` | Postcondición (c), segunda mitad: «y no admite uso». | 1 | Pasa |
| `test_CO122_registra_el_reenvio_en_auditoria` | Postcondición: entrada «Reenvío del enlace de activación» con actor y momento. | 1 | Pasa |
| `test_CO123_el_estado_pasa_de_activo_a_inactivo` | Postcondición (c): «u.estado pasó de Activo a Inactivo». | 1 | Pasa |
| `test_CO123_la_cuenta_no_puede_volver_a_iniciar_sesion` | Postcondición (c): «el usuario no puede volver a iniciar sesión» (I-11). | 1 | Pasa |
| `test_CO123_invalida_los_tokens_de_todos_los_dispositivos` | Postcondición: «todos sus tokens de sesión, en cualquier dispositivo, quedaron invalidados de forma inmediata». | 1 | Pasa |
| `test_CO123_el_historial_del_usuario_se_conserva_integro` | Postcondición negativa explícita: «el historial de operaciones registradas por ese usuario se conservó íntegro en el log». | 1 | Pasa |
| `test_CO123_registra_la_baja_en_auditoria` | Postcondición: entrada «Baja de usuario del sistema» con actor y momento. | 1 | Pasa |
| `test_CO123_no_se_puede_dar_de_baja_al_ultimo_administrador` | Excepción E1: se bloquea (I-12). | 1 | Pasa |
| `test_CO124_el_estado_pasa_de_inactivo_a_pendiente_de_activacion` | Postcondición (c): «u.estado pasó de Inactivo a Pendiente de activación (no a Activo)». | 1 | Pasa |
| `test_CO124_la_credencial_anterior_queda_invalidada` | Postcondición (c): «u.credencial quedó invalidada». | 1 | Pasa |
| `test_CO124_se_creo_un_enlace_de_activacion_con_48_horas` | Postcondición (a): «se creó un EnlaceActivacion con vigencia de 48 horas». | 1 | Pasa |
| `test_CO124_el_enlace_se_envia_al_correo_de_la_cuenta` | Postcondición: «enviado al correo de la cuenta». | 1 | Pasa |
| `test_CO124_el_historial_del_usuario_se_conserva_integro` | Postcondición: «el historial de operaciones del usuario en el log se conservó íntegro». | 1 | Pasa |
| `test_CO124_registra_la_reactivacion_en_auditoria` | Postcondición: entrada «Reactivación de usuario del sistema» con actor y momento. | 1 | Pasa |
| `test_CO124_el_rol_queda_con_el_valor_declarado` | Postcondición (c): «u.rol quedó con el valor declarado». | 1 | Pasa |
| `test_CO124_la_auditoria_incluye_el_rol_asignado` | Postcondición: entrada «Reactivación de usuario del sistema» […] «incluyendo el rol asignado». | 1 | Pasa |
| `test_CO199_la_pantalla_permite_modificar_el_rol_antes_de_confirmar` | Responsabilidad de CO-199: «presentar el rol con el que quedará reactivada, permitiendo modificarlo antes de confirmar». | 1 | Pasa |
| `test_CO125_la_auditoria_se_escribe_antes_de_eliminar_el_registro` | Postcondición, en el orden que «es parte del contrato»: primero la entrada, después la eliminación física. | 1 | Pasa |
| `test_CO125_se_elimino_fisicamente_la_instancia` | Postcondición (a): «se eliminó físicamente la instancia u : Usuario del sistema». | 1 | Pasa |
| `test_CO125_el_correo_queda_disponible_para_un_alta_nueva` | Postcondición: «el correo quedó disponible para un alta nueva (I-10 deja de bloquearlo)». | 1 | Pasa |
| `test_CO125_el_enlace_pendiente_queda_invalidado` | Postcondición (c): «el EnlaceActivacion pendiente quedó invalidado». | 1 | Pasa |
| `test_CO125_el_enlace_eliminado_ya_no_abre_nada` | La otra mitad de «invalidado»: la llave tampoco sirve. | 1 | Pasa |
| `test_CO125_una_cuenta_activa_no_se_elimina` | Excepción E2: «la cuenta está en estado Activo o Inactivo: la operación no se ofrece». | 1 | Pasa |
| `test_CO125_una_cuenta_inactiva_no_se_elimina` | Excepción E2, la otra mitad del estado. | 1 | Pasa |
| `test_CO125_una_pendiente_que_ya_inicio_sesion_no_se_elimina` | Excepción E1 y Notas: «no alcanza con estar Pendiente: una cuenta reactivada por CO-124 también lo está, y ésa sí tiene historial». | 1 | Pasa |
| `test_CO156_abandonar_antes_de_confirmar_no_cambia_nada` | Postcondición: «ninguna. | 3 | Pasa |
| `test_CO197_abrir_la_edicion_no_modifica_el_estado` | CO-197. | 1 | Pasa |
| `test_CO198_solicitar_la_baja_no_modifica_el_estado` | CO-198. | 1 | Pasa |
| `test_CO198_no_se_ofrece_sobre_el_ultimo_administrador` | CO-198, excepción E1: «última cuenta Administrador activa: se bloquea» (I-12). | 1 | Pasa |
| `test_CO199_solicitar_la_reactivacion_no_modifica_el_estado` | CO-199. | 1 | Pasa |
| `test_CO200_solicitar_la_eliminacion_no_modifica_el_estado` | CO-200. | 1 | Pasa |
| `test_CO201_el_listado_presenta_nombre_correo_rol_y_estado` | CO-201. | 1 | Pasa |
| `test_CO201_el_listado_no_modifica_el_estado` | CO-201. | 1 | Pasa |
| `test_acceso_CO201_el_listado_de_personal_es_solo_del_administrador` | Precondición de CO-201: «rol Administrador validado en el servidor» (RNF-03). | 2 | Pasa |
| `test_acceso_CO123_la_baja_de_usuario_es_solo_del_administrador` | Precondición de CO-123: la operación es del Administrador. | 2 | Pasa |
| `test_acceso_CO125_la_eliminacion_es_solo_del_administrador` | Precondición de CO-125: la operación es del Administrador. | 2 | Pasa |
| `test_CO202_la_ficha_no_modifica_el_estado` | Postcondición: ninguna. | 1 | Pasa |
| `test_CO202_una_cuenta_activa_ofrece_modificar_y_dar_de_baja` | CO202 una cuenta activa ofrece modificar y dar de baja | 1 | Pasa |
| `test_CO202_una_cuenta_pendiente_ofrece_reenviar_y_eliminar` | CO202 una cuenta pendiente ofrece reenviar y eliminar | 1 | Pasa |
| `test_CO202_una_cuenta_inactiva_ofrece_unicamente_reactivar` | CO202 una cuenta inactiva ofrece unicamente reactivar | 1 | Pasa |
| `test_CO202_no_ofrece_la_baja_del_ultimo_administrador` | «La interfaz no decide, refleja»: lo que el servidor rechaza (CO-198 E1) no se ofrece. | 1 | Pasa |
| `test_CO202_por_la_direccion_real_con_rol_cajero_se_deniega` | CO202 por la direccion real con rol cajero se deniega | 1 | Pasa |
| `test_CO202_una_cuenta_de_cliente_no_tiene_ficha_de_personal` | Las cuentas de Cliente tienen su ficha de sólo lectura (CO-195). | 1 | Pasa |

### `test_correos.py`

Los enlaces con token tienen que llegar enteros al correo.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_enlace_de_activacion_llega_entero` | El enlace de activacion llega entero | 1 | Pasa |
| `test_el_enlace_de_recuperacion_llega_entero` | El enlace de recuperacion llega entero | 1 | Pasa |
| `test_los_acentos_llegan_legibles` | Sin codificar, el cuerpo se lee tal cual: importa porque en desarrollo el correo se lee crudo en la consola del `runserver`. | 1 | Pasa |
| `test_ninguna_linea_del_cuerpo_queda_partida` | Ninguna linea del cuerpo queda partida | 1 | Pasa |

### `test_crear_administrador_inicial.py`

El comando de consola que crea la primera cuenta Administrador.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_crea_una_cuenta_administrador_activa` | Crea una cuenta administrador activa | 1 | Pasa |
| `test_la_cuenta_no_es_un_superusuario` | La regla que sacó al admin de Django: no existe ninguna cuenta fuera de los tres roles. | 1 | Pasa |
| `test_el_nombre_queda_partido_como_lo_guarda_django` | El nombre queda partido como lo guarda django | 1 | Pasa |
| `test_queda_en_el_registro_de_auditoria_y_sin_actor` | Es la única cuenta del sistema que nace sin que otra cuenta la haya creado. | 1 | Pasa |
| `test_no_corre_si_ya_hay_un_administrador_activo` | No corre si ya hay un administrador activo | 1 | Pasa |
| `test_si_el_unico_administrador_esta_de_baja_el_comando_si_corre` | La condición es que no haya ninguno **activo**: un sistema con el único Administrador dado de baja no tiene quién lo administre, que es justo el caso que este comando resuelve. | 1 | Pasa |
| `test_un_cajero_activo_no_cuenta_como_administrador` | Un cajero activo no cuenta como administrador | 1 | Pasa |
| `test_un_correo_ya_registrado_se_rechaza` | I-10: el correo identifica una sola cuenta en cualquier estado. | 1 | Pasa |
| `test_una_contrasena_debil_se_rechaza_como_en_cualquier_otro_camino` | Una contrasena debil se rechaza como en cualquier otro camino | 1 | Pasa |
| `test_un_nombre_que_no_es_un_nombre_se_rechaza` | Un nombre que no es un nombre se rechaza | 1 | Pasa |
| `test_un_correo_sin_arroba_se_rechaza` | Un correo sin arroba se rechaza | 1 | Pasa |
| `test_la_cuenta_creada_puede_iniciar_sesion` | La prueba de que sirve para algo: es el arranque del sistema. | 1 | Pasa |

### `test_eliminar_pendiente.py`

Eliminación de una cuenta que nunca se activó.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_la_pantalla_pide_confirmacion_explicita` | La pantalla pide confirmacion explicita | 1 | Pasa |
| `test_eliminar_una_cuenta_pendiente_la_borra` | Eliminar una cuenta pendiente la borra | 1 | Pasa |
| `test_eliminar_libera_el_correo_para_darlo_de_alta_de_nuevo` | Es el motivo por el que existe esta operación. | 1 | Pasa |
| `test_una_cuenta_que_alguna_vez_se_uso_no_se_elimina` | Una cuenta que alguna vez se uso no se elimina | 2 | Pasa |
| `test_la_auditoria_sobrevive_al_borrado_con_el_correo` | La auditoria sobrevive al borrado con el correo | 1 | Pasa |
| `test_el_registro_del_alta_tambien_sigue_consultable` | El registro del alta tambien sigue consultable | 1 | Pasa |
| `test_solo_el_administrador_puede_eliminar` | Solo el administrador puede eliminar | 1 | Pasa |

### `test_listado_clientes.py`

Consulta de cuentas de Cliente desde el backoffice (solo lectura).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_la_pantalla_lista_solo_cuentas_de_cliente` | La pantalla lista solo cuentas de cliente | 1 | Pasa |
| `test_la_tabla_no_ofrece_acciones_sobre_las_cuentas` | Es de consulta: dar de baja un Cliente es el CU-CLI-BAJ, todavía sin documentar. | 1 | Pasa |
| `test_muestra_el_telefono_armado_y_la_direccion` | Muestra el telefono armado y la direccion | 1 | Pasa |
| `test_avisa_cuando_una_cuenta_no_tiene_consentimiento_registrado` | Una cuenta sin fecha de aceptación no salió del registro público. | 1 | Pasa |
| `test_el_buscador_encuentra_por_nombre_correo_y_telefono` | El buscador encuentra por nombre correo y telefono | 3 | Pasa |
| `test_el_filtro_por_provincia` | El filtro por provincia | 1 | Pasa |
| `test_el_filtro_por_estado` | El filtro por estado | 1 | Pasa |
| `test_una_provincia_inventada_en_la_url_se_ignora` | Un valor cualquiera en la query string no filtra de más ni rompe. | 1 | Pasa |
| `test_el_pedido_parcial_devuelve_solo_la_tabla` | El pedido parcial devuelve solo la tabla | 1 | Pasa |
| `test_solo_el_administrador_consulta_los_clientes` | RNF-03: el control es del servidor, no de que el menú no muestre el enlace. | 2 | Pasa |
| `test_sin_sesion_redirige_al_login` | Sin sesion redirige al login | 1 | Pasa |

### `test_listado_usuarios.py`

Buscador y filtros de la tabla de usuarios del sistema.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_la_busqueda_filtra_por_nombre` | La busqueda filtra por nombre | 1 | Pasa |
| `test_la_busqueda_filtra_por_correo` | La busqueda filtra por correo | 1 | Pasa |
| `test_el_filtro_de_rol_deja_solo_ese_rol` | El filtro de rol deja solo ese rol | 1 | Pasa |
| `test_el_filtro_de_estado_deja_solo_ese_estado` | El filtro de estado deja solo ese estado | 1 | Pasa |
| `test_los_filtros_se_combinan_con_la_busqueda` | Los filtros se combinan con la busqueda | 1 | Pasa |
| `test_un_filtro_con_un_valor_invalido_se_ignora` | Un parámetro pisado a mano en la URL no filtra de más ni rompe la vista. | 3 | Pasa |
| `test_sin_resultados_se_explica_en_la_voz_del_sistema` | Sin resultados se explica en la voz del sistema | 1 | Pasa |
| `test_se_informa_cuantos_resultados_hay` | Se informa cuantos resultados hay | 1 | Pasa |
| `test_la_fila_del_propio_usuario_esta_marcada` | El Administrador se ve a sí mismo en la tabla: conviene que lo sepa. | 1 | Pasa |
| `test_los_filtros_siguen_siendo_selects_de_verdad` | Los filtros son `select` nativos (`identidad_visual.md`, Formularios). | 1 | Pasa |
| `test_el_pedido_parcial_devuelve_solo_la_tabla` | Es lo que consume el buscador en vivo: el fragmento, no la pantalla. | 1 | Pasa |
| `test_el_pedido_parcial_tambien_exige_ser_administrador` | El pedido parcial tambien exige ser administrador | 1 | Pasa |

### `test_login.py`

CU-AUT-INI — Iniciar Sesión.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_login_exitoso_crea_sesion_y_redirige_segun_rol` | Login exitoso crea sesion y redirige segun rol | 3 | Pasa |
| `test_login_exitoso_registra_el_inicio_en_auditoria` | Login exitoso registra el inicio en auditoria | 1 | Pasa |
| `test_login_acepta_el_correo_sin_distinguir_mayusculas` | Login acepta el correo sin distinguir mayusculas | 1 | Pasa |
| `test_contrasena_incorrecta_no_crea_sesion_y_muestra_mensaje_generico` | Contrasena incorrecta no crea sesion y muestra mensaje generico | 1 | Pasa |
| `test_correo_inexistente_devuelve_exactamente_el_mismo_mensaje` | No debe poder distinguirse "no existe la cuenta" de "erraste la clave". | 1 | Pasa |
| `test_cuenta_inactiva_no_crea_sesion` | Cuenta inactiva no crea sesion | 1 | Pasa |
| `test_cuenta_inactiva_no_se_revela_a_quien_no_sabe_la_contrasena` | Sin la contraseña correcta, una cuenta inactiva responde como cualquier otra. | 1 | Pasa |
| `test_usuario_con_sesion_activa_no_ve_la_pantalla_de_login` | Precondición del CU: no tiene una sesión vigente en el dispositivo. | 1 | Pasa |

### `test_logout.py`

CU-AUT-FIN — Cerrar Sesión.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_logout_invalida_la_sesion_actual` | Logout invalida la sesion actual | 1 | Pasa |
| `test_logout_no_afecta_las_sesiones_de_otros_dispositivos` | Logout no afecta las sesiones de otros dispositivos | 1 | Pasa |
| `test_logout_queda_registrado_en_auditoria` | Logout queda registrado en auditoria | 1 | Pasa |
| `test_logout_no_acepta_get` | Un GET no puede desloguear: evita que un enlace externo cierre la sesión. | 1 | Pasa |

### `test_models.py`

El modelo de usuario: las garantías que la base sostiene por su cuenta.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_crear_usuario_con_rol_por_defecto` | Crear usuario con rol por defecto | 1 | Pasa |
| `test_la_contrasena_se_guarda_hasheada` | La contrasena se guarda hasheada | 1 | Pasa |
| `test_el_correo_se_normaliza_a_minusculas` | El correo se normaliza a minusculas | 1 | Pasa |
| `test_no_permite_dos_cuentas_con_el_mismo_correo` | No permite dos cuentas con el mismo correo | 1 | Pasa |

### `test_modificacion_usuario.py`

CU-USR-MOD — Modificar Usuario del Sistema.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_formulario_precarga_los_datos_actuales` | El formulario precarga los datos actuales | 1 | Pasa |
| `test_modificar_datos_sin_tocar_el_rol_no_invalida_la_sesion` | Modificar datos sin tocar el rol no invalida la sesion | 1 | Pasa |
| `test_modificar_el_rol_invalida_la_sesion_del_usuario` | Modificar el rol invalida la sesion del usuario | 1 | Pasa |
| `test_modificar_el_rol_no_toca_las_sesiones_de_los_demas` | Modificar el rol no toca las sesiones de los demas | 1 | Pasa |
| `test_no_se_le_puede_quitar_el_rol_al_unico_administrador_activo` | No se le puede quitar el rol al unico administrador activo | 1 | Pasa |
| `test_se_le_puede_quitar_el_rol_si_queda_otro_administrador_activo` | Se le puede quitar el rol si queda otro administrador activo | 1 | Pasa |
| `test_cambiarse_el_rol_a_uno_mismo_cierra_la_propia_sesion` | La sesión invalidada puede ser la del propio Administrador que edita. | 1 | Pasa |
| `test_un_correo_ya_usado_por_otra_cuenta_no_actualiza_nada` | Un correo ya usado por otra cuenta no actualiza nada | 1 | Pasa |
| `test_conservar_el_propio_correo_no_es_un_conflicto` | Conservar el propio correo no es un conflicto | 1 | Pasa |
| `test_la_auditoria_registra_valores_anteriores_y_nuevos` | La auditoria registra valores anteriores y nuevos | 1 | Pasa |
| `test_guardar_sin_cambios_no_ensucia_la_auditoria` | Guardar sin cambios no ensucia la auditoria | 1 | Pasa |
| `test_regenerar_el_enlace_de_activacion_invalida_el_anterior` | Regenerar el enlace de activacion invalida el anterior | 1 | Pasa |
| `test_regenerar_el_enlace_queda_en_auditoria` | Regenerar el enlace queda en auditoria | 1 | Pasa |
| `test_no_se_regenera_el_enlace_de_una_cuenta_ya_activa` | No se regenera el enlace de una cuenta ya activa | 1 | Pasa |
| `test_solo_el_administrador_puede_editar` | Solo el administrador puede editar | 1 | Pasa |

### `test_pantallas_backoffice.py`

Chequeos de las pantallas del Módulo 13 que no son de lógica de negocio.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_ninguna_pantalla_filtra_comentarios_del_template` | `{# ... | 1 | Pasa |

### `test_parametros_de_seguridad.py`

La sección Seguridad de Parámetros (`CO-130`; `CO-114`; B-12-001, plan 00, A3).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO130_la_seccion_seguridad_guarda_los_dos_valores_y_los_audita` | CO130 la seccion seguridad guarda los dos valores y los audita | 1 | Pasa |
| `test_CO130_E2_un_valor_fuera_de_rango_no_guarda_nada` | CO130 E2 un valor fuera de rango no guarda nada | 1 | Pasa |
| `test_CO114_E1_el_bloqueo_dura_el_periodo_parametrizado` | CO114 E1 el bloqueo dura el periodo parametrizado | 1 | Pasa |
| `test_CO114_la_sesion_vence_por_inactividad_segun_el_parametro` | CO114 la sesion vence por inactividad segun el parametro | 1 | Pasa |
| `test_acceso_el_cajero_no_cambia_los_parametros_de_seguridad` | Acceso el cajero no cambia los parametros de seguridad | 1 | Pasa |
| `test_CO207_parametros_presenta_todas_las_secciones_sin_modificar_nada` | `CU-CFG-PAR` paso 2: con los módulos construidos, ya no falta ninguna sección. | 1 | Pasa |
| `test_CO053_desde_parametros_el_margen_global_se_cambia_en_su_pantalla` | `CU-CFG-PAR` A1: el panel no edita el margen; enlaza a `CO-053`, que recalcula. | 1 | Pasa |

### `test_reactivacion_usuario.py`

Reactivación y congelamiento de una cuenta dada de baja.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_la_pantalla_pide_confirmacion_explicita` | La pantalla pide confirmacion explicita | 1 | Pasa |
| `test_reactivar_deja_la_cuenta_pendiente_y_manda_enlace` | Reactivar deja la cuenta pendiente y manda enlace | 1 | Pasa |
| `test_reactivar_invalida_la_contrasena_anterior` | El acceso no vuelve con la credencial vieja: hay que elegir una nueva. | 1 | Pasa |
| `test_una_cuenta_reactivada_no_puede_entrar_hasta_usar_el_enlace` | Una cuenta reactivada no puede entrar hasta usar el enlace | 1 | Pasa |
| `test_la_cuenta_reactivada_conserva_su_historial` | El historial es de la cuenta y sobrevive a la vuelta. | 1 | Pasa |
| `test_la_reactivacion_puede_devolver_la_cuenta_con_otro_rol` | CO-124: «u.rol quedó con el valor declarado», no con el que tenía al darse de baja. | 1 | Pasa |
| `test_la_reactivacion_queda_en_auditoria` | La reactivacion queda en auditoria | 1 | Pasa |
| `test_no_se_reactiva_una_cuenta_que_no_esta_de_baja` | No se reactiva una cuenta que no esta de baja | 1 | Pasa |
| `test_solo_el_administrador_puede_reactivar` | Solo el administrador puede reactivar | 1 | Pasa |
| `test_no_se_puede_abrir_la_edicion_de_una_cuenta_de_baja` | No se puede abrir la edicion de una cuenta de baja | 1 | Pasa |
| `test_un_post_directo_tampoco_modifica_una_cuenta_de_baja` | RNF-03: esconder el botón no es una restricción; el chequeo va en la vista. | 1 | Pasa |
| `test_la_tabla_ofrece_reactivar_y_no_editar` | La tabla ofrece reactivar y no editar | 1 | Pasa |
| `test_una_cuenta_reactivada_no_se_puede_eliminar` | Quedó Pendiente, pero tiene historial: el borrado físico no corresponde. | 1 | Pasa |

### `test_recuperar_contrasena.py`

CU-AUT-REC — Recuperar Contraseña.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_correo_existente_e_inexistente_devuelven_el_mismo_mensaje` | Correo existente e inexistente devuelven el mismo mensaje | 1 | Pasa |
| `test_solo_se_envia_correo_a_una_cuenta_real` | Solo se envia correo a una cuenta real | 1 | Pasa |
| `test_una_cuenta_inactiva_no_recibe_enlace` | Una cuenta inactiva no recibe enlace | 1 | Pasa |
| `test_el_correo_incluye_un_enlace_utilizable` | El correo incluye un enlace utilizable | 1 | Pasa |
| `test_un_token_valido_permite_cambiar_la_contrasena` | Un token valido permite cambiar la contrasena | 1 | Pasa |
| `test_un_token_expirado_es_rechazado` | Un token expirado es rechazado | 1 | Pasa |
| `test_un_token_vigente_a_los_29_minutos_sigue_sirviendo` | Un token vigente a los 29 minutos sigue sirviendo | 1 | Pasa |
| `test_un_token_ya_usado_no_puede_reutilizarse` | Un token ya usado no puede reutilizarse | 1 | Pasa |
| `test_contrasenas_que_no_coinciden_no_cambian_nada_y_no_queman_el_token` | Contrasenas que no coinciden no cambian nada y no queman el token | 1 | Pasa |
| `test_contrasena_debil_es_rechazada_con_el_motivo` | Contrasena debil es rechazada con el motivo | 1 | Pasa |
| `test_el_cambio_invalida_todas_las_sesiones_activas` | El cambio invalida todas las sesiones activas | 1 | Pasa |
| `test_el_cambio_queda_registrado_en_auditoria` | El cambio queda registrado en auditoria | 1 | Pasa |

### `test_registro_cliente.py`

CU-CLI-ALT — Registrar Cuenta de Cliente.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_registro_crea_una_cuenta_de_cliente_activa` | El registro crea una cuenta de cliente activa | 1 | Pasa |
| `test_la_contrasena_se_guarda_hasheada` | RNF-04: en la base no puede quedar la contraseña en texto plano. | 1 | Pasa |
| `test_el_registro_inicia_sesion_automaticamente` | El registro inicia sesion automaticamente | 1 | Pasa |
| `test_el_registro_envia_el_correo_de_bienvenida` | El registro envia el correo de bienvenida | 1 | Pasa |
| `test_el_registro_queda_en_el_log_de_auditoria` | El registro queda en el log de auditoria | 1 | Pasa |
| `test_el_inicio_de_sesion_automatico_tambien_se_audita` | El `login()` de la vista pasa por la misma signal que el CU-AUT-INI. | 1 | Pasa |
| `test_los_datos_opcionales_se_guardan` | Los datos opcionales se guardan | 1 | Pasa |
| `test_los_datos_opcionales_pueden_quedar_vacios` | Los datos opcionales pueden quedar vacios | 1 | Pasa |
| `test_la_aceptacion_de_la_politica_queda_persistida` | La aceptacion de la politica queda persistida | 1 | Pasa |
| `test_sin_aceptar_la_politica_no_se_crea_la_cuenta` | Sin aceptar la politica no se crea la cuenta | 1 | Pasa |
| `test_un_correo_ya_registrado_es_rechazado_y_ofrece_recuperar_la_contrasena` | Un correo ya registrado es rechazado y ofrece recuperar la contrasena | 1 | Pasa |
| `test_el_correo_repetido_se_detecta_aunque_cambie_la_capitalizacion` | El modelo normaliza a minúsculas: "Lucia@" y "lucia@" son la misma cuenta. | 1 | Pasa |
| `test_contrasenas_distintas_conservan_los_datos_ya_ingresados` | Contrasenas distintas conservan los datos ya ingresados | 1 | Pasa |
| `test_una_contrasena_que_no_cumple_los_requisitos_minimos_es_rechazada` | Los requisitos los ponen los `AUTH_PASSWORD_VALIDATORS`, no reglas propias. | 1 | Pasa |
| `test_un_campo_obligatorio_vacio_no_crea_la_cuenta` | Un campo obligatorio vacio no crea la cuenta | 1 | Pasa |
| `test_un_nombre_de_menos_de_tres_letras_es_rechazado` | Se cuentan letras, no caracteres: "A.B" tiene tres pero no es un nombre. | 4 | Pasa |
| `test_un_nombre_con_caracteres_especiales_es_rechazado` | Un nombre con caracteres especiales es rechazado | 6 | Pasa |
| `test_los_nombres_reales_se_aceptan` | La validación no puede dejar afuera apellidos que existen de verdad. | 6 | Pasa |
| `test_los_espacios_de_mas_se_limpian_antes_de_validar` | Los espacios de mas se limpian antes de validar | 1 | Pasa |
| `test_el_pais_viene_predeterminado_en_argentina` | El pais viene predeterminado en argentina | 1 | Pasa |
| `test_los_codigos_de_pais_salen_del_catalogo_externo` | No hay una lista escrita a mano: viene del servicio (o de su respaldo). | 1 | Pasa |
| `test_un_codigo_de_pais_fuera_del_catalogo_es_rechazado` | Un codigo de pais fuera del catalogo es rechazado | 1 | Pasa |
| `test_un_numero_de_telefono_invalido_es_rechazado` | El caso que motivó desarmar el teléfono: un "-1" no es un teléfono. | 6 | Pasa |
| `test_un_codigo_de_area_invalido_es_rechazado` | Un codigo de area invalido es rechazado | 4 | Pasa |
| `test_un_codigo_de_pais_invalido_es_rechazado` | Un codigo de pais invalido es rechazado | 4 | Pasa |
| `test_el_telefono_se_normaliza_en_vez_de_rechazarse` | El telefono se normaliza en vez de rechazarse | 4 | Pasa |
| `test_un_numero_sin_codigo_de_area_es_rechazado` | Medio teléfono no se puede discar: o van las dos partes o ninguna. | 1 | Pasa |
| `test_un_codigo_de_area_sin_numero_es_rechazado` | Un codigo de area sin numero es rechazado | 1 | Pasa |
| `test_el_pais_vacio_vuelve_al_predeterminado` | El pais vacio vuelve al predeterminado | 1 | Pasa |
| `test_la_direccion_completa_se_guarda_con_todos_sus_campos` | La direccion completa se guarda con todos sus campos | 1 | Pasa |
| `test_una_direccion_incompleta_es_rechazada` | Sin calle, localidad, código postal o provincia no se puede despachar nada. | 4 | Pasa |
| `test_los_campos_accesorios_solos_tampoco_alcanzan` | Un depto sin dirección no es una dirección. | 1 | Pasa |
| `test_un_codigo_postal_invalido_es_rechazado` | Un codigo postal invalido es rechazado | 4 | Pasa |
| `test_el_codigo_postal_se_guarda_en_mayusculas` | El codigo postal se guarda en mayusculas | 1 | Pasa |
| `test_una_provincia_inventada_es_rechazada` | El desplegable no es la restricción: el servidor valida contra el catálogo. | 1 | Pasa |
| `test_la_provincia_arranca_sin_elegir` | La provincia arranca sin elegir | 1 | Pasa |
| `test_las_provincias_del_formulario_salen_del_catalogo_oficial` | No hay una lista escrita a mano: viene de georef (o de su respaldo). | 1 | Pasa |
| `test_el_registro_funciona_aunque_la_api_de_provincias_este_caida` | La fixture `sin_red` ya simula la caída: esto verifica que no bloquea. | 1 | Pasa |
| `test_un_cpa_de_otra_provincia_es_rechazado` | La N de N3300ABC es de Misiones: con Corrientes elegida, algo está mal. | 1 | Pasa |
| `test_el_codigo_postal_de_cuatro_digitos_no_se_contradice` | Sin letra no declara provincia, así que no hay nada que cruzar. | 1 | Pasa |
| `test_un_cpa_que_coincide_con_la_provincia_pasa` | Un cpa que coincide con la provincia pasa | 1 | Pasa |
| `test_un_campo_con_error_queda_marcado_para_el_lector_de_pantalla` | El borde rojo no existe para quien no ve la pantalla. | 1 | Pasa |
| `test_un_campo_sin_error_no_lleva_la_marca` | Un campo sin error no lleva la marca | 1 | Pasa |
| `test_el_formulario_es_de_acceso_publico` | El formulario es de acceso publico | 1 | Pasa |
| `test_quien_ya_tiene_sesion_no_vuelve_al_registro` | Precondición del CU: el registro es para quien no tiene sesión previa. | 1 | Pasa |
| `test_el_rol_no_se_puede_elegir_desde_el_formulario` | El rol lo fija el servidor: un POST con `rol` no puede escalar permisos. | 1 | Pasa |
| `test_el_estado_no_se_puede_elegir_desde_el_formulario` | El estado no se puede elegir desde el formulario | 1 | Pasa |

### `test_sesion.py`

CU-AUT-INI, comportamiento adicional: expiración por inactividad y renovación.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_login_avisa_cuando_se_llega_por_sesion_expirada` | El login avisa cuando se llega por sesion expirada | 1 | Pasa |
| `test_el_login_normal_no_muestra_el_aviso_de_expiracion` | El login normal no muestra el aviso de expiracion | 1 | Pasa |
| `test_renovar_extiende_la_sesion_del_usuario_autenticado` | Renovar extiende la sesion del usuario autenticado | 1 | Pasa |
| `test_renovar_sin_sesion_redirige_al_login` | Renovar sin sesion redirige al login | 1 | Pasa |
| `test_renovar_no_acepta_get` | Renovar no acepta get | 1 | Pasa |

---

## almacen — `apps/almacen`

### `test_acceso_y_concurrencia_almacen.py`

Acceso al stock almacenado por la dirección real, y escrituras a la vez.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_acceso_el_cliente_no_entra_al_panel_del_stock` | Acceso el cliente no entra al panel del stock | 1 | Pasa |
| `test_acceso_el_cajero_no_modifica_el_plazo` | Acceso el cajero no modifica el plazo | 1 | Pasa |
| `test_acceso_el_personal_no_usa_el_stock_de_mi_cuenta` | Acceso el personal no usa el stock de mi cuenta | 2 | Pasa |
| `test_acceso_un_cliente_no_pide_el_envio_de_lo_ajeno` | Acceso un cliente no pide el envio de lo ajeno | 1 | Pasa |
| `test_acceso_el_menu_lleva_al_stock_en_local` | Acceso el menu lleva al stock en local | 1 | Pasa |
| `test_concurrencia_dos_pestanas_que_piden_el_envio_generan_una_sola_solicitud` | Concurrencia dos pestanas que piden el envio generan una sola solicitud | 1 | Pasa |
| `test_concurrencia_el_despacho_y_el_retiro_del_mismo_articulo_registran_uno` | Concurrencia el despacho y el retiro del mismo articulo registran uno | 1 | Pasa |
| `test_concurrencia_el_vencimiento_y_el_pedido_de_envio_no_se_pisan` | Concurrencia el vencimiento y el pedido de envio no se pisan | 1 | Pasa |

### `test_contratos_18_almacen.py`

Contratos del stock almacenado en local (plan 18).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO095_el_articulo_diferido_queda_retenido_uno_por_unidad` | CO095 el articulo diferido queda retenido uno por unidad | 1 | Pasa |
| `test_CO095_el_pedido_muestra_el_articulo_en_el_local_y_deja_de_contar_como_demorado` | CO095 el pedido muestra el articulo en el local y deja de contar como demorado | 1 | Pasa |
| `test_CO215_lista_lo_propio_con_lo_proximo_a_vencer_y_lo_pendiente_en_solo_lectura` | CO215 lista lo propio con lo proximo a vencer y lo pendiente en solo lectura | 1 | Pasa |
| `test_CO215_A1_sin_articulos_lo_dice` | CO215 A1 sin articulos lo dice | 1 | Pasa |
| `test_CO216_resume_valor_costo_y_direccion_sin_registrar_nada` | CO216 resume valor costo y direccion sin registrar nada | 1 | Pasa |
| `test_CO216_desde_el_monto_minimo_el_envio_es_gratis` | CO216 desde el monto minimo el envio es gratis | 1 | Pasa |
| `test_CO216_no_se_puede_pedir_lo_de_otro_ni_lo_que_no_esta_disponible` | CO216 no se puede pedir lo de otro ni lo que no esta disponible | 1 | Pasa |
| `test_CO087_la_direccion_del_envio_no_toca_el_perfil` | CO087 la direccion del envio no toca el perfil | 1 | Pasa |
| `test_CO151_E1_sin_direccion_no_se_confirma` | CO151 E1 sin direccion no se confirma | 1 | Pasa |
| `test_CO151_gratis_genera_la_solicitud_y_avisa_al_administrador` | CO151 gratis genera la solicitud y avisa al administrador | 1 | Pasa |
| `test_CO151_A1_pago_aprobado_genera_la_solicitud_con_su_transaccion` | CO151 A1 pago aprobado genera la solicitud con su transaccion | 1 | Pasa |
| `test_CO151_A1_pago_rechazado_no_genera_nada` | CO151 A1 pago rechazado no genera nada | 1 | Pasa |
| `test_CO089_E3_si_el_articulo_vencio_mientras_pagaba_se_reembolsa` | CO089 E3 si el articulo vencio mientras pagaba se reembolsa | 1 | Pasa |
| `test_CO156_volver_sin_confirmar_el_envio_no_registra_nada` | CO156 volver sin confirmar el envio no registra nada | 1 | Pasa |
| `test_CO151_el_cierre_de_caja_cuenta_el_envio_como_online` | CO151 el cierre de caja cuenta el envio como online | 1 | Pasa |
| `test_CO217_lista_todos_los_clientes_con_filtros` | CO217 lista todos los clientes con filtros | 2 | Pasa |
| `test_CO218_la_ficha_muestra_origen_fechas_valor_e_historial` | CO218 la ficha muestra origen fechas valor e historial | 1 | Pasa |
| `test_CO218_el_cajero_no_ve_la_accion_del_plazo` | CO218 el cajero no ve la accion del plazo | 1 | Pasa |
| `test_CO152_despachar_la_solicitud_registra_cada_articulo_y_avisa` | CO152 despachar la solicitud registra cada articulo y avisa | 2 | Pasa |
| `test_CO152_E1_si_un_articulo_cambio_no_se_registra_nada` | CO152 E1 si un articulo cambio no se registra nada | 1 | Pasa |
| `test_CO227_el_retiro_registra_al_titular_sin_avisarle` | CO227 el retiro registra al titular sin avisarle | 2 | Pasa |
| `test_CO227_E1_lo_pendiente_de_despacho_no_se_retira` | CO227 E1 lo pendiente de despacho no se retira | 1 | Pasa |
| `test_CO153_cambia_la_fecha_con_motivo_y_avisa_al_cliente` | CO153 cambia la fecha con motivo y avisa al cliente | 1 | Pasa |
| `test_CO153_E1_E2_fecha_no_futura_o_motivo_vacio_se_rechazan` | CO153 E1 E2 fecha no futura o motivo vacio se rechazan | 3 | Pasa |
| `test_CO153_un_articulo_en_estado_final_no_tiene_plazo` | CO153 un articulo en estado final no tiene plazo | 1 | Pasa |
| `test_CO154_avisa_una_vez_por_fecha_lo_que_vence_en_los_dias_de_aviso` | CO154 avisa una vez por fecha lo que vence en los dias de aviso | 1 | Pasa |
| `test_CO154_lo_vencido_disponible_vuelve_al_stock_con_su_valor_en_puntos` | CO154 lo vencido disponible vuelve al stock con su valor en puntos | 1 | Pasa |
| `test_CO154_A1_lo_vencido_con_envio_pendiente_se_extiende_tres_dias_cada_vez` | CO154 A1 lo vencido con envio pendiente se extiende tres dias cada vez | 1 | Pasa |
| `test_CO154_E2_sin_articulos_elegibles_no_hace_nada` | CO154 E2 sin articulos elegibles no hace nada | 1 | Pasa |
| `test_CO154_el_temporizador_corre_el_ciclo` | CO154 el temporizador corre el ciclo | 1 | Pasa |
| `test_CO154_en_estado_final_no_se_toca` | CO154 en estado final no se toca | 1 | Pasa |

---

## caja — `apps/caja`

### `test_concurrencia_caja.py`

`CO-126` bajo concurrencia real: dos usuarios cierran la caja a la vez.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO126_dos_cierres_a_la_vez_dejan_uno_solo_con_cada_transaccion_una_vez` | CO126 dos cierres a la vez dejan uno solo con cada transaccion una vez | 1 | Pasa |

### `test_contratos_14_caja.py`

Pruebas de contrato de la caja (`CU-CAJ-CIE`, plan 14): `CO-203`, `CO-126`, `CO-127`.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO203_el_resumen_previo_totaliza_por_canal_y_por_medio` | CO203 el resumen previo totaliza por canal y por medio | 1 | Pasa |
| `test_CO203_A1_lista_las_pendientes_de_verificacion_aparte` | CO203 A1 lista las pendientes de verificacion aparte | 1 | Pasa |
| `test_CO203_avisa_lo_de_dias_anteriores_sin_cerrar` | CO203 avisa lo de dias anteriores sin cerrar | 1 | Pasa |
| `test_CO203_cuenta_las_compras_pagadas_solo_con_puntos` | CO203 cuenta las compras pagadas solo con puntos | 1 | Pasa |
| `test_CO203_E2_sin_movimientos` | CO203 E2 sin movimientos | 1 | Pasa |
| `test_CO203_no_modifica_el_estado_del_sistema` | CO203 no modifica el estado del sistema | 1 | Pasa |
| `test_CO126_a_se_crea_el_cierre` | CO126 a se crea el cierre | 1 | Pasa |
| `test_CO126_b_el_cierre_queda_asociado_a_las_transacciones_incluidas` | CO126 b el cierre queda asociado a las transacciones incluidas | 1 | Pasa |
| `test_CO126_c_fecha_totales_y_cuentas` | CO126 c fecha totales y cuentas | 1 | Pasa |
| `test_CO126_c_las_incluidas_pasan_a_incluidas_en_cierre` | CO126 c las incluidas pasan a incluidas en cierre | 1 | Pasa |
| `test_CO126_c_las_pendientes_y_rechazadas_quedan_fuera` | CO126 c las pendientes y rechazadas quedan fuera | 1 | Pasa |
| `test_CO126_queda_en_la_auditoria_con_los_totales` | CO126 queda en la auditoria con los totales | 1 | Pasa |
| `test_CO126_E1_no_hay_segundo_cierre_en_el_dia` | CO126 E1 no hay segundo cierre en el dia | 1 | Pasa |
| `test_CO126_lo_vendido_despues_entra_en_el_cierre_siguiente` | CO126 lo vendido despues entra en el cierre siguiente | 1 | Pasa |
| `test_CO126_E2_sin_movimientos_no_hay_cierre` | CO126 E2 sin movimientos no hay cierre | 1 | Pasa |
| `test_CO126_la_base_no_admite_dos_cierres_de_la_misma_fecha` | CO126 la base no admite dos cierres de la misma fecha | 1 | Pasa |
| `test_CO127_el_csv_trae_cada_transaccion_y_los_totales` | CO127 el csv trae cada transaccion y los totales | 1 | Pasa |
| `test_CO127_queda_en_la_auditoria` | CO127 queda en la auditoria | 1 | Pasa |
| `test_acceso_el_cliente_recibe_403_en_la_caja` | Acceso el cliente recibe 403 en la caja | 2 | Pasa |
| `test_acceso_el_cliente_no_puede_cerrar` | Acceso el cliente no puede cerrar | 1 | Pasa |
| `test_acceso_el_administrador_tambien_cierra` | Acceso el administrador tambien cierra | 1 | Pasa |

---

## Catálogo — `apps/catalog`

### `test_alta_lote_importado.py`

Alta de lote de material editorial importado.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_cre_y_el_margen_quedan_congelados_en_el_lote` | Postcondición del CU: la auditoría tiene que poder decir con qué números se fijaron estos precios, y los dos cambian con el tiempo. | 1 | Pasa |
| `test_el_precio_final_sale_de_la_formula_de_rf_10` | `C × (1 + R) × (1 + M)` = 1000 × 1,1 × 1,4 = 1540. | 1 | Pasa |
| `test_el_cre_del_lote_se_aplica_a_todos_los_items` | El cre del lote se aplica a todos los items | 1 | Pasa |
| `test_el_costo_en_origen_es_obligatorio` | El costo en origen es obligatorio | 1 | Pasa |
| `test_la_calculadora_de_envio_es_obligatoria` | Sin los dos totales no hay CRE, y sin CRE no hay precio. | 1 | Pasa |
| `test_editar_el_precio_final_sin_confirmar_muestra_la_advertencia` | El CU pide que el Administrador confirme. | 1 | Pasa |
| `test_editar_el_precio_final_confirmado_marca_precio_manual` | Editar el precio final confirmado marca precio manual | 1 | Pasa |
| `test_el_precio_base_no_cambia_al_editar_el_precio_final` | RF-10: el precio base se almacena siempre y nunca se deriva del final. | 1 | Pasa |
| `test_confirmar_el_precio_calculado_no_lo_marca_como_manual` | Escribir el mismo número que calculó el sistema no es editarlo. | 1 | Pasa |
| `test_un_lote_sin_ediciones_deja_todos_los_productos_alcanzables_por_la_propagacion` | Para que el recálculo de CU-PVP-MAR los alcance a todos por defecto. | 1 | Pasa |
| `test_la_cotizacion_convierte_el_costo_en_origen_a_pesos` | La cotizacion convierte el costo en origen a pesos | 1 | Pasa |
| `test_un_lote_en_pesos_se_guarda_con_cotizacion_uno` | Se guarda el 1 en vez de dejarlo en nulo: así el cálculo de cualquier ítem se reconstruye igual, con conversión o sin ella. | 1 | Pasa |
| `test_una_moneda_fuera_del_catalogo_es_rechazada` | El negocio importa en tres monedas y el desplegable ofrece esas tres. | 4 | Pasa |
| `test_una_moneda_extranjera_sin_cotizacion_es_rechazada` | Una moneda extranjera sin cotizacion es rechazada | 1 | Pasa |
| `test_una_cotizacion_sobre_un_lote_en_pesos_es_rechazada` | Se rechaza en vez de ignorarla: descartar en silencio un número que alguien escribió es la forma más rápida de que un precio salga mal sin que nadie se entere. | 1 | Pasa |
| `test_la_pantalla_ofrece_la_cotizacion_de_referencia` | La sugerencia se ofrece; el que decide es el Administrador. | 1 | Pasa |
| `test_el_estado_sigue_la_misma_logica_que_cu_01` | El estado sigue la misma logica que cu 01 | 1 | Pasa |
| `test_un_duplicado_se_excluye_y_el_resto_se_registra` | Un duplicado se excluye y el resto se registra | 1 | Pasa |
| `test_dos_importados_sin_formato_del_mismo_tomo_chocan_entre_si` | En SQL dos nulos no son iguales, así que sin el `Coalesce` de la restricción el mismo tomo entraría dos veces sin que nada lo impida. | 1 | Pasa |
| `test_la_auditoria_conserva_el_cre_y_el_margen_usados` | La auditoria conserva el cre y el margen usados | 1 | Pasa |
| `test_el_resumen_muestra_el_desglose_del_lote` | El resumen muestra el desglose del lote | 1 | Pasa |

### `test_alta_lote_nacional.py`

Alta de lote de material editorial nacional.

**Casos de prueba que ejecuta:** CP-25.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_los_items_heredan_la_clasificacion_y_el_precio_de_la_cabecera` | Los items heredan la clasificacion y el precio de la cabecera | 1 | Pasa |
| `test_con_la_cabecera_puesta_manda_la_cabecera_aunque_el_item_declare_otra_cosa` | El ítem llega bloqueado en la pantalla, y el servidor sostiene la regla. | 1 | Pasa |
| `test_un_item_desbloqueado_declara_su_propia_clasificacion` | Un item desbloqueado declara su propia clasificacion | 1 | Pasa |
| `test_desbloquear_un_item_convierte_el_lote_en_mixto` | La cabecera deja de describir al lote, así que se la vacía. | 1 | Pasa |
| `test_un_item_puede_sobrescribir_el_precio_sin_desbloquear_nada` | El precio y el estado siempre se pueden pisar por ítem: lo que el bloqueo protege es la clasificación, no los valores del alta. | 1 | Pasa |
| `test_el_precio_editado_a_mano_queda_excluido_de_la_propagacion` | Sin la marca, un cambio de la tabla de precios le pisaría después una decisión que alguien tomó a propósito. | 1 | Pasa |
| `test_el_producto_queda_vinculado_a_su_combinacion_de_la_tabla` | El precio de un nacional es un vínculo, no una foto (RF-11). | 1 | Pasa |
| `test_en_un_lote_mixto_cada_item_declara_sus_propios_datos` | En un lote mixto cada item declara sus propios datos | 1 | Pasa |
| `test_en_un_lote_mixto_falta_la_editorial_del_item` | En un lote mixto falta la editorial del item | 1 | Pasa |
| `test_en_un_lote_mixto_falta_el_tipo_del_item` | En un lote mixto falta el tipo del item | 1 | Pasa |
| `test_sin_precio_de_referencia_el_alta_pide_el_precio_a_mano` | Que la combinación no esté en la tabla no bloquea el alta: solo obliga a escribir el precio. | 1 | Pasa |
| `test_el_formato_es_obligatorio_para_un_tipo_que_lo_usa` | El formato es obligatorio para un tipo que lo usa | 1 | Pasa |
| `test_un_tipo_que_no_usa_formato_no_lo_pide_ni_lo_guarda` | Un artbook no se clasifica por tamaño: si viene un formato, se descarta. | 1 | Pasa |
| `test_un_comic_se_da_de_alta_sin_declarar_ninguna_etiqueta` | Las etiquetas describen, no identifican: un tomo sin ninguna es un producto completo, solo más difícil de encontrar. | 1 | Pasa |
| `test_las_etiquetas_de_la_cabecera_las_heredan_todos_los_items` | Es el motivo por el que viven en la cabecera: veinte tomos de la misma serie comparten franquicia y género igual que comparten editorial. | 1 | Pasa |
| `test_la_cabecera_dibuja_las_etiquetas_agrupadas` | Si el campo no llega a la pantalla, el formulario lo acepta igual pero nadie puede usarlo: es el tipo de hueco que solo se ve mirando el HTML. | 1 | Pasa |
| `test_un_item_puede_sumar_etiquetas_propias` | Un item puede sumar etiquetas propias | 1 | Pasa |
| `test_declarar_la_misma_etiqueta_arriba_y_abajo_no_la_duplica` | Declarar la misma etiqueta arriba y abajo no la duplica | 1 | Pasa |
| `test_una_etiqueta_desactivada_no_se_puede_elegir` | Una etiqueta desactivada no se puede elegir | 1 | Pasa |
| `test_un_item_se_puede_marcar_como_solo_para_adultos` | No es una etiqueta: cambia lo que el sistema hace con el producto, así que es un campo y la tienda va a preguntar por él, no por una cadena. | 1 | Pasa |
| `test_por_defecto_un_producto_no_es_solo_para_adultos` | Por defecto un producto no es solo para adultos | 1 | Pasa |
| `test_el_precio_depende_de_los_tres_campos` | La misma editorial y el mismo tipo, en dos tamaños, valen distinto. | 1 | Pasa |
| `test_con_fecha_de_llegada_el_producto_nace_en_pre_venta` | Con fecha de llegada el producto nace en pre venta | 1 | Pasa |
| `test_sin_fecha_de_llegada_el_producto_nace_activo` | Sin fecha de llegada el producto nace activo | 1 | Pasa |
| `test_el_item_puede_sobrescribir_el_estado_de_la_cabecera` | El item puede sobrescribir el estado de la cabecera | 1 | Pasa |
| `test_un_item_duplicado_se_excluye_y_los_demas_se_crean` | Un duplicado no es un fallo del lote, es una exclusión esperada. | 1 | Pasa |
| `test_el_duplicado_se_detecta_sin_distinguir_mayusculas` | El duplicado se detecta sin distinguir mayusculas | 1 | Pasa |
| `test_el_mismo_tomo_en_otro_formato_no_es_duplicado` | Dos ediciones del mismo tomo son dos productos: distinto precio, distinto stock y las dos pueden estar en la góndola al mismo tiempo. | 1 | Pasa |
| `test_una_editorial_distinta_no_es_duplicado` | Una editorial distinta no es duplicado | 1 | Pasa |
| `test_el_resumen_informa_la_colision_con_enlace_a_la_ficha` | El resumen informa la colision con enlace a la ficha | 1 | Pasa |
| `test_la_confirmacion_genera_una_unica_entrada_de_auditoria` | Una entrada consolidada por lote, no una por ítem. | 1 | Pasa |
| `test_la_auditoria_apunta_al_lote_y_no_a_una_cuenta` | La auditoria apunta al lote y no a una cuenta | 1 | Pasa |
| `test_un_fallo_tecnico_no_deja_productos_a_medio_crear` | RNF-06: la creación del lote es atómica. | 1 | Pasa |
| `test_un_item_sin_stock_declarado_nace_en_cero` | El sistema no inventa unidades que nadie contó. | 1 | Pasa |
| `test_el_stock_declarado_se_respeta` | El stock declarado se respeta | 1 | Pasa |
| `test_sin_portada_el_producto_queda_marcado_como_imagen_pendiente` | Sin portada el producto queda marcado como imagen pendiente | 1 | Pasa |
| `test_un_item_sin_titulo_no_se_registra` | Un item sin titulo no se registra | 1 | Pasa |
| `test_un_lote_sin_ningun_item_no_se_guarda` | Un lote sin ningun item no se guarda | 1 | Pasa |
| `test_un_lote_de_un_solo_item_es_valido` | Un lote de un solo item es valido | 1 | Pasa |
| `test_solo_el_administrador_da_de_alta_lotes` | Solo el administrador da de alta lotes | 2 | Pasa |
| `test_sin_sesion_el_alta_redirige_al_login` | Sin sesion el alta redirige al login | 1 | Pasa |

### `test_alta_no_editorial.py`

CU-CAT-ALT — Registrar Alta de Producto No Editorial.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_alta_crea_el_producto` | El alta crea el producto | 1 | Pasa |
| `test_nace_activo_y_con_su_codigo` | CU-CAT-ALT asigna exclusivamente Activo, y todo producto nace identificado. | 1 | Pasa |
| `test_el_codigo_escrito_a_mano_se_respeta` | CU-CAT-ALT paso 3 lista el "código de producto interno" entre los opcionales. | 1 | Pasa |
| `test_los_opcionales_se_guardan` | Los opcionales se guardan | 1 | Pasa |
| `test_la_marca_es_opcional` | Es el caso que reescribió el modelo: hay merch genérico y no oficial. | 1 | Pasa |
| `test_la_imagen_no_bloquea_el_alta` | CU-CAT-ALT paso 2 la lista entre los obligatorios; se unifica con A5 de `alta_editorial.md`, donde la portada tampoco bloquea. | 1 | Pasa |
| `test_los_obligatorios_bloquean_el_alta` | E1: se resaltan, el formulario permanece abierto y no se registra nada. | 4 | Pasa |
| `test_el_formulario_conserva_lo_ya_escrito` | E1 lo pide explícitamente: no se reinicia vacío. | 1 | Pasa |
| `test_una_categoria_editorial_se_rechaza` | El recorte del desplegable es comodidad; la validación es del servidor. | 1 | Pasa |
| `test_el_formulario_no_ofrece_el_estado` | No hay campo que mandar: el sistema asigna Activo. | 1 | Pasa |
| `test_un_precio_desmesurado_se_rechaza` | Un precio desmesurado se rechaza | 1 | Pasa |
| `test_el_duplicado_no_se_registra_sin_confirmar` | El duplicado no se registra sin confirmar | 1 | Pasa |
| `test_el_duplicado_se_informa_con_enlace_a_la_ficha_existente` | E2 pide el enlace, no solo el aviso: sin él hay que ir a buscarlo a mano. | 1 | Pasa |
| `test_confirmando_el_duplicado_el_alta_procede` | Dos llaveros de Naruto de proveedores distintos son dos productos. | 1 | Pasa |
| `test_los_dos_duplicados_tienen_códigos_distintos` | Es lo que hace posible convivir: la identidad nunca fue el nombre. | 1 | Pasa |
| `test_el_mismo_nombre_en_otra_categoria_no_es_duplicado` | La clave del CU es nombre **+ categoría**: un llavero y una carta con el mismo nombre no chocan. | 1 | Pasa |
| `test_la_confirmacion_no_se_ofrece_cuando_no_hay_choque` | Ofrecerla siempre la volvería un clic automático, que es lo mismo que no tenerla — el mismo motivo por el que la confirmación de cambio de correo no aparece en el alta de proveedor. | 1 | Pasa |
| `test_el_duplicado_ignora_mayusculas_y_espacios` | El duplicado ignora mayusculas y espacios | 1 | Pasa |
| `test_la_consulta_encuentra_el_choque_exacto` | La consulta encuentra el choque exacto | 1 | Pasa |
| `test_la_consulta_avisa_de_parecidos_en_otras_categorias` | Que exista en Merchandising es información útil aunque se lo esté cargando en TCG: puede ser el aviso de que la categoría es la equivocada. | 1 | Pasa |
| `test_la_consulta_no_devuelve_nada_con_un_nombre_muy_corto` | Con una letra, todo el catálogo es un parecido. | 1 | Pasa |
| `test_la_consulta_no_valida_nada` | Se puede esquivar, ignorar o no llegar nunca: el duplicado se informa igual al guardar. | 1 | Pasa |
| `test_el_alta_queda_auditada` | La postcondición pide fecha, hora y datos del producto creado. | 1 | Pasa |
| `test_el_alta_es_exclusiva_del_administrador` | El Cajero consulta el inventario (CU-CAT-INV) pero no da de alta nada. | 2 | Pasa |
| `test_el_inventario_enlaza_el_alta` | El inventario enlaza el alta | 1 | Pasa |
| `test_sin_categorias_activas_la_pantalla_lo_dice` | Sin ninguna, el desplegable aparecería vacío y sin explicar por qué. | 1 | Pasa |

### `test_asistencias_de_carga.py`

Las ayudas que la pantalla de carga pide al servidor mientras se escribe.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_devuelve_el_precio_de_la_combinacion` | Devuelve el precio de la combinacion | 1 | Pasa |
| `test_una_combinacion_sin_precio_devuelve_nulo` | Una combinacion sin precio devuelve nulo | 1 | Pasa |
| `test_cambiar_solo_el_formato_cambia_el_precio` | Es la razón de ser de la consulta: el tamaño es lo que fija el precio. | 1 | Pasa |
| `test_un_parametro_invalido_no_rompe_la_consulta` | Un parametro invalido no rompe la consulta | 4 | Pasa |
| `test_la_consulta_de_precios_no_se_abre_sin_ser_administrador` | La consulta de precios no se abre sin ser administrador | 1 | Pasa |
| `test_crea_la_editorial_y_devuelve_su_identificador` | Crea la editorial y devuelve su identificador | 1 | Pasa |
| `test_el_alta_rapida_normaliza_igual_que_la_pantalla_completa` | Los dos caminos crean lo mismo, así que usan el mismo formulario: si tuvieran reglas distintas, el atajo sería la puerta para meter duplicados. | 1 | Pasa |
| `test_el_alta_rapida_rechaza_una_editorial_repetida` | El alta rapida rechaza una editorial repetida | 1 | Pasa |
| `test_el_alta_rapida_rechaza_un_nombre_vacio` | El alta rapida rechaza un nombre vacio | 1 | Pasa |
| `test_el_alta_rapida_queda_auditada` | El alta rapida queda auditada | 1 | Pasa |
| `test_la_editorial_nueva_se_puede_usar_enseguida` | Sin esto el atajo no serviría de nada: habría que recargar la pantalla y perder el lote a medio escribir. | 1 | Pasa |
| `test_el_alta_rapida_es_solo_del_administrador` | El alta rapida es solo del administrador | 2 | Pasa |
| `test_la_pantalla_recibe_las_banderas_de_cada_tipo` | Qué muestra cada tipo viaja como dato y no escrito en el JavaScript: es la misma bandera —y la misma lista de formatos— que lee el servidor, así los dos lados no pueden discrepar. | 1 | Pasa |
| `test_el_alta_rapida_de_tipo_es_editorial_y_queda_auditada` | A1 de CU-CFG-TPA: desde la carga de un lote el rubro es el de la pantalla. | 1 | Pasa |
| `test_el_alta_rapida_de_formato_lo_declara_para_el_tipo_de_la_carga` | A1 de CU-CFG-FMA: queda declarado para el tipo elegido, salvo que se indique que aplica a todos. | 1 | Pasa |
| `test_el_alta_rapida_de_formato_rechaza_un_repetido` | El alta rapida de formato rechaza un repetido | 1 | Pasa |

### `test_baja_producto.py`

CU-CAT-BAJ — Dar de Baja Producto (Editorial o No Editorial), y la reactivación.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_la_pantalla_muestra_las_cuatro_categorias` | Las cuatro se declaran aunque ninguna se pueda calcular: agregar cada una después es llenar un hueco y no rediseñar la pantalla. | 1 | Pasa |
| `test_lo_que_no_se_puede_calcular_se_dice` | Un cero se leería como "no afecta a nadie". | 1 | Pasa |
| `test_el_informe_trae_el_stock_y_el_estado` | No son categorías del CU. | 1 | Pasa |
| `test_hoy_ninguna_categoria_se_puede_determinar` | Hoy ninguna categoria se puede determinar | 1 | Pasa |
| `test_ver_el_informe_no_da_de_baja` | El GET es el informe, no la acción. | 1 | Pasa |
| `test_la_baja_descataloga_el_producto` | La baja descataloga el producto | 1 | Pasa |
| `test_la_baja_no_borra_nada` | La postcondición pide conservarlo en el inventario y en el historial. | 1 | Pasa |
| `test_tambien_se_da_de_baja_un_articulo_no_editorial` | Tambien se da de baja un articulo no editorial | 1 | Pasa |
| `test_un_producto_en_pre_venta_se_puede_dar_de_baja` | Un producto en pre venta se puede dar de baja | 1 | Pasa |
| `test_la_baja_queda_registrada` | La baja queda registrada | 1 | Pasa |
| `test_una_segunda_baja_no_registra_de_nuevo` | El clásico doble envío. | 1 | Pasa |
| `test_un_titulo_cancelado_por_editorial_no_admite_la_baja` | Es un estado terminal: un tomo cancelado no llega nunca y no se reactiva. | 1 | Pasa |
| `test_la_pantalla_lo_dice_antes_de_ofrecer_el_boton` | La pantalla lo dice antes de ofrecer el boton | 1 | Pasa |
| `test_la_reactivacion_devuelve_el_producto_al_catalogo` | La reactivacion devuelve el producto al catalogo | 1 | Pasa |
| `test_vuelve_con_la_misma_identidad` | Volver a cargarlo no sería equivalente: el código es único e inmutable, así que el producto reingresaría con otra identidad y sin su historial. | 1 | Pasa |
| `test_vuelve_a_activo_y_no_al_estado_anterior` | Un producto que estaba en Pre-venta cuando se lo dio de baja lleva meses fuera del catálogo, y su fecha de llegada ya no describe nada. | 1 | Pasa |
| `test_la_reactivacion_queda_registrada` | La reactivacion queda registrada | 1 | Pasa |
| `test_reactivar_algo_que_ya_esta_activo_no_hace_nada` | Reactivar algo que ya esta activo no hace nada | 1 | Pasa |
| `test_el_ciclo_completo_conserva_el_historial` | Es lo que la baja lógica se propuso conservar: las dos entradas apuntan al mismo producto y la ficha las muestra juntas. | 1 | Pasa |
| `test_la_ficha_ofrece_editar_y_dar_de_baja` | La ficha ofrece editar y dar de baja | 1 | Pasa |
| `test_la_ficha_de_un_descatalogado_ofrece_reactivar_y_no_dar_de_baja` | La ficha de un descatalogado ofrece reactivar y no dar de baja | 1 | Pasa |
| `test_la_ficha_del_cajero_no_ofrece_ninguna_accion` | CU-CAT-INV paso 6 se la reserva al Administrador. | 1 | Pasa |
| `test_el_cajero_no_da_de_baja_ni_reactiva` | El cajero no da de baja ni reactiva | 2 | Pasa |
| `test_sin_sesion_redirige_al_login` | Sin sesion redirige al login | 2 | Pasa |

### `test_borradores.py`

La generación de borradores desde una extracción (CU-ALT-NOV pasos 5, 6, 7 y 9).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_un_producto_anunciado_se_convierte_en_borrador` | Un producto anunciado se convierte en borrador | 1 | Pasa |
| `test_el_borrador_hereda_la_editorial_y_el_rubro_del_proveedor` | El correo no los trae y el modelo no los inventa: los aporta la ficha del proveedor (A7). | 1 | Pasa |
| `test_el_stock_inicial_sale_de_la_configuracion` | Es el único stock del sistema que nace con un número que nadie contó, y por eso el de las altas manuales es cero y este no (A3). | 1 | Pasa |
| `test_el_borrador_guarda_de_que_correo_y_proveedor_salio` | El borrador guarda de que correo y proveedor salio | 1 | Pasa |
| `test_un_producto_que_ya_esta_en_el_catalogo_se_omite` | Un producto que ya esta en el catalogo se omite | 1 | Pasa |
| `test_el_duplicado_se_detecta_por_isbn_aunque_el_titulo_este_escrito_distinto` | Es justamente lo que la tupla no atrapa: el mismo tomo anunciado como "Berserk edición deluxe vol. | 1 | Pasa |
| `test_el_duplicado_se_detecta_por_la_tupla_cuando_no_hay_isbn` | El duplicado se detecta por la tupla cuando no hay isbn | 1 | Pasa |
| `test_un_duplicado_no_frena_a_los_demas_productos_del_correo` | Una exclusión esperada no es un fallo transaccional: es la misma regla con la que un duplicado no aborta el alta en lote de CU-ALT-NAC. | 1 | Pasa |
| `test_dos_filas_con_el_mismo_isbn_generan_un_solo_borrador` | Son el mismo tomo aunque les hayan escrito el título distinto. | 1 | Pasa |
| `test_se_omite_el_segundo_repetido_y_no_los_dos` | Marcar los dos obligaría a adivinar cuál había que conservar. | 1 | Pasa |
| `test_dos_filas_sin_isbn_y_con_la_misma_tupla_tambien_se_detectan` | Dos filas sin isbn y con la misma tupla tambien se detectan | 1 | Pasa |
| `test_dos_tomos_distintos_de_la_misma_serie_no_son_repetidos` | Comparar solo el título rechazaría el tomo 6 porque ya está el 5. | 1 | Pasa |
| `test_un_producto_sin_titulo_no_llega_a_la_cola` | Un borrador sin título solo se podría rechazar: no hay con qué buscarlo ni con qué mostrarlo. | 1 | Pasa |
| `test_una_fecha_futura_deja_el_borrador_en_pre_venta` | Una fecha futura deja el borrador en pre venta | 1 | Pasa |
| `test_sin_fecha_el_borrador_nace_activo` | Sin fecha el borrador nace activo | 1 | Pasa |
| `test_una_fecha_ya_pasada_no_se_conserva` | Si el material ya llegó, el producto va Activo y sin fecha (A10). | 1 | Pasa |
| `test_la_fecha_propia_de_una_fila_pisa_al_periodo_del_correo` | La fecha propia de una fila pisa al periodo del correo | 1 | Pasa |
| `test_una_pre_venta_siempre_tiene_fecha` | A10: sin fecha no se puede vigilar, y el producto quedaría en pre-venta para siempre, invisible para el ciclo que debería sacarlo de ahí. | 1 | Pasa |
| `test_el_formato_anunciado_se_resuelve_contra_el_catalogo` | El formato anunciado se resuelve contra el catalogo | 1 | Pasa |
| `test_un_formato_que_no_existe_se_descarta_con_su_reparo` | Un formato que no existe se descarta con su reparo | 1 | Pasa |
| `test_un_formato_que_no_se_ofrece_para_ese_tipo_se_descarta` | A20: un formato enviado a mano que no aplique se rechaza. | 1 | Pasa |
| `test_en_un_tipo_que_no_usa_formato_no_se_busca_ninguno` | En un artbook el tamaño no fija el precio, así que no hay nada que resolver y tampoco nada que reparar. | 1 | Pasa |
| `test_un_producto_sin_precio_genera_un_borrador_incompleto` | CU-ALT-NOV: los que el modelo identificó pero no pudo completar generan borradores incompletos, y van a la **misma** cola que los demás. | 1 | Pasa |
| `test_el_fallo_parcial_deja_completos_e_incompletos_en_la_misma_cola` | El fallo parcial deja completos e incompletos en la misma cola | 1 | Pasa |
| `test_un_proveedor_sin_editorial_deja_los_borradores_bloqueados` | Una distribuidora trae varias editoriales y el correo no dice cuál: esos borradores sí hay que completarlos a mano, y el estado lo dice. | 1 | Pasa |
| `test_la_confianza_se_guarda_campo_por_campo` | CU-ALT-REV depende de esa granularidad para decidir qué es confirmable en lote: un único nivel global no alcanzaría. | 1 | Pasa |
| `test_una_confianza_baja_nace_sin_revisar` | Es la acción afirmativa que CU-ALT-REV paso 3 exige antes de confirmar. | 1 | Pasa |
| `test_una_confianza_alta_no_exige_revision` | Una confianza alta no exige revision | 1 | Pasa |
| `test_un_nivel_inventado_se_guarda_como_bajo` | Al alza sería peor: un valor raro leído como "alta" haría que un dato dudoso se confirme en lote sin que nadie lo mire. | 1 | Pasa |
| `test_los_reparos_del_producto_viajan_al_borrador` | Los reparos del producto viajan al borrador | 1 | Pasa |
| `test_un_reparo_del_correo_entero_se_copia_a_cada_borrador` | La cola de CU-ALT-REV se mira de a un borrador por vez: un reparo que solo viviera en el correo no lo vería nadie desde ahí. | 1 | Pasa |
| `test_regenerar_reemplaza_los_borradores_abiertos_en_vez_de_duplicarlos` | Regenerar reemplaza los borradores abiertos en vez de duplicarlos | 1 | Pasa |
| `test_regenerar_conserva_los_ya_resueltos` | Son historia: volver a proponerlos sería reabrir una decisión tomada. | 1 | Pasa |
| `test_la_generacion_deja_una_sola_entrada_de_auditoria` | Consolidada por correo, no una por borrador: lo que se quiere reconstruir después es qué produjo este correo, y treinta filas lo esconderían. | 1 | Pasa |
| `test_la_auditoria_apunta_al_correo_y_dice_con_que_prompt_se_extrajo` | La auditoria apunta al correo y dice con que prompt se extrajo | 1 | Pasa |
| `test_la_auditoria_registra_al_administrador_cuando_lo_hay` | La auditoria registra al administrador cuando lo hay | 1 | Pasa |
| `test_la_fecha_heredada_del_periodo_no_lleva_confianza` | Salió corriendo el pipeline contra el modelo de verdad, y es grave. | 1 | Pasa |
| `test_la_fecha_propia_de_una_fila_si_lleva_confianza` | Ahí sí hay un juicio del modelo que registrar: leyó una celda y dudó. | 1 | Pasa |
| `test_sin_ninguna_fecha_tampoco_se_guarda_confianza_de_fecha` | Un borrador Activo sin fecha no tiene nada que revisar sobre ella: la fecha ni siquiera es bloqueante ahí. | 1 | Pasa |

### `test_casos_borde.py`

Acto 2 · Casos borde: entradas válidas pero extremas, y entradas inválidas (plan 00).

**Casos de prueba que ejecuta:** CP-01, CP-06, CP-11.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_D2_01_los_textos_no_latinos_se_guardan_tal_cual` | D2 01 los textos no latinos se guardan tal cual | 4 | Pasa |
| `test_D2_01_el_maximo_exacto_entra_y_uno_mas_se_rechaza` | D2 01 el maximo exacto entra y uno mas se rechaza | 1 | Pasa |
| `test_D2_01_solo_espacios_se_rechaza` | D2 01 solo espacios se rechaza | 1 | Pasa |
| `test_D2_01_mayusculas_y_espacios_sobrantes_son_el_mismo_nombre` | D2 01 mayusculas y espacios sobrantes son el mismo nombre | 1 | Pasa |
| `test_D2_02_isbn_valido_con_y_sin_guiones` | D2 02 isbn valido con y sin guiones | 5 | Pasa |
| `test_D2_02_isbn_con_digito_incorrecto_se_rechaza_con_motivo` | D2 02 isbn con digito incorrecto se rechaza con motivo | 3 | Pasa |
| `test_D2_02_codigo_interno_repetido_se_bloquea` | D2 02 codigo interno repetido se bloquea | 1 | Pasa |
| `test_D2_02_codigo_de_barras_repetido_se_bloquea` | D2 02 codigo de barras repetido se bloquea | 1 | Pasa |
| `test_D2_03_precios_imposibles_se_rechazan_sin_registrar` | D2 03 precios imposibles se rechazan sin registrar | 7 | Pasa |
| `test_D2_03_el_importe_maximo_exacto_entra_y_un_centavo_mas_se_rechaza` | D2 03 el importe maximo exacto entra y un centavo mas se rechaza | 1 | Pasa |
| `test_D2_03_el_cre_conserva_sus_decimales_hasta_el_precio_final` | Redondear el CRE antes de aplicarlo cambia el precio: el cálculo no lo hace. | 1 | Pasa |
| `test_D2_04_la_oferta_descuenta_hasta_las_23_59_y_no_a_las_00_00` | D2 04 la oferta descuenta hasta las 23 59 y no a las 00 00 | 1 | Pasa |

### `test_concurrencia_catalogos.py`

Doble clic en el alta de un catálogo: dos envíos del mismo nombre a la vez.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO137_y_CO141_doble_envio_del_alta_deja_uno_y_avisa_sin_error` | CO137 y CO141 doble envio del alta deja uno y avisa sin error | 2 | Pasa |

### `test_concurrencia_ofertas.py`

I-20 bajo concurrencia real: dos Administradores registran ofertas solapadas a la vez.

**Casos de prueba que ejecuta:** CP-05.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO054_dos_ofertas_solapadas_registradas_a_la_vez_dejan_una` | CO054 dos ofertas solapadas registradas a la vez dejan una | 1 | Pasa |

### `test_contratos_02_catalogo.py`

Pruebas de contrato del módulo 02 · Catálogo.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO156_abandonar_la_confirmacion_no_cambia_el_producto` | Postcondición: «ninguna. | 2 | Pasa |
| `test_CO038_registrar_grupo_lo_crea_activo_y_auditado` | CO038 registrar grupo lo crea activo y auditado | 1 | Pasa |
| `test_CO038_E1_la_colision_enlaza_el_grupo_existente` | CO038 E1 la colision enlaza el grupo existente | 1 | Pasa |
| `test_CO039_reactivar_el_grupo_no_reactiva_sus_etiquetas` | E9: el sistema no distingue las que bajó el grupo de las que ya estaban. | 1 | Pasa |
| `test_CO040_solicitar_baja_de_grupo_informa_etiquetas_y_productos` | CO040 solicitar baja de grupo informa etiquetas y productos | 1 | Pasa |
| `test_CO041_la_baja_del_grupo_alcanza_a_sus_etiquetas_y_conserva_las_asignaciones` | CO041 la baja del grupo alcanza a sus etiquetas y conserva las asignaciones | 1 | Pasa |
| `test_CO156_abandonar_la_baja_de_grupo_o_etiqueta_no_cambia_nada` | CU-CAT-GRB A1 y CU-CAT-ETB A1. | 2 | Pasa |
| `test_CO164_consultar_grupos_lista_activos_e_inactivos_con_sus_etiquetas` | CO164 consultar grupos lista activos e inactivos con sus etiquetas | 1 | Pasa |
| `test_CO042_registrar_etiqueta_la_crea_activa_en_su_grupo` | CO042 registrar etiqueta la crea activa en su grupo | 1 | Pasa |
| `test_CO042_E1_la_colision_es_dentro_del_grupo_y_enlaza_la_existente` | CO042 E1 la colision es dentro del grupo y enlaza la existente | 1 | Pasa |
| `test_CO042_no_se_crea_en_un_grupo_dado_de_baja` | Precondición: el grupo existe en estado activo. | 1 | Pasa |
| `test_CO043_mover_la_etiqueta_conserva_sus_asignaciones_y_su_estado` | CO043 mover la etiqueta conserva sus asignaciones y su estado | 1 | Pasa |
| `test_CO043_E3_no_se_reactiva_dentro_de_un_grupo_dado_de_baja` | CO043 E3 no se reactiva dentro de un grupo dado de baja | 1 | Pasa |
| `test_CO043_reactivar_moviendola_a_un_grupo_activo` | CO043 reactivar moviendola a un grupo activo | 1 | Pasa |
| `test_CO044_solicitar_baja_de_etiqueta_informa_sus_productos` | CO044 solicitar baja de etiqueta informa sus productos | 1 | Pasa |
| `test_CO045_confirmar_baja_de_etiqueta_la_retira_y_conserva_sus_asignaciones` | CO045 confirmar baja de etiqueta la retira y conserva sus asignaciones | 1 | Pasa |
| `test_CO045_la_edicion_del_producto_la_presenta_marcada_y_no_la_pierde` | «En la edición de un producto que la tiene asignada se presenta marcada y puede quitarse (CO-030).» Antes, el desplegable sólo ofrecía las activas y guardar cualquier otro cambio la perdía sin que nadie lo decidiera. | 1 | Pasa |
| `test_CO037_exportar_inventario_trae_las_filas_del_listado_filtrado` | CO037 exportar inventario trae las filas del listado filtrado | 1 | Pasa |
| `test_CO037_el_cajero_no_exporta_por_la_direccion_real` | La única acción de CU-CAT-INV restringida por rol, validada en el servidor. | 1 | Pasa |
| `test_CO037_el_cajero_no_ve_la_opcion_de_exportar` | CO037 el cajero no ve la opcion de exportar | 1 | Pasa |
| `test_CO162_consultar_inventario_filtra_por_editorial` | CO162 consultar inventario filtra por editorial | 1 | Pasa |
| `test_CO162_el_filtro_ofrece_las_etiquetas_inactivas_marcadas` | Para localizar los productos que las conservan (comentario de la ficha). | 1 | Pasa |
| `test_CO163_la_ficha_dibuja_para_el_cajero_solo_sus_campos` | «El Cajero ve nombre, imagen, tipo, estado, stock y precio. | 1 | Pasa |
| `test_CO163_los_indicadores_que_no_puede_calcular_se_declaran_no_disponibles` | CO163 los indicadores que no puede calcular se declaran no disponibles | 1 | Pasa |
| `test_CO165_consultar_etiquetas_de_grupo_paginadas_con_busqueda_y_estado` | CO165 consultar etiquetas de grupo paginadas con busqueda y estado | 1 | Pasa |

### `test_contratos_03_ofertas.py`

Pruebas de contrato de las ofertas (módulo 03, plan 03 segunda parte).

**Casos de prueba que ejecuta:** CP-11.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_porcentaje_se_calcula_con_decimal_exacto_y_redondea_al_peso` | El porcentaje se calcula con decimal exacto y redondea al peso | 1 | Pasa |
| `test_el_dia_de_vencimiento_todavia_descuenta` | El dia de vencimiento todavia descuenta | 1 | Pasa |
| `test_la_oferta_individual_manda_sobre_la_de_su_tipo` | La oferta individual manda sobre la de su tipo | 1 | Pasa |
| `test_una_oferta_dada_de_baja_no_descuenta` | Una oferta dada de baja no descuenta | 1 | Pasa |
| `test_CO054_registrar_con_inicio_hoy_la_deja_activa_y_aplicada_en_los_dos_canales` | CO054 registrar con inicio hoy la deja activa y aplicada en los dos canales | 1 | Pasa |
| `test_CO054_con_inicio_futuro_queda_programada_y_no_descuenta_todavia` | CO054 con inicio futuro queda programada y no descuenta todavia | 1 | Pasa |
| `test_CO054_por_tipo_se_asocia_al_tipo_y_alcanza_a_sus_productos` | CO054 por tipo se asocia al tipo y alcanza a sus productos | 1 | Pasa |
| `test_CO054_no_toca_el_precio_guardado_del_producto` | CO054 no toca el precio guardado del producto | 1 | Pasa |
| `test_CO054_E1_el_vencimiento_tiene_que_ser_futuro` | CO054 E1 el vencimiento tiene que ser futuro | 2 | Pasa |
| `test_CO054_el_inicio_no_puede_pasar_al_vencimiento` | CO054 el inicio no puede pasar al vencimiento | 1 | Pasa |
| `test_CO054_E2_rechaza_el_solapamiento_con_el_nombre_y_el_periodo` | CO054 E2 rechaza el solapamiento con el nombre y el periodo | 1 | Pasa |
| `test_CO054_E2_no_cuentan_las_dadas_de_baja_ni_las_de_otro_alcance` | CO054 E2 no cuentan las dadas de baja ni las de otro alcance | 1 | Pasa |
| `test_CO054_rechaza_un_porcentaje_de_cien` | CO054 rechaza un porcentaje de cien | 1 | Pasa |
| `test_CO054_E3_un_monto_que_supera_el_precio_pide_confirmacion_y_no_registra` | CO054 E3 un monto que supera el precio pide confirmacion y no registra | 1 | Pasa |
| `test_CO054_A1_un_tipo_sin_productos_registra_con_aviso` | CO054 A1 un tipo sin productos registra con aviso | 1 | Pasa |
| `test_CO055_confirmar_registra_y_deja_en_un_peso_a_los_que_no_alcanzan` | CO055 confirmar registra y deja en un peso a los que no alcanzan | 1 | Pasa |
| `test_CO168_abre_con_los_campos_actuales` | CO168 abre con los campos actuales | 1 | Pasa |
| `test_CO168_E2_vencida_o_dada_de_baja_no_abre_ni_guarda` | CO168 E2 vencida o dada de baja no abre ni guarda | 2 | Pasa |
| `test_CO056_cambiar_el_valor_de_una_activa_actualiza_precio_carrito_y_log` | CO056 cambiar el valor de una activa actualiza precio carrito y log | 1 | Pasa |
| `test_CO056_A1_reducir_el_alcance_restaura_a_los_que_quedan_afuera` | CO056 A1 reducir el alcance restaura a los que quedan afuera | 1 | Pasa |
| `test_CO056_E1_un_solapamiento_no_actualiza_ningun_campo` | CO056 E1 un solapamiento no actualiza ningun campo | 1 | Pasa |
| `test_CO056_mover_el_inicio_al_futuro_la_vuelve_programada` | CO056 mover el inicio al futuro la vuelve programada | 1 | Pasa |
| `test_CO056_sin_cambios_no_audita` | CO056 sin cambios no audita | 1 | Pasa |
| `test_CO057_el_informe_cuenta_productos_con_descuento_y_carritos` | CO057 el informe cuenta productos con descuento y carritos | 1 | Pasa |
| `test_CO057_E1_una_vencida_informa_que_ya_expiro_y_no_registra_nada` | CO057 E1 una vencida informa que ya expiro y no registra nada | 1 | Pasa |
| `test_CO156_cancelar_la_baja_no_cambia_nada` | CO156 cancelar la baja no cambia nada | 1 | Pasa |
| `test_CO058_confirmar_la_deja_dada_de_baja_y_restaura_precio_y_carritos` | CO058 confirmar la deja dada de baja y restaura precio y carritos | 1 | Pasa |
| `test_CO058_una_programada_tambien_se_da_de_baja` | CO058 una programada tambien se da de baja | 1 | Pasa |
| `test_CO058_una_dada_de_baja_no_se_reactiva_ni_se_audita_dos_veces` | CO058 una dada de baja no se reactiva ni se audita dos veces | 1 | Pasa |
| `test_CO059_activa_las_programadas_y_vence_las_activas_con_su_entrada` | CO059 activa las programadas y vence las activas con su entrada | 1 | Pasa |
| `test_CO059_correrlo_dos_veces_no_duplica_nada` | CO059 correrlo dos veces no duplica nada | 1 | Pasa |
| `test_CO169_lista_de_la_mas_reciente_a_la_mas_vieja_con_su_estado_por_fecha` | CO169 lista de la mas reciente a la mas vieja con su estado por fecha | 1 | Pasa |
| `test_CO169_filtra_por_estado_texto_y_fechas` | CO169 filtra por estado texto y fechas | 7 | Pasa |
| `test_CO169_E1_sin_resultados_ofrece_limpiar_y_E2_sin_ofertas_ofrece_la_alta` | CO169 E1 sin resultados ofrece limpiar y E2 sin ofertas ofrece la alta | 1 | Pasa |
| `test_CO170_la_ficha_muestra_los_dos_precios_y_las_acciones_del_estado` | CO170 la ficha muestra los dos precios y las acciones del estado | 1 | Pasa |
| `test_CO170_una_vencida_es_de_solo_lectura` | CO170 una vencida es de solo lectura | 1 | Pasa |
| `test_la_tienda_tacha_el_precio_original` | La tienda tacha el precio original | 1 | Pasa |
| `test_el_filtro_de_precio_mide_el_precio_con_oferta` | El filtro de precio mide el precio con oferta | 1 | Pasa |
| `test_el_carrito_muestra_el_precio_con_oferta` | El carrito muestra el precio con oferta | 1 | Pasa |
| `test_solo_el_administrador_gestiona_ofertas` | Solo el administrador gestiona ofertas | 2 | Pasa |
| `test_sin_sesion_redirige_al_inicio_de_sesion` | Sin sesion redirige al inicio de sesion | 1 | Pasa |
| `test_el_producto_debe_ser_del_catalogo_activo` | El producto debe ser del catalogo activo | 1 | Pasa |

### `test_contratos_03_pricing.py`

Pruebas de contrato del módulo 03 · Pricing.

**Casos de prueba que ejecuta:** CP-02, CP-03.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO166_consultar_tabla_con_filtros_combinables` | CO166 consultar tabla con filtros combinables | 1 | Pasa |
| `test_CO049_registrar_combinacion_crea_la_fila_y_no_toca_productos` | CO049 registrar combinacion crea la fila y no toca productos | 1 | Pasa |
| `test_CO049_E1_la_combinacion_existente_se_enlaza_y_no_se_registra` | CO049 E1 la combinacion existente se enlaza y no se registra | 1 | Pasa |
| `test_CO049_E2_una_combinacion_imposible_se_rechaza` | CO049 E2 una combinacion imposible se rechaza | 4 | Pasa |
| `test_CO049_E3_un_precio_no_mayor_que_cero_se_rechaza` | CO049 E3 un precio no mayor que cero se rechaza | 1 | Pasa |
| `test_CO047_solicitar_modificacion_informa_el_alcance_sin_cambiar_nada` | CO047 solicitar modificacion informa el alcance sin cambiar nada | 1 | Pasa |
| `test_CO047_sin_vinculados_informa_que_solo_afecta_a_la_tabla` | CO047 sin vinculados informa que solo afecta a la tabla | 1 | Pasa |
| `test_CO047_E1_un_precio_no_mayor_que_cero_se_rechaza` | CO047 E1 un precio no mayor que cero se rechaza | 1 | Pasa |
| `test_CO048_confirmar_propaga_a_los_vinculados_y_respeta_las_excepciones` | CO048 confirmar propaga a los vinculados y respeta las excepciones | 1 | Pasa |
| `test_CO048_el_informe_cuenta_lo_mismo_que_se_propaga` | CO048 el informe cuenta lo mismo que se propaga | 1 | Pasa |
| `test_CO048_no_toca_el_precio_base` | Postcondición negativa: sólo cambia `Producto.precio`. | 1 | Pasa |
| `test_CO156_abandonar_la_modificacion_no_cambia_el_precio` | CU-PVP-TBM A1: ver el informe y volver. | 1 | Pasa |
| `test_CO050_solicitar_baja_cuenta_todos_los_vinculados` | CO050 solicitar baja cuenta todos los vinculados | 1 | Pasa |
| `test_CO051_confirmar_baja_desvincula_y_conserva_precio_y_marca` | CO051 confirmar baja desvincula y conserva precio y marca | 1 | Pasa |
| `test_CO156_abandonar_la_baja_de_una_combinacion_no_cambia_nada` | CU-PVP-TBB A1. | 1 | Pasa |
| `test_CO031_un_nacional_a_mano_vuelve_a_la_tabla_y_se_vincula` | CO031 un nacional a mano vuelve a la tabla y se vincula | 1 | Pasa |
| `test_CO031_un_nacional_que_perdio_su_fila_se_vuelve_a_vincular` | El caso que `CO-051` promete: «pueden vincularse otra vez». | 1 | Pasa |
| `test_CO031_un_importado_a_mano_vuelve_al_margen_vigente_desde_su_base` | CO031 un importado a mano vuelve al margen vigente desde su base | 1 | Pasa |
| `test_CO031_no_aplica_a_un_producto_que_ya_sigue_su_fuente` | Precondición: precio a mano, o nacional sin vínculo con fila. | 1 | Pasa |
| `test_CO167_consultar_margen_lo_expresa_como_porcentaje` | CO167 consultar margen lo expresa como porcentaje | 1 | Pasa |
| `test_CO052_simular_informa_el_impacto_sin_cambiar_nada` | CO052 simular informa el impacto sin cambiar nada | 1 | Pasa |
| `test_CO052_sin_importados_la_precondicion_no_se_cumple` | C-11: mandan los contratos. | 1 | Pasa |
| `test_CO052_A1_todos_a_mano_avisa_que_no_afecta_a_ninguno` | CO052 A1 todos a mano avisa que no afecta a ninguno | 1 | Pasa |
| `test_CO053_confirmar_recalcula_desde_el_precio_base_con_decimal_exacto` | CO053 confirmar recalcula desde el precio base con decimal exacto | 1 | Pasa |
| `test_CO053_no_toca_a_los_nacionales` | CO053 no toca a los nacionales | 1 | Pasa |
| `test_CO156_abandonar_el_cambio_de_margen_lo_deja_como_estaba` | CU-PVP-MAR A2: simular y no confirmar. | 1 | Pasa |
| `test_el_cajero_no_opera_los_precios` | El cajero no opera los precios | 6 | Pasa |

### `test_contratos_17_catalogos.py`

Pruebas de contrato del módulo 17 · catálogos de clasificación.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO137_registrar_editorial_la_crea_activa_normalizada_y_auditada` | CO137 registrar editorial la crea activa normalizada y auditada | 1 | Pasa |
| `test_CO137_E1_la_colision_enlaza_la_existente_con_su_estado_y_no_registra` | CO137 E1 la colision enlaza la existente con su estado y no registra | 1 | Pasa |
| `test_CO137_E2_un_nombre_vacio_tras_normalizar_se_rechaza` | CO137 E2 un nombre vacio tras normalizar se rechaza | 1 | Pasa |
| `test_CO138_editar_editorial_corrige_el_nombre_y_conserva_sus_asociaciones` | CO138 editar editorial corrige el nombre y conserva sus asociaciones | 1 | Pasa |
| `test_CO138_reactivar_la_vuelve_a_ofrecer_en_los_formularios` | CO138 reactivar la vuelve a ofrecer en los formularios | 1 | Pasa |
| `test_CO138_la_modificacion_no_da_de_baja` | Postcondición negativa: la operación no pasa de activa a inactiva. | 1 | Pasa |
| `test_CO138_E1_la_colision_no_registra_el_cambio` | CO138 E1 la colision no registra el cambio | 1 | Pasa |
| `test_CO139_solicitar_baja_de_editorial_informa_las_tres_cantidades_sin_cambiar_nada` | CO139 solicitar baja de editorial informa las tres cantidades sin cambiar nada | 1 | Pasa |
| `test_CO139_la_precondicion_exige_que_este_activa` | CO139 la precondicion exige que este activa | 1 | Pasa |
| `test_CO140_confirmar_baja_de_editorial_la_desactiva_y_conserva_todo` | CO140 confirmar baja de editorial la desactiva y conserva todo | 1 | Pasa |
| `test_CO140_un_borrador_que_la_hereda_registra_un_reparo_y_no_se_confirma` | CO140 un borrador que la hereda registra un reparo y no se confirma | 1 | Pasa |
| `test_CO140_reactivarla_destraba_el_borrador` | CO140 reactivarla destraba el borrador | 1 | Pasa |
| `test_CO140_confirmar_dos_veces_no_deja_dos_bajas` | La segunda confirmación relee el estado bajo bloqueo y se retira. | 1 | Pasa |
| `test_CO156_abandonar_la_baja_de_un_catalogo_no_cambia_nada` | CU-CFG-EDB A1, TPB A1, FMB A1: abrir la confirmación y volver. | 3 | Pasa |
| `test_CO211_consultar_editoriales_lista_activas_e_inactivas_con_sus_productos` | CO211 consultar editoriales lista activas e inactivas con sus productos | 1 | Pasa |
| `test_CO141_registrar_tipo_con_su_rubro_y_su_clasificacion` | CO141 registrar tipo con su rubro y su clasificacion | 1 | Pasa |
| `test_CO142_E2_no_cambia_el_rubro_de_un_tipo_con_productos` | CO142 E2 no cambia el rubro de un tipo con productos | 1 | Pasa |
| `test_CO142_E4_no_deja_de_clasificarse_por_formato_con_combinaciones_en_uso` | CO142 E4 no deja de clasificarse por formato con combinaciones en uso | 1 | Pasa |
| `test_CO142_dejar_de_clasificarse_por_formato_rompe_sus_combinaciones` | CO142 dejar de clasificarse por formato rompe sus combinaciones | 1 | Pasa |
| `test_CO142_reactivar_el_tipo_lo_vuelve_a_ofrecer` | CO142 reactivar el tipo lo vuelve a ofrecer | 1 | Pasa |
| `test_CO146_declarar_formatos_de_tipo_forma_y_rompe_combinaciones` | CO146 declarar formatos de tipo forma y rompe combinaciones | 1 | Pasa |
| `test_CO146_no_ofrece_ni_toca_los_formatos_que_aplican_a_todos` | T3: un formato universal no se declara tipo por tipo. | 1 | Pasa |
| `test_CO146_E5_no_se_quita_un_formato_en_uso` | CO146 E5 no se quita un formato en uso | 1 | Pasa |
| `test_CO212_consultar_tipos_con_rubro_formatos_y_productos` | CO212 consultar tipos con rubro formatos y productos | 1 | Pasa |
| `test_CO220_solicitar_baja_de_tipo_cuenta_las_ofertas_vivas_del_tipo` | Cuentan las Programadas y las Activas según sus fechas; no las vencidas, las dadas de baja ni las de un producto suelto (R-17-003). | 1 | Pasa |
| `test_CO221_confirmar_baja_de_tipo_conserva_sus_vinculos` | CO221 confirmar baja de tipo conserva sus vinculos | 1 | Pasa |
| `test_CO221_un_borrador_que_hereda_el_tipo_no_se_confirma` | CO221 un borrador que hereda el tipo no se confirma | 1 | Pasa |
| `test_CO144_registrar_formato_con_tipos_declarados` | CO144 registrar formato con tipos declarados | 1 | Pasa |
| `test_CO144_un_formato_que_aplica_a_todos_no_declara_tipos` | CO144 un formato que aplica a todos no declara tipos | 1 | Pasa |
| `test_CO145_pasar_a_aplica_a_todos_rompe_los_tipos_declarados` | CO145 pasar a aplica a todos rompe los tipos declarados | 1 | Pasa |
| `test_CO145_E3_no_deja_sin_declarar_un_tipo_en_uso` | CO145 E3 no deja sin declarar un tipo en uso | 1 | Pasa |
| `test_CO145_reactivar_el_formato_lo_vuelve_a_ofrecer` | CO145 reactivar el formato lo vuelve a ofrecer | 1 | Pasa |
| `test_CO147_solicitar_baja_de_formato_informa_las_tres_cantidades` | CO147 solicitar baja de formato informa las tres cantidades | 1 | Pasa |
| `test_CO148_confirmar_baja_de_formato_conserva_productos_filas_y_tipos` | CO148 confirmar baja de formato conserva productos filas y tipos | 1 | Pasa |
| `test_CO148_un_borrador_con_el_formato_dado_de_baja_no_se_confirma` | CO148 un borrador con el formato dado de baja no se confirma | 1 | Pasa |
| `test_CO213_consultar_formatos_con_alcance_y_productos` | CO213 consultar formatos con alcance y productos | 1 | Pasa |
| `test_el_cajero_no_opera_los_catalogos` | El cajero no opera los catalogos | 8 | Pasa |

### `test_edicion_producto.py`

CU-CAT-EDI — Editar Producto (Editorial o No Editorial).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_se_edita_un_tomo` | Se edita un tomo | 1 | Pasa |
| `test_se_edita_un_articulo_no_editorial` | Se edita un articulo no editorial | 1 | Pasa |
| `test_la_pantalla_de_cada_rubro_ofrece_sus_campos` | Una vista y dos formularios: el tomo pide volumen y el artículo, marca. | 1 | Pasa |
| `test_guardar_sin_cambios_no_registra_nada` | No es un error, pero tampoco una modificación: el historial no miente. | 1 | Pasa |
| `test_el_codigo_no_se_puede_cambiar` | Es la identidad del producto y el modelo la declara inmutable. | 1 | Pasa |
| `test_el_estado_no_se_puede_cambiar_desde_la_edicion` | Descatalogar tiene que pasar por el informe de impacto de CU-CAT-BAJ. | 1 | Pasa |
| `test_editar_sin_tocar_la_identidad_no_es_un_duplicado` | El caso que rompería una búsqueda que no se excluya a sí misma: sin esto ningún producto se podría guardar dos veces. | 1 | Pasa |
| `test_el_choque_con_otro_tomo_se_informa` | El choque con otro tomo se informa | 1 | Pasa |
| `test_el_choque_editorial_no_se_puede_confirmar` | Las dos políticas de duplicado son opuestas, y es correcto. | 1 | Pasa |
| `test_el_choque_no_editorial_si_se_puede_confirmar` | El otro rubro no tiene restricción de base y su duplicado es una advertencia: dos llaveros de Naruto pueden ser dos productos (corrección 21). | 1 | Pasa |
| `test_el_isbn_repetido_se_detecta` | El ISBN identifica una edición: dos filas con el mismo son la misma. | 1 | Pasa |
| `test_un_isbn_con_el_digito_mal_se_rechaza` | Se verifica la aritmética, no una consulta externa. | 1 | Pasa |
| `test_el_articulo_no_editorial_tambien_se_excluye_a_si_mismo` | El articulo no editorial tambien se excluye a si mismo | 1 | Pasa |
| `test_cambiar_el_precio_exige_confirmacion` | El cartel avisa; el que exige es el servidor. | 1 | Pasa |
| `test_confirmado_el_precio_cambia_y_queda_marcado` | Confirmado el precio cambia y queda marcado | 1 | Pasa |
| `test_sin_tocar_el_precio_no_se_pide_nada` | Sin tocar el precio no se pide nada | 1 | Pasa |
| `test_un_precio_ya_manual_no_vuelve_a_pedir_confirmacion` | No hay vínculo que romper. | 1 | Pasa |
| `test_el_precio_desmesurado_se_rechaza` | El precio desmesurado se rechaza | 1 | Pasa |
| `test_la_modificacion_queda_registrada` | La modificacion queda registrada | 1 | Pasa |
| `test_el_registro_guarda_el_par_anterior_y_nuevo` | Solo el estado final no permite reconstruir nada. | 1 | Pasa |
| `test_el_registro_nombra_los_campos_del_rubro` | La marca solo existe en un rubro y el volumen solo en el otro. | 1 | Pasa |
| `test_un_producto_descatalogado_se_edita` | A diferencia de una cuenta de usuario, que se congela al darse de baja: un producto de baja no habilita nada, y mantener sus datos al día es lo que permite reactivarlo. | 1 | Pasa |
| `test_la_pantalla_avisa_que_esta_fuera_del_catalogo` | La pantalla avisa que esta fuera del catalogo | 1 | Pasa |
| `test_el_cajero_no_edita` | CU-CAT-INV le abre la consulta al Cajero; editar sigue siendo del Administrador. | 1 | Pasa |
| `test_sin_sesion_redirige_al_login` | Sin sesion redirige al login | 1 | Pasa |
| `test_el_tomo_no_ofrece_categorias_del_otro_rubro` | El tomo no ofrece categorias del otro rubro | 1 | Pasa |
| `test_las_etiquetas_se_pueden_cambiar` | Las etiquetas se pueden cambiar | 1 | Pasa |
| `test_un_tipo_ajeno_al_rubro_se_rechaza` | El recorte del desplegable es comodidad; la validación es del servidor. | 1 | Pasa |
| `test_los_dos_rubros_llegan_a_su_propia_ficha` | La vista baja a la instancia de la hija, que es sobre la que trabaja su formulario. | 1 | Pasa |

### `test_filtros_publicos_de_etiquetas.py`

La parte de `CO-039`, `CO-041`, `CO-043` y `CO-045` sobre el catálogo público.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO041_el_grupo_dado_de_baja_y_sus_etiquetas_dejan_de_ofrecerse_en_la_tienda` | CO041 el grupo dado de baja y sus etiquetas dejan de ofrecerse en la tienda | 1 | Pasa |
| `test_CO039_el_grupo_reactivado_vuelve_a_ofrecer_las_etiquetas_activas` | CO039 el grupo reactivado vuelve a ofrecer las etiquetas activas | 1 | Pasa |
| `test_CO045_la_etiqueta_dada_de_baja_deja_de_ofrecerse_en_la_tienda` | CO045 la etiqueta dada de baja deja de ofrecerse en la tienda | 1 | Pasa |
| `test_CO043_la_etiqueta_reactivada_vuelve_a_ofrecerse_en_la_tienda` | CO043 la etiqueta reactivada vuelve a ofrecerse en la tienda | 1 | Pasa |

### `test_inventario.py`

Inventario y ficha de producto: la contraparte de lectura del alta.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_inventario_lista_los_productos_cargados` | El inventario lista los productos cargados | 1 | Pasa |
| `test_el_buscador_filtra_por_titulo` | El buscador filtra por titulo | 1 | Pasa |
| `test_los_filtros_ignoran_un_valor_inventado` | Un valor arbitrario en la query string no rompe ni filtra de más. | 1 | Pasa |
| `test_el_filtro_de_estado_funciona` | El filtro de estado funciona | 1 | Pasa |
| `test_el_filtro_de_etiqueta_funciona` | Las etiquetas no identifican un producto, pero son la forma natural de recortar el catálogo: "todo lo de Marvel" cruza editoriales y tipos, y ninguno de los otros filtros junta eso. | 1 | Pasa |
| `test_el_desplegable_de_etiquetas_solo_ofrece_las_que_filtran_algo` | Es el único eje que puede no aplicarle a ningún producto —ninguna es obligatoria—, así que una etiqueta sin productos ocuparía lugar en el desplegable sin filtrar nada. | 1 | Pasa |
| `test_un_producto_puede_tener_varias_etiquetas` | Es el defecto que la franquicia no podía expresar: Marvel publica cómics de Star Wars, o sea Marvel **y** Star Wars. | 1 | Pasa |
| `test_la_ficha_agrupa_las_etiquetas_por_su_grupo` | Sin el grupo, la ficha mostraría "Marvel, Shonen, Edición limitada" como una bolsa. | 1 | Pasa |
| `test_el_parcial_devuelve_solo_el_fragmento_de_la_tabla` | El parcial devuelve solo el fragmento de la tabla | 1 | Pasa |
| `test_la_ficha_muestra_los_datos_del_producto` | La ficha muestra los datos del producto | 1 | Pasa |
| `test_la_ficha_marca_la_portada_pendiente` | La ficha marca la portada pendiente | 1 | Pasa |
| `test_la_ficha_de_un_importado_muestra_la_composicion_del_precio` | La ficha de un importado muestra la composicion del precio | 1 | Pasa |
| `test_la_ficha_avisa_cuando_el_precio_es_manual` | La ficha avisa cuando el precio es manual | 1 | Pasa |
| `test_el_inventario_avisa_cuando_esta_vacio` | El inventario avisa cuando esta vacio | 1 | Pasa |
| `test_el_alta_avisa_si_falta_configurar_editoriales` | Sin editoriales no se puede dar de alta nada, y la pantalla lo dice. | 1 | Pasa |
| `test_con_editoriales_cargadas_no_aparece_el_aviso` | Con editoriales cargadas no aparece el aviso | 1 | Pasa |
| `test_el_inventario_no_filtra_datos_al_cliente` | 403 sin datos parciales, igual que la tabla de usuarios. | 1 | Pasa |
| `test_el_cajero_puede_consultar_el_inventario` | CU-CAT-INV lo declara actor: verifica disponibilidad para responder consultas de mostrador. | 1 | Pasa |
| `test_el_cajero_puede_abrir_la_ficha` | El cajero puede abrir la ficha | 1 | Pasa |
| `test_la_ficha_no_se_abre_para_un_cliente` | La ficha no se abre para un cliente | 1 | Pasa |
| `test_las_dos_pantallas_de_alta_se_dibujan_enteras` | Humo: las dos cargan con sus ítems vacíos y con el molde del `<template>`. | 2 | Pasa |
| `test_cada_item_ofrece_quitarlo_y_duplicarlo` | Contrato con el script de la pantalla: los `data-` son lo que busca. | 1 | Pasa |
| `test_el_molde_de_items_nuevos_trae_los_mismos_campos_que_los_dibujados` | El ítem que se agrega desde el navegador sale del `empty_form`. | 1 | Pasa |
| `test_el_alta_de_importados_muestra_la_calculadora_de_envio` | El alta de importados muestra la calculadora de envio | 1 | Pasa |
| `test_el_alta_de_nacionales_no_muestra_la_calculadora_de_envio` | El alta de nacionales no muestra la calculadora de envio | 1 | Pasa |
| `test_el_menu_del_administrador_ofrece_el_catalogo` | El menu del administrador ofrece el catalogo | 1 | Pasa |
| `test_no_se_pueden_cargar_dos_productos_con_la_misma_tupla` | La restricción de la base es la que realmente garantiza la unicidad: dos altas simultáneas pasarían las dos validaciones de formulario. | 1 | Pasa |
| `test_la_restriccion_tambien_alcanza_a_los_productos_sin_formato` | En SQL dos nulos no son iguales: sin el `Coalesce` de la restricción, dos importados del mismo tomo entrarían los dos sin que nada lo impida. | 2 | Pasa |
| `test_un_producto_nuevo_no_nace_demorado` | Un producto nuevo no nace demorado | 1 | Pasa |
| `test_el_indicador_convive_con_pre_venta_y_no_la_reemplaza` | "Demorado" no es un estado: como estado habría que elegir entre perder el "Pre-venta" o inventar un "Pre-venta demorado". | 1 | Pasa |
| `test_un_producto_activo_no_figura_demorado_aunque_quede_la_bandera` | Leer la bandera sola mostraría "Demorado" en el catálogo sobre algo que ya está en la góndola. | 1 | Pasa |
| `test_la_fecha_estimada_pisa_a_la_programada` | Para que la ficha y las notificaciones digan lo mismo sin que cada una elija por su cuenta cuál de las dos mostrar. | 1 | Pasa |
| `test_sin_fecha_estimada_vale_la_programada` | Demorado sin fecha nueva es el flujo A1 del CU y un caso normal: el proveedor muchas veces avisa que se atrasa sin saber para cuándo. | 1 | Pasa |
| `test_la_vista_por_defecto_muestra_solo_los_activos` | Paso 2: "todos los productos en estado Activo". | 1 | Pasa |
| `test_un_estado_vacio_explicito_muestra_todos` | No es lo mismo que no mandar el parámetro: sin él se aplica el valor por defecto. | 1 | Pasa |
| `test_los_descatalogados_llevan_su_etiqueta` | Paso 4: se presentan con una etiqueta visual diferenciada. | 1 | Pasa |
| `test_el_orden_por_defecto_es_alfabetico` | Lo pide el paso 2. | 1 | Pasa |
| `test_el_orden_por_lo_ultimo_cargado_sigue_disponible` | Cambiar el orden por defecto no puede romper el uso que le da Alta Editorial: después de cargar un lote se quiere ver lo recién cargado. | 1 | Pasa |
| `test_un_orden_inventado_cae_en_el_por_defecto` | Un valor de la query string no puede romper la pantalla. | 1 | Pasa |
| `test_el_filtro_de_stock_separa_lo_que_hay_de_lo_que_no` | Es el filtro que más usa el Cajero: la pregunta del mostrador es "¿lo tenés?", no "¿en qué estado está?". | 1 | Pasa |
| `test_sin_filtro_de_stock_se_ven_los_dos` | Sin filtro de stock se ven los dos | 1 | Pasa |
| `test_el_catalogo_vacio_se_distingue_del_filtro_sin_resultados` | Se rompió al darle un valor por defecto al estado: con un filtro siempre puesto, un catálogo vacío se anunciaba como "ningún resultado", que manda a buscar un problema donde no lo hay. | 1 | Pasa |
| `test_el_administrador_ve_el_historial_de_modificaciones` | El administrador ve el historial de modificaciones | 1 | Pasa |
| `test_el_cajero_no_ve_la_informacion_interna` | No se esconde con CSS: no se dibuja. | 1 | Pasa |
| `test_la_ficha_no_inventa_las_cifras_que_no_puede_calcular` | Un cero acá se leería como "nadie lo tiene reservado", que es la conclusión equivocada para decidir una baja. | 1 | Pasa |
| `test_el_historial_sale_del_log_de_auditoria` | Sale del log genérico, que desde A8 tiene un índice sobre `(objetivo_tipo, objetivo_pk)` puesto exactamente para esta consulta. | 1 | Pasa |

### `test_isbn.py`

El ISBN: normalización, dígito verificador y detección de duplicados.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_se_guarda_sin_guiones_ni_espacios` | Se normaliza al guardar y no solo al comparar: si no, el mismo ISBN escrito de dos formas serían dos productos para cualquier consulta que se olvide de normalizar, y la restricción de la base es una de esas. | 4 | Pasa |
| `test_la_x_final_va_en_mayuscula` | Es un dígito que vale diez, no una letra: en minúscula rompería la comparación exacta. | 1 | Pasa |
| `test_un_valor_vacio_se_normaliza_a_cadena_vacia` | Un valor vacio se normaliza a cadena vacia | 1 | Pasa |
| `test_un_isbn_bien_formado_pasa` | Un isbn bien formado pasa | 4 | Pasa |
| `test_un_digito_cambiado_se_detecta` | Es el caso que justifica verificar: un ISBN mal copiado no falla de forma ruidosa, pasa a identificar un producto que no existe y el chequeo de duplicados deja de encontrar el que sí. | 1 | Pasa |
| `test_un_largo_que_no_es_de_isbn_se_rechaza` | Un largo que no es de isbn se rechaza | 3 | Pasa |
| `test_las_letras_donde_no_van_se_rechazan` | Las letras donde no van se rechazan | 3 | Pasa |
| `test_verificar_no_consulta_nada_externo` | La fixture corta la red. | 1 | Pasa |
| `test_dos_productos_no_pueden_compartir_isbn` | Dos productos no pueden compartir isbn | 1 | Pasa |
| `test_muchos_productos_pueden_no_tener_isbn` | La restricción es parcial a propósito: el "sin ISBN" se representa con la cadena vacía, y una unicidad común los haría chocar a todos entre sí. | 1 | Pasa |
| `test_el_isbn_encuentra_el_duplicado_aunque_el_titulo_este_escrito_distinto` | Es lo que la tupla no atrapa, y el motivo por el que el ISBN va primero: el mismo tomo anunciado con otro nombre sigue siendo el mismo tomo. | 1 | Pasa |
| `test_sin_isbn_se_cae_a_la_tupla_de_siempre` | Sin isbn se cae a la tupla de siempre | 1 | Pasa |
| `test_un_isbn_que_no_esta_no_impide_encontrar_por_la_tupla` | Un producto viejo cargado sin ISBN puede ser el mismo tomo que uno nuevo que sí lo trae: si el ISBN no encuentra nada, todavía hay que mirar la tupla. | 1 | Pasa |
| `test_el_alta_guarda_el_isbn_normalizado` | El alta guarda el isbn normalizado | 1 | Pasa |
| `test_un_isbn_invalido_frena_el_item` | Un isbn invalido frena el item | 1 | Pasa |
| `test_el_isbn_es_opcional` | No todo producto tiene uno, y exigirlo trabaría el alta de todo el material que no responde a estándares editoriales (RF-05). | 1 | Pasa |
| `test_un_item_con_isbn_ya_cargado_se_excluye_del_lote` | E1 de CU-ALT-NAC con el criterio nuevo: el duplicado se excluye e informa, y los demás ítems del lote se cargan igual. | 1 | Pasa |
| `test_dos_items_con_el_mismo_isbn_en_el_mismo_envio_se_marcan` | A11 con el criterio nuevo: se marca el segundo, y se detecta aunque los títulos estén escritos distinto. | 1 | Pasa |
| `test_la_ficha_muestra_el_isbn` | La ficha muestra el isbn | 1 | Pasa |
| `test_dos_ediciones_del_mismo_tomo_tienen_isbn_distinto` | Es la razón por la que el ISBN resuelve lo que A13 resolvía con esfuerzo: el B6 y el Deluxe del mismo volumen son dos ediciones y dos ISBN. | 1 | Pasa |

### `test_jerarquia_de_producto.py`

La jerarquía de producto: identidad, rubro y las garantías de la base.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_un_producto_nace_con_codigo_aunque_nadie_se_lo_de` | Es la identidad de la fila: no puede faltar nunca. | 1 | Pasa |
| `test_el_codigo_del_no_editorial_lleva_su_propio_prefijo` | El prefijo es seguro porque el rubro de una fila no cambia: una fila no salta de una tabla hija a la otra. | 1 | Pasa |
| `test_un_codigo_escrito_a_mano_se_respeta` | Híbrido a propósito: la comiquería ya tiene una nomenclatura en sus planillas y el sistema no tiene por qué pisarla. | 1 | Pasa |
| `test_dos_productos_no_pueden_compartir_codigo` | Dos productos no pueden compartir codigo | 1 | Pasa |
| `test_el_codigo_no_se_regenera_al_volver_a_guardar` | Si cambiara, dejaría de servir para lo único que sirve: identificar. | 1 | Pasa |
| `test_los_codigos_generados_no_se_repiten_entre_rubros` | Se derivan de la clave primaria, que es compartida por la jerarquía, así que el prefijo es lo único que los separa. | 1 | Pasa |
| `test_dos_tomos_con_la_misma_tupla_chocan_en_la_base` | La restricción vieja abarcaba dos tablas y se perdió con la jerarquía. | 1 | Pasa |
| `test_la_clave_ignora_mayusculas_y_espacios_de_mas` | Quien carga "Batman " un martes y "batman" el jueves está cargando el mismo tomo. | 1 | Pasa |
| `test_dos_importados_sin_formato_tambien_chocan` | A13: en SQL dos nulos no son iguales, así que sin el cero de relleno dos importados sin formato —que es lo normal— no chocarían nunca entre sí. | 1 | Pasa |
| `test_la_misma_obra_de_dos_editoriales_son_dos_productos` | Es el caso que ordenó todo el modelo: la edición de Ivrea y la de Norma son la misma obra y **dos productos distintos**. | 1 | Pasa |
| `test_el_origen_no_entra_en_la_identidad` | `origen` es **cómo se forma el precio**, no qué es la cosa. | 1 | Pasa |
| `test_la_clave_se_recalcula_al_cambiar_un_campo_de_la_tupla` | La clave se recalcula al cambiar un campo de la tupla | 1 | Pasa |
| `test_el_codigo_de_barras_existe_en_los_dos_rubros` | **Un ISBN-13 es un EAN-13.** Los prefijos 978 y 979 son "Bookland", el país ficticio que GS1 reservó para libros dentro del sistema EAN, y el dígito verificador usa los mismos pesos alternados. | 1 | Pasa |
| `test_el_codigo_de_barras_es_opcional` | El merch genérico no lo trae, y el material editorial de fondo puede tener un ISBN-10, que no es un EAN válido. | 1 | Pasa |
| `test_dos_productos_no_pueden_compartir_codigo_de_barras` | Igual que el ISBN y por el mismo motivo: son identificadores del mundo, y dos productos con el mismo número son el mismo producto. | 1 | Pasa |
| `test_el_choque_de_codigo_de_barras_cruza_los_rubros` | Es consecuencia de que la restricción viva en la entidad general, y es lo correcto: el número identifica la cosa, no el rubro en el que la guardamos. | 1 | Pasa |
| `test_varios_productos_sin_codigo_de_barras_conviven` | La restricción es parcial: si no lo fuera, todos los que no lo tienen chocarían entre sí por compartir la cadena vacía. | 1 | Pasa |
| `test_el_isbn_no_se_copia_al_codigo_de_barras` | Se decidió **no** derivarlo: son el mismo número, pero mientras no haya lector la utilidad no está definida y sería lógica que nada ejercita. | 1 | Pasa |
| `test_la_marca_es_opcional` | Es el caso que rompió el modelo viejo: hay merch genérico y no oficial. | 1 | Pasa |
| `test_dos_articulos_del_mismo_nombre_y_categoria_pueden_convivir` | CU-CAT-ALT E2 lo trata como bloqueo y el catálogo real no lo tolera: dos llaveros de Naruto de proveedores distintos son dos productos. | 1 | Pasa |
| `test_un_tomo_no_acepta_una_categoria_no_editorial` | Un tomo no acepta una categoria no editorial | 1 | Pasa |
| `test_un_articulo_no_acepta_un_tipo_editorial` | Un articulo no acepta un tipo editorial | 1 | Pasa |
| `test_el_material_no_editorial_no_admite_pre_venta` | CU-CAT-ALT lo dice en sus comentarios, y se valida en el modelo y no escondiendo la opción en la pantalla. | 1 | Pasa |
| `test_usa_formato_no_sirve_como_discriminador_de_rubro` | El atajo que parece obvio y no lo es: Artbook, Novela ligera y Libro son editoriales y ya tienen `usa_formato` en falso. | 1 | Pasa |
| `test_especifico_devuelve_la_hija_desde_el_padre` | La herencia con tabla por hija no baja sola: sin esto el inventario no puede leer `volumen` ni `marca`. | 1 | Pasa |
| `test_especifico_sobre_una_hija_se_devuelve_a_si_misma` | Especifico sobre una hija se devuelve a si misma | 1 | Pasa |
| `test_el_inventario_devuelve_los_dos_rubros_en_una_sola_consulta` | Es lo que la herencia con tabla propia hace posible y las clases abstractas no: CU-CAT-INV pide un listado único sobre los dos rubros. | 1 | Pasa |
| `test_el_discriminador_lo_escribe_el_modelo` | Que lo complete quien crea el objeto sería pedirle que repita algo que el propio tipo ya dice. | 1 | Pasa |
| `test_el_precio_es_el_base_redondeado_en_los_dos_rubros` | La invariante que justifica que `precio_base` esté siempre presente. | 1 | Pasa |
| `test_no_se_puede_guardar_un_producto_sin_rubro` | No hay productos sueltos: todos son de un rubro o del otro. | 1 | Pasa |
| `test_guardar_por_la_entidad_general_tambien_se_rechaza` | Protege de paso la clave de edición: guardar por la general no la recalcula, porque no toca la tabla de la especialización. | 1 | Pasa |
| `test_las_dos_especializaciones_se_guardan_sin_problema` | Las dos especializaciones se guardan sin problema | 1 | Pasa |
| `test_un_alta_fallida_no_deja_una_fila_sin_codigo` | Las dos escrituras del código van en una transacción: el código se deriva de la clave primaria, así que hay que insertar para calcularlo, y sin la transacción hay un instante en el que la fila existe sin código. | 1 | Pasa |

### `test_mejoras_de_carga.py`

Historial del producto, galería de imágenes, medidas de los formatos, alta al vuelo de etiquetas y equivalencias de moneda (sesión del 2026-10-02).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_historial_de_un_tomo_cargado_por_lote_empieza_en_su_alta` | El historial de un tomo cargado por lote empieza en su alta | 1 | Pasa |
| `test_cambiar_solo_las_etiquetas_se_registra_y_se_avisa` | Cambiar solo las etiquetas se registra y se avisa | 1 | Pasa |
| `test_una_sinopsis_distinta_del_mismo_largo_tambien_se_registra` | Una sinopsis distinta del mismo largo tambien se registra | 1 | Pasa |
| `test_el_detalle_usa_comillas_angulares` | El detalle usa comillas angulares | 1 | Pasa |
| `test_la_edicion_agrega_imagenes_procesadas_y_las_registra` | La edicion agrega imagenes procesadas y las registra | 1 | Pasa |
| `test_quitar_una_imagen_reordena_y_borra_el_archivo` | Quitar una imagen reordena y borra el archivo | 1 | Pasa |
| `test_no_se_pasan_de_ocho_imagenes` | No se pasan de ocho imagenes | 1 | Pasa |
| `test_una_imagen_invalida_se_nombra_y_no_guarda_nada` | Una imagen invalida se nombra y no guarda nada | 1 | Pasa |
| `test_el_alta_no_editorial_carga_imagenes_y_la_ficha_las_muestra` | El alta no editorial carga imagenes y la ficha las muestra | 1 | Pasa |
| `test_los_desplegables_de_formato_muestran_las_medidas` | Los desplegables de formato muestran las medidas | 1 | Pasa |
| `test_el_dialogo_recibe_los_grupos_activos` | El dialogo recibe los grupos activos | 1 | Pasa |
| `test_crea_la_etiqueta_en_un_grupo_existente` | Crea la etiqueta en un grupo existente | 1 | Pasa |
| `test_crea_el_grupo_nuevo_y_la_etiqueta_juntos` | Crea el grupo nuevo y la etiqueta juntos | 1 | Pasa |
| `test_si_la_etiqueta_falla_tampoco_queda_el_grupo` | Si la etiqueta falla tampoco queda el grupo | 1 | Pasa |
| `test_el_cajero_no_crea_etiquetas_al_vuelo` | El cajero no crea etiquetas al vuelo | 1 | Pasa |
| `test_las_altas_ofrecen_el_alta_al_vuelo_de_etiquetas` | Las altas ofrecen el alta al vuelo de etiquetas | 1 | Pasa |
| `test_las_equivalencias_dividen_por_la_cotizacion_de_referencia` | Las equivalencias dividen por la cotizacion de referencia | 1 | Pasa |
| `test_la_tabla_de_precios_muestra_las_equivalencias` | La tabla de precios muestra las equivalencias | 1 | Pasa |

### `test_nombres_de_catalogo.py`

Los catálogos que se identifican por su nombre no distinguen mayúsculas.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_mismo_nombre_en_otra_caja_se_rechaza` | El mismo nombre en otra caja se rechaza | 1 | Pasa |
| `test_el_aviso_nombra_al_registro_existente` | Sin el nombre tal como está guardado, hay que ir a buscarlo a la lista. | 1 | Pasa |
| `test_los_espacios_de_mas_se_normalizan` | Los espacios de mas se normalizan | 1 | Pasa |
| `test_editarse_a_si_mismo_no_es_un_duplicado` | Guardar un registro sin tocarle el nombre tiene que seguir andando: el choque se busca contra los demás, no contra uno mismo. | 1 | Pasa |
| `test_se_le_puede_corregir_la_capitalizacion` | El caso que rompería una comparación ingenua contra sí mismo: cambiar "zeta de prueba" por "Zeta de prueba" es la misma fila, no un duplicado. | 1 | Pasa |
| `test_la_restriccion_esta_en_la_base` | Sin esto la regla vale solo para quien pase por el formulario, y un `create()` en un comando o en un import la esquiva sin avisar. | 1 | Pasa |
| `test_la_pantalla_de_edicion_abre` | La pantalla de edicion abre | 1 | Pasa |
| `test_la_edicion_rechaza_el_choque_con_otro` | La edicion rechaza el choque con otro | 1 | Pasa |
| `test_solo_el_administrador_edita` | Solo el administrador edita | 1 | Pasa |

### `test_pantalla_etiquetas.py`

Las pantallas de etiquetas: los grupos (CU-CAT-GRC) y las etiquetas de cada grupo (CU-CAT-ETC).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_los_grupos_enlazan_a_sus_etiquetas` | Los grupos enlazan a sus etiquetas | 1 | Pasa |
| `test_un_grupo_inactivo_se_marca` | Un grupo inactivo se marca | 1 | Pasa |
| `test_sin_grupos_ofrece_el_alta` | Sin grupos ofrece el alta | 1 | Pasa |
| `test_lista_las_etiquetas_del_grupo_y_no_las_de_otro` | Lista las etiquetas del grupo y no las de otro | 1 | Pasa |
| `test_muestra_cuantos_productos_usan_cada_etiqueta` | Muestra cuantos productos usan cada etiqueta | 1 | Pasa |
| `test_cada_etiqueta_enlaza_a_su_modificacion_y_a_su_baja` | Cada etiqueta enlaza a su modificacion y a su baja | 1 | Pasa |
| `test_el_buscador_filtra` | El buscador filtra | 1 | Pasa |
| `test_el_filtro_por_estado` | El filtro por estado | 1 | Pasa |
| `test_sin_coincidencias_lo_dice` | Sin coincidencias lo dice | 1 | Pasa |
| `test_el_listado_se_pagina_de_a_cincuenta` | `CO-165` dice «paginado» sin decir cuánto: se toma el tamaño de `CO-205`. | 1 | Pasa |
| `test_un_grupo_dado_de_baja_lo_avisa_y_no_ofrece_alta` | Un grupo dado de baja lo avisa y no ofrece alta | 1 | Pasa |
| `test_solo_el_administrador_las_consulta` | Solo el administrador las consulta | 2 | Pasa |
| `test_sin_sesion_redirige_al_login` | Sin sesion redirige al login | 1 | Pasa |
| `test_el_alta_de_etiqueta_vuelve_a_su_grupo` | El alta de etiqueta vuelve a su grupo | 1 | Pasa |
| `test_el_alta_desde_un_grupo_lo_trae_elegido` | El alta desde un grupo lo trae elegido | 1 | Pasa |
| `test_el_alta_de_grupo_vuelve_a_los_grupos` | El alta de grupo vuelve a los grupos | 1 | Pasa |

### `test_pantalla_revision.py`

Las pantallas de la revisión de borradores (CU-ALT-REV).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_la_cola_lista_los_borradores_pendientes` | La cola lista los borradores pendientes | 1 | Pasa |
| `test_la_cola_vacia_lo_dice_y_apunta_a_donde_se_generan` | Sin borradores pendientes: informa y no presenta nada (excepción del CU). | 1 | Pasa |
| `test_la_cola_distingue_incompletos_de_confianza_baja` | No son lo mismo y no se arreglan igual: al incompleto le falta un dato, al dudoso hay que mirarle uno que ya está. | 1 | Pasa |
| `test_solo_se_puede_seleccionar_lo_que_el_lote_va_a_confirmar` | Ofrecer la casilla en un incompleto sería invitar a un clic que termina en una advertencia. | 1 | Pasa |
| `test_la_cola_no_muestra_una_sesion_hasta_que_haya_una_accion` | La cola no muestra una sesion hasta que haya una accion | 1 | Pasa |
| `test_el_buscador_filtra_por_titulo` | El buscador filtra por titulo | 1 | Pasa |
| `test_la_ficha_muestra_los_reparos_del_borrador` | La ficha muestra los reparos del borrador | 1 | Pasa |
| `test_guardar_sin_confirmar_deja_el_borrador_en_la_cola` | Guardar sin confirmar deja el borrador en la cola | 1 | Pasa |
| `test_confirmar_desde_la_ficha_crea_el_producto` | Confirmar desde la ficha crea el producto | 1 | Pasa |
| `test_el_titulo_editado_es_el_que_llega_al_producto` | El titulo editado es el que llega al producto | 1 | Pasa |
| `test_un_isbn_mal_escrito_a_mano_se_rechaza` | El pipeline ya lo verifica al extraer, pero acá lo escribe una persona: es exactamente el momento del error de transcripción (A19). | 1 | Pasa |
| `test_una_pre_venta_sin_fecha_no_se_puede_guardar` | Una pre venta sin fecha no se puede guardar | 1 | Pasa |
| `test_rechazar_sin_motivo_no_descarta_nada` | Rechazar sin motivo no descarta nada | 1 | Pasa |
| `test_rechazar_con_motivo_descarta_el_borrador` | Rechazar con motivo descarta el borrador | 1 | Pasa |
| `test_un_borrador_ya_resuelto_no_se_vuelve_a_resolver` | El doble envío del formulario es el caso normal, no el raro. | 1 | Pasa |
| `test_la_ficha_de_un_borrador_resuelto_no_ofrece_acciones` | La ficha de un borrador resuelto no ofrece acciones | 1 | Pasa |
| `test_la_ficha_pide_la_casilla_por_cada_campo_de_confianza_baja` | La ficha pide la casilla por cada campo de confianza baja | 1 | Pasa |
| `test_confirmar_sin_revisar_la_confianza_baja_se_bloquea` | Se valida en el servidor y no escondiendo el botón: un POST armado a mano confirmaría igual un dato que nadie miró (RNF-03). | 1 | Pasa |
| `test_confirmar_marcando_la_casilla_funciona` | Confirmar marcando la casilla funciona | 1 | Pasa |
| `test_revisar_un_campo_y_no_el_otro_sigue_bloqueando` | La acción es por campo, no un "revisé este borrador" genérico. | 1 | Pasa |
| `test_la_marca_de_revisado_se_puede_retirar` | Dejar la marca puesta haría que un dato vuelto a poner en duda siguiera contando como mirado. | 1 | Pasa |
| `test_el_lote_confirma_los_seleccionados` | El lote confirma los seleccionados | 1 | Pasa |
| `test_el_lote_informa_lo_que_excluyo` | Se informa la exclusión: sin eso, el borrador que quedó afuera desaparecería de la vista sin explicación. | 1 | Pasa |
| `test_el_lote_sin_seleccion_no_hace_nada` | El lote sin seleccion no hace nada | 1 | Pasa |
| `test_cerrar_manda_el_pedido_y_lo_informa` | Cerrar manda el pedido y lo informa | 1 | Pasa |
| `test_cerrar_sin_sesion_en_curso_lo_dice` | Cerrar sin sesion en curso lo dice | 1 | Pasa |
| `test_cerrar_una_sesion_de_solo_rechazos_no_manda_pedidos` | Cerrar una sesion de solo rechazos no manda pedidos | 1 | Pasa |
| `test_la_cola_muestra_la_sesion_en_curso` | La cola muestra la sesion en curso | 1 | Pasa |
| `test_las_pantallas_son_solo_del_administrador` | Las pantallas son solo del administrador | 2 | Pasa |
| `test_el_menu_enlaza_la_revision` | El menu enlaza la revision | 1 | Pasa |
| `test_confirmar_desde_la_pantalla_deja_al_producto_atado_a_su_proveedor` | Confirmar desde la pantalla deja al producto atado a su proveedor | 1 | Pasa |
| `test_la_ficha_avisa_si_el_producto_ya_esta_en_el_catalogo` | Salió de correr el pipeline sobre dos correos que anunciaban los mismos tomos: los borradores del segundo quedaban en la cola sin ninguna marca, y la única forma de enterarse era apretar «confirmar» y recibir el rechazo. | 1 | Pasa |
| `test_un_borrador_sin_duplicado_no_lleva_ese_aviso` | Un borrador sin duplicado no lleva ese aviso | 1 | Pasa |
| `test_la_ficha_de_un_confirmado_no_se_avisa_a_si_misma` | El "duplicado" de un borrador confirmado sería el producto que él mismo creó, y avisarlo sería absurdo. | 1 | Pasa |

### `test_parametros.py`

Parámetros globales: clasificación del catálogo, precios y configuración.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_sistema_arranca_con_tipos_y_formatos_cargados` | Sin al menos un tipo no se puede dar de alta ningún producto: una instalación nueva no puede quedar trabada esperando que alguien adivine qué cargar primero. | 1 | Pasa |
| `test_los_tipos_con_grilla_de_tamanos_usan_formato` | Los tipos con grilla de tamanos usan formato | 2 | Pasa |
| `test_los_tipos_sin_grilla_de_tamanos_no_usan_formato` | Los tipos sin grilla de tamanos no usan formato | 3 | Pasa |
| `test_el_sistema_arranca_con_los_grupos_de_etiqueta_sembrados` | No pretenden ser la taxonomía completa: existen para que la pantalla no arranque vacía y el primer producto se pueda describir sin inventar los ejes desde cero. | 1 | Pasa |
| `test_hay_grupos_para_el_rubro_no_editorial` | Los sembrados originalmente describen material editorial, y la pantalla de una figura ofrecía cuatro ejes y ninguno aplicable: una figura no tiene demografía ni género literario, y etiquetarla igual ensucia los filtros. | 1 | Pasa |
| `test_franquicia_sirve_para_los_dos_rubros` | Es el único eje compartido, y por eso no se duplicó: una figura de Marvel y un cómic de Marvel comparten franquicia. | 1 | Pasa |
| `test_la_pantalla_enlaza_los_catalogos_y_los_precios` | Cada catálogo y la tabla de precios tienen su pantalla (`CU-CFG-EDC`, `TPC`, `FMC`, `CU-CAT-GRC`, `CU-PVP-TBC`); el margen también, porque cambiarlo propaga precios (`CU-CFG-PAR` A1). | 1 | Pasa |
| `test_las_etiquetas_se_administran_en_su_propia_pantalla` | Salieron de acá porque son el único catálogo abierto de los seis. | 1 | Pasa |
| `test_el_margen_ya_no_se_edita_desde_parametros` | `CU-CFG-PAR` A1: el panel enlaza a `CU-PVP-MAR` en vez de editarlo. | 1 | Pasa |
| `test_se_avisa_cuando_una_editorial_no_tiene_precios` | Se avisa cuando una editorial no tiene precios | 1 | Pasa |
| `test_solo_el_administrador_ve_los_parametros` | Solo el administrador ve los parametros | 2 | Pasa |
| `test_la_configuracion_nace_con_los_valores_de_settings` | Estrenar la pantalla no puede cambiar ningún cálculo. | 1 | Pasa |
| `test_no_puede_haber_dos_configuraciones` | Si hubiera dos nadie sabría cuál rige, y el precio de los importados dependería de cuál se leyó primero. | 1 | Pasa |
| `test_la_configuracion_no_se_borra` | La configuracion no se borra | 1 | Pasa |
| `test_guardar_el_stock_por_defecto_lo_deja_vigente_y_auditado` | Guardar el stock por defecto lo deja vigente y auditado | 1 | Pasa |
| `test_un_stock_por_defecto_absurdo_es_rechazado` | Un stock por defecto absurdo es rechazado | 1 | Pasa |
| `test_se_puede_dar_de_alta_una_editorial` | Se puede dar de alta una editorial | 1 | Pasa |
| `test_el_nombre_de_la_editorial_se_normaliza` | Sin esto, en seis meses conviven tres editoriales con el mismo nombre y los productos quedan repartidos entre las tres. | 1 | Pasa |
| `test_una_editorial_repetida_es_rechazada` | Una editorial repetida es rechazada | 3 | Pasa |
| `test_se_puede_dar_de_alta_un_tipo_con_su_bandera` | `usa_formato` es la única que quedó: es la que gobierna una restricción real, porque el formato entra en la tabla de precios. | 1 | Pasa |
| `test_se_puede_editar_un_formato` | Se puede editar un formato | 1 | Pasa |
| `test_el_alta_de_un_parametro_queda_auditada` | El alta de un parametro queda auditada | 1 | Pasa |
| `test_se_puede_cargar_un_precio_de_referencia` | Se puede cargar un precio de referencia | 1 | Pasa |
| `test_no_se_puede_repetir_la_misma_combinacion` | No se puede repetir la misma combinacion | 1 | Pasa |
| `test_la_tabla_no_ofrece_tipos_que_no_usan_formato` | Un artbook no tiene con qué completar la clave: su precio va a mano. | 1 | Pasa |
| `test_un_precio_negativo_es_rechazado` | Un precio negativo es rechazado | 1 | Pasa |
| `test_eliminar_un_precio_no_toca_los_productos_ya_cargados` | El producto guarda su precio: lo que se pierde es el pre-completado. | 1 | Pasa |
| `test_la_baja_de_un_precio_pide_confirmacion` | La baja de un precio pide confirmacion | 1 | Pasa |
| `test_las_altas_de_parametros_son_solo_del_administrador` | Las altas de parametros son solo del administrador | 4 | Pasa |
| `test_se_puede_dar_de_alta_una_etiqueta` | Se puede dar de alta una etiqueta | 1 | Pasa |
| `test_el_nombre_de_la_etiqueta_se_normaliza` | El nombre de la etiqueta se normaliza | 1 | Pasa |
| `test_una_etiqueta_repetida_en_el_mismo_grupo_es_rechazada` | La comparación ignora mayúsculas: es la misma etiqueta escrita distinto. | 1 | Pasa |
| `test_el_mismo_nombre_en_otro_grupo_si_se_puede` | La unicidad es por grupo: "Terror" puede ser un género y también el nombre de una colección, y son dos etiquetas distintas. | 1 | Pasa |
| `test_una_etiqueta_de_una_letra_es_rechazada` | Una sola letra no describe nada y casi siempre es un enter de más. | 1 | Pasa |
| `test_una_etiqueta_sin_grupo_es_rechazada` | El grupo es lo que la hace filtrable: sin él no se sabe en qué faceta de la tienda tendría que aparecer. | 1 | Pasa |
| `test_el_alta_de_etiqueta_queda_auditada` | El alta de etiqueta queda auditada | 1 | Pasa |
| `test_se_puede_dar_de_alta_un_grupo_de_etiquetas` | Se puede dar de alta un grupo de etiquetas | 1 | Pasa |
| `test_un_grupo_repetido_es_rechazado` | Un grupo repetido es rechazado | 1 | Pasa |
| `test_solo_el_administrador_administra_etiquetas` | Solo el administrador administra etiquetas | 2 | Pasa |
| `test_un_formato_que_aplica_a_todos_es_universal` | «Aplica a todos los tipos» es un atributo (B-17-004), no una lista vacía. | 1 | Pasa |
| `test_un_formato_con_tipos_declarados_solo_aplica_a_esos` | Un formato con tipos declarados solo aplica a esos | 1 | Pasa |
| `test_el_alta_solo_ofrece_los_formatos_del_tipo_elegido` | Es lo que baja el desplegable de quince opciones a las que aplican, en la pantalla que más campos pide. | 1 | Pasa |
| `test_un_precio_de_referencia_con_un_formato_que_no_aplica_es_rechazado` | Una fila para una combinación imposible es una fila muerta: no va a coincidir nunca con ningún producto y confunde a quien la lea. | 1 | Pasa |
| `test_se_puede_cambiar_a_un_proveedor_remoto` | Se puede cambiar a un proveedor remoto | 1 | Pasa |
| `test_un_proveedor_remoto_sin_clave_se_rechaza` | Sin clave no va a contestar nunca, y el fallo aparecería recién en la pantalla de diagnóstico. | 1 | Pasa |
| `test_un_proveedor_remoto_sin_modelo_se_rechaza` | Los proveedores hospedan cientos: sin nombrarlo devuelven un error que cuesta interpretar. | 1 | Pasa |
| `test_dejar_la_clave_vacia_no_la_borra` | El campo llega vacío siempre, así que un vacío significa "no la cambies" y no "borrala". | 1 | Pasa |
| `test_la_clave_nunca_se_dibuja_entera` | La pantalla no puede ser un lugar del que copiar el secreto. | 1 | Pasa |
| `test_la_clave_no_entra_en_la_auditoria` | El log es inmutable y consultable: un secreto que pasa por ahí queda ahí para siempre. | 1 | Pasa |
| `test_el_cambio_de_modelo_queda_auditado` | El cambio de modelo queda auditado | 1 | Pasa |
| `test_guardar_el_modelo_no_toca_el_margen` | Son dos formularios porque se tocan por motivos distintos: un error en uno no puede borrar lo escrito en el otro. | 1 | Pasa |
| `test_una_direccion_sin_la_ruta_de_la_api_se_rechaza` | Pegar la dirección base del servidor es el error más natural acá, y el formulario lo aceptaba: quedaba una configuración que no puede funcionar y el diagnóstico decía "no parece una API compatible", que es verdad pero no dice qué corregir. | 1 | Pasa |
| `test_la_direccion_completa_se_acepta_en_los_dos_modos` | La direccion completa se acepta en los dos modos | 1 | Pasa |
| `test_la_barra_final_de_mas_no_molesta` | La barra final de mas no molesta | 1 | Pasa |

### `test_parametros_compra.py`

`CO-130` en la sección «Compra online» de Parámetros (plan 07, sexta parte).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO130_los_parametros_de_la_compra_pasan_a_los_declarados` | CO130 los parametros de la compra pasan a los declarados | 1 | Pasa |
| `test_CO130_una_entrada_de_auditoria_por_cada_parametro_modificado` | CO130 una entrada de auditoria por cada parametro modificado | 1 | Pasa |
| `test_CO130_solo_se_audita_lo_que_cambio` | CO130 solo se audita lo que cambio | 1 | Pasa |
| `test_CO130_guardar_sin_cambios_no_deja_entradas` | CO130 guardar sin cambios no deja entradas | 1 | Pasa |
| `test_CO130_b_la_configuracion_queda_asociada_al_administrador` | CO130 b la configuracion queda asociada al administrador | 1 | Pasa |
| `test_CO130_los_valores_operativos_no_cambian_al_guardar_la_compra` | CO130 los valores operativos no cambian al guardar la compra | 1 | Pasa |
| `test_CO130_un_valor_fuera_de_rango_no_se_guarda` | CO130 un valor fuera de rango no se guarda | 8 | Pasa |
| `test_CO130_la_pantalla_muestra_la_seccion_de_compra_online` | CO130 la pantalla muestra la seccion de compra online | 1 | Pasa |
| `test_acceso_solo_el_administrador_guarda_la_compra_online` | Acceso solo el administrador guarda la compra online | 2 | Pasa |
| `test_la_pantalla_muestra_que_significan_los_dos_numeros` | La pantalla muestra que significan los dos numeros | 1 | Pasa |

### `test_precios.py`

RF-10 — la aritmética del precio importado.

**Casos de prueba que ejecuta:** CP-01.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_cre_es_el_cociente_entre_el_envio_y_la_compra` | El cre es el cociente entre el envio y la compra | 1 | Pasa |
| `test_el_cre_se_guarda_con_seis_decimales` | Es un factor que multiplica a todos los ítems: redondearlo a dos arrastraría el error del cociente a cada precio del lote. | 1 | Pasa |
| `test_un_valor_de_compra_en_cero_da_un_cre_de_cero` | No hay contra qué prorratear el envío. | 1 | Pasa |
| `test_la_formula_encadena_costo_cre_y_margen` | `precio_final = C × (1 + R) × (1 + M)`, la condición de verificación de RF-10. | 1 | Pasa |
| `test_casos_de_la_formula` | Casos de la formula | 3 | Pasa |
| `test_el_precio_base_conserva_centavos` | Es el valor que se persiste para recalcular en CU-PVP-MAR: redondearlo al peso metería el error del redondeo dentro de cada recálculo futuro. | 1 | Pasa |
| `test_el_precio_final_se_redondea_al_peso` | El precio final se redondea al peso | 1 | Pasa |
| `test_el_medio_peso_redondea_para_arriba` | El medio peso redondea para arriba | 3 | Pasa |
| `test_sin_cotizacion_el_importe_ya_esta_en_pesos` | Sin cotizacion el importe ya esta en pesos | 1 | Pasa |
| `test_la_cotizacion_convierte_el_costo_en_origen_a_pesos` | Agregado a la fuente: el CU habla de 'costo base en origen' sin decir en qué moneda. | 1 | Pasa |
| `test_el_desglose_convierte_antes_de_aplicar_el_cre` | El desglose convierte antes de aplicar el cre | 1 | Pasa |
| `test_el_recalculo_de_cu_13_sale_del_precio_base_almacenado` | Ante un margen nuevo, el precio final se recalcula sin los datos del lote. | 1 | Pasa |

### `test_revision_borradores.py`

Revisar y confirmar borradores (CU-ALT-REV), del lado de las reglas.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_confirmar_crea_el_producto` | Confirmar crea el producto | 1 | Pasa |
| `test_el_producto_nace_atado_al_proveedor_que_lo_anuncio` | Es la única vía por la que ese dato se llena: las altas manuales no lo piden (A4 de proveedores). | 1 | Pasa |
| `test_el_borrador_queda_confirmado_y_apunta_a_su_producto` | El borrador queda confirmado y apunta a su producto | 1 | Pasa |
| `test_una_pre_venta_conserva_su_fecha` | Una pre venta conserva su fecha | 1 | Pasa |
| `test_el_precio_se_redondea_al_peso` | A1: el precio final es el número que se cobra, y en una comiquería no se cobran centavos. | 1 | Pasa |
| `test_un_precio_que_coincide_con_la_tabla_no_queda_manual` | Un precio que coincide con la tabla no queda manual | 1 | Pasa |
| `test_un_precio_distinto_del_de_la_tabla_queda_manual` | A4: si el precio confirmado no es el de la tabla, alguien lo decidió a propósito y la propagación de CU-PVP-MAR no debe pisárselo. | 1 | Pasa |
| `test_sin_fila_en_la_tabla_la_marca_no_aplica` | No hay de dónde propagarle, así que no se lo marca como manual. | 1 | Pasa |
| `test_un_bloqueante_vacio_impide_confirmar` | Un bloqueante vacio impide confirmar | 1 | Pasa |
| `test_una_pre_venta_sin_fecha_no_se_puede_confirmar` | Bloqueante condicional del CU, y A10: sin fecha quedaría en pre-venta para siempre, invisible para el ciclo que debería sacarla de ahí. | 1 | Pasa |
| `test_el_mismo_borrador_sin_fecha_se_confirma_si_nace_activo` | La fecha es bloqueante **solo** si el borrador quedaría en Pre-venta. | 1 | Pasa |
| `test_un_producto_que_se_cargo_mientras_tanto_bloquea_la_confirmacion` | Entre que el borrador se generó y que alguien lo confirma pueden pasar días: la comprobación del pipeline caducó y hay que rehacerla. | 1 | Pasa |
| `test_confirmar_dos_veces_no_duplica_el_producto` | La segunda confirmación encuentra el borrador ya resuelto y se retira. | 1 | Pasa |
| `test_el_lote_confirma_todos_los_que_estan_en_condiciones` | El lote confirma todos los que estan en condiciones | 1 | Pasa |
| `test_el_lote_excluye_la_confianza_baja_sin_bloquear_al_resto` | Es la excepción central del CU: se informa la exclusión y el borrador permanece en cola para revisión individual. | 1 | Pasa |
| `test_una_confianza_baja_ya_revisada_no_excluye_del_lote` | La acción afirmativa del paso 3 es lo que la desbloquea. | 1 | Pasa |
| `test_la_confianza_media_no_excluye_del_lote` | El CU habla de confianza **baja**: la media no traba nada. | 1 | Pasa |
| `test_un_borrador_de_confianza_baja_si_se_puede_confirmar_de_a_uno` | La pantalla exige la acción afirmativa antes de dejar apretar el botón; el servicio no la vuelve a exigir en el camino individual. | 1 | Pasa |
| `test_rechazar_exige_motivo` | Rechazar exige motivo | 1 | Pasa |
| `test_rechazar_persiste_el_motivo_y_lo_audita` | Rechazar persiste el motivo y lo audita | 1 | Pasa |
| `test_rechazar_no_crea_ningun_producto` | Rechazar no crea ningun producto | 1 | Pasa |
| `test_mirar_la_cola_no_abre_una_sesion` | Se crea con la primera acción: abrirla al entrar llenaría la tabla de tandas vacías cada vez que alguien pasa a ver qué hay. | 1 | Pasa |
| `test_la_primera_confirmacion_abre_la_sesion` | La primera confirmacion abre la sesion | 1 | Pasa |
| `test_las_acciones_siguientes_reusan_la_misma_sesion` | Las acciones siguientes reusan la misma sesion | 1 | Pasa |
| `test_dos_revisores_tienen_sesiones_distintas` | Mezclarlas haría que el pedido consolidado de uno se lleve los productos del otro. | 1 | Pasa |
| `test_cerrar_manda_un_correo_por_proveedor` | Cerrar manda un correo por proveedor | 1 | Pasa |
| `test_cada_correo_lleva_solo_los_productos_de_su_proveedor` | Cada correo lleva solo los productos de su proveedor | 1 | Pasa |
| `test_el_pedido_lleva_las_cantidades_de_stock_solicitadas` | El pedido lleva las cantidades de stock solicitadas | 1 | Pasa |
| `test_una_sesion_sin_confirmaciones_no_manda_ningun_correo` | Solo rechazos: la sesión queda registrada, pero un correo vacío sería peor que no mandarlo. | 1 | Pasa |
| `test_dos_sesiones_el_mismo_dia_son_dos_correos_separados` | No reabre pedidos de sesiones anteriores: son dos decisiones distintas y el proveedor tiene que poder tratarlas como tales. | 1 | Pasa |
| `test_el_envio_se_reintenta_tres_veces` | El envio se reintenta tres veces | 1 | Pasa |
| `test_un_envio_fallido_no_revierte_los_productos` | El alta y el pedido son operaciones separadas: un correo que no salió no puede deshacer productos que ya están en el catálogo. | 1 | Pasa |
| `test_el_fallo_queda_registrado_con_el_proveedor` | El CU pide notificar indicando **cuál** proveedor falló: sin el nombre el aviso no sirve para ir a mandarlo a mano. | 1 | Pasa |
| `test_un_proveedor_caido_no_frena_al_resto` | Un proveedor caido no frena al resto | 1 | Pasa |
| `test_cada_confirmacion_deja_su_entrada` | "Qué pasó en esta tanda" la contesta la sesión; "de dónde salió este producto" solo la contesta esta entrada. | 1 | Pasa |
| `test_el_cierre_registra_confirmados_rechazados_y_pendientes` | El cierre registra confirmados rechazados y pendientes | 1 | Pasa |
| `test_el_stock_por_defecto_de_la_configuracion_llega_al_producto` | El stock por defecto de la configuracion llega al producto | 1 | Pasa |
| `test_una_carrera_contra_la_base_se_trata_como_duplicado` | La restricción de la base es la que **realmente** garantiza la unicidad. | 1 | Pasa |
| `test_un_proveedor_sin_productos_confirmados_no_recibe_correo` | Nada que pedir no es un fallo: es una sesión donde ese proveedor no aportó ningún producto. | 1 | Pasa |

### `test_validaciones.py`

Entradas mal puestas en la carga de lotes.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_un_valor_negativo_en_el_item_es_rechazado` | Un valor negativo en el item es rechazado | 2 | Pasa |
| `test_un_volumen_negativo_es_rechazado` | Un volumen negativo es rechazado | 1 | Pasa |
| `test_un_costo_en_origen_negativo_es_rechazado` | Un costo en origen negativo es rechazado | 1 | Pasa |
| `test_un_total_negativo_del_lote_es_rechazado` | Un total negativo del lote es rechazado | 2 | Pasa |
| `test_una_cotizacion_negativa_es_rechazada` | Una cotizacion negativa es rechazada | 1 | Pasa |
| `test_un_precio_en_cero_es_rechazado` | Un producto de precio cero no es una promoción, es un cero de menos. | 1 | Pasa |
| `test_un_valor_de_compra_en_cero_es_rechazado` | Es el divisor del CRE: sin él no hay contra qué prorratear el envío. | 1 | Pasa |
| `test_un_envio_en_cero_es_valido` | Hay proveedores que bonifican el envío: el CRE da cero y el precio base termina siendo el costo. | 1 | Pasa |
| `test_un_stock_en_cero_es_valido` | Un stock en cero es valido | 1 | Pasa |
| `test_un_volumen_absurdo_es_rechazado` | Un volumen absurdo es rechazado | 1 | Pasa |
| `test_un_stock_absurdo_es_rechazado` | Un stock absurdo es rechazado | 1 | Pasa |
| `test_un_precio_absurdo_es_rechazado` | Un precio absurdo es rechazado | 1 | Pasa |
| `test_un_precio_que_no_es_un_numero_es_rechazado` | Un precio que no es un numero es rechazado | 5 | Pasa |
| `test_un_volumen_que_no_es_entero_es_rechazado` | Un volumen que no es entero es rechazado | 3 | Pasa |
| `test_un_titulo_de_una_sola_letra_es_rechazado` | Un titulo de una sola letra es rechazado | 1 | Pasa |
| `test_un_titulo_de_solo_espacios_es_rechazado` | Django recorta los extremos, así que el campo queda vacío y obligatorio. | 1 | Pasa |
| `test_los_espacios_de_mas_del_titulo_se_normalizan` | Sin esto, "Akira vol" y "Akira vol" serían dos productos distintos para cualquiera que compare sin normalizar. | 1 | Pasa |
| `test_un_estado_inventado_es_rechazado` | El alta ofrece dos estados; los otros tres son consecuencia de algo posterior y no se pueden elegir desde acá. | 1 | Pasa |
| `test_un_formato_inexistente_es_rechazado` | Un formato inexistente es rechazado | 1 | Pasa |
| `test_un_tipo_inexistente_es_rechazado` | Un tipo inexistente es rechazado | 1 | Pasa |
| `test_una_editorial_inexistente_es_rechazada` | Una editorial inexistente es rechazada | 1 | Pasa |
| `test_una_editorial_inactiva_no_se_puede_elegir` | Una editorial dada de baja no se ofrece, y tampoco se acepta si alguien manda su identificador a mano. | 1 | Pasa |
| `test_una_fecha_de_llegada_pasada_es_rechazada_en_el_item` | Una fecha de llegada pasada es rechazada en el item | 1 | Pasa |
| `test_una_fecha_de_llegada_pasada_es_rechazada_en_la_cabecera` | Una fecha de llegada pasada es rechazada en la cabecera | 1 | Pasa |
| `test_la_fecha_de_hoy_se_acepta` | El lote que llega hoy es el caso más común de todos. | 1 | Pasa |
| `test_una_fecha_invalida_es_rechazada` | Una fecha invalida es rechazada | 1 | Pasa |
| `test_pre_venta_sin_fecha_es_rechazada` | El ciclo que transiciona las pre-ventas busca por fecha de llegada: una pre-venta sin fecha no se puede vigilar y quedaría colgada para siempre. | 1 | Pasa |
| `test_pre_venta_con_fecha_de_la_cabecera_se_acepta` | Pre venta con fecha de la cabecera se acepta | 1 | Pasa |
| `test_dos_items_identicos_en_el_mismo_lote_se_marcan` | Distinto del duplicado contra el catálogo: este todavía se puede corregir sin perder nada, y avisarlo al guardar sería tarde. | 1 | Pasa |
| `test_el_repetido_se_detecta_sin_distinguir_mayusculas` | El repetido se detecta sin distinguir mayusculas | 1 | Pasa |
| `test_el_primero_de_los_repetidos_no_se_marca` | Solo se señala el que sobra: marcar los dos obligaría a adivinar cuál de los dos había que borrar. | 1 | Pasa |
| `test_dos_volumenes_distintos_no_son_repetidos` | Dos volumenes distintos no son repetidos | 1 | Pasa |
| `test_un_contador_de_items_manipulado_no_rompe_la_pantalla` | El formulario de gestión viaja en el HTML y se puede editar a mano. | 1 | Pasa |
| `test_un_envio_sin_formulario_de_gestion_no_rompe_la_pantalla` | Un envio sin formulario de gestion no rompe la pantalla | 1 | Pasa |
| `test_los_items_vacios_se_descartan_sin_dar_error` | La pantalla arranca con tres ítems en blanco: los que no se toquen no tienen por qué reclamar campos obligatorios. | 1 | Pasa |
| `test_un_archivo_que_no_es_imagen_es_rechazado` | Un archivo que no es imagen es rechazado | 1 | Pasa |

---

## Núcleo — `apps/core`

### `test_auditoria.py`

El registro de auditoría: lo que queda escrito y lo que no se puede reescribir.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_registrar_completa_el_correo_del_actor` | Registrar completa el correo del actor | 1 | Pasa |
| `test_una_entrada_de_auditoria_no_se_puede_modificar` | Una entrada de auditoria no se puede modificar | 1 | Pasa |
| `test_una_entrada_de_auditoria_no_se_puede_borrar` | Una entrada de auditoria no se puede borrar | 1 | Pasa |
| `test_la_traza_sobrevive_a_la_baja_del_usuario` | La traza sobrevive a la baja del usuario | 1 | Pasa |

### `test_componentes.py`

Los controles de formulario del modo operativo están todos vestidos.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_la_hoja_de_estilo_cubre_algo` | Si la lectura del archivo dejara de encontrar selectores, el test de abajo pasaría solo y no probaría nada. | 1 | Pasa |
| `test_ninguna_pantalla_operativa_dibuja_un_control_sin_estilo` | Ninguna pantalla operativa dibuja un control sin estilo | 1 | Pasa |
| `test_la_pantalla_de_alta_usa_los_tipos_que_habian_quedado_sin_estilo` | El caso que originó el problema: número, fecha y área de texto. | 1 | Pasa |
| `test_el_area_de_texto_tambien_esta_cubierta` | El area de texto tambien esta cubierta | 1 | Pasa |
| `test_las_pantallas_operativas_traen_los_componentes_propios` | La vista previa de la imagen elegida se arma con JavaScript y se conserva. | 1 | Pasa |
| `test_los_campos_obligatorios_se_marcan_solos` | El asterisco sale de `field.required`, no de un dato escrito a mano. | 1 | Pasa |
| `test_las_pantallas_de_producto_dibujan_el_campo_de_portada` | Las pantallas de producto dibujan el campo de portada | 1 | Pasa |
| `test_el_selector_de_etiquetas_dibuja_el_select_real` | Lo que viaja en el POST es el `<select multiple>`: el buscador con fichas se arma encima. | 1 | Pasa |
| `test_el_selector_de_etiquetas_trae_las_etiquetas_como_opciones` | El `<select>` salía vacío en el alta no editorial y en las dos ediciones: el formulario le cambiaba el widget **después** de asignarle el queryset, y el widget nuevo quedaba sin opciones. | 1 | Pasa |
| `test_los_desplegables_son_nativos_y_el_propio_solo_falta_base_select` | B-00-011: el formulario dibuja el `<select>` nativo, que es el que envía el valor y el que leen los guiones. | 1 | Pasa |
| `test_los_cuatro_niveles_estan_definidos` | Los cuatro niveles estan definidos | 1 | Pasa |
| `test_el_nivel_3_vive_solo_donde_hay_filas` | Su presencia comunica algo concreto. | 1 | Pasa |
| `test_ninguna_pantalla_repite_el_boton_principal` | Uno por pantalla. | 1 | Pasa |
| `test_el_boton_de_texto_no_lleva_copia_y_antepone_la_flecha_al_volver` | La copia en `data-texto` sólo servía para el barrido de color, que se retiró. | 1 | Pasa |

### `test_configuracion_del_modelo.py`

La configuración del modelo de lenguaje, y el diagnóstico de sus fallos.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_una_respuesta_buena_trae_los_datos` | Una respuesta buena trae los datos | 1 | Pasa |
| `test_sin_conexion_se_distingue_de_un_rechazo` | Sin conexion se distingue de un rechazo | 1 | Pasa |
| `test_un_rechazo_conserva_el_codigo` | Es lo que antes se perdía: el servidor **contestó**, y contestó que no. | 1 | Pasa |
| `test_el_cuerpo_del_error_se_conserva` | Los proveedores explican ahí por qué rechazaron, y sin leerlo el diagnóstico se queda en el número. | 1 | Pasa |
| `test_una_respuesta_que_no_es_json_se_distingue` | Pasa cuando la dirección apunta a algo que no es la API que se cree: es un problema de configuración, no de red. | 1 | Pasa |
| `test_los_catalogos_siguen_recibiendo_json_o_nada` | `pedir_json` descarta el diagnóstico a propósito: un catálogo tiene respaldo local y hace lo mismo sea cual sea el motivo. | 1 | Pasa |
| `test_el_pedido_usa_la_configuracion_guardada` | Cambiar de proveedor desde la pantalla tiene que surtir efecto sin reiniciar el servidor: para eso existe la pantalla. | 1 | Pasa |
| `test_sin_clave_no_se_manda_la_cabecera` | Un servidor local no la pide, y algunos rechazan el pedido si llega vacía. | 1 | Pasa |
| `test_el_chequeo_de_estado_manda_la_credencial` | Antes iba sin ella, y contra un proveedor que la exige en el catálogo de modelos la pantalla informaba "caído" con el servicio vivo. | 1 | Pasa |
| `test_una_clave_vencida_no_se_reporta_como_servicio_caido` | Es el fallo más probable con un proveedor remoto, y el que peor se diagnostica desde un mensaje genérico. | 1 | Pasa |
| `test_sin_credito_se_dice_con_todas_las_letras` | Sin credito se dice con todas las letras | 1 | Pasa |
| `test_el_limite_de_pedidos_se_explica` | 429 es lo habitual con los modelos gratuitos, y sin traducirlo la pantalla muestra un número. | 1 | Pasa |
| `test_un_modelo_inexistente_muestra_el_motivo_del_proveedor` | Mensaje real de OpenRouter al pedirle un identificador que no existe. | 1 | Pasa |
| `test_una_extraccion_rechazada_no_se_confunde_con_el_servicio_caido` | Una extraccion rechazada no se confunde con el servicio caido | 1 | Pasa |
| `test_un_error_del_proveedor_con_codigo_200_se_reconoce` | Pasa con los modelos gratuitos hospedados: la pasarela contesta bien y el fallo es del modelo de arriba. | 1 | Pasa |
| `test_la_clave_se_muestra_enmascarada` | La clave se muestra enmascarada | 1 | Pasa |
| `test_sin_clave_no_hay_nada_que_enmascarar` | Sin clave no hay nada que enmascarar | 1 | Pasa |
| `test_la_direccion_del_catalogo_se_deduce_de_la_del_chat` | Funciona igual con LM Studio que con un proveedor remoto, porque `/v1/` es parte de la convención de la API que los dos implementan. | 1 | Pasa |

### `test_consola.py`

La salida de consola en ASCII.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_los_diacriticos_se_sacan_conservando_la_lectura` | Se descompone y se quitan las tildes en vez de reemplazar la letra entera: "Tankobon" se lee, "T?nk?bon" no. | 4 | Pasa |
| `test_lo_que_no_tiene_equivalente_se_reemplaza_sin_romper` | Un kanji no se puede transcribir. | 1 | Pasa |
| `test_el_resultado_siempre_se_puede_escribir_en_la_consola` | La garantía que el módulo entero existe para dar. | 1 | Pasa |
| `test_un_valor_vacio_no_rompe` | Un asunto ausente es normal; que el comando explote por eso, no. | 2 | Pasa |

### `test_contratos_07_tienda.py`

Pruebas de contrato del módulo 07 · Tienda online (CU-TDA-CAT).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO176_por_defecto_activos_con_stock_de_lo_mas_nuevo_a_lo_mas_viejo` | CO176 por defecto activos con stock de lo mas nuevo a lo mas viejo | 1 | Pasa |
| `test_CO176_descatalogados_cancelados_y_para_adultos_no_se_ven_bajo_ningun_filtro` | CO176 descatalogados cancelados y para adultos no se ven bajo ningun filtro | 4 | Pasa |
| `test_CO176_los_filtros_de_estado` | CO176 los filtros de estado | 1 | Pasa |
| `test_CO176_busqueda_tipo_editorial_etiqueta_y_precio` | CO176 busqueda tipo editorial etiqueta y precio | 1 | Pasa |
| `test_CO176_E1_sin_resultados_ofrece_limpiar_los_filtros` | CO176 E1 sin resultados ofrece limpiar los filtros | 1 | Pasa |
| `test_CO176_se_pagina_de_a_24` | CO176 se pagina de a 24 | 1 | Pasa |
| `test_CO177_la_ficha_ofrece_la_accion_de_su_estado` | CO177 la ficha ofrece la accion de su estado | 4 | Pasa |
| `test_CO177_un_producto_no_visible_responde_404` | CO177 un producto no visible responde 404 | 1 | Pasa |
| `test_CO177_volver_conserva_los_filtros` | CO177 volver conserva los filtros | 1 | Pasa |
| `test_el_catalogo_y_la_portada_son_publicos` | Precondición de `CO-176`; la portada, desde que se resolvió C-20. | 1 | Pasa |
| `test_la_identidad_nace_con_los_valores_de_vineta_nocturna` | La identidad nace con los valores de vineta nocturna | 1 | Pasa |
| `test_un_secundario_ilegible_sobre_el_fondo_se_rechaza` | Un secundario ilegible sobre el fondo se rechaza | 1 | Pasa |
| `test_el_texto_sobre_el_primario_lo_elige_el_sistema` | El texto sobre el primario lo elige el sistema | 1 | Pasa |

### `test_contratos_16_auditoria.py`

Pruebas de contrato del módulo 16 · Auditoría (CU-AUD-CON).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO205_consultar_log_de_a_50_de_la_mas_reciente_a_la_mas_antigua` | CO205 consultar log de a 50 de la mas reciente a la mas antigua | 1 | Pasa |
| `test_CO205_filtra_por_actor_accion_entidad_rol_y_fechas` | CO205 filtra por actor accion entidad rol y fechas | 1 | Pasa |
| `test_CO205_un_rango_de_fechas_sin_entradas_lo_dice` | CO205 un rango de fechas sin entradas lo dice | 1 | Pasa |
| `test_CO206_el_detalle_presenta_la_entrada_completa` | CO206 el detalle presenta la entrada completa | 1 | Pasa |
| `test_CO129_exportar_trae_todo_el_filtro_y_no_solo_la_pagina` | CO129 exportar trae todo el filtro y no solo la pagina | 1 | Pasa |
| `test_CO129_las_celdas_no_se_interpretan_como_formulas` | CO129 las celdas no se interpretan como formulas | 1 | Pasa |
| `test_el_log_no_admite_escritura_ni_para_el_administrador` | El log no admite escritura ni para el administrador | 4 | Pasa |
| `test_el_rol_equivocado_no_consulta_ni_exporta` | El rol equivocado no consulta ni exporta | 2 | Pasa |
| `test_sin_sesion_va_al_login` | Sin sesion va al login | 1 | Pasa |

### `test_contratos_17_contenido.py`

Pruebas de contrato del módulo 17 · contenido de la tienda.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_RNF05_un_banner_grande_se_guarda_solo_en_webp_con_1920_de_lado_mayor` | RNF05 un banner grande se guarda solo en webp con 1920 de lado mayor | 1 | Pasa |
| `test_RNF05_por_defecto_el_lado_mayor_es_800` | RNF05 por defecto el lado mayor es 800 | 1 | Pasa |
| `test_RNF05_una_imagen_invalida_informa_el_problema_especifico` | RNF05 una imagen invalida informa el problema especifico | 2 | Pasa |
| `test_RNF05_una_imagen_que_excede_el_tamano_se_rechaza` | RNF05 una imagen que excede el tamano se rechaza | 1 | Pasa |
| `test_CO210_consultar_faq_presenta_lo_publicado_en_el_editor` | CO210 consultar faq presenta lo publicado en el editor | 1 | Pasa |
| `test_CO135_publicar_reemplaza_el_contenido_y_queda_en_la_tienda` | CO135 publicar reemplaza el contenido y queda en la tienda | 1 | Pasa |
| `test_CO135_la_vista_previa_no_publica` | CO135 la vista previa no publica | 1 | Pasa |
| `test_CO135_el_markdown_se_publica_sin_html_crudo` | C-16: lo que el Administrador escribe no puede inyectar guiones. | 1 | Pasa |
| `test_CO135_vacio_no_publica_sin_confirmacion` | CO135 vacio no publica sin confirmacion | 1 | Pasa |
| `test_CO136_confirmar_la_faq_vacia_la_deja_en_blanco` | CO136 confirmar la faq vacia la deja en blanco | 1 | Pasa |
| `test_CO132_agregar_banner_lo_pone_al_final_procesado_y_publicado` | CO132 agregar banner lo pone al final procesado y publicado | 1 | Pasa |
| `test_CO132_E1_una_imagen_invalida_no_agrega_nada` | CO132 E1 una imagen invalida no agrega nada | 1 | Pasa |
| `test_CO209_consultar_banners_en_orden_con_la_vista_previa` | CO209 consultar banners en orden con la vista previa | 1 | Pasa |
| `test_CO133_mover_un_banner_reajusta_a_los_demas` | CO133 mover un banner reajusta a los demas | 1 | Pasa |
| `test_CO133_reemplazar_la_imagen_conserva_la_posicion_y_borra_la_anterior` | CO133 reemplazar la imagen conserva la posicion y borra la anterior | 1 | Pasa |
| `test_CO133_E1_imagen_invalida_no_registra_tampoco_la_posicion` | CO133 E1 imagen invalida no registra tampoco la posicion | 1 | Pasa |
| `test_CO133_la_posicion_fuera_de_rango_se_rechaza` | CO133 la posicion fuera de rango se rechaza | 1 | Pasa |
| `test_CO134_eliminar_reajusta_y_conserva_el_orden_relativo` | CO134 eliminar reajusta y conserva el orden relativo | 1 | Pasa |
| `test_CO134_sin_confirmacion_no_hay_eliminacion` | CU-CFG-BNB A1: abrir la confirmación y volver. | 1 | Pasa |
| `test_el_carrusel_tiene_anterior_siguiente_y_pausar` | `identidad_visual.md`: un contenido que cambia solo debe poder detenerse. | 1 | Pasa |
| `test_CO208_consultar_identidad_presenta_los_valores_actuales` | CO208 consultar identidad presenta los valores actuales | 1 | Pasa |
| `test_CO131_actualizar_identidad_aplica_a_la_tienda_y_audita_lo_anterior` | CO131 actualizar identidad aplica a la tienda y audita lo anterior | 1 | Pasa |
| `test_CO131_E1_un_hex_invalido_no_aplica_ningun_cambio` | CO131 E1 un hex invalido no aplica ningun cambio | 1 | Pasa |
| `test_CO131_el_nombre_y_el_correo_son_obligatorios` | CO131 el nombre y el correo son obligatorios | 1 | Pasa |
| `test_CO131_E2_una_imagen_invalida_se_descarta_y_no_aplica_nada` | CO131 E2 una imagen invalida se descarta y no aplica nada | 1 | Pasa |
| `test_CO131_el_fondo_puede_ser_una_imagen` | C-07: el fondo de la tienda puede ser imagen. | 1 | Pasa |
| `test_CO131_la_tienda_carga_la_hoja_sin_cambiar_el_backoffice` | CO131 la tienda carga la hoja sin cambiar el backoffice | 1 | Pasa |
| `test_el_intervalo_del_carrusel_nace_en_10_y_se_edita_en_parametros` | El intervalo del carrusel nace en 10 y se edita en parametros | 1 | Pasa |
| `test_el_intervalo_no_puede_ser_cero` | El intervalo no puede ser cero | 1 | Pasa |
| `test_el_cajero_no_edita_el_contenido_de_la_tienda` | El cajero no edita el contenido de la tienda | 4 | Pasa |
| `test_CO131_la_imagen_del_ingreso_se_procesa_y_se_audita` | B-07-020: la imagen que acompaña a las pantallas de acceso, en la identidad. | 1 | Pasa |
| `test_CO131_quitar_el_logo_y_la_imagen_del_ingreso_vuelve_a_lo_predeterminado` | B-07-025: las dos imágenes se pueden quitar; la tienda vuelve a su vista predeterminada y la auditoría lo dice. | 1 | Pasa |

### `test_correo.py`

Los correos salen de verdad, dejan copia en la consola y llevan el estilo del sistema.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_la_paleta_de_los_correos_es_la_de_los_tokens` | La paleta de los correos es la de los tokens | 1 | Pasa |
| `test_los_estilos_solo_usan_colores_de_la_paleta` | Los estilos solo usan colores de la paleta | 1 | Pasa |
| `test_la_plantilla_de_correo_no_escribe_colores_ni_carga_recursos` | La plantilla de correo no escribe colores ni carga recursos | 1 | Pasa |
| `test_el_nombre_y_el_contacto_de_la_tienda_firman_el_correo` | El nombre y el contacto de la tienda firman el correo | 1 | Pasa |
| `test_la_activacion_lleva_la_version_con_estilo_y_el_mismo_enlace` | La activacion lleva la version con estilo y el mismo enlace | 1 | Pasa |
| `test_la_recuperacion_lleva_la_version_con_estilo_y_el_mismo_enlace` | La recuperacion lleva la version con estilo y el mismo enlace | 1 | Pasa |
| `test_la_bienvenida_lleva_la_version_con_estilo` | La bienvenida lleva la version con estilo | 1 | Pasa |
| `test_el_aviso_de_bloqueo_lleva_la_version_con_estilo` | El aviso de bloqueo lleva la version con estilo | 1 | Pasa |
| `test_el_pedido_va_en_tabla_y_escapa_lo_que_escribe_el_usuario` | El pedido va en tabla y escapa lo que escribe el usuario | 1 | Pasa |
| `test_ninguna_linea_del_correo_pasa_el_limite_del_protocolo` | Una línea de más de 998 caracteres obliga a recodificar la parte entera. | 1 | Pasa |
| `test_sin_servidor_el_correo_queda_solo_en_la_consola` | Sin servidor el correo queda solo en la consola | 1 | Pasa |
| `test_con_servidor_sale_por_smtp_y_deja_la_copia` | Con servidor sale por smtp y deja la copia | 1 | Pasa |
| `test_un_fallo_del_servidor_levanta_y_la_copia_igual_queda` | Un fallo del servidor levanta y la copia igual queda | 1 | Pasa |
| `test_sin_mensajes_no_hace_nada` | Sin mensajes no hace nada | 1 | Pasa |
| `test_el_pedido_reintenta_cuando_el_servidor_real_falla` | El pedido reintenta cuando el servidor real falla | 1 | Pasa |

### `test_cotizaciones.py`

Cotización del peso frente a las monedas con las que se importa.

**Casos de prueba que ejecuta:** CP-04.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_dolar_sale_directo_de_la_paridad_contra_el_peso` | El dolar sale directo de la paridad contra el peso | 1 | Pasa |
| `test_el_euro_y_el_yen_salen_por_paridad_cruzada` | 1500 pesos por dólar y 0,8 euros por dólar dan 1875 pesos por euro. | 1 | Pasa |
| `test_solo_se_ofrecen_las_tres_monedas_del_negocio` | El servicio devuelve 160 monedas; el desplegable ofrece tres. | 1 | Pasa |
| `test_el_peso_vale_un_peso_sin_consultar_nada` | La moneda local no depende de que ningún servicio esté en línea. | 1 | Pasa |
| `test_una_respuesta_sin_exito_se_trata_como_caida` | Una respuesta sin exito se trata como caida | 1 | Pasa |
| `test_una_respuesta_sin_la_paridad_del_peso_no_sirve` | Una respuesta sin la paridad del peso no sirve | 1 | Pasa |
| `test_una_paridad_rota_no_genera_una_cotizacion` | Un cero o un negativo no son un dato: son una respuesta rota. | 4 | Pasa |
| `test_una_moneda_rota_se_descarta_sin_tirar_abajo_las_otras` | Una moneda rota se descarta sin tirar abajo las otras | 1 | Pasa |
| `test_la_segunda_consulta_sale_de_la_cache` | La segunda consulta sale de la cache | 1 | Pasa |
| `test_si_la_api_no_responde_se_usa_el_respaldo_local` | Si la api no responde se usa el respaldo local | 1 | Pasa |
| `test_el_respaldo_versionado_tiene_las_tres_monedas_y_su_fecha` | El respaldo versionado tiene las tres monedas y su fecha | 1 | Pasa |
| `test_una_cotizacion_de_hace_meses_se_marca_como_desactualizada` | El aviso existe porque un tipo de cambio viejo no es como una provincia vieja: usarlo sin mirarlo deja mal el precio de todo el lote. | 1 | Pasa |
| `test_una_cotizacion_de_hoy_no_se_marca_como_desactualizada` | Una cotizacion de hoy no se marca como desactualizada | 1 | Pasa |
| `test_sin_ninguna_cotizacion_se_considera_desactualizada` | Ante la duda, se avisa: es preferible una revisión de más que un precio calculado con un dato que nadie sabe de cuándo es. | 1 | Pasa |
| `test_el_resumen_para_la_pantalla_trae_todo_masticado` | El resumen para la pantalla trae todo masticado | 1 | Pasa |
| `test_el_comando_reescribe_el_respaldo` | El comando reescribe el respaldo | 1 | Pasa |
| `test_el_comando_no_pisa_el_respaldo_si_la_api_falla` | El comando no pisa el respaldo si la api falla | 1 | Pasa |
| `test_las_cabeceras_de_las_integraciones_son_ascii` | Un valor de cabecera HTTP viaja en ASCII. | 1 | Pasa |

### `test_estilo_vineta.py`

Viñeta Nocturna no se degrada sin que nadie lo note.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_los_tokens_del_sistema_son_los_del_responsable` | `TOKENS_VISUALES.md`: «Este documento y ese archivo dicen lo mismo». | 1 | Pasa |
| `test_las_fuentes_estan_autoalojadas` | Las fuentes estan autoalojadas | 1 | Pasa |
| `test_la_hoja_de_componentes_no_escribe_colores` | Los componentes leen semánticos; los valores viven en `tokens.css`. | 1 | Pasa |
| `test_la_hoja_de_componentes_no_usa_nada_de_lo_prohibido` | La hoja de componentes no usa nada de lo prohibido | 1 | Pasa |
| `test_las_sombras_son_duras` | Sin desenfoque: el tercer largo de toda sombra es 0, o es un token. | 1 | Pasa |
| `test_solo_hay_animaciones_del_catalogo` | Solo hay animaciones del catalogo | 1 | Pasa |
| `test_el_movimiento_reducido_esta_declarado` | El movimiento reducido esta declarado | 1 | Pasa |
| `test_el_modo_operativo_no_lee_las_variables_de_la_tienda` | El modo operativo no lee las variables de la tienda | 1 | Pasa |
| `test_la_plantilla_no_trae_estilo_propio` | La plantilla no trae estilo propio | 1 | Pasa |
| `test_el_sticker_no_aparece_en_el_mostrador` | Bangers, «nunca en el operativo». | 1 | Pasa |
| `test_los_archivos_del_sistema_anterior_ya_no_estan` | Los archivos del sistema anterior ya no estan | 1 | Pasa |

### `test_filas_portada.py`

Las filas de la portada de la tienda (plan 07, tercera y cuarta parte).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_administrador_agrega_una_fila_de_etiqueta_y_otra_de_grupo` | El administrador agrega una fila de etiqueta y otra de grupo | 1 | Pasa |
| `test_una_fila_sin_origen_se_rechaza_y_no_se_guarda_nada` | Una fila sin origen se rechaza y no se guarda nada | 1 | Pasa |
| `test_eliminar_una_fila` | Eliminar una fila | 1 | Pasa |
| `test_guardar_sin_cambios_no_audita` | Guardar sin cambios no audita | 1 | Pasa |
| `test_solo_el_administrador_configura_las_filas` | Solo el administrador configura las filas | 2 | Pasa |
| `test_la_portada_muestra_las_filas_en_su_orden_con_sus_productos` | La portada muestra las filas en su orden con sus productos | 1 | Pasa |
| `test_la_fila_trae_hasta_doce_y_sin_lo_que_la_tienda_no_muestra` | La fila trae hasta doce y sin lo que la tienda no muestra | 1 | Pasa |
| `test_no_se_dibujan_las_filas_vacias_inactivas_o_de_etiquetas_dadas_de_baja` | No se dibujan las filas vacias inactivas o de etiquetas dadas de baja | 1 | Pasa |
| `test_el_catalogo_filtra_por_grupo_para_el_ver_todo` | El catalogo filtra por grupo para el ver todo | 1 | Pasa |
| `test_reordenar_las_tarjetas_cambia_el_orden_y_se_audita` | Reordenar las tarjetas cambia el orden y se audita | 1 | Pasa |
| `test_la_imagen_de_la_fila_se_guarda_procesada_y_se_audita` | La imagen de la fila se guarda procesada y se audita | 1 | Pasa |
| `test_un_archivo_que_no_es_imagen_se_rechaza_y_no_se_guarda_nada` | Un archivo que no es imagen se rechaza y no se guarda nada | 1 | Pasa |
| `test_quitar_la_imagen_de_una_fila` | Quitar la imagen de una fila | 1 | Pasa |
| `test_el_gestor_trae_la_tarjeta_vacia_para_agregar_y_los_mandos` | El gestor trae la tarjeta vacia para agregar y los mandos | 1 | Pasa |
| `test_el_pie_lleva_las_filas_activas_al_catalogo` | La cinta de accesos se quitó (B-07-021): los accesos quedan en el pie. | 1 | Pasa |
| `test_el_encabezado_busca_en_el_catalogo` | El encabezado busca en el catalogo | 1 | Pasa |
| `test_el_globo_de_ayuda_aparece_si_hay_preguntas_publicadas` | El globo de ayuda aparece si hay preguntas publicadas | 1 | Pasa |
| `test_la_fila_abre_con_su_imagen_o_con_el_abanico_de_portadas` | La fila abre con su imagen o con el abanico de portadas | 1 | Pasa |

### `test_georef.py`

Integración con georef-ar-api: caché, respaldo y degradación.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_las_provincias_salen_de_la_api_ordenadas` | Las provincias salen de la api ordenadas | 1 | Pasa |
| `test_la_segunda_consulta_sale_de_la_cache` | No se castiga a un servicio público gratuito con una consulta por visita. | 1 | Pasa |
| `test_si_la_api_no_responde_se_usa_el_respaldo_local` | El registro no puede depender de que un tercero esté en línea. | 1 | Pasa |
| `test_el_respaldo_se_cachea_por_menos_tiempo_que_la_api` | Si el servicio vuelve enseguida, no seguimos un día con la foto vieja. | 1 | Pasa |
| `test_un_error_de_red_no_se_propaga` | `pedir_json` traga la excepción: la pantalla tiene que renderizar igual. | 1 | Pasa |
| `test_el_respaldo_versionado_tiene_las_veinticuatro_jurisdicciones` | El respaldo versionado tiene las veinticuatro jurisdicciones | 1 | Pasa |
| `test_las_localidades_se_devuelven_sin_repetir_y_ordenadas` | Las localidades se devuelven sin repetir y ordenadas | 1 | Pasa |
| `test_sin_provincia_no_se_consulta_la_api` | Sin provincia no se consulta la api | 1 | Pasa |
| `test_si_la_api_no_responde_las_localidades_quedan_vacias` | Se pierde la sugerencia, no la posibilidad de escribir la localidad. | 1 | Pasa |
| `test_la_cache_de_localidades_es_por_provincia` | La cache de localidades es por provincia | 1 | Pasa |
| `test_el_endpoint_de_localidades_es_publico` | El registro es público (CU-CLI-ALT): pedir localidades no puede exigir sesión. | 1 | Pasa |
| `test_el_endpoint_sin_provincia_devuelve_lista_vacia` | El endpoint sin provincia devuelve lista vacia | 1 | Pasa |
| `test_el_comando_reescribe_el_respaldo` | El comando reescribe el respaldo | 1 | Pasa |
| `test_el_comando_no_pisa_el_respaldo_si_la_api_falla` | Un respaldo vacío es peor que uno viejo: deja el formulario sin provincias. | 1 | Pasa |

### `test_inmutabilidad_auditoria_en_la_base.py`

I-13: una entrada del log no se modifica ni se borra, **por ningún camino**.

**Casos de prueba que ejecuta:** CP-22.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_I13_un_update_de_queryset_no_modifica_la_entrada` | I13 un update de queryset no modifica la entrada | 1 | Pasa |
| `test_I13_un_delete_de_queryset_no_borra_la_entrada` | I13 un delete de queryset no borra la entrada | 1 | Pasa |
| `test_I13_el_sql_directo_tampoco_puede` | I13 el sql directo tampoco puede | 3 | Pasa |
| `test_I13_eliminar_la_cuenta_del_actor_conserva_la_entrada_con_el_correo` | El `SET_NULL` de la clave foránea es la única escritura que la base admite. | 1 | Pasa |
| `test_I13_poner_en_nulo_el_actor_junto_con_otro_cambio_se_rechaza` | I13 poner en nulo el actor junto con otro cambio se rechaza | 1 | Pasa |
| `test_I13_las_altas_siguen_funcionando` | I13 las altas siguen funcionando | 1 | Pasa |

### `test_paises.py`

Catálogo de códigos telefónicos de país.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_los_paises_salen_de_la_api_ordenados_por_nombre` | Los paises salen de la api ordenados por nombre | 1 | Pasa |
| `test_una_fila_sin_codigo_se_descarta_sin_romper_el_resto` | Una fila sin codigo se descarta sin romper el resto | 1 | Pasa |
| `test_el_codigo_se_recorta_al_primer_grupo_de_digitos` | "+1 684" es Estados Unidos con un área adentro: el país es "+1". | 1 | Pasa |
| `test_una_respuesta_con_error_se_trata_como_caida` | Una respuesta con error se trata como caida | 1 | Pasa |
| `test_la_segunda_consulta_sale_de_la_cache` | La segunda consulta sale de la cache | 1 | Pasa |
| `test_si_la_api_no_responde_se_usa_el_respaldo_local` | Si la api no responde se usa el respaldo local | 1 | Pasa |
| `test_todos_los_codigos_del_respaldo_entran_en_el_campo` | `Usuario.telefono_pais` tiene `max_length=4`: "+999" es el tope. | 1 | Pasa |
| `test_el_comando_reescribe_el_respaldo` | El comando reescribe el respaldo | 1 | Pasa |
| `test_el_comando_no_pisa_el_respaldo_si_la_api_falla` | El comando no pisa el respaldo si la api falla | 1 | Pasa |

### `test_panel.py`

Tablero de entrada del Administrador y menú lateral del backoffice.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_las_cifras_cuentan_cada_estado_por_separado` | Las cifras cuentan cada estado por separado | 1 | Pasa |
| `test_muestra_la_actividad_reciente_del_log` | Muestra la actividad reciente del log | 1 | Pasa |
| `test_la_actividad_se_recorta_a_las_ultimas_doce_entradas` | La actividad se recorta a las ultimas doce entradas | 1 | Pasa |
| `test_los_bloqueos_del_dia_se_muestran` | Los bloqueos del dia se muestran | 1 | Pasa |
| `test_sin_bloqueos_el_contador_esta_en_cero` | Sin bloqueos el contador esta en cero | 1 | Pasa |
| `test_solo_el_administrador_entra_al_panel` | Solo el administrador entra al panel | 2 | Pasa |
| `test_el_menu_lateral_enlaza_las_secciones_disponibles` | El menu lateral enlaza las secciones disponibles | 1 | Pasa |
| `test_el_menu_marca_la_pantalla_en_la_que_se_esta` | El menu marca la pantalla en la que se esta | 1 | Pasa |

### `test_permisos_por_rol.py`

RNF-03: el control de acceso por rol se valida siempre del lado del servidor.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_cada_rol_entra_a_su_propia_seccion` | Cada rol entra a su propia seccion | 1 | Pasa |
| `test_un_rol_que_no_corresponde_recibe_403` | Un request directo con el rol equivocado corta en 403, sin datos parciales. | 4 | Pasa |
| `test_sin_sesion_redirige_al_login` | Sin sesion redirige al login | 2 | Pasa |

### `test_plantillas.py`

Reglas que tienen que cumplir todas las plantillas del proyecto.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_hay_plantillas_para_revisar` | Si el recorrido dejara de encontrar archivos, el test de abajo pasaría solo. | 1 | Pasa |
| `test_ninguna_plantilla_usa_comentarios_de_varias_lineas` | Ninguna plantilla usa comentarios de varias lineas | 1 | Pasa |
| `test_las_pantallas_publicas_se_renderizan_sin_sesion` | Humo: las tres pantallas públicas cargan enteras para un visitante. | 1 | Pasa |

### `test_portada_y_formato.py`

Los textos configurables de la portada (B-17-015) y el formato de los importes.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_los_importes_se_escriben_como_en_la_guia` | Los importes se escriben como en la guia | 5 | Pasa |
| `test_la_portada_muestra_los_textos_que_escribe_el_administrador` | La portada muestra los textos que escribe el administrador | 1 | Pasa |
| `test_un_texto_vacio_vuelve_a_su_valor_inicial` | Un texto vacio vuelve a su valor inicial | 1 | Pasa |
| `test_sin_mensajes_el_ticker_anuncia_lo_ultimo_que_llego` | Sin mensajes el ticker anuncia lo ultimo que llego | 1 | Pasa |

### `test_respaldo.py`

El comando de respaldo de la base.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_deja_un_respaldo_con_la_fecha_en_el_nombre` | Deja un respaldo con la fecha en el nombre | 1 | Pasa |
| `test_crea_la_carpeta_si_no_existe` | Una tarea programada corre sin nadie mirando: si el destino no existe, tiene que crearlo y no fallar. | 1 | Pasa |
| `test_el_formato_es_el_propio_de_postgresql` | `custom` viene comprimido y permite restaurar una tabla sola; un `.sql` plano no permite ni lo uno ni lo otro. | 1 | Pasa |
| `test_no_espera_una_contrasena_por_teclado` | Sin `--no-password`, un respaldo mal configurado no falla: se cuelga esperando a alguien que en una tarea programada no está. | 1 | Pasa |
| `test_la_contrasena_no_va_en_los_argumentos` | Los argumentos de un proceso los lee cualquiera que liste procesos. | 1 | Pasa |
| `test_la_contrasena_va_por_el_entorno` | La contrasena va por el entorno | 1 | Pasa |
| `test_un_respaldo_ilegible_se_descarta` | `pg_dump` puede terminar en 0 y dejar el archivo truncado. | 1 | Pasa |
| `test_si_pg_dump_falla_no_queda_un_archivo_a_medias` | Si pg dump falla no queda un archivo a medias | 1 | Pasa |
| `test_un_pg_dump_mas_viejo_que_el_servidor_se_rechaza` | Se niega a volcar y el mensaje aparece justo cuando hace falta el respaldo. | 1 | Pasa |
| `test_sin_pg_restore_no_se_respalda` | Sin con qué verificar, el comando no genera nada: un respaldo sin verificar es la mitad del trabajo y toda la falsa tranquilidad. | 1 | Pasa |
| `test_conserva_los_mas_nuevos_y_borra_el_resto` | Conserva los mas nuevos y borra el resto | 1 | Pasa |
| `test_conservar_cero_no_borra_nada` | Conservar cero no borra nada | 1 | Pasa |
| `test_no_toca_lo_que_no_genero` | Borrar por antigüedad archivos ajenos es la peor forma de fallar que tiene un limpiador, y la carpeta puede tener cualquier cosa. | 1 | Pasa |
| `test_verificar_solo_no_genera_un_respaldo_nuevo` | Verificar solo no genera un respaldo nuevo | 1 | Pasa |
| `test_verificar_solo_avisa_si_alguno_esta_roto` | Verificar solo avisa si alguno esta roto | 1 | Pasa |
| `test_verificar_solo_con_la_carpeta_vacia_no_es_un_error` | Es el estado del primer día, y una tarea programada que devuelve error ese día manda a buscar un problema que no existe. | 1 | Pasa |
| `test_la_salida_es_ascii` | La consola de Windows corre en cp1252: un acento la hace reventar con el trabajo ya hecho y sin decir cuánto se procesó. | 1 | Pasa |

### `test_servir.py`

El comando que sirve el sistema en la demostración (`docs/despliegue/DEMOSTRACION.md`).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_escucha_solo_en_la_interfaz_local_por_defecto` | Del lado de afuera atiende el proxy con TLS; `waitress` no se expone. | 1 | Pasa |
| `test_el_puerto_y_los_hilos_se_pueden_cambiar` | El puerto y los hilos se pueden cambiar | 1 | Pasa |

### `test_tienda_quinta_parte.py`

La tienda pública, plan 07, quinta parte (B-07-013 a B-07-019, C-20).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO176_varios_tipos_a_la_vez_suman_productos` | CO176 varios tipos a la vez suman productos | 1 | Pasa |
| `test_CO176_etiquetas_del_mismo_grupo_suman_y_de_grupos_distintos_restringen` | CO176 etiquetas del mismo grupo suman y de grupos distintos restringen | 1 | Pasa |
| `test_CO176_los_estados_son_interruptores` | CO176 los estados son interruptores | 1 | Pasa |
| `test_CO176_proximos_a_llegar_ordena_por_la_fecha_vigente` | CO176 proximos a llegar ordena por la fecha vigente | 1 | Pasa |
| `test_CO176_con_parcial_responde_solo_los_resultados` | CO176 con parcial responde solo los resultados | 1 | Pasa |
| `test_el_panel_ofrece_solo_opciones_con_productos` | El panel ofrece solo opciones con productos | 1 | Pasa |
| `test_un_invitado_ve_la_portada` | Un invitado ve la portada | 1 | Pasa |
| `test_lo_que_se_viene_trae_las_pre_ventas_la_mas_proxima_primero` | Lo que se viene trae las pre ventas la mas proxima primero | 1 | Pasa |
| `test_sin_pre_ventas_no_hay_lo_que_se_viene` | Sin pre ventas no hay lo que se viene | 1 | Pasa |
| `test_carteles_de_tomo_1_y_de_novedad` | B-07-024: «¡TOMO 1!» en el tomo 1 de una serie; «¡NOVEDAD!» en lo que se dio de alta hace menos de treinta días y ya está a la venta. | 1 | Pasa |
| `test_la_tarjeta_ofrece_agregar_a_invitados_y_clientes_y_no_al_personal` | La tarjeta ofrece agregar a invitados y clientes y no al personal | 1 | Pasa |
| `test_CO083_agregar_desde_la_tarjeta_responde_json_con_las_unidades` | CO083 agregar desde la tarjeta responde json con las unidades | 1 | Pasa |
| `test_CO083_desde_la_tarjeta_el_tope_de_stock_se_avisa_igual` | CO083 desde la tarjeta el tope de stock se avisa igual | 1 | Pasa |
| `test_CO083_el_personal_no_agrega_desde_la_tarjeta` | CO083 el personal no agrega desde la tarjeta | 1 | Pasa |
| `test_las_pantallas_de_acceso_van_partidas_y_sin_distracciones` | Las pantallas de acceso van partidas y sin distracciones | 2 | Pasa |
| `test_el_acceso_muestra_la_imagen_del_ingreso_o_el_logo_o_el_nombre` | B-07-020: la imagen que carga el Administrador; sin ella, el logo; sin logo, el nombre de la tienda. | 1 | Pasa |
| `test_el_ticker_nombra_cada_serie_una_vez` | B-07-023: dos tomos de la misma serie recién llegados son un solo «Llegó». | 1 | Pasa |
| `test_el_menu_de_la_tienda_es_todo_texto` | B-07-027: los enlaces del menú público son rótulos, sin íconos. | 1 | Pasa |
| `test_CO084_cambiar_la_cantidad_devuelve_el_carrito_recalculado` | CO084 cambiar la cantidad devuelve el carrito recalculado | 1 | Pasa |
| `test_CO084_sin_stock_suficiente_se_topea_y_se_avisa` | CO084 sin stock suficiente se topea y se avisa | 1 | Pasa |
| `test_CO085_quitar_devuelve_el_carrito_sin_la_linea` | CO085 quitar devuelve el carrito sin la linea | 1 | Pasa |
| `test_sin_guion_el_carrito_sigue_con_su_boton` | Sin guion el carrito sigue con su boton | 1 | Pasa |
| `test_la_ficha_ofrece_mas_de_la_serie_en_orden` | La ficha ofrece mas de la serie en orden | 1 | Pasa |
| `test_un_tomo_solo_no_tiene_mas_de_la_serie` | Un tomo solo no tiene mas de la serie | 1 | Pasa |
| `test_las_filas_no_llevan_contador_y_la_busqueda_tiene_atajo` | Las filas no llevan contador y la busqueda tiene atajo | 1 | Pasa |

### `test_volumen_consultas.py`

D5-04 · Volumen sin degradación: cada listado paginado hace las mismas consultas con pocos registros que con muchos (plan 00).

**Casos de prueba que ejecuta:** CP-28.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_listado_no_hace_mas_consultas_con_mas_registros` | El listado no hace mas consultas con mas registros | 1 | Pasa |
| `test_el_catalogo_publico_no_hace_mas_consultas_con_mas_productos` | El catalogo publico no hace mas consultas con mas productos | 1 | Pasa |

---

## devoluciones — `apps/devoluciones`

### `test_acceso_y_concurrencia_devoluciones.py`

Acceso a las devoluciones por la dirección real, y resoluciones a la vez.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_acceso_solo_el_administrador_consulta_y_resuelve_casos` | Acceso solo el administrador consulta y resuelve casos | 2 | Pasa |
| `test_acceso_sin_sesion_las_devoluciones_llevan_al_ingreso` | Acceso sin sesion las devoluciones llevan al ingreso | 1 | Pasa |
| `test_acceso_el_personal_no_abre_reclamos_desde_mi_cuenta` | Acceso el personal no abre reclamos desde mi cuenta | 2 | Pasa |
| `test_acceso_la_foto_la_ven_el_administrador_y_su_cliente_y_nadie_mas` | Acceso la foto la ven el administrador y su cliente y nadie mas | 1 | Pasa |
| `test_acceso_la_foto_no_tiene_direccion_publica` | Acceso la foto no tiene direccion publica | 1 | Pasa |
| `test_acceso_el_menu_del_administrador_lleva_a_devoluciones` | Acceso el menu del administrador lleva a devoluciones | 1 | Pasa |
| `test_concurrencia_dos_administradores_que_resuelven_el_mismo_caso_registran_uno` | Concurrencia dos administradores que resuelven el mismo caso registran uno | 1 | Pasa |
| `test_concurrencia_dos_cambios_por_la_ultima_unidad_autorizan_uno` | Concurrencia dos cambios por la ultima unidad autorizan uno | 1 | Pasa |
| `test_concurrencia_dos_pestanas_que_reclaman_el_mismo_articulo_abren_un_caso` | Concurrencia dos pestanas que reclaman el mismo articulo abren un caso | 1 | Pasa |
| `test_un_caso_inexistente_responde_404_en_todas_sus_pantallas` | Un caso inexistente responde 404 en todas sus pantallas | 1 | Pasa |
| `test_un_caso_ya_resuelto_no_ofrece_ni_admite_otra_resolucion` | Un caso ya resuelto no ofrece ni admite otra resolucion | 1 | Pasa |
| `test_el_cambio_sin_producto_elegido_no_registra_nada` | El cambio sin producto elegido no registra nada | 1 | Pasa |
| `test_el_cambio_por_un_producto_sin_stock_vuelve_a_la_busqueda` | El cambio por un producto sin stock vuelve a la busqueda | 1 | Pasa |
| `test_el_rechazo_desde_la_pantalla_avisa_y_vuelve_a_la_ficha` | El rechazo desde la pantalla avisa y vuelve a la ficha | 1 | Pasa |
| `test_una_foto_que_falta_en_el_almacenamiento_responde_404` | Una foto que falta en el almacenamiento responde 404 | 1 | Pasa |
| `test_un_filtro_desconocido_muestra_los_pendientes` | Un filtro desconocido muestra los pendientes | 1 | Pasa |

### `test_arrepentimiento_y_garantia.py`

Las devoluciones reformuladas (plan 00, C1).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_boton_esta_en_la_cabecera_de_la_tienda` | El boton esta en la cabecera de la tienda | 1 | Pasa |
| `test_CO185_sin_sesion_el_numero_y_el_correo_de_la_compra_abren_el_pedido` | CO185 sin sesion el numero y el correo de la compra abren el pedido | 1 | Pasa |
| `test_CO185_un_correo_que_no_coincide_no_revela_el_pedido` | CO185 un correo que no coincide no revela el pedido | 1 | Pasa |
| `test_CO185_con_sesion_el_cliente_ve_sus_compras_dentro_del_plazo` | CO185 con sesion el cliente ve sus compras dentro del plazo | 1 | Pasa |
| `test_CO099_arrepentirse_abre_un_caso_por_linea_con_la_linea_entera_y_sin_fotos` | CO099 arrepentirse abre un caso por linea con la linea entera y sin fotos | 1 | Pasa |
| `test_CO099_el_arrepentimiento_es_solo_para_compras_online` | CO099 el arrepentimiento es solo para compras online | 1 | Pasa |
| `test_CO099_E1_los_dos_plazos_son_independientes` | CO099 E1 los dos plazos son independientes | 1 | Pasa |
| `test_CO099_un_arrepentimiento_y_una_garantia_no_conviven_en_la_misma_linea` | CO099 un arrepentimiento y una garantia no conviven en la misma linea | 1 | Pasa |
| `test_CO101_el_arrepentimiento_se_reembolsa_por_el_medio_de_pago_y_vuelve_al_stock` | CO101 el arrepentimiento se reembolsa por el medio de pago y vuelve al stock | 1 | Pasa |
| `test_CO101_arrepentirse_del_pedido_entero_reintegra_tambien_el_envio` | CO101 arrepentirse del pedido entero reintegra tambien el envio | 1 | Pasa |
| `test_CO101_el_reembolso_por_el_medio_descuenta_los_puntos_ganados` | CO101 el reembolso por el medio descuenta los puntos ganados | 1 | Pasa |
| `test_CO101_lo_pagado_con_puntos_vuelve_en_puntos_y_no_por_el_medio` | CO101 lo pagado con puntos vuelve en puntos y no por el medio | 1 | Pasa |
| `test_CO101_en_el_mostrador_no_hay_reembolso_por_el_medio` | CO101 en el mostrador no hay reembolso por el medio | 1 | Pasa |
| `test_CO100_el_arrepentimiento_no_admite_cambio_ni_en_el_servicio_ni_en_la_base` | CO100 el arrepentimiento no admite cambio ni en el servicio ni en la base | 1 | Pasa |
| `test_CO100_el_reemplazo_tiene_que_ser_de_la_misma_editorial_y_formato` | CO100 el reemplazo tiene que ser de la misma editorial y formato | 1 | Pasa |
| `test_la_ficha_del_caso_muestra_el_contacto_y_solo_las_resoluciones_que_admite` | La ficha del caso muestra el contacto y solo las resoluciones que admite | 1 | Pasa |
| `test_acceso_el_cajero_no_registra_un_reembolso_por_el_medio` | Acceso el cajero no registra un reembolso por el medio | 1 | Pasa |
| `test_flujo_el_invitado_se_arrepiente_y_el_local_reembolsa` | Flujo el invitado se arrepiente y el local reembolsa | 1 | Pasa |
| `test_el_plazo_de_garantia_se_configura_en_parametros` | El plazo de garantia se configura en parametros | 1 | Pasa |

### `test_contratos_09_devoluciones.py`

Contratos de devoluciones (plan 09).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO185_presenta_los_articulos_sin_reclamo_y_los_motivos_sin_modificar_nada` | CO185 presenta los articulos sin reclamo y los motivos sin modificar nada | 1 | Pasa |
| `test_CO185_E1_vencido_el_plazo_informa_y_no_abre_el_formulario` | CO185 E1 vencido el plazo informa y no abre el formulario | 1 | Pasa |
| `test_CO185_E2_con_todos_los_articulos_reclamados_informa_el_caso_y_su_estado` | CO185 E2 con todos los articulos reclamados informa el caso y su estado | 1 | Pasa |
| `test_CO185_no_ofrece_las_lineas_canceladas_ni_las_de_despacho_diferido` | CO185 no ofrece las lineas canceladas ni las de despacho diferido | 1 | Pasa |
| `test_CO185_un_pedido_sin_despachar_no_admite_reclamo` | CO185 un pedido sin despachar no admite reclamo | 1 | Pasa |
| `test_CO099_crea_el_caso_pendiente_con_sus_datos` | CO099 crea el caso pendiente con sus datos | 1 | Pasa |
| `test_CO099_el_caso_queda_asociado_a_la_linea_reclamada` | CO099 el caso queda asociado a la linea reclamada | 1 | Pasa |
| `test_CO099_guarda_cada_foto_convertida_a_webp_fuera_de_la_carpeta_publica` | CO099 guarda cada foto convertida a webp fuera de la carpeta publica | 1 | Pasa |
| `test_CO099_confirma_al_cliente_la_apertura` | CO099 confirma al cliente la apertura | 1 | Pasa |
| `test_CO099_avisa_al_administrador_del_caso_nuevo` | CO099 avisa al administrador del caso nuevo | 1 | Pasa |
| `test_CO099_registra_la_apertura_con_el_actor_y_el_momento` | CO099 registra la apertura con el actor y el momento | 1 | Pasa |
| `test_CO099_E1_vencido_el_plazo_no_registra_nada` | CO099 E1 vencido el plazo no registra nada | 1 | Pasa |
| `test_CO099_el_plazo_corre_desde_el_despacho_con_el_parametro_vigente` | CO099 el plazo corre desde el despacho con el parametro vigente | 1 | Pasa |
| `test_CO099_E2_un_articulo_con_un_caso_rechazado_no_admite_otro` | CO099 E2 un articulo con un caso rechazado no admite otro | 1 | Pasa |
| `test_CO099_I19_la_base_no_admite_dos_casos_sobre_la_misma_linea` | CO099 I19 la base no admite dos casos sobre la misma linea | 1 | Pasa |
| `test_CO099_E3_sin_fotos_no_registra_y_el_formulario_sigue_abierto` | CO099 E3 sin fotos no registra y el formulario sigue abierto | 1 | Pasa |
| `test_CO099_E4_un_archivo_que_no_es_imagen_se_descarta_con_el_problema_especifico` | CO099 E4 un archivo que no es imagen se descarta con el problema especifico | 1 | Pasa |
| `test_CO099_E4_una_foto_que_excede_el_tamano_maximo_se_rechaza` | CO099 E4 una foto que excede el tamano maximo se rechaza | 1 | Pasa |
| `test_CO099_E4_un_formato_no_aceptado_se_rechaza` | CO099 E4 un formato no aceptado se rechaza | 1 | Pasa |
| `test_CO099_mas_de_cinco_fotos_no_se_admiten` | CO099 mas de cinco fotos no se admiten | 1 | Pasa |
| `test_CO099_un_pedido_de_otro_cliente_responde_404` | CO099 un pedido de otro cliente responde 404 | 1 | Pasa |
| `test_CO186_lista_los_pendientes_mas_antiguos_primero_sin_modificar_nada` | CO186 lista los pendientes mas antiguos primero sin modificar nada | 1 | Pasa |
| `test_CO186_E2_sin_pendientes_muestra_el_panel_vacio_con_acceso_al_historial` | CO186 E2 sin pendientes muestra el panel vacio con acceso al historial | 1 | Pasa |
| `test_CO186_el_historial_muestra_los_resueltos_y_los_rechazados` | CO186 el historial muestra los resueltos y los rechazados | 1 | Pasa |
| `test_CO187_presenta_el_caso_con_sus_fotos_sin_modificar_nada` | CO187 presenta el caso con sus fotos sin modificar nada | 1 | Pasa |
| `test_CO100_el_caso_pasa_de_pendiente_a_resuelto_con_cambio` | CO100 el caso pasa de pendiente a resuelto con cambio | 1 | Pasa |
| `test_CO100_el_caso_queda_asociado_al_producto_de_reemplazo` | CO100 el caso queda asociado al producto de reemplazo | 1 | Pasa |
| `test_CO100_el_stock_del_reemplazo_baja_una_unidad` | CO100 el stock del reemplazo baja una unidad | 1 | Pasa |
| `test_CO100_el_reemplazo_que_llega_a_cero_pasa_a_agotado` | CO100 el reemplazo que llega a cero pasa a agotado | 1 | Pasa |
| `test_CO100_el_reemplazo_queda_a_nombre_del_cliente_en_el_stock_en_local` | CO100 el reemplazo queda a nombre del cliente en el stock en local | 1 | Pasa |
| `test_CO100_registra_la_resolucion_con_el_tipo_el_administrador_y_el_momento` | CO100 registra la resolucion con el tipo el administrador y el momento | 1 | Pasa |
| `test_CO100_avisa_al_cliente_con_el_reemplazo_y_las_instrucciones` | CO100 avisa al cliente con el reemplazo y las instrucciones | 1 | Pasa |
| `test_CO100_E1_sin_stock_no_registra_nada` | CO100 E1 sin stock no registra nada | 1 | Pasa |
| `test_CO100_E1_la_pantalla_no_deja_elegir_un_producto_sin_stock` | CO100 E1 la pantalla no deja elegir un producto sin stock | 1 | Pasa |
| `test_CO100_no_toca_el_producto_reclamado_ni_los_puntos` | CO100 no toca el producto reclamado ni los puntos | 1 | Pasa |
| `test_CO100_un_caso_que_ya_no_esta_pendiente_no_se_vuelve_a_resolver` | CO100 un caso que ya no esta pendiente no se vuelve a resolver | 1 | Pasa |
| `test_CO101_el_caso_pasa_de_pendiente_a_resuelto_con_reembolso` | CO101 el caso pasa de pendiente a resuelto con reembolso | 1 | Pasa |
| `test_CO101_acredita_un_lote_de_reembolso_por_una_unidad_con_la_caducidad_estandar` | CO101 acredita un lote de reembolso por una unidad con la caducidad estandar | 1 | Pasa |
| `test_CO101_el_movimiento_de_acreditacion_queda_con_su_saldo_y_su_caso` | CO101 el movimiento de acreditacion queda con su saldo y su caso | 1 | Pasa |
| `test_CO101_una_unidad_pagada_con_puntos_devuelve_su_parte_hacia_arriba` | CO101 una unidad pagada con puntos devuelve su parte hacia arriba | 1 | Pasa |
| `test_CO101_registra_la_resolucion_con_el_tipo_el_administrador_y_el_momento` | CO101 registra la resolucion con el tipo el administrador y el momento | 1 | Pasa |
| `test_CO101_avisa_al_cliente_con_el_saldo_actualizado` | CO101 avisa al cliente con el saldo actualizado | 1 | Pasa |
| `test_CO101_descuenta_los_puntos_ganados_con_la_compra_y_no_toca_el_stock` | CO101 descuenta los puntos ganados con la compra y no toca el stock | 1 | Pasa |
| `test_CO101_un_caso_ya_resuelto_no_acredita_dos_veces` | CO101 un caso ya resuelto no acredita dos veces | 1 | Pasa |
| `test_CO102_el_caso_pasa_a_rechazado_con_el_motivo_declarado` | CO102 el caso pasa a rechazado con el motivo declarado | 1 | Pasa |
| `test_CO102_registra_el_rechazo_con_el_actor_y_el_momento` | CO102 registra el rechazo con el actor y el momento | 1 | Pasa |
| `test_CO102_avisa_al_cliente_con_el_motivo` | CO102 avisa al cliente con el motivo | 1 | Pasa |
| `test_CO102_sin_motivo_no_registra_nada` | CO102 sin motivo no registra nada | 1 | Pasa |
| `test_CO102_no_acredita_puntos_ni_toca_el_stock` | CO102 no acredita puntos ni toca el stock | 1 | Pasa |
| `test_CO130_el_plazo_de_devolucion_pasa_al_declarado_y_queda_auditado` | CO130 el plazo de devolucion pasa al declarado y queda auditado | 1 | Pasa |
| `test_CO130_E1_el_plazo_bajo_el_piso_legal_se_rechaza_solo_y_los_demas_se_guardan` | CO130 E1 el plazo bajo el piso legal se rechaza solo y los demas se guardan | 1 | Pasa |
| `test_CO130_E2_otro_campo_invalido_no_guarda_nada_aunque_el_plazo_tambien_falle` | CO130 E2 otro campo invalido no guarda nada aunque el plazo tambien falle | 1 | Pasa |
| `test_CO130_la_base_no_admite_un_plazo_bajo_el_piso_legal` | CO130 la base no admite un plazo bajo el piso legal | 1 | Pasa |
| `test_flujo_el_cliente_reclama_y_el_administrador_reembolsa_en_puntos` | Flujo el cliente reclama y el administrador reembolsa en puntos | 1 | Pasa |
| `test_flujo_el_administrador_busca_el_reemplazo_y_autoriza_el_cambio` | Flujo el administrador busca el reemplazo y autoriza el cambio | 1 | Pasa |

---

## pedidos — `apps/pedidos`

### `test_acceso_y_concurrencia_pedidos.py`

Acceso a la gestión de pedidos por la dirección real, y dos administradores a la vez.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_acceso_solo_el_administrador_ve_y_avanza_pedidos` | Acceso solo el administrador ve y avanza pedidos | 6 | Pasa |
| `test_acceso_sin_sesion_va_al_ingreso` | Acceso sin sesion va al ingreso | 1 | Pasa |
| `test_acceso_el_menu_del_administrador_lleva_a_pedidos` | Acceso el menu del administrador lleva a pedidos | 1 | Pasa |
| `test_CO092_dos_administradores_que_avanzan_a_la_vez_avanzan_un_solo_paso` | CO092 dos administradores que avanzan a la vez avanzan un solo paso | 1 | Pasa |

### `test_acceso_y_concurrencia_preventa.py`

Acceso al ciclo de la pre-venta y a la demora por la dirección real, y escrituras a la vez.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_acceso_solo_el_administrador_opera_la_preventa` | Acceso solo el administrador opera la preventa | 2 | Pasa |
| `test_acceso_la_ficha_ofrece_las_acciones_de_preventa_solo_cuando_aplican` | Acceso la ficha ofrece las acciones de preventa solo cuando aplican | 1 | Pasa |
| `test_acceso_el_panel_muestra_las_preventas_por_llegar` | Acceso el panel muestra las preventas por llegar | 1 | Pasa |
| `test_acceso_los_parametros_de_la_preventa_se_guardan_y_se_auditan` | Acceso los parametros de la preventa se guardan y se auditan | 1 | Pasa |
| `test_acceso_un_cliente_no_decide_sobre_el_pedido_de_otro` | Acceso un cliente no decide sobre el pedido de otro | 1 | Pasa |
| `test_acceso_el_personal_no_decide_por_el_cliente` | Acceso el personal no decide por el cliente | 2 | Pasa |
| `test_acceso_sin_sesion_la_decision_va_al_ingreso` | Acceso sin sesion la decision va al ingreso | 1 | Pasa |
| `test_concurrencia_dos_pestanas_que_confirman_registran_una_sola_decision` | Concurrencia dos pestanas que confirman registran una sola decision | 1 | Pasa |
| `test_concurrencia_la_llegada_y_la_cancelacion_del_cliente_no_se_pisan` | Concurrencia la llegada y la cancelacion del cliente no se pisan | 1 | Pasa |
| `test_concurrencia_dos_administradores_que_confirman_el_mismo_ingreso_lo_cuentan_una_vez` | Concurrencia dos administradores que confirman el mismo ingreso lo cuentan una vez | 1 | Pasa |
| `test_concurrencia_la_cancelacion_por_la_editorial_y_la_compra_no_dejan_reservas_vivas` | Concurrencia la cancelacion por la editorial y la compra no dejan reservas vivas | 1 | Pasa |

### `test_contratos_01_preventa.py`

Contratos del ciclo de la pre-venta (plan 01): `CO-011` a `CO-015`, `CO-026`, `CO-027`.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO011_avisa_las_proximas_y_las_de_hoy_sin_cambiar_nada` | CO011 avisa las proximas y las de hoy sin cambiar nada | 1 | Pasa |
| `test_CO011_correr_dos_veces_el_mismo_dia_no_repite_avisos` | CO011 correr dos veces el mismo dia no repite avisos | 1 | Pasa |
| `test_CO011_fuera_del_horizonte_o_sin_preventas_no_avisa` | CO011 fuera del horizonte o sin preventas no avisa | 1 | Pasa |
| `test_CO011_una_demorada_cuya_fecha_estimada_paso_se_recuerda_una_vez` | CO011 una demorada cuya fecha estimada paso se recuerda una vez | 1 | Pasa |
| `test_CO011_el_temporizador_corre_los_ciclos_de_la_preventa_y_la_demora` | CO011 el temporizador corre los ciclos de la preventa y la demora | 1 | Pasa |
| `test_CO012_escala_lo_vencido_sin_ingreso_ni_demora_y_lo_audita` | CO012 escala lo vencido sin ingreso ni demora y lo audita | 1 | Pasa |
| `test_CO012_escala_una_vez_por_dia_mientras_siga_sin_resolver` | CO012 escala una vez por dia mientras siga sin resolver | 1 | Pasa |
| `test_CO012_no_escala_lo_que_tiene_demora_registrada` | CO012 no escala lo que tiene demora registrada | 1 | Pasa |
| `test_CO013_confirmar_ingreso_activa_productos_y_pasa_pedidos_a_pendiente_de_armado` | CO013 confirmar ingreso activa productos y pasa pedidos a pendiente de armado | 1 | Pasa |
| `test_CO013_lo_recibido_cubre_las_reservas_en_orden_de_compra` | CO013 lo recibido cubre las reservas en orden de compra | 1 | Pasa |
| `test_CO013_no_saltea_una_reserva_que_no_alcanza` | CO013 no saltea una reserva que no alcanza | 1 | Pasa |
| `test_CO013_un_pedido_con_otra_preventa_sigue_esperando` | CO013 un pedido con otra preventa sigue esperando | 1 | Pasa |
| `test_CO013_A1_un_faltante_vencido_se_demora_con_la_cascada_de_CO015` | CO013 A1 un faltante vencido se demora con la cascada de CO015 | 1 | Pasa |
| `test_CO013_un_faltante_que_todavia_no_vence_no_cambia` | CO013 un faltante que todavia no vence no cambia | 1 | Pasa |
| `test_CO013_E3_un_producto_que_falla_queda_en_preventa_y_los_demas_siguen` | CO013 E3 un producto que falla queda en preventa y los demas siguen | 1 | Pasa |
| `test_CO013_rechaza_unidades_negativas` | CO013 rechaza unidades negativas | 1 | Pasa |
| `test_CO013_el_articulo_de_despacho_diferido_llega_disponible_y_cierra_la_compensacion` | CO013 el articulo de despacho diferido llega disponible y cierra la compensacion | 1 | Pasa |
| `test_CO013_por_la_pantalla_se_revisa_y_despues_se_confirma` | CO013 por la pantalla se revisa y despues se confirma | 1 | Pasa |
| `test_CO013_la_pantalla_rechaza_unidades_invalidas` | CO013 la pantalla rechaza unidades invalidas | 3 | Pasa |
| `test_CO013_la_pantalla_agrupa_por_fecha_y_editorial` | CO013 la pantalla agrupa por fecha y editorial | 1 | Pasa |
| `test_CO013_un_producto_que_ya_no_esta_en_preventa_se_informa` | CO013 un producto que ya no esta en preventa se informa | 1 | Pasa |
| `test_CO014_informa_pedidos_y_clientes_sin_registrar_nada` | CO014 informa pedidos y clientes sin registrar nada | 1 | Pasa |
| `test_CO014_A3_sin_pedidos_lo_dice` | CO014 A3 sin pedidos lo dice | 1 | Pasa |
| `test_CO014_E1_la_fecha_estimada_debe_ser_posterior_a_hoy` | CO014 E1 la fecha estimada debe ser posterior a hoy | 2 | Pasa |
| `test_CO014_rechaza_lo_ya_demorado_lo_vencido_y_lo_que_no_es_preventa` | CO014 rechaza lo ya demorado lo vencido y lo que no es preventa | 1 | Pasa |
| `test_CO015_confirmar_demora_marca_el_producto_y_transiciona_los_pedidos` | CO015 confirmar demora marca el producto y transiciona los pedidos | 1 | Pasa |
| `test_CO015_A1_sin_fecha_estimada_el_aviso_la_omite` | CO015 A1 sin fecha estimada el aviso la omite | 1 | Pasa |
| `test_CO015_A3_sin_pedidos_registra_la_demora_sin_avisos` | CO015 A3 sin pedidos registra la demora sin avisos | 1 | Pasa |
| `test_CO015_E2_un_pedido_que_falla_no_frena_a_los_demas` | CO015 E2 un pedido que falla no frena a los demas | 1 | Pasa |
| `test_CO156_volver_desde_el_informe_de_demora_no_registra_nada` | CO156 volver desde el informe de demora no registra nada | 1 | Pasa |
| `test_CO026_informa_reservas_por_cliente_y_los_puntos_a_reembolsar` | CO026 informa reservas por cliente y los puntos a reembolsar | 1 | Pasa |
| `test_CO026_sin_reservas_lo_dice_con_cero` | CO026 sin reservas lo dice con cero | 1 | Pasa |
| `test_CO027_cancela_reservas_reembolsa_en_puntos_y_cancela_el_producto` | CO027 cancela reservas reembolsa en puntos y cancela el producto | 1 | Pasa |
| `test_CO027_sin_reservas_solo_cambia_el_estado` | CO027 sin reservas solo cambia el estado | 1 | Pasa |
| `test_CO027_incluye_las_reservas_ya_demoradas` | CO027 incluye las reservas ya demoradas | 1 | Pasa |
| `test_CO027_E1_si_falla_un_reembolso_no_queda_nada` | CO027 E1 si falla un reembolso no queda nada | 1 | Pasa |
| `test_CO027_no_se_cancela_lo_que_no_esta_en_preventa` | CO027 no se cancela lo que no esta en preventa | 1 | Pasa |
| `test_CO156_volver_desde_la_cancelacion_no_cambia_nada` | CO156 volver desde la cancelacion no cambia nada | 1 | Pasa |
| `test_CO013_la_revision_dice_que_faltante_se_demora_y_cual_no_cambia` | CO013 la revision dice que faltante se demora y cual no cambia | 1 | Pasa |
| `test_CO015_el_servicio_rechaza_una_fecha_estimada_que_no_es_futura` | CO015 el servicio rechaza una fecha estimada que no es futura | 1 | Pasa |

### `test_contratos_08_demora.py`

Contratos del Cliente ante una demora (plan 08, segunda parte).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO184_muestra_el_articulo_sus_fechas_y_las_tres_opciones` | CO184 muestra el articulo sus fechas y las tres opciones | 1 | Pasa |
| `test_CO184_el_detalle_del_pedido_ofrece_elegir_que_hacer` | CO184 el detalle del pedido ofrece elegir que hacer | 1 | Pasa |
| `test_CO184_E1_con_la_ventana_vencida_no_hay_opciones` | CO184 E1 con la ventana vencida no hay opciones | 1 | Pasa |
| `test_CO184_sin_nada_para_despachar_no_ofrece_recibir_lo_disponible` | CO184 sin nada para despachar no ofrece recibir lo disponible | 1 | Pasa |
| `test_CO184_con_otra_preventa_esperando_no_ofrece_recibir_lo_disponible` | CO184 con otra preventa esperando no ofrece recibir lo disponible | 1 | Pasa |
| `test_CO094_pide_confirmar_con_la_consecuencia_sin_registrar` | CO094 pide confirmar con la consecuencia sin registrar | 2 | Pasa |
| `test_CO094_una_opcion_que_no_corresponde_se_rechaza` | CO094 una opcion que no corresponde se rechaza | 1 | Pasa |
| `test_CO095_pausar_registra_la_decision_y_el_pedido_sigue_esperando` | CO095 pausar registra la decision y el pedido sigue esperando | 1 | Pasa |
| `test_CO095_al_llegar_el_articulo_pausado_el_pedido_pasa_a_pendiente_de_armado` | CO095 al llegar el articulo pausado el pedido pasa a pendiente de armado | 1 | Pasa |
| `test_CO095_despacho_diferido_empaqueta_lo_disponible_y_el_pedido` | CO095 despacho diferido empaqueta lo disponible y el pedido | 1 | Pasa |
| `test_CO095_el_despacho_no_arrastra_al_articulo_diferido` | CO095 el despacho no arrastra al articulo diferido | 1 | Pasa |
| `test_CO095_no_se_decide_dos_veces` | CO095 no se decide dos veces | 1 | Pasa |
| `test_CO095_con_la_ventana_vencida_se_rechaza_en_el_servidor` | CO095 con la ventana vencida se rechaza en el servidor | 1 | Pasa |
| `test_CO156_volver_desde_la_confirmacion_no_registra_nada` | CO156 volver desde la confirmacion no registra nada | 1 | Pasa |
| `test_CO098_cancelar_reembolsa_el_valor_en_puntos_y_no_toca_el_stock` | CO098 cancelar reembolsa el valor en puntos y no toca el stock | 1 | Pasa |
| `test_CO098_pagado_con_puntos_devuelve_los_mismos_puntos` | CO098 pagado con puntos devuelve los mismos puntos | 1 | Pasa |
| `test_CO098_un_pedido_sin_otros_articulos_se_cancela_y_devuelve_el_envio` | CO098 un pedido sin otros articulos se cancela y devuelve el envio | 1 | Pasa |
| `test_CO098_E1_si_falla_no_queda_nada_y_avisa_al_administrador` | CO098 E1 si falla no queda nada y avisa al administrador | 1 | Pasa |
| `test_CO098_cancelado_el_articulo_sale_del_historial_activo` | CO098 cancelado el articulo sale del historial activo | 1 | Pasa |
| `test_CO096_cierra_las_ventanas_vencidas_y_avisa_al_administrador` | CO096 cierra las ventanas vencidas y avisa al administrador | 1 | Pasa |
| `test_CO096_mira_la_decision_y_no_el_estado` | CO096 mira la decision y no el estado | 1 | Pasa |
| `test_CO096_no_repite_ni_toca_las_vigentes` | CO096 no repite ni toca las vigentes | 1 | Pasa |
| `test_CO097_acredita_el_5_por_ciento_por_semana_cumplida` | CO097 acredita el 5 por ciento por semana cumplida | 1 | Pasa |
| `test_CO097_correr_dos_veces_o_antes_de_la_semana_no_acredita_de_mas` | CO097 correr dos veces o antes de la semana no acredita de mas | 1 | Pasa |
| `test_CO097_el_tope_del_25_por_ciento_cierra_el_acumulador` | CO097 el tope del 25 por ciento cierra el acumulador | 1 | Pasa |
| `test_CO097_E1_un_articulo_que_llego_o_se_cancelo_no_acredita` | CO097 E1 un articulo que llego o se cancelo no acredita | 1 | Pasa |
| `test_CO097_E2_un_acumulador_en_el_tope_y_abierto_se_cierra_sin_acreditar` | CO097 E2 un acumulador en el tope y abierto se cierra sin acreditar | 1 | Pasa |
| `test_CO097_E3_sin_acumuladores_no_hace_nada` | CO097 E3 sin acumuladores no hace nada | 1 | Pasa |
| `test_CO098_con_envio_gratis_el_pedido_cancelado_solo_devuelve_el_articulo` | CO098 con envio gratis el pedido cancelado solo devuelve el articulo | 1 | Pasa |

### `test_contratos_08_pedidos.py`

Pruebas de contrato de la gestión de pedidos (plan 08, primera parte).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO182_lista_los_pedidos_del_mas_reciente_al_mas_viejo` | CO182 lista los pedidos del mas reciente al mas viejo | 1 | Pasa |
| `test_CO182_cada_fila_trae_cliente_o_invitado_canal_estado_y_total` | CO182 cada fila trae cliente o invitado canal estado y total | 1 | Pasa |
| `test_CO182_filtra_por_estado_cliente_canal_y_demorados` | CO182 filtra por estado cliente canal y demorados | 4 | Pasa |
| `test_CO182_filtra_por_rango_de_fechas` | CO182 filtra por rango de fechas | 1 | Pasa |
| `test_CO182_E1_sin_resultados_informa_y_ofrece_limpiar` | CO182 E1 sin resultados informa y ofrece limpiar | 1 | Pasa |
| `test_CO182_un_filtro_invalido_se_ignora` | CO182 un filtro invalido se ignora | 1 | Pasa |
| `test_CO182_hace_las_mismas_consultas_con_pocos_o_muchos_pedidos` | CO182 hace las mismas consultas con pocos o muchos pedidos | 1 | Pasa |
| `test_CO182_no_modifica_el_estado_del_sistema` | CO182 no modifica el estado del sistema | 1 | Pasa |
| `test_CO183_muestra_cliente_items_puntos_pago_y_linea_de_tiempo` | CO183 muestra cliente items puntos pago y linea de tiempo | 1 | Pasa |
| `test_CO183_en_un_estado_automatico_no_ofrece_avanzar` | CO183 en un estado automatico no ofrece avanzar | 1 | Pasa |
| `test_CO183_un_pedido_pagado_sólo_con_puntos_lo_dice` | CO183 un pedido pagado sólo con puntos lo dice | 1 | Pasa |
| `test_CO183_no_modifica_el_estado_del_sistema` | CO183 no modifica el estado del sistema | 1 | Pasa |
| `test_CO092_c_el_estado_pasa_al_unico_siguiente` | CO092 c el estado pasa al unico siguiente | 3 | Pasa |
| `test_CO092_c_armado_no_toca_las_lineas` | CO092 c armado no toca las lineas | 1 | Pasa |
| `test_CO092_c_empaquetado_y_despachado_avanzan_las_lineas_disponibles` | CO092 c empaquetado y despachado avanzan las lineas disponibles | 1 | Pasa |
| `test_CO092_c_las_lineas_demoradas_no_avanzan` | CO092 c las lineas demoradas no avanzan | 1 | Pasa |
| `test_CO092_queda_una_transicion_en_la_linea_de_tiempo` | CO092 queda una transicion en la linea de tiempo | 1 | Pasa |
| `test_CO092_queda_en_la_auditoria_con_el_estado_anterior_y_el_nuevo` | CO092 queda en la auditoria con el estado anterior y el nuevo | 1 | Pasa |
| `test_CO092_el_cliente_recibe_la_notificacion` | CO092 el cliente recibe la notificacion | 1 | Pasa |
| `test_CO092_el_invitado_recibe_la_notificacion_en_su_correo` | CO092 el invitado recibe la notificacion en su correo | 1 | Pasa |
| `test_CO092_un_correo_caido_no_deshace_el_avance` | CO092 un correo caido no deshace el avance | 1 | Pasa |
| `test_CO092_E1_un_estado_automatico_no_se_avanza_a_mano` | CO092 E1 un estado automatico no se avanza a mano | 2 | Pasa |
| `test_CO092_un_pedido_despachado_no_tiene_siguiente` | CO092 un pedido despachado no tiene siguiente | 1 | Pasa |
| `test_CO092_no_se_saltea_un_paso_si_el_pedido_cambio_en_otra_pantalla` | CO092 no se saltea un paso si el pedido cambio en otra pantalla | 1 | Pasa |
| `test_CO092_E2_con_decision_pendiente_advierte_y_no_avanza` | CO092 E2 con decision pendiente advierte y no avanza | 1 | Pasa |
| `test_CO092_la_confirmacion_muestra_el_estado_actual_y_el_siguiente` | CO092 la confirmacion muestra el estado actual y el siguiente | 1 | Pasa |
| `test_CO093_avanza_y_los_pendientes_conservan_su_estado` | CO093 avanza y los pendientes conservan su estado | 1 | Pasa |
| `test_la_primera_transicion_es_la_del_estado_inicial` | La primera transicion es la del estado inicial | 1 | Pasa |

---

## puntos — `apps/puntos`

### `test_acceso_y_concurrencia_ajuste.py`

Acceso al ajuste de puntos por la dirección real, y débitos y caducidades a la vez.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_acceso_solo_el_administrador_consulta_y_ajusta_puntos` | Acceso solo el administrador consulta y ajusta puntos | 2 | Pasa |
| `test_acceso_sin_sesion_el_ajuste_lleva_al_ingreso` | Acceso sin sesion el ajuste lleva al ingreso | 1 | Pasa |
| `test_acceso_el_panel_de_puntos_no_existe_para_una_cuenta_de_personal` | Acceso el panel de puntos no existe para una cuenta de personal | 1 | Pasa |
| `test_concurrencia_dos_debitos_que_suman_mas_que_el_saldo_registran_uno` | Concurrencia dos debitos que suman mas que el saldo registran uno | 1 | Pasa |
| `test_concurrencia_la_caducidad_y_un_debito_sobre_el_mismo_lote_no_lo_cuentan_dos_veces` | Concurrencia la caducidad y un debito sobre el mismo lote no lo cuentan dos veces | 1 | Pasa |

### `test_contratos_10_caducidad_y_ajuste.py`

Contratos de la caducidad y el ajuste manual de puntos (plan 10, segunda parte).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO105_el_lote_con_caducidad_alcanzada_pasa_a_vencido_con_disponible_cero` | CO105 el lote con caducidad alcanzada pasa a vencido con disponible cero | 1 | Pasa |
| `test_CO105_el_saldo_del_cliente_baja_en_lo_que_vencio` | CO105 el saldo del cliente baja en lo que vencio | 1 | Pasa |
| `test_CO105_los_lotes_con_caducidad_futura_no_se_tocan` | CO105 los lotes con caducidad futura no se tocan | 1 | Pasa |
| `test_CO105_E2_un_lote_comprometido_en_un_canje_en_curso_no_se_modifica` | CO105 E2 un lote comprometido en un canje en curso no se modifica | 1 | Pasa |
| `test_CO105_E2_un_canje_abandonado_hace_mas_de_un_dia_no_difiere_la_caducidad` | CO105 E2 un canje abandonado hace mas de un dia no difiere la caducidad | 1 | Pasa |
| `test_CO105_registra_cada_lote_con_el_cliente_la_cantidad_y_la_fecha` | CO105 registra cada lote con el cliente la cantidad y la fecha | 1 | Pasa |
| `test_CO105_el_historial_muestra_el_debito_por_caducidad_con_su_saldo` | CO105 el historial muestra el debito por caducidad con su saldo | 1 | Pasa |
| `test_CO105_avisa_a_cada_cliente_una_vez_con_sus_lotes_y_su_saldo` | CO105 avisa a cada cliente una vez con sus lotes y su saldo | 1 | Pasa |
| `test_CO105_A1_sin_lotes_vencidos_no_invalida_ni_avisa_ni_registra` | CO105 A1 sin lotes vencidos no invalida ni avisa ni registra | 1 | Pasa |
| `test_CO105_E1_un_lote_que_falla_queda_como_estaba_y_el_ciclo_sigue` | CO105 E1 un lote que falla queda como estaba y el ciclo sigue | 1 | Pasa |
| `test_CO105_los_puntos_vencidos_no_se_recuperan_al_correr_otra_vez` | CO105 los puntos vencidos no se recuperan al correr otra vez | 1 | Pasa |
| `test_CO105_corre_en_el_temporizador` | CO105 corre en el temporizador | 1 | Pasa |
| `test_aviso_previo_sale_dentro_de_los_dias_configurados_una_sola_vez` | Aviso previo sale dentro de los dias configurados una sola vez | 1 | Pasa |
| `test_aviso_previo_toma_los_dias_del_parametro` | Aviso previo toma los dias del parametro | 1 | Pasa |
| `test_CO130_el_aviso_previo_se_configura_en_parametros` | CO130 el aviso previo se configura en parametros | 1 | Pasa |
| `test_CO191_presenta_saldo_lotes_comprometido_y_movimientos_sin_modificar_nada` | CO191 presenta saldo lotes comprometido y movimientos sin modificar nada | 1 | Pasa |
| `test_CO191_la_ficha_del_cliente_lleva_a_sus_puntos` | CO191 la ficha del cliente lleva a sus puntos | 1 | Pasa |
| `test_CO191_una_cuenta_inactiva_no_admite_el_panel` | CO191 una cuenta inactiva no admite el panel | 1 | Pasa |
| `test_CO106_la_acreditacion_crea_un_lote_de_ajuste_manual_con_la_caducidad_estandar` | CO106 la acreditacion crea un lote de ajuste manual con la caducidad estandar | 1 | Pasa |
| `test_CO106_el_debito_consume_lotes_por_caducidad_y_el_que_llega_a_cero_se_agota` | CO106 el debito consume lotes por caducidad y el que llega a cero se agota | 1 | Pasa |
| `test_CO106_el_debito_no_toca_lo_comprometido_en_un_canje` | CO106 el debito no toca lo comprometido en un canje | 1 | Pasa |
| `test_CO106_crea_el_movimiento_con_tipo_cantidad_motivo_y_saldo` | CO106 crea el movimiento con tipo cantidad motivo y saldo | 2 | Pasa |
| `test_CO106_registra_tipo_cantidad_saldos_motivo_y_administrador` | CO106 registra tipo cantidad saldos motivo y administrador | 1 | Pasa |
| `test_CO106_avisa_al_cliente_el_tipo_la_cantidad_y_el_saldo` | CO106 avisa al cliente el tipo la cantidad y el saldo | 1 | Pasa |
| `test_CO106_presenta_el_saldo_actualizado_al_administrador` | CO106 presenta el saldo actualizado al administrador | 1 | Pasa |
| `test_CO106_E1_un_debito_mayor_que_lo_libre_informa_el_maximo_y_no_registra` | CO106 E1 un debito mayor que lo libre informa el maximo y no registra | 1 | Pasa |
| `test_CO106_E2_sin_motivo_no_registra_y_conserva_lo_ingresado` | CO106 E2 sin motivo no registra y conserva lo ingresado | 1 | Pasa |
| `test_CO106_la_cantidad_tiene_que_ser_mayor_que_cero` | CO106 la cantidad tiene que ser mayor que cero | 4 | Pasa |
| `test_CO106_una_cuenta_inactiva_no_admite_ajustes` | CO106 una cuenta inactiva no admite ajustes | 1 | Pasa |
| `test_CO106_volver_sin_confirmar_no_registra_nada` | CO106 volver sin confirmar no registra nada | 1 | Pasa |

### `test_contratos_10_puntos.py`

Pruebas de contrato de «Mis puntos» (plan 10): `CO-188` y `CO-189`, y el saldo siempre a la vista en el encabezado (B-10-002).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO188_el_saldo_con_su_equivalencia_en_pesos` | CO188 el saldo con su equivalencia en pesos | 1 | Pasa |
| `test_CO188_cada_lote_con_origen_monto_disponible_y_caducidad` | CO188 cada lote con origen monto disponible y caducidad | 1 | Pasa |
| `test_CO188_destaca_los_lotes_que_vencen_dentro_de_30_dias` | CO188 destaca los lotes que vencen dentro de 30 dias | 1 | Pasa |
| `test_CO188_el_historial_descendente_con_saldo_resultante_y_su_pedido` | CO188 el historial descendente con saldo resultante y su pedido | 1 | Pasa |
| `test_CO188_A1_sin_puntos_saldo_cero_y_mensajes` | CO188 A1 sin puntos saldo cero y mensajes | 1 | Pasa |
| `test_CO188_no_muestra_los_puntos_de_otro_cliente` | CO188 no muestra los puntos de otro cliente | 1 | Pasa |
| `test_CO188_no_modifica_el_estado_del_sistema` | CO188 no modifica el estado del sistema | 1 | Pasa |
| `test_CO189_filtra_por_tipo_y_muestra_el_total` | CO189 filtra por tipo y muestra el total | 1 | Pasa |
| `test_CO189_filtra_por_rango_de_fechas` | CO189 filtra por rango de fechas | 1 | Pasa |
| `test_CO189_E1_sin_resultados_informa_y_ofrece_limpiar` | CO189 E1 sin resultados informa y ofrece limpiar | 1 | Pasa |
| `test_CO189_un_filtro_invalido_se_ignora` | CO189 un filtro invalido se ignora | 1 | Pasa |
| `test_el_saldo_esta_a_la_vista_en_la_tienda` | El saldo esta a la vista en la tienda | 1 | Pasa |
| `test_el_saldo_no_aparece_para_invitados_ni_personal` | El saldo no aparece para invitados ni personal | 3 | Pasa |

### `test_descuento_de_ganados.py`

Los puntos ganados con una compra que se reembolsa (plan 00, C2; RF-19).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_lo_ganado_se_reparte_en_proporcion_a_lo_pagado_hacia_abajo` | Lo ganado se reparte en proporcion a lo pagado hacia abajo | 1 | Pasa |
| `test_una_unidad_pagada_con_puntos_no_gano_nada` | Una unidad pagada con puntos no gano nada | 1 | Pasa |
| `test_el_descuento_nunca_deja_el_saldo_negativo_ni_toca_lo_comprometido` | El descuento nunca deja el saldo negativo ni toca lo comprometido | 1 | Pasa |
| `test_CO098_cancelar_el_demorado_descuenta_lo_que_gano` | CO098 cancelar el demorado descuenta lo que gano | 1 | Pasa |
| `test_CO027_la_cancelacion_en_lote_descuenta_lo_que_gano_cada_reserva` | CO027 la cancelacion en lote descuenta lo que gano cada reserva | 1 | Pasa |
| `test_CO154_el_vencimiento_descuenta_lo_que_gano_la_unidad` | CO154 el vencimiento descuenta lo que gano la unidad | 1 | Pasa |

### `test_servicios.py`

Unidad: la conversión de dinero a puntos, la caducidad y el débito FIFO (B-07-033).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_la_acreditacion_es_el_reintegro_en_pesos_convertido_a_puntos` | 10 % de reintegro y 1 punto = $10: cada $100 pagados suman 1 punto, hacia abajo. | 6 | Pasa |
| `test_el_ejemplo_de_parametros_5_por_ciento_y_10_pesos` | El ejemplo de parametros 5 por ciento y 10 pesos | 1 | Pasa |
| `test_cambiar_el_valor_del_punto_no_cambia_el_reintegro_en_pesos` | Cambiar el valor del punto no cambia el reintegro en pesos | 1 | Pasa |
| `test_el_canje_redondea_hacia_arriba` | El canje redondea hacia arriba | 5 | Pasa |
| `test_una_equivalencia_con_centavos_no_pierde_precision` | Una equivalencia con centavos no pierde precision | 1 | Pasa |
| `test_la_caducidad_suma_meses_de_calendario` | La caducidad suma meses de calendario | 4 | Pasa |
| `test_el_saldo_es_la_suma_de_los_lotes_activos` | El saldo es la suma de los lotes activos | 1 | Pasa |
| `test_el_debito_consume_primero_el_lote_que_caduca_antes` | El debito consume primero el lote que caduca antes | 1 | Pasa |
| `test_un_debito_que_no_alcanza_no_toca_ningun_lote` | Un debito que no alcanza no toca ningun lote | 1 | Pasa |
| `test_acreditar_o_debitar_cero_no_hace_nada` | Acreditar o debitar cero no hace nada | 1 | Pasa |
| `test_la_base_no_admite_un_lote_con_mas_disponible_que_lo_acreditado` | La base no admite un lote con mas disponible que lo acreditado | 1 | Pasa |
| `test_la_base_no_admite_un_lote_activo_sin_disponible` | La base no admite un lote activo sin disponible | 1 | Pasa |
| `test_el_envio_es_gratis_desde_el_monto_minimo_inclusive` | El envio es gratis desde el monto minimo inclusive | 3 | Pasa |

---

## restock — `apps/restock`

### `test_acceso_y_concurrencia_restock.py`

Acceso a la propuesta de restock por la dirección real, y escrituras a la vez.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_acceso_solo_el_administrador_opera_el_restock` | Acceso solo el administrador opera el restock | 2 | Pasa |
| `test_acceso_el_menu_del_administrador_lleva_al_restock` | Acceso el menu del administrador lleva al restock | 1 | Pasa |
| `test_concurrencia_dos_clics_en_avisarme_dejan_una_suscripcion` | Concurrencia dos clics en avisarme dejan una suscripcion | 1 | Pasa |
| `test_concurrencia_el_ciclo_y_el_boton_dejan_una_sola_propuesta_pendiente` | Concurrencia el ciclo y el boton dejan una sola propuesta pendiente | 1 | Pasa |
| `test_concurrencia_dos_administradores_despachan_al_mismo_proveedor_una_vez` | Concurrencia dos administradores despachan al mismo proveedor una vez | 1 | Pasa |

### `test_contratos_05_restock.py`

Contratos de restock (plan 05): `CO-067` a `CO-077`, `CO-174`, `CO-175`.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO075_suscribirse_desde_la_ficha_de_un_agotado` | CO075 suscribirse desde la ficha de un agotado | 1 | Pasa |
| `test_CO075_E1_no_registra_un_duplicado` | CO075 E1 no registra un duplicado | 1 | Pasa |
| `test_CO075_E2_si_ya_hay_stock_no_se_suscribe` | CO075 E2 si ya hay stock no se suscribe | 1 | Pasa |
| `test_CO075_el_invitado_va_al_ingreso_y_el_personal_no_puede` | CO075 el invitado va al ingreso y el personal no puede | 1 | Pasa |
| `test_CO076_cancelar_elimina_la_suscripcion_sin_auditar` | CO076 cancelar elimina la suscripcion sin auditar | 1 | Pasa |
| `test_CO077_reponer_por_la_edicion_avisa_a_los_primeros_n` | CO077 reponer por la edicion avisa a los primeros n | 1 | Pasa |
| `test_CO077_con_mas_unidades_que_suscriptores_avisa_a_todos` | CO077 con mas unidades que suscriptores avisa a todos | 1 | Pasa |
| `test_CO077_A1_sin_suscriptores_no_registra_nada` | CO077 A1 sin suscriptores no registra nada | 1 | Pasa |
| `test_CO077_E1_un_envio_que_falla_tres_veces_conserva_el_turno` | CO077 E1 un envio que falla tres veces conserva el turno | 1 | Pasa |
| `test_CO077_E2_quien_cancela_no_cede_su_cupo` | CO077 E2 quien cancela no cede su cupo | 1 | Pasa |
| `test_CO077_el_articulo_que_vuelve_por_vencimiento_tambien_avisa` | CO077 el articulo que vuelve por vencimiento tambien avisa | 1 | Pasa |
| `test_CO077_bajar_el_stock_no_avisa` | CO077 bajar el stock no avisa | 1 | Pasa |
| `test_CO067_arma_la_propuesta_por_proveedor_con_la_cantidad_sugerida` | CO067 arma la propuesta por proveedor con la cantidad sugerida | 1 | Pasa |
| `test_CO067_E1_sin_elegibles_no_genera_y_lo_registra_una_vez_por_semana` | CO067 E1 sin elegibles no genera y lo registra una vez por semana | 1 | Pasa |
| `test_CO067_E3_con_una_pendiente_no_genera_otra_y_avisa` | CO067 E3 con una pendiente no genera otra y avisa | 1 | Pasa |
| `test_CO067_E4_se_abstiene_si_hubo_una_propuesta_en_la_semana` | CO067 E4 se abstiene si hubo una propuesta en la semana | 1 | Pasa |
| `test_CO068_el_disparo_manual_genera_aunque_haya_una_reciente_y_omite_el_ciclo` | CO068 el disparo manual genera aunque haya una reciente y omite el ciclo | 1 | Pasa |
| `test_CO068_E1_sin_elegibles_igual_omite_el_ciclo_de_la_semana` | CO068 E1 sin elegibles igual omite el ciclo de la semana | 1 | Pasa |
| `test_CO068_E3_con_una_pendiente_se_rechaza` | CO068 E3 con una pendiente se rechaza | 1 | Pasa |
| `test_CO174_muestra_la_propuesta_por_proveedor` | CO174 muestra la propuesta por proveedor | 1 | Pasa |
| `test_CO174_E1_sin_propuesta_lo_dice` | CO174 E1 sin propuesta lo dice | 1 | Pasa |
| `test_CO175_lista_las_lineas_del_proveedor` | CO175 lista las lineas del proveedor | 1 | Pasa |
| `test_CO069_ajustar_la_cantidad_conserva_los_suscriptores` | CO069 ajustar la cantidad conserva los suscriptores | 1 | Pasa |
| `test_CO070_quitar_elimina_la_linea` | CO070 quitar elimina la linea | 1 | Pasa |
| `test_CO071_agregar_va_al_grupo_de_su_proveedor` | CO071 agregar va al grupo de su proveedor | 1 | Pasa |
| `test_CO072_despachar_envia_el_correo_y_marca_las_lineas` | CO072 despachar envia el correo y marca las lineas | 1 | Pasa |
| `test_CO072_E2_si_el_correo_falla_el_proveedor_sigue_pendiente` | CO072 E2 si el correo falla el proveedor sigue pendiente | 1 | Pasa |
| `test_CO072_el_grupo_sin_proveedor_no_se_despacha` | CO072 el grupo sin proveedor no se despacha | 1 | Pasa |
| `test_CO073_descartar_exige_motivo_y_cierra_si_era_el_ultimo` | CO073 descartar exige motivo y cierra si era el ultimo | 1 | Pasa |
| `test_CO073_descartar_un_proveedor_no_afecta_a_los_demas` | CO073 descartar un proveedor no afecta a los demas | 1 | Pasa |
| `test_CO074_E2_sin_correo_no_se_envia_y_se_registra` | CO074 E2 sin correo no se envia y se registra | 1 | Pasa |
| `test_CO013_lo_que_sobra_al_llegar_una_preventa_avisa_a_los_suscriptores` | CO013 lo que sobra al llegar una preventa avisa a los suscriptores | 1 | Pasa |

---

## Proveedores — `apps/suppliers`

### `test_alta_proveedor.py`

CU-PRV-ALT — Registrar Proveedor Editorial.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_alta_deja_el_proveedor_activo` | Postcondición del CU: queda registrado con estado Activo. | 1 | Pasa |
| `test_el_correo_queda_habilitado_como_remitente_valido` | La otra postcondición, y la que le da sentido al módulo entero. | 1 | Pasa |
| `test_los_campos_opcionales_no_traban_el_alta` | E1 solo se dispara con los obligatorios: nombre de contacto, teléfono y notas pueden quedar vacíos. | 1 | Pasa |
| `test_los_campos_opcionales_se_guardan_cuando_vienen` | Los campos opcionales se guardan cuando vienen | 1 | Pasa |
| `test_falta_un_campo_obligatorio_y_no_procede` | E1: se resaltan los faltantes y el formulario permanece abierto. | 2 | Pasa |
| `test_una_razon_social_repetida_es_rechazada` | Una razon social repetida es rechazada | 1 | Pasa |
| `test_un_correo_repetido_es_rechazado` | Un correo repetido es rechazado | 1 | Pasa |
| `test_el_conflicto_se_informa_con_enlace_a_la_ficha_existente` | E2 lo pide explícitamente: sin el enlace, el aviso obligaría a salir a buscar el proveedor a mano. | 1 | Pasa |
| `test_la_razon_social_repetida_se_detecta_sin_distinguir_mayusculas` | "Editorial Ivrea" y "EDITORIAL IVREA" son el mismo proveedor escrito distinto: con dos filas habría dos agendas del mismo interlocutor. | 1 | Pasa |
| `test_el_correo_repetido_se_detecta_sin_distinguir_mayusculas` | El correo repetido se detecta sin distinguir mayusculas | 1 | Pasa |
| `test_una_razon_social_de_una_letra_es_rechazada` | Una sola letra no distingue a nadie y casi siempre es un enter de más. | 1 | Pasa |
| `test_la_razon_social_se_normaliza` | La razon social se normaliza | 1 | Pasa |
| `test_el_correo_se_guarda_en_minuscula` | Es la clave con la que CU-ALT-NOV reconoce un remitente: normalizarlo al guardar hace que la búsqueda del pipeline y la pantalla digan lo mismo. | 1 | Pasa |
| `test_el_alta_queda_auditada` | El alta queda auditada | 1 | Pasa |
| `test_solo_el_administrador_da_de_alta_proveedores` | Solo el administrador da de alta proveedores | 2 | Pasa |
| `test_sin_sesion_el_alta_redirige_al_login` | Sin sesion el alta redirige al login | 1 | Pasa |

### `test_baja_proveedor.py`

CU-PRV-BAJ — Dar de Baja Proveedor Editorial, y la reactivación que lo revierte.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_informe_cuenta_los_productos_vinculados` | El informe cuenta los productos vinculados | 1 | Pasa |
| `test_sin_impacto_el_informe_lo_dice_explicitamente` | A1: si no hay impacto, el informe lo indica en vez de mostrarse vacío. | 1 | Pasa |
| `test_el_informe_cuenta_la_propuesta_de_restock_pendiente` | B-04-001: la propuesta pendiente con un pedido sin despachar a este proveedor. | 1 | Pasa |
| `test_mirar_el_informe_no_da_de_baja_nada` | A2: el Administrador puede revisar el impacto y no confirmar. | 1 | Pasa |
| `test_la_baja_deja_el_proveedor_inactivo` | La baja deja el proveedor inactivo | 1 | Pasa |
| `test_la_baja_saca_el_correo_del_filtro_de_remitentes` | Es la postcondición que le da sentido a la baja: el pipeline de CU-ALT-NOV deja de procesar sus mensajes. | 1 | Pasa |
| `test_los_productos_conservan_la_referencia_al_proveedor` | La baja es lógica: el CU pide expresamente que el historial sobreviva. | 1 | Pasa |
| `test_la_baja_queda_auditada_con_el_impacto` | La baja queda auditada con el impacto | 1 | Pasa |
| `test_dar_de_baja_dos_veces_no_registra_dos_bajas` | El doble envío del formulario es el caso normal, no el raro. | 1 | Pasa |
| `test_reactivar_devuelve_el_correo_al_filtro_de_remitentes` | Reactivar devuelve el correo al filtro de remitentes | 1 | Pasa |
| `test_reactivar_conserva_los_datos_y_el_historial` | Reactivar conserva los datos y el historial | 1 | Pasa |
| `test_reactivar_queda_auditado` | Reactivar queda auditado | 1 | Pasa |
| `test_reactivar_uno_ya_activo_no_hace_nada` | Reactivar uno ya activo no hace nada | 1 | Pasa |
| `test_la_baja_no_bloquea_la_razon_social_para_siempre` | Es el motivo por el que la reactivación existe: la razón social y el correo son únicos *en cualquier estado*, así que sin vuelta atrás un proveedor dado de baja se bloquearía a sí mismo. | 1 | Pasa |
| `test_solo_el_administrador_da_de_baja` | Solo el administrador da de baja | 2 | Pasa |
| `test_solo_el_administrador_reactiva` | Solo el administrador reactiva | 2 | Pasa |

### `test_borradores_del_correo.py`

El pipeline entero: de un `.eml` en la cola a borradores con su portada.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_procesar_un_correo_de_la_cola_deja_sus_borradores` | Procesar un correo de la cola deja sus borradores | 1 | Pasa |
| `test_un_correo_que_no_es_de_novedades_no_genera_borradores` | Es lo que justifica que la cola exista: por la casilla del proveedor llegan facturas y saludos, y ninguno tiene que ensuciar la revisión. | 1 | Pasa |
| `test_si_el_modelo_no_contesta_no_se_genera_ningun_borrador` | Un fallo del servicio no puede dejar medio borrador cargado. | 1 | Pasa |
| `test_la_portada_embebida_termina_como_archivo_del_borrador` | No se descarga de ninguna URL: ya vino adentro del correo (corrección 16). | 1 | Pasa |
| `test_el_borrador_conserva_el_identificador_de_su_portada` | Es lo que permite volver a sacarla del archivo original si algo sale mal, sin tener que adivinar cuál era. | 1 | Pasa |
| `test_una_portada_inventada_deja_el_borrador_sin_imagen_y_con_su_reparo` | La extracción ya descarta el identificador que no existe entre las partes del correo; acá se verifica que eso llegue hasta el borrador. | 1 | Pasa |
| `test_un_producto_sin_portada_no_interrumpe_al_resto` | CU-ALT-NOV: la portada que falta no corta el procesamiento del correo. | 1 | Pasa |
| `test_el_logo_del_encabezado_no_se_confunde_con_una_portada` | El correo de ejemplo trae un logo embebido que **no** es tapa de nada. | 1 | Pasa |
| `test_sin_archivo_guardado_los_borradores_salen_igual_sin_portada` | El archivo es el respaldo, no una precondición: si faltara, la revisión sigue siendo posible y la portada se adjunta a mano. | 1 | Pasa |
| `test_el_periodo_anunciado_llega_hasta_la_fecha_del_borrador` | El periodo anunciado llega hasta la fecha del borrador | 1 | Pasa |
| `test_reprocesar_un_correo_no_duplica_sus_borradores` | Ajustar el prompt y volver a correr es el caso normal, no el raro. | 1 | Pasa |
| `test_la_ficha_muestra_los_borradores_generados` | Van junto al contenido del que salieron: un borrador con el precio del tomo siguiente solo se nota teniendo las dos cosas a la vista. | 1 | Pasa |
| `test_la_ficha_marca_los_borradores_incompletos` | La ficha marca los borradores incompletos | 1 | Pasa |
| `test_la_ficha_ofrece_aprobar_desde_la_pantalla` | La aprobación de `CO-017` se hace desde la ficha (CU-PRV-COL paso 4), y ya no con una instrucción de consola. | 1 | Pasa |
| `test_un_correo_sin_procesar_no_muestra_la_seccion_de_borradores` | Una sección vacía se leería como "no generó nada", que es distinto de "todavía no se procesó". | 1 | Pasa |

### `test_cola_de_correos.py`

La cola de aprobación: ingesta, pantallas y descarte.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_un_correo_de_un_proveedor_habilitado_entra_a_la_cola` | Un correo de un proveedor habilitado entra a la cola | 1 | Pasa |
| `test_el_correo_queda_archivado_entero` | CU-ALT-NOV pide archivar el original como respaldo. | 1 | Pasa |
| `test_se_guarda_el_contenido_extraido_y_el_resumen_de_las_portadas` | El contenido se guarda y no se recalcula al leer: es exactamente lo que se le va a mandar al modelo, y tenerlo escrito hace que el paso siguiente sea reproducible. | 1 | Pasa |
| `test_un_remitente_no_registrado_no_genera_nada` | E1 de CU-ALT-NOV: se loguea y el ciclo sigue con el mensaje siguiente. | 1 | Pasa |
| `test_un_proveedor_dado_de_baja_no_alimenta_la_cola` | Un proveedor dado de baja no alimenta la cola | 1 | Pasa |
| `test_un_proveedor_con_el_procesamiento_apagado_tampoco` | Es el efecto práctico del interruptor de A6: le seguís comprando, pero su casilla no entra al pipeline. | 1 | Pasa |
| `test_el_mismo_correo_dos_veces_no_se_duplica` | Un ciclo que se ejecuta dos veces —porque se reintentó, o porque el mensaje quedó sin marcar en la casilla— no puede encolar dos filas. | 1 | Pasa |
| `test_reingerir_no_pisa_un_correo_ya_resuelto` | Si lo pisara, un correo ya descartado volvería a la cola en cada pasada. | 1 | Pasa |
| `test_un_correo_sin_identificador_no_entra` | Sin `Message-ID` no hay clave de idempotencia, y cada pasada lo volvería a encolar. | 1 | Pasa |
| `test_un_aviso_de_demora_entra_igual_a_la_cola` | No se procesa distinto todavía, pero entra: es la razón de ser de la cola de aprobación —por la casilla del proveedor no llegan solo novedades—. | 1 | Pasa |
| `test_la_cola_lista_los_correos` | La cola lista los correos | 1 | Pasa |
| `test_la_cola_cuenta_los_pendientes` | La cola cuenta los pendientes | 1 | Pasa |
| `test_la_cola_vacia_no_es_un_error` | Es el resultado normal de un ciclo sin novedades, que el propio CU-ALT-NOV contempla en E6. | 1 | Pasa |
| `test_el_buscador_de_la_cola_filtra` | El buscador de la cola filtra | 1 | Pasa |
| `test_la_ficha_muestra_el_contenido_extraido` | Es lo que permite darse cuenta de que la extracción salió mal antes de gastar un solo ciclo del modelo. | 1 | Pasa |
| `test_la_ficha_muestra_las_portadas_embebidas` | La ficha muestra las portadas embebidas | 1 | Pasa |
| `test_la_ficha_muestra_que_va_a_heredar_el_borrador` | Si el proveedor tiene la editorial equivocada, todo lo que salga de este correo va a nacer mal: hay que poder verlo antes de aprobar. | 1 | Pasa |
| `test_descartar_lo_saca_de_la_cola` | Descartar lo saca de la cola | 1 | Pasa |
| `test_el_motivo_del_descarte_es_obligatorio` | Mismo criterio que el rechazo de un borrador en CU-ALT-REV: una cola llena de descartes sin explicación no sirve para entender nada después. | 1 | Pasa |
| `test_un_motivo_de_una_letra_no_alcanza` | Un motivo de una letra no alcanza | 1 | Pasa |
| `test_el_descarte_queda_auditado` | El descarte queda auditado | 1 | Pasa |
| `test_un_correo_ya_resuelto_no_se_vuelve_a_resolver` | El doble envío del formulario es el caso normal, no el raro. | 1 | Pasa |
| `test_la_ficha_de_un_resuelto_no_ofrece_descartarlo` | La ficha de un resuelto no ofrece descartarlo | 1 | Pasa |
| `test_el_get_de_la_ficha_no_resuelve_nada` | El get de la ficha no resuelve nada | 1 | Pasa |
| `test_la_cola_es_solo_del_administrador` | La cola es solo del administrador | 2 | Pasa |
| `test_el_menu_enlaza_la_cola` | El menu enlaza la cola | 1 | Pasa |

### `test_comando_extraer.py`

El comando `extraer_novedades`: la puerta por la que hoy corre el pipeline.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_sin_argumentos_no_procesa_nada` | El modelo corre local y cada pasada son minutos de GPU: un comando que procese todo por omisión es la forma más rápida de gastar una tarde. | 1 | Pasa |
| `test_un_correo_inexistente_lo_dice_en_vez_de_callarse` | Un correo inexistente lo dice en vez de callarse | 1 | Pasa |
| `test_procesa_el_correo_que_se_le_nombra` | Procesa el correo que se le nombra | 1 | Pasa |
| `test_con_pendientes_recorre_la_cola` | Con pendientes recorre la cola | 1 | Pasa |
| `test_una_cola_vacia_lo_informa` | Una cola vacia lo informa | 1 | Pasa |
| `test_informa_por_separado_lo_entendido_y_lo_generado` | Es la diferencia que dice si el pipeline está funcionando o si el catálogo ya tenía todo. | 1 | Pasa |
| `test_enumera_lo_omitido_con_su_motivo` | Enumera lo omitido con su motivo | 1 | Pasa |
| `test_informa_los_reparos_del_modelo` | Informa los reparos del modelo | 1 | Pasa |
| `test_un_correo_que_no_era_de_novedades_lo_aclara` | Sin esta línea, cero borradores se leería como un fallo del pipeline. | 1 | Pasa |
| `test_si_el_modelo_esta_caido_lo_dice_y_no_genera_nada` | Si el modelo esta caido lo dice y no genera nada | 1 | Pasa |
| `test_la_salida_es_ascii_aunque_el_correo_traiga_de_todo` | El asunto, el título y los motivos vienen del proveedor y del modelo: pueden traer kanji, tildes o comillas angulares. | 1 | Pasa |

### `test_concurrencia_correos.py`

`CO-017` E1 bajo concurrencia real: dos Administradores aprueban el mismo correo a la vez.

**Casos de prueba que ejecuta:** CP-08.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO017_dos_aprobaciones_simultaneas_procesan_una_sola_vez` | CO017 dos aprobaciones simultaneas procesan una sola vez | 1 | Pasa |

### `test_concurrencia_proveedores.py`

Doble clic en el alta de un proveedor (`CO-060`): dos envíos idénticos a la vez.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO060_doble_envio_del_alta_deja_uno_y_avisa_sin_error` | CO060 doble envio del alta deja uno y avisa sin error | 1 | Pasa |

### `test_consulta_proveedores.py`

CU-PRV-CON — Consultar Proveedores: el listado y la ficha.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_listado_muestra_los_proveedores` | El listado muestra los proveedores | 1 | Pasa |
| `test_el_listado_sale_ordenado_alfabeticamente` | CU-PRV-CON paso 2: la vista por defecto es alfabética. | 1 | Pasa |
| `test_cada_fila_trae_la_cantidad_de_productos_vinculados` | Lo pide el paso 2, y se anota en la consulta: contarlo por fila serían tantas consultas extra como proveedores haya. | 1 | Pasa |
| `test_el_buscador_encuentra_por_los_tres_campos` | Paso 3: búsqueda por texto libre. | 3 | Pasa |
| `test_el_filtro_de_estado_funciona` | El filtro de estado funciona | 1 | Pasa |
| `test_un_estado_inventado_se_ignora` | Un valor arbitrario en la query string no rompe ni filtra de más. | 1 | Pasa |
| `test_el_parcial_devuelve_solo_el_fragmento_de_la_tabla` | El parcial devuelve solo el fragmento de la tabla | 1 | Pasa |
| `test_sin_proveedores_ofrece_el_acceso_directo_al_alta` | E2 del CU: la vista vacía informa y ofrece el camino a CU-PRV-ALT. | 1 | Pasa |
| `test_un_filtro_sin_resultados_ofrece_limpiarlo` | E1 del CU. | 1 | Pasa |
| `test_consultar_no_genera_entrada_de_auditoria` | Postcondición explícita del CU: solo lectura. | 1 | Pasa |
| `test_la_ficha_muestra_los_datos_de_contacto` | La ficha muestra los datos de contacto | 1 | Pasa |
| `test_la_ficha_lista_los_productos_vinculados` | La ficha lista los productos vinculados | 1 | Pasa |
| `test_la_ficha_dice_si_el_correo_se_reconoce_como_remitente` | Es la consecuencia práctica del estado, y no se deduce sola de la palabra "Inactivo". | 1 | Pasa |
| `test_la_ficha_encadena_las_acciones_del_modulo` | CU-PRV-CON paso 5: desde la ficha se inician CU-PRV-EDI y CU-PRV-BAJ. | 1 | Pasa |
| `test_la_ficha_de_un_inactivo_ofrece_reactivar_y_no_dar_de_baja` | La ficha de un inactivo ofrece reactivar y no dar de baja | 1 | Pasa |
| `test_la_ficha_avisa_que_falta_el_historial_de_restock` | El paso 4 del CU lo pide, pero el módulo de Restock no existe. | 1 | Pasa |
| `test_el_listado_no_filtra_datos_a_otros_roles` | El listado no filtra datos a otros roles | 2 | Pasa |
| `test_el_menu_del_administrador_enlaza_proveedores` | El menu del administrador enlaza proveedores | 1 | Pasa |

### `test_contratos_04_proveedores.py`

Pruebas de contrato del módulo 04 · Proveedores (cola de correos y abandono).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO017_aprobar_pasa_el_correo_de_pendiente_a_procesado` | CO017 aprobar pasa el correo de pendiente a procesado | 1 | Pasa |
| `test_CO017_crea_un_borrador_por_producto_con_sus_asociaciones` | CO017 crea un borrador por producto con sus asociaciones | 1 | Pasa |
| `test_CO017_la_operacion_queda_auditada` | CO017 la operacion queda auditada | 1 | Pasa |
| `test_CO017_el_resumen_informa_generados_omitidos_y_reparos` | CO017 el resumen informa generados omitidos y reparos | 1 | Pasa |
| `test_CO017_E1_un_correo_ya_tomado_por_otro_no_se_vuelve_a_procesar` | Otro Administrador lo aprobó mientras éste lo tenía abierto. | 1 | Pasa |
| `test_CO017_E1_la_segunda_aprobacion_encuentra_el_correo_tomado` | La transición es condicionada: sólo la primera aprobación pasa. | 1 | Pasa |
| `test_CO017_E4_si_el_servicio_no_responde_el_correo_falla_y_queda_en_la_cola` | CO017 E4 si el servicio no responde el correo falla y queda en la cola | 1 | Pasa |
| `test_CO017_E4_si_no_identifica_ningun_producto_el_correo_falla` | CO017 E4 si no identifica ningun producto el correo falla | 1 | Pasa |
| `test_CO017_por_la_direccion_real_con_rol_cajero_no_procesa` | CO017 por la direccion real con rol cajero no procesa | 1 | Pasa |
| `test_CO017_no_acepta_get` | Una operación con efecto no se dispara con un enlace. | 1 | Pasa |
| `test_CO018_descartar_registra_estado_motivo_y_responsable` | CO018 descartar registra estado motivo y responsable | 1 | Pasa |
| `test_CO018_E3_sin_motivo_no_se_descarta` | CO018 E3 sin motivo no se descarta | 1 | Pasa |
| `test_CO019_reemplaza_solo_los_borradores_abiertos` | CO019 reemplaza solo los borradores abiertos | 1 | Pasa |
| `test_CO019_queda_auditado` | CO019 queda auditado | 1 | Pasa |
| `test_CO019_si_la_extraccion_falla_los_abiertos_se_conservan` | Las excepciones de CO-017 aplican: un corte del servicio no borra trabajo. | 1 | Pasa |
| `test_CO019_un_correo_pendiente_no_se_reprocesa` | Precondición: el correo está Procesado o Falló el procesamiento. | 1 | Pasa |
| `test_CO019_la_ficha_ofrece_reprocesar_solo_si_corresponde` | CO019 la ficha ofrece reprocesar solo si corresponde | 1 | Pasa |
| `test_CO157_consultar_la_cola_no_modifica_nada` | CO157 consultar la cola no modifica nada | 1 | Pasa |
| `test_CO157_por_la_direccion_real_con_rol_cajero_se_deniega` | CO157 por la direccion real con rol cajero se deniega | 1 | Pasa |
| `test_CO158_abrir_la_ficha_muestra_el_contenido_y_no_modifica_nada` | CO158 abrir la ficha muestra el contenido y no modifica nada | 1 | Pasa |
| `test_CO158_la_ficha_de_un_pendiente_ofrece_aprobar_y_descartar` | CO158 la ficha de un pendiente ofrece aprobar y descartar | 1 | Pasa |
| `test_CO156_abandonar_la_confirmacion_no_cambia_el_proveedor` | Postcondición: «ninguna. | 2 | Pasa |

### `test_diagnostico_llm.py`

La pantalla de diagnóstico del modelo de lenguaje.

**Casos de prueba que ejecuta:** CP-07.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_muestra_el_servicio_en_linea_con_sus_modelos` | Muestra el servicio en linea con sus modelos | 1 | Pasa |
| `test_muestra_el_servicio_caido_cuando_no_responde` | `pedir` devuelve `None` sin conexión. | 1 | Pasa |
| `test_el_estado_se_consulta_con_un_timeout_corto` | No con el del modelo. | 1 | Pasa |
| `test_el_catalogo_de_modelos_se_deduce_de_la_direccion_del_chat` | Se deduce en vez de pedir otra variable de entorno: son del mismo servidor, y configurar las dos es una oportunidad más de que queden apuntando a lugares distintos. | 1 | Pasa |
| `test_una_direccion_que_no_parece_esa_api_lo_dice` | Una direccion que no parece esa api lo dice | 1 | Pasa |
| `test_un_servicio_sin_modelos_cargados_se_distingue_de_uno_caido` | Responde, así que no está caído — pero no va a poder generar nada. | 1 | Pasa |
| `test_muestra_con_que_esta_configurado` | Muestra con que esta configurado | 1 | Pasa |
| `test_la_muestra_viene_cargada_y_es_editable` | El valor de la pantalla no es correr una prueba fija sino poder pegar el contenido de un correo que salió mal y ver qué entiende. | 1 | Pasa |
| `test_cada_carga_trae_una_muestra_distinta` | Mostrar siempre los mismos tres tomos deja la duda de si el modelo los está reconociendo en vez de leerlos. | 1 | Pasa |
| `test_la_muestra_trae_un_isbn_corrupto_a_proposito` | Es la mitad interesante de la demostración: se ve que el sistema lo detecta, no solo que el modelo copia bien. | 1 | Pasa |
| `test_probar_muestra_lo_que_el_modelo_entendio` | Probar muestra lo que el modelo entendio | 1 | Pasa |
| `test_la_prueba_declara_los_identificadores_de_portada_de_la_muestra` | Sin declararlos, la comprobación de portada inexistente no tendría contra qué comparar y la demostración mostraría una validación que no valida. | 1 | Pasa |
| `test_los_reparos_se_muestran_en_pantalla` | Es lo que hace visible que el sistema le desconfía al modelo. | 1 | Pasa |
| `test_muestra_el_prompt_que_recibe_el_modelo` | Con la versión, que es lo que vuelve comparable un resultado con otro. | 1 | Pasa |
| `test_muestra_la_respuesta_en_crudo` | Cuando algo sale raro es lo único que explica por qué. | 1 | Pasa |
| `test_informa_cuanto_tardo` | Con un modelo local, la diferencia entre dos segundos y dos minutos decide si el pipeline necesita una cola de verdad. | 1 | Pasa |
| `test_un_contenido_vacio_no_se_manda_al_modelo` | Gastar una pasada del modelo en una caja vacía es tirar minutos de GPU. | 1 | Pasa |
| `test_si_el_servicio_esta_caido_ni_se_intenta_la_extraccion` | Intentarla esperaría el timeout largo entero —minutos— para fallar por lo mismo que el chequeo de estado ya sabe. | 1 | Pasa |
| `test_una_respuesta_ilegible_se_distingue_del_servicio_caido` | Se arreglan en lugares distintos: uno es infraestructura, el otro es el prompt o el modelo elegido. | 1 | Pasa |
| `test_la_pantalla_es_solo_del_administrador` | Deja ver la configuración del servicio y permite gastarle tiempo de cómputo: no es información ni una acción para cualquier rol. | 2 | Pasa |
| `test_el_menu_la_enlaza_dentro_de_proveedores` | El menu la enlaza dentro de proveedores | 1 | Pasa |
| `test_la_pantalla_muestra_el_periodo_que_copio_el_modelo` | La pantalla muestra el periodo que copio el modelo | 1 | Pasa |
| `test_la_pantalla_muestra_la_fecha_interpretada` | Son dos valores encadenados y hay que ver los dos: un período que el modelo leyó bien y el intérprete no entendió se arregla en otro lugar que uno que el modelo no encontró. | 1 | Pasa |
| `test_un_periodo_ilegible_se_ve_en_la_pantalla` | Su efecto —todos los borradores naciendo Activos— es de los que no dan ningún síntoma, así que tiene que decirse acá. | 1 | Pasa |
| `test_sin_periodo_la_pantalla_lo_dice_sin_alarmar` | No anunciar fecha es el caso normal, no un problema. | 1 | Pasa |
| `test_la_pantalla_dice_con_que_estado_nacerian_los_borradores` | Es la consecuencia concreta del período, y es lo que se viene a mirar. | 1 | Pasa |
| `test_un_periodo_pasado_deja_los_borradores_activos` | Un periodo pasado deja los borradores activos | 1 | Pasa |
| `test_la_pantalla_muestra_la_confianza_que_no_es_alta` | La pantalla muestra la confianza que no es alta | 1 | Pasa |
| `test_la_muestra_de_la_pantalla_anuncia_un_periodo_futuro` | Si anunciara una fecha pasada, el banco de pruebas nunca ejercitaría la rama de Pre-venta, que es de la que hay que desconfiar. | 1 | Pasa |
| `test_solo_se_muestra_el_modelo_configurado` | Solo se muestra el modelo configurado | 1 | Pasa |
| `test_se_avisa_si_el_servidor_no_ofrece_el_modelo_configurado` | Adelanta el 404 más común —un identificador mal copiado— antes de gastar una corrida y recibirlo en medio de un procesamiento. | 1 | Pasa |
| `test_con_el_modelo_disponible_se_dice_que_lo_ofrece` | Con el modelo disponible se dice que lo ofrece | 1 | Pasa |
| `test_sin_modelo_declarado_se_muestran_los_cargados` | Ahí sí la lista **es** la respuesta: es lo que el servidor va a contestar. | 1 | Pasa |
| `test_el_total_de_modelos_se_dice_como_cifra` | La cifra sirve —confirma que la dirección apunta a la API que se cree—; la lista de nombres, no. | 1 | Pasa |
| `test_el_modo_no_nombra_proveedores` | Los dos valores describen dónde corre el modelo; qué empresa lo hospeda es un dato de la dirección. | 1 | Pasa |

### `test_edicion_proveedor.py`

CU-PRV-EDI — Editar Proveedor Editorial.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_se_editan_los_datos_de_contacto` | Se editan los datos de contacto | 1 | Pasa |
| `test_cambiar_el_correo_sin_confirmar_es_rechazado` | La advertencia del CU no es informativa: es una puerta. | 1 | Pasa |
| `test_cambiar_el_correo_confirmado_redirige_el_pipeline` | Postcondición del CU: CU-ALT-NOV empieza a procesar el nuevo y deja de procesar el anterior a partir de la confirmación. | 1 | Pasa |
| `test_editar_otros_campos_no_pide_confirmacion` | La confirmación es del cambio de correo, no de la edición: pedirla siempre la convertiría en un clic automático. | 1 | Pasa |
| `test_el_alta_no_ofrece_la_confirmacion_de_cambio_de_correo` | En un alta no hay correo anterior que invalidar. | 1 | Pasa |
| `test_un_correo_de_otro_proveedor_es_rechazado` | E2: no se puede pisar el remitente de otro. | 1 | Pasa |
| `test_guardar_sin_cambiar_el_correo_propio_no_choca_consigo_mismo` | Guardar sin cambiar el correo propio no choca consigo mismo | 1 | Pasa |
| `test_un_proveedor_inactivo_si_se_puede_editar` | La precondición de CU-PRV-EDI dice "cualquier estado", y acá no hay nada que congelar: un proveedor de baja no habilita nada mientras lo esté, porque el filtro de remitentes mira el estado antes que el correo. | 1 | Pasa |
| `test_la_auditoria_guarda_los_valores_anteriores_y_nuevos` | El CU lo pide explícitamente: con solo el estado final no se puede reconstruir qué pasó. | 1 | Pasa |
| `test_guardar_sin_cambios_no_genera_entrada_de_auditoria` | Un log lleno de entradas vacías esconde las que importan. | 1 | Pasa |
| `test_solo_el_administrador_edita_proveedores` | Solo el administrador edita proveedores | 2 | Pasa |

### `test_extraccion.py`

La extracción del modelo: el prompt, la validación y lo que se guarda.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_extrae_los_productos_de_un_correo_de_novedades` | Extrae los productos de un correo de novedades | 1 | Pasa |
| `test_el_resultado_dice_con_que_version_del_prompt_se_extrajo` | Un borrador de marzo y otro de junio no son comparables, y cuando algo salga raro la primera pregunta va a ser con cuál se hizo. | 1 | Pasa |
| `test_el_esquema_le_exige_al_servidor_la_forma_de_la_respuesta` | Es la primera de las tres defensas: con el esquema declarado, el modelo **no puede** emitir algo que no encaje, y la validación deja de tener que ocuparse de la estructura. | 1 | Pasa |
| `test_el_contenido_del_correo_va_separado_de_las_instrucciones` | Mezclarlos haría que el texto de un correo se pueda leer como una instrucción más. | 1 | Pasa |
| `test_un_aviso_de_demora_no_produce_productos` | Si el modelo clasificó "demora" y devolvió productos igual, se ignoran: mezclar las dos cosas es el error que la clasificación viene a evitar. | 1 | Pasa |
| `test_una_intencion_inventada_se_toma_como_otro` | Una intencion inventada se toma como otro | 1 | Pasa |
| `test_un_isbn_que_no_verifica_se_descarta_con_su_reparo` | Es la defensa que atrapa un ISBN alucinado. | 1 | Pasa |
| `test_un_isbn_con_guiones_se_normaliza` | Un isbn con guiones se normaliza | 1 | Pasa |
| `test_sin_isbn_no_hay_reparo` | No tenerlo es válido; inventarlo no. | 1 | Pasa |
| `test_una_portada_que_no_esta_en_el_correo_se_ignora` | Sin esta comprobación, el borrador quedaría apuntando a una imagen que no existe y el fallo aparecería recién al intentar adjuntarla. | 1 | Pasa |
| `test_el_marcador_completo_tambien_se_acepta` | El modelo a veces devuelve el marcador entero en vez del identificador. | 1 | Pasa |
| `test_el_precio_se_lee_venga_como_venga` | El prompt lo pide limpio, pero llega con signo y separador de miles igual. | 4 | Pasa |
| `test_un_precio_ilegible_deja_el_producto_incompleto` | Un precio ilegible deja el producto incompleto | 3 | Pasa |
| `test_un_precio_en_cero_se_rechaza` | Un precio en cero se rechaza | 1 | Pasa |
| `test_el_volumen_se_lee_aunque_venga_con_texto` | El volumen se lee aunque venga con texto | 1 | Pasa |
| `test_un_volumen_ilegible_deja_su_reparo` | Un tomo único puede venir sin volumen; "primavera" es otra cosa. | 1 | Pasa |
| `test_un_producto_sin_titulo_lo_dice` | Sin título no hay forma de identificarlo, ni siquiera para revisarlo a mano en la cola. | 1 | Pasa |
| `test_el_resumen_cuenta_completos_incompletos_y_con_reparos` | Es lo que va al log de auditoría y a la salida del comando: sin eso, la única forma de saber cómo salió una pasada es abrir el correo. | 1 | Pasa |
| `test_se_declara_el_modelo_cuando_esta_configurado` | Vacío significa "el que esté cargado", que es lo cómodo con LM Studio; contra un servicio remoto hay que nombrarlo. | 1 | Pasa |
| `test_una_confianza_inventada_se_toma_como_baja` | Al alza sería peor: un valor raro leído como "alta" haría que un dato dudoso se confirme en lote sin que nadie lo mire (CU-ALT-REV). | 1 | Pasa |
| `test_sin_confianza_declarada_no_rompe` | Sin confianza declarada no rompe | 1 | Pasa |
| `test_si_el_servicio_no_responde_no_se_extrae_nada` | `pedir` devuelve `None` cuando no hay conexión, y eso tiene que llegar como un motivo, no como una excepción: el ciclo sigue con el correo siguiente. | 1 | Pasa |
| `test_una_respuesta_que_no_es_json_se_reporta_como_ilegible` | Pasa cuando el modelo envuelve el JSON en prosa. | 1 | Pasa |
| `test_un_modelo_de_razonamiento_deja_la_respuesta_en_otro_campo` | Caso real, no hipotético: `qwen3.5` en LM Studio devolvió el JSON entero en `reasoning_content` con `content` vacío. | 1 | Pasa |
| `test_si_vienen_los_dos_campos_manda_el_principal` | `reasoning_content` es el razonamiento, no la respuesta: solo se usa cuando no hay otra cosa. | 1 | Pasa |
| `test_un_error_en_el_cuerpo_se_reporta_como_rechazo` | Antes salía como "respuesta ilegible" y mandaba a revisar el prompt, que estaba bien. | 1 | Pasa |
| `test_una_respuesta_sin_forma_no_rompe` | La respuesta viene de afuera: un servidor que conteste distinto no puede tumbar el ciclo con un `KeyError`. | 1 | Pasa |
| `test_el_texto_crudo_se_conserva_aunque_no_se_haya_podido_leer` | Es lo único con lo que se puede entender por qué falló; sin él, ajustar el prompt es adivinar. | 1 | Pasa |
| `test_una_extraccion_exitosa_deja_el_correo_procesado` | Una extraccion exitosa deja el correo procesado | 1 | Pasa |
| `test_un_correo_sin_productos_identificados_queda_fallido` | `CO-017` E4: «no identifica ningún producto» es un fallo, y el correo queda en la cola para reprocesarlo. | 1 | Pasa |
| `test_si_el_servicio_esta_caido_el_correo_queda_fallido` | Si el servicio esta caido el correo queda fallido | 1 | Pasa |
| `test_el_motivo_distingue_el_servicio_caido_de_la_respuesta_ilegible` | Se arreglan en lugares distintos: uno es infraestructura, el otro es el prompt o el modelo elegido. | 1 | Pasa |
| `test_las_portadas_del_correo_se_usan_para_validar_la_extraccion` | El correo sabe qué imágenes trae, y eso es lo que permite descartar una inventada. | 1 | Pasa |
| `test_reprocesar_pisa_la_extraccion_anterior` | Ajustar el prompt y volver a correr tiene que dejar el resultado nuevo, no dos resultados conviviendo. | 1 | Pasa |
| `test_la_ficha_muestra_lo_que_entendio_el_modelo` | Es el paso siguiente de la misma idea que muestra el contenido extraído: cada etapa del pipeline se puede mirar antes de que la próxima gaste algo. | 1 | Pasa |
| `test_la_fecha_se_lee_venga_como_venga` | La fecha se lee venga como venga | 7 | Pasa |
| `test_una_fecha_que_no_se_entiende_devuelve_nada` | Una fecha que no se entiende devuelve nada | 7 | Pasa |
| `test_el_periodo_del_correo_se_interpreta` | El correo anuncia el período en la prosa de alrededor de la tabla, no en cada fila: es de ahí que los borradores heredan la fecha. | 1 | Pasa |
| `test_un_correo_sin_periodo_no_deja_reparo` | No anunciar fecha es el caso normal, no un problema: esos borradores nacen Activos, que es exactamente lo que pide CU-ALT-NOV paso 6. | 1 | Pasa |
| `test_un_periodo_ilegible_deja_su_reparo` | Sin esto, todos los borradores del correo nacerían Activos y no habría forma de saber por qué. | 1 | Pasa |
| `test_la_fecha_propia_de_una_fila_pisa_al_periodo` | La fecha propia de una fila pisa al periodo | 1 | Pasa |
| `test_una_fecha_de_fila_ilegible_deja_reparo_en_ese_producto` | Una fecha de fila ilegible deja reparo en ese producto | 1 | Pasa |
| `test_el_periodo_de_un_correo_que_no_es_de_novedades_se_ignora` | Mezclar las dos cosas es el error que la clasificación viene a evitar. | 1 | Pasa |
| `test_el_periodo_y_las_fechas_quedan_en_lo_que_se_guarda` | La ficha las muestra, y el generador de borradores las lee de acá. | 1 | Pasa |

### `test_lectura_de_correos.py`

Lectura de un correo de novedades: de bytes MIME a texto parseable.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_el_remitente_sale_pelado_aunque_venga_con_nombre_de_fantasia` | Un `From` real llega como `"Novedades Ivrea" <novedades@ivrea.test>` y el matcheo del proveedor compara direcciones, no cadenas enteras. | 1 | Pasa |
| `test_el_remitente_se_normaliza_a_minuscula` | La caja de una dirección no la distingue, y el proveedor se guarda en minúscula: comparar en crudo dejaría afuera mensajes legítimos. | 1 | Pasa |
| `test_se_leen_asunto_identificador_y_fecha` | Se leen asunto identificador y fecha | 1 | Pasa |
| `test_un_correo_sin_identificador_lo_deja_vacio` | Sin `Message-ID` no hay forma de saber si un correo ya se leyó. | 1 | Pasa |
| `test_cada_producto_queda_en_una_fila_con_sus_columnas` | Es la corrección 15: aplanar a texto plano rompe la asociación fila-columna y el modelo empieza a atribuirle a un tomo el precio del siguiente. | 1 | Pasa |
| `test_el_precio_queda_en_la_misma_fila_que_su_titulo` | El error que la corrección evita no da ningún síntoma: se descubre tres meses después mirando un precio raro. | 1 | Pasa |
| `test_la_prosa_que_envuelve_la_tabla_no_se_pierde` | Las tablas vienen anidadas —el HTML de un correo maqueta con tablas— y ahí vive el período del envío, que es de donde los borradores van a heredar la fecha. | 1 | Pasa |
| `test_una_fila_de_una_sola_celda_no_parece_un_producto` | El encabezado con el logo es maquetado, no datos. | 1 | Pasa |
| `test_la_hoja_de_estilos_no_entra_al_contenido` | La hoja de estilos no entra al contenido | 1 | Pasa |
| `test_un_correo_de_prosa_se_lee_como_prosa` | Un aviso de demora no tiene tabla, y tiene que salir legible igual: es el otro tipo de correo que llega por la misma casilla. | 1 | Pasa |
| `test_las_portadas_vienen_dentro_del_correo` | Es la corrección 16: CU-ALT-NOV supone una descarga por URL, y acá no hay nada que descargar. | 1 | Pasa |
| `test_cada_imagen_queda_marcada_dentro_de_la_fila_de_su_producto` | Sin el marcador habría que correlacionar por orden, y el logo del encabezado corre todo un lugar. | 1 | Pasa |
| `test_los_marcadores_coinciden_con_las_partes_del_correo` | Si no coincidieran, la resolución fallaría en silencio y el borrador quedaría con "Imagen pendiente" sin que nadie entienda por qué. | 1 | Pasa |
| `test_el_identificador_se_compara_venga_como_venga` | El `src` del HTML puede venir codificado y la cabecera de la parte llega entre ángulos: sin normalizar los dos lados, el marcador nunca encontraría su imagen. | 4 | Pasa |
| `test_un_correo_sin_imagenes_se_lee_igual` | Un correo sin imagenes se lee igual | 1 | Pasa |
| `test_un_html_mal_cerrado_no_pierde_la_ultima_fila` | Los correos mal formados llegan, y perder el último producto en silencio es peor que fallar. | 1 | Pasa |
| `test_un_cuerpo_vacio_no_rompe` | Un cuerpo vacio no rompe | 1 | Pasa |
| `test_una_fecha_ilegible_no_tumba_la_lectura` | La fecha es un dato de presentación; el orden de la cola lo da cuándo lo recibimos nosotros. | 1 | Pasa |
| `test_una_imagen_por_enlace_tambien_deja_rastro_en_la_fila` | Las dos formas conviven en la práctica. | 1 | Pasa |
| `test_una_imagen_sin_origen_ni_descripcion_se_ignora` | Un espaciador de un pixel no es un dato: meterlo en la fila agregaría una columna que no existe. | 1 | Pasa |
| `test_una_celda_sin_fila_no_pierde_su_texto` | HTML roto, pero el texto que traía se conserva igual. | 1 | Pasa |
| `test_un_correo_solo_de_texto_plano_se_lee_igual` | Estos proveedores mandan HTML, pero un correo sin parte HTML no puede quedar sin contenido: se trata su texto como párrafos. | 1 | Pasa |

### `test_monitoreo_casilla.py`

`CO-016 ejecutarCicloMonitoreoCasilla` (plan 00, A1).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO016_encola_lo_de_un_proveedor_habilitado_sin_procesarlo` | CO016 encola lo de un proveedor habilitado sin procesarlo | 1 | Pasa |
| `test_CO016_E1_un_remitente_no_registrado_no_se_encola_y_el_ciclo_sigue` | CO016 E1 un remitente no registrado no se encola y el ciclo sigue | 1 | Pasa |
| `test_CO016_I16_correr_dos_veces_no_encola_dos_veces` | CO016 I16 correr dos veces no encola dos veces | 1 | Pasa |
| `test_CO016_E3_sin_conexion_avisa_al_administrador_y_no_encola` | CO016 E3 sin conexion avisa al administrador y no encola | 1 | Pasa |
| `test_CO016_respeta_la_frecuencia_configurada` | CO016 respeta la frecuencia configurada | 1 | Pasa |
| `test_CO016_sin_casilla_configurada_no_hace_nada` | CO016 sin casilla configurada no hace nada | 1 | Pasa |
| `test_CO016_corre_en_el_temporizador` | CO016 corre en el temporizador | 1 | Pasa |

### `test_muestras.py`

El generador de contenido de muestra para el banco de pruebas.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_todo_isbn_generado_lo_acepta_la_verificacion` | Quinientos valores, dos implementaciones independientes. | 1 | Pasa |
| `test_todo_isbn_roto_lo_rechaza_la_verificacion` | La otra mitad: que el generador de rotos genere rotos de verdad. | 1 | Pasa |
| `test_el_roto_difiere_del_valido_en_un_solo_digito` | Es el error que se comete al transcribir, y el que la verificación tiene que atrapar. | 1 | Pasa |
| `test_numeros_distintos_dan_isbn_distintos` | Si se repitieran, una muestra con varios productos chocaría contra la restricción de unicidad al confirmarlos. | 1 | Pasa |
| `test_los_isbn_empiezan_como_uno_argentino` | 978 de Bookland más 987 de Argentina: que la muestra arranque bien hace que se parezca a lo que llega de verdad. | 1 | Pasa |
| `test_la_muestra_tiene_la_forma_de_un_correo_extraido` | La muestra tiene la forma de un correo extraido | 1 | Pasa |
| `test_trae_las_trampas_de_un_correo_real` | Probar contra un correo ideal no prueba nada: el logo no es un producto y la fila de encabezado tampoco. | 1 | Pasa |
| `test_exactamente_un_producto_trae_el_isbn_roto` | Ni ninguno —no se vería la validación— ni todos, que haría parecer que el modelo lee mal siempre. | 1 | Pasa |
| `test_cual_sale_roto_no_es_siempre_el_mismo` | Si fuera siempre el último, alcanzaría con mirar la última fila para saber qué va a pasar antes de correr la prueba. | 1 | Pasa |
| `test_declara_los_identificadores_de_portada_que_trae` | Sin ellos, la comprobación de portada inexistente no tendría contra qué comparar y la demostración mostraría una validación que no valida. | 1 | Pasa |
| `test_la_misma_semilla_da_la_misma_muestra` | Un test que necesite una muestra conocida tiene que poder pedirla. | 1 | Pasa |
| `test_sin_semilla_las_muestras_difieren` | Sin semilla las muestras difieren | 1 | Pasa |
| `test_se_puede_pedir_la_cantidad_de_productos` | Se puede pedir la cantidad de productos | 3 | Pasa |
| `test_el_periodo_anunciado_es_futuro` | Con una fecha ya pasada, todos los borradores nacen Activos y el banco de pruebas nunca ejercita la rama de Pre-venta — que es la que tiene consecuencias: un producto que no llegó figurando disponible no da ningún síntoma hasta que alguien lo compra. | 1 | Pasa |
| `test_el_periodo_se_declara_y_coincide_con_el_texto` | La muestra dice qué debería salir de ella, para que verificarlo no obligue a volver a interpretar el texto acá — eso compararía la muestra consigo misma. | 1 | Pasa |
| `test_el_periodo_varia_entre_muestras` | Mismo motivo que los títulos y los ISBN: un valor fijo deja la duda de si el modelo lo lee o lo reconoce de verlo siempre igual. | 1 | Pasa |
| `test_el_vencimiento_de_pedidos_es_un_señuelo_sin_año` | Es una segunda fecha en la misma prosa, y el modelo tiene que copiar el período y no el vencimiento. | 1 | Pasa |

### `test_pipeline_de_novedades.py`

Lo que el proveedor le aporta al procesamiento automático de CU-ALT-NOV.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_un_proveedor_con_las_novedades_apagadas_no_es_remitente_valido` | El caso que justifica que el campo exista: le seguís comprando, pero sus correos no alimentan el pipeline. | 1 | Pasa |
| `test_apagarlo_no_lo_da_de_baja` | Son dos cosas distintas: el proveedor sigue activo para todo lo demás —pedidos de restock, contacto, historial—, solo que su casilla no se lee. | 1 | Pasa |
| `test_con_novedades_habilitadas_pide_las_dos_condiciones` | Con novedades habilitadas pide las dos condiciones | 1 | Pasa |
| `test_el_alta_lo_deja_habilitado_por_defecto` | Postcondición de CU-PRV-ALT: el correo queda habilitado como remitente válido. | 1 | Pasa |
| `test_se_puede_dar_de_alta_con_el_procesamiento_apagado` | Sirve para registrar al proveedor primero y probar el parseo después. | 1 | Pasa |
| `test_el_proveedor_declara_la_editorial_bajo_la_que_publica` | El proveedor declara la editorial bajo la que publica | 1 | Pasa |
| `test_sin_editorial_declarada_el_proveedor_trae_varias` | El vacío significa algo: distribuidora o servicio conjunto, y ahí sí la editorial se extrae de cada correo. | 1 | Pasa |
| `test_solo_se_ofrecen_editoriales_y_tipos_activos` | Vincular un proveedor a una editorial dada de baja dejaría sus borradores apuntando a algo que ya no aparece en ningún desplegable del alta. | 1 | Pasa |
| `test_el_alta_ofrece_crear_la_editorial_sin_salir_de_la_pantalla` | Vincularlo a una editorial que todavía no existe es el caso normal la primera vez. | 1 | Pasa |
| `test_apagar_el_procesamiento_queda_auditado` | Sin esto, "por qué de Ivrea no llega nada desde marzo" sería una pregunta sin respuesta: el pipeline deja de generar borradores en silencio. | 1 | Pasa |
| `test_cambiar_la_editorial_queda_auditado_con_los_dos_valores` | Cambia bajo qué sello nacen todos los borradores siguientes. | 1 | Pasa |
| `test_la_ficha_distingue_los_dos_motivos_por_los_que_no_se_procesa` | "Activo" ya no alcanza para responder por qué de un proveedor no llega nada, y los dos motivos se arreglan en lugares distintos. | 1 | Pasa |
| `test_la_ficha_muestra_la_cabecera_de_sus_borradores` | La ficha muestra la cabecera de sus borradores | 1 | Pasa |
| `test_la_ficha_de_una_distribuidora_lo_dice` | La ficha de una distribuidora lo dice | 1 | Pasa |
| `test_el_listado_marca_solo_al_activo_con_las_novedades_apagadas` | Es el único caso invisible: que un proveedor de baja no alimente el pipeline ya lo dice su estado, y que uno normal sí lo haga es lo esperable. | 1 | Pasa |
| `test_un_proveedor_normal_no_lleva_ninguna_marca` | Un proveedor normal no lleva ninguna marca | 1 | Pasa |
| `test_el_tablero_cuenta_aparte_los_que_alimentan_el_pipeline` | La diferencia entre "activos" y "alimentan" es justo el grupo que de otro modo quedaría invisible. | 1 | Pasa |

### `test_remitentes.py`

El filtro de remitentes válidos: lo que este módulo le aporta a CU-ALT-NOV.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_un_proveedor_activo_es_remitente_valido` | Un proveedor activo es remitente valido | 1 | Pasa |
| `test_un_proveedor_inactivo_no_lo_es` | Es el efecto de CU-PRV-BAJ: la baja saca el correo del filtro. | 1 | Pasa |
| `test_un_proveedor_con_el_procesamiento_apagado_tampoco` | La otra mitad del filtro: son dos condiciones, no una. | 1 | Pasa |
| `test_un_correo_desconocido_no_devuelve_nada` | E1 de CU-ALT-NOV: el remitente no registrado no se procesa. | 1 | Pasa |
| `test_la_busqueda_ignora_las_mayusculas` | Un encabezado de correo puede traer cualquier caja. | 2 | Pasa |
| `test_los_espacios_alrededor_no_estorban` | Los espacios alrededor no estorban | 1 | Pasa |
| `test_un_remitente_vacio_no_encuentra_nada` | Un correo sin remitente legible no puede caer por casualidad en el primer proveedor de la tabla. | 2 | Pasa |
| `test_activos_solo_devuelve_los_activos` | Activos solo devuelve los activos | 1 | Pasa |
| `test_el_proveedor_se_identifica_por_su_razon_social` | Es lo que se lee en el log de auditoría y en los desplegables. | 1 | Pasa |

---

## Tienda — `apps/tienda`

### `test_acceso_compra.py`

Control de acceso y frontera de la compra, siempre por la dirección real.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_acceso_el_personal_recibe_403_en_la_compra` | Acceso el personal recibe 403 en la compra | 10 | Pasa |
| `test_acceso_el_checkout_pide_iniciar_sesion_al_invitado` | Acceso el checkout pide iniciar sesion al invitado | 1 | Pasa |
| `test_acceso_el_resultado_de_otro_cliente_responde_404` | Acceso el resultado de otro cliente responde 404 | 1 | Pasa |
| `test_frontera_un_aviso_con_firma_invalida_se_rechaza_sin_efecto` | Frontera un aviso con firma invalida se rechaza sin efecto | 1 | Pasa |
| `test_frontera_un_aviso_sin_firma_se_rechaza` | Frontera un aviso sin firma se rechaza | 1 | Pasa |
| `test_frontera_un_aviso_firmado_ilegible_se_rechaza` | Frontera un aviso firmado ilegible se rechaza | 1 | Pasa |
| `test_frontera_un_aviso_de_una_referencia_desconocida_responde_404` | Frontera un aviso de una referencia desconocida responde 404 | 1 | Pasa |
| `test_frontera_una_pasarela_inexistente_responde_400` | Frontera una pasarela inexistente responde 400 | 1 | Pasa |
| `test_frontera_el_aviso_no_pide_csrf` | Viene de servidor a servidor: con CSRF exigido, ninguna pasarela podría avisar. | 1 | Pasa |
| `test_frontera_la_pasarela_de_prueba_no_procesa_dos_veces` | Frontera la pasarela de prueba no procesa dos veces | 1 | Pasa |
| `test_frontera_la_pasarela_de_prueba_rechaza_con_un_motivo_conocido` | Frontera la pasarela de prueba rechaza con un motivo conocido | 1 | Pasa |
| `test_frontera_un_cobro_pendiente_muestra_la_espera` | Frontera un cobro pendiente muestra la espera | 1 | Pasa |

### `test_barra_envio.py`

La barra del envío gratis (B-07-037): el cálculo y dónde se dibuja.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_la_barra_avanza_con_el_subtotal_sobre_el_minimo` | La barra avanza con el subtotal sobre el minimo | 5 | Pasa |
| `test_desde_el_minimo_el_envio_es_gratis` | Desde el minimo el envio es gratis | 1 | Pasa |
| `test_el_carrito_muestra_el_envio_la_barra_y_el_total_con_envio` | El carrito muestra el envio la barra y el total con envio | 1 | Pasa |
| `test_al_alcanzar_el_minimo_dice_que_el_envio_es_gratis` | Al alcanzar el minimo dice que el envio es gratis | 1 | Pasa |
| `test_el_checkout_tambien_dibuja_la_barra` | El checkout tambien dibuja la barra | 1 | Pasa |
| `test_CO089_la_confirmacion_lleva_el_enlace_de_seguimiento` | CO089 la confirmacion lleva el enlace de seguimiento | 1 | Pasa |

### `test_cobros_abandonados.py`

Los cobros abandonados (plan 00, C3) y la sincronización de cotizaciones (A2).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_un_cobro_pendiente_de_mas_de_un_dia_se_descarta` | Un cobro pendiente de mas de un dia se descarta | 1 | Pasa |
| `test_un_pago_aprobado_despues_de_descartado_se_reembolsa_y_no_genera_pedido` | Un pago aprobado despues de descartado se reembolsa y no genera pedido | 1 | Pasa |
| `test_CO155_y_los_cobros_abandonados_corren_en_el_temporizador` | CO155 y los cobros abandonados corren en el temporizador | 1 | Pasa |
| `test_CO155_la_sincronizacion_guarda_el_respaldo_cuando_la_api_responde` | CO155 la sincronizacion guarda el respaldo cuando la api responde | 1 | Pasa |

### `test_concurrencia_carrito.py`

`CO-083` bajo concurrencia real: dos pestañas suman el mismo producto a la vez.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO083_dos_pestanas_que_agregan_a_la_vez_dejan_una_linea_con_la_suma` | CO083 dos pestanas que agregan a la vez dejan una linea con la suma | 1 | Pasa |

### `test_concurrencia_compra.py`

`CO-089` bajo concurrencia real (RNF-06; B-07-035).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO089_dos_pagos_aprobados_del_ultimo_ejemplar_generan_un_solo_pedido` | CO089 dos pagos aprobados del ultimo ejemplar generan un solo pedido | 1 | Pasa |
| `test_CO089_el_mismo_aviso_repetido_en_paralelo_genera_un_solo_pedido` | CO089 el mismo aviso repetido en paralelo genera un solo pedido | 1 | Pasa |
| `test_CO089_el_mismo_saldo_canjeado_en_dos_compras_a_la_vez_se_gasta_una_sola_vez` | CO089 el mismo saldo canjeado en dos compras a la vez se gasta una sola vez | 1 | Pasa |

### `test_contratos_07_carrito.py`

Pruebas de contrato del carrito (módulo 07, plan 07 segunda parte).

**Casos de prueba que ejecuta:** CP-02, CP-03.

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO083_el_invitado_crea_un_carrito_de_sesion_con_la_linea` | CO083 el invitado crea un carrito de sesion con la linea | 1 | Pasa |
| `test_CO083_el_cliente_crea_un_carrito_persistente_asociado_a_su_cuenta` | CO083 el cliente crea un carrito persistente asociado a su cuenta | 1 | Pasa |
| `test_CO083_si_ya_estaba_suma_a_la_misma_linea` | CO083 si ya estaba suma a la misma linea | 1 | Pasa |
| `test_CO083_E1_la_cantidad_no_pasa_del_stock_y_se_informa_el_maximo` | CO083 E1 la cantidad no pasa del stock y se informa el maximo | 1 | Pasa |
| `test_CO083_A1_la_pre_venta_se_reserva_sin_tope_de_stock` | CO083 A1 la pre venta se reserva sin tope de stock | 1 | Pasa |
| `test_CO083_rechaza_una_cantidad_que_no_es_al_menos_uno` | CO083 rechaza una cantidad que no es al menos uno | 3 | Pasa |
| `test_CO083_un_producto_sin_stock_no_se_agrega` | CO083 un producto sin stock no se agrega | 1 | Pasa |
| `test_CO083_un_producto_fuera_de_la_tienda_responde_404` | CO083 un producto fuera de la tienda responde 404 | 1 | Pasa |
| `test_CO083_no_toca_el_producto_ni_se_audita` | CO083 no toca el producto ni se audita | 1 | Pasa |
| `test_CO083_volver_a_una_direccion_externa_se_ignora` | CO083 volver a una direccion externa se ignora | 1 | Pasa |
| `test_CO084_la_linea_queda_con_la_cantidad_declarada` | CO084 la linea queda con la cantidad declarada | 1 | Pasa |
| `test_CO084_E1_no_pasa_del_stock` | CO084 E1 no pasa del stock | 1 | Pasa |
| `test_CO084_E2_menos_de_uno_se_rechaza_y_la_linea_no_cambia` | CO084 E2 menos de uno se rechaza y la linea no cambia | 1 | Pasa |
| `test_CO084_A1_en_pre_venta_no_hay_tope` | CO084 A1 en pre venta no hay tope | 1 | Pasa |
| `test_CO084_la_linea_de_otro_carrito_responde_404` | CO084 la linea de otro carrito responde 404 | 1 | Pasa |
| `test_CO085_la_linea_deja_de_existir_y_el_producto_sigue_igual` | CO085 la linea deja de existir y el producto sigue igual | 1 | Pasa |
| `test_CO085_la_linea_de_otro_carrito_responde_404` | CO085 la linea de otro carrito responde 404 | 1 | Pasa |
| `test_CO178_presenta_las_lineas_con_precio_subtotal_y_total` | CO178 presenta las lineas con precio subtotal y total | 1 | Pasa |
| `test_CO178_A1_el_carrito_vacio_ofrece_el_catalogo` | CO178 A1 el carrito vacio ofrece el catalogo | 1 | Pasa |
| `test_CO178_A3_y_A4_la_disponibilidad_se_deriva_del_producto` | CO178 A3 y A4 la disponibilidad se deriva del producto | 1 | Pasa |
| `test_CO178_A4_la_pre_venta_figura_siempre_disponible` | CO178 A4 la pre venta figura siempre disponible | 1 | Pasa |
| `test_CO178_la_consulta_no_modifica_nada` | CO178 la consulta no modifica nada | 1 | Pasa |
| `test_CO048_confirmar_modificacion_actualiza_las_lineas_y_el_carrito_avisa` | CO048 confirmar modificacion actualiza las lineas y el carrito avisa | 1 | Pasa |
| `test_CO048_no_toca_las_lineas_de_otros_productos` | CO048 no toca las lineas de otros productos | 1 | Pasa |
| `test_CO053_confirmar_cambio_de_margen_actualiza_las_lineas` | CO053 confirmar cambio de margen actualiza las lineas | 1 | Pasa |
| `test_cambiar_la_cantidad_apaga_el_aviso_de_precio` | Cambiar la cantidad apaga el aviso de precio | 1 | Pasa |
| `test_CO086_sin_carrito_propio_el_de_sesion_pasa_a_la_cuenta` | CO086 sin carrito propio el de sesion pasa a la cuenta | 1 | Pasa |
| `test_CO086_con_carrito_propio_suma_con_tope_y_elimina_el_de_sesion` | CO086 con carrito propio suma con tope y elimina el de sesion | 1 | Pasa |
| `test_CO086_el_personal_que_inicia_sesion_descarta_el_carrito_de_invitado` | CO086 el personal que inicia sesion descarta el carrito de invitado | 1 | Pasa |
| `test_el_personal_no_tiene_carrito` | El personal no tiene carrito | 2 | Pasa |
| `test_la_ficha_ofrece_agregar_y_el_encabezado_cuenta_las_unidades` | La ficha ofrece agregar y el encabezado cuenta las unidades | 1 | Pasa |

### `test_contratos_07_compra.py`

Pruebas de contrato de la compra con cuenta (`CU-TDA-CMP`, plan 07 sexta parte).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO179_con_todas_las_lineas_disponibles_transfiere_al_checkout` | CO179 con todas las lineas disponibles transfiere al checkout | 1 | Pasa |
| `test_CO179_una_linea_no_disponible_bloquea_y_vuelve_al_carrito` | CO179 una linea no disponible bloquea y vuelve al carrito | 1 | Pasa |
| `test_CO179_stock_insuficiente_bloquea` | CO179 stock insuficiente bloquea | 1 | Pasa |
| `test_CO179_no_modifica_el_estado_del_sistema` | CO179 no modifica el estado del sistema | 1 | Pasa |
| `test_CO179_el_invitado_que_elige_comprar_como_invitado_va_al_formulario` | CO179 el invitado que elige comprar como invitado va al formulario | 1 | Pasa |
| `test_CO179_el_invitado_sin_elegir_va_a_iniciar_sesion_y_vuelve_al_checkout` | CO179 el invitado sin elegir va a iniciar sesion y vuelve al checkout | 1 | Pasa |
| `test_CO180_presenta_lineas_direccion_del_perfil_envio_y_subtotal` | CO180 presenta lineas direccion del perfil envio y subtotal | 1 | Pasa |
| `test_CO180_desde_el_monto_minimo_el_envio_es_gratis` | CO180 desde el monto minimo el envio es gratis | 1 | Pasa |
| `test_CO180_E1_stock_perdido_por_compra_concurrente_vuelve_al_carrito` | CO180 E1 stock perdido por compra concurrente vuelve al carrito | 1 | Pasa |
| `test_CO180_no_modifica_el_estado_del_sistema` | CO180 no modifica el estado del sistema | 1 | Pasa |
| `test_CO087_la_direccion_del_checkout_pasa_a_la_declarada` | CO087 la direccion del checkout pasa a la declarada | 1 | Pasa |
| `test_CO087_la_direccion_del_perfil_no_se_modifica` | CO087 la direccion del perfil no se modifica | 1 | Pasa |
| `test_CO087_devuelve_el_costo_de_envio` | CO087 devuelve el costo de envio | 1 | Pasa |
| `test_CO087_una_direccion_incoherente_no_se_declara` | CO087 una direccion incoherente no se declara | 1 | Pasa |
| `test_CO087_sin_numero_de_calle_no_se_declara` | CO087 sin numero de calle no se declara | 1 | Pasa |
| `test_CO103_la_linea_queda_cubierta_y_el_total_baja_su_precio` | CO103 la linea queda cubierta y el total baja su precio | 1 | Pasa |
| `test_CO103_ningun_lote_de_puntos_se_modifica_ni_se_audita` | CO103 ningun lote de puntos se modifica ni se audita | 1 | Pasa |
| `test_CO103_E1_saldo_insuficiente_no_cubre_y_lo_informa` | CO103 E1 saldo insuficiente no cubre y lo informa | 1 | Pasa |
| `test_CO103_E1_no_hay_canje_parcial_entre_dos_lineas` | CO103 E1 no hay canje parcial entre dos lineas | 1 | Pasa |
| `test_CO103_E2_se_verifica_con_el_precio_de_hoy` | CO103 E2 se verifica con el precio de hoy | 1 | Pasa |
| `test_CO103_sin_saldo_no_hay_canje` | CO103 sin saldo no hay canje | 1 | Pasa |
| `test_CO103_los_puntos_requeridos_redondean_hacia_arriba` | CO103 los puntos requeridos redondean hacia arriba | 1 | Pasa |
| `test_CO103_la_linea_de_otro_carrito_responde_404` | CO103 la linea de otro carrito responde 404 | 1 | Pasa |
| `test_CO104_la_linea_vuelve_a_su_precio_sin_tocar_lotes` | CO104 la linea vuelve a su precio sin tocar lotes | 1 | Pasa |
| `test_CO190_A2_si_el_total_queda_en_cero_lo_informa_sin_cambiar_nada` | CO190 A2 si el total queda en cero lo informa sin cambiar nada | 1 | Pasa |
| `test_CO088_con_total_mayor_que_cero_emite_la_solicitud_de_cobro_con_su_referencia` | CO088 con total mayor que cero emite la solicitud de cobro con su referencia | 1 | Pasa |
| `test_CO088_con_total_mayor_que_cero_no_cambia_el_dominio` | CO088 con total mayor que cero no cambia el dominio | 1 | Pasa |
| `test_CO088_congela_lineas_precios_direccion_y_canje` | CO088 congela lineas precios direccion y canje | 1 | Pasa |
| `test_CO088_sin_direccion_completa_no_confirma` | CO088 sin direccion completa no confirma | 1 | Pasa |
| `test_CO088_A2_con_todo_cubierto_y_envio_gratis_confirma_sin_pasarela` | CO088 A2 con todo cubierto y envio gratis confirma sin pasarela | 1 | Pasa |
| `test_CO088_A2_no_ocurre_si_hay_que_pagar_el_envio` | CO088 A2 no ocurre si hay que pagar el envio | 1 | Pasa |
| `test_CO088_un_canje_que_el_saldo_ya_no_cubre_pide_revisar` | CO088 un canje que el saldo ya no cubre pide revisar | 1 | Pasa |
| `test_CO089_a_crea_el_pedido_con_una_linea_por_linea_del_carrito_y_la_transaccion` | CO089 a crea el pedido con una linea por linea del carrito y la transaccion | 1 | Pasa |
| `test_CO089_b_asociaciones_del_pedido` | CO089 b asociaciones del pedido | 1 | Pasa |
| `test_CO089_c_numero_unico_canal_online_y_pendiente_de_armado` | CO089 c numero unico canal online y pendiente de armado | 1 | Pasa |
| `test_CO089_c_la_direccion_queda_copiada_y_no_sigue_al_perfil` | CO089 c la direccion queda copiada y no sigue al perfil | 1 | Pasa |
| `test_CO089_c_el_precio_unitario_queda_congelado` | CO089 c el precio unitario queda congelado | 1 | Pasa |
| `test_CO089_c_la_linea_cubierta_guarda_el_valor_de_su_canje` | CO089 c la linea cubierta guarda el valor de su canje | 1 | Pasa |
| `test_CO089_c_la_transaccion_queda_aprobada_con_referencia_y_monto` | CO089 c la transaccion queda aprobada con referencia y monto | 1 | Pasa |
| `test_CO089_c_el_stock_baja_y_el_que_llega_a_cero_pasa_a_agotado` | CO089 c el stock baja y el que llega a cero pasa a agotado | 1 | Pasa |
| `test_CO089_c_debita_los_lotes_de_caducidad_mas_proxima_primero` | CO089 c debita los lotes de caducidad mas proxima primero | 1 | Pasa |
| `test_CO089_c_acredita_los_puntos_de_lo_pagado_en_dinero_sin_el_envio` | CO089 c acredita los puntos de lo pagado en dinero sin el envio | 1 | Pasa |
| `test_CO089_a_el_carrito_queda_vaciado` | CO089 a el carrito queda vaciado | 1 | Pasa |
| `test_CO089_queda_registrado_en_la_auditoria_con_el_actor` | CO089 queda registrado en la auditoria con el actor | 1 | Pasa |
| `test_CO089_con_pre_venta_nace_esperando_stock_y_la_linea_reservada` | CO089 con pre venta nace esperando stock y la linea reservada | 1 | Pasa |
| `test_CO089_los_puntos_acreditados_redondean_hacia_abajo` | CO089 los puntos acreditados redondean hacia abajo | 1 | Pasa |
| `test_CO089_envia_la_confirmacion_despues_del_commit` | CO089 envia la confirmacion despues del commit | 1 | Pasa |
| `test_CO089_un_correo_caido_no_deshace_el_pedido` | CO089 un correo caido no deshace el pedido | 1 | Pasa |
| `test_CO089_la_pantalla_de_resultado_muestra_el_numero_y_el_estado` | CO089 la pantalla de resultado muestra el numero y el estado | 1 | Pasa |
| `test_CO089_un_aviso_repetido_no_genera_un_segundo_pedido` | CO089 un aviso repetido no genera un segundo pedido | 1 | Pasa |
| `test_CO089_E2_un_pago_rechazado_no_modifica_nada` | CO089 E2 un pago rechazado no modifica nada | 1 | Pasa |
| `test_CO089_E2_el_rechazo_se_informa_con_el_mensaje_de_la_pasarela` | CO089 E2 el rechazo se informa con el mensaje de la pasarela | 1 | Pasa |
| `test_CO089_E2_el_rechazo_queda_en_la_auditoria` | CO089 E2 el rechazo queda en la auditoria | 1 | Pasa |
| `test_CO089_E3_stock_perdido_mientras_se_pagaba_no_deja_nada_y_reembolsa` | CO089 E3 stock perdido mientras se pagaba no deja nada y reembolsa | 1 | Pasa |
| `test_CO089_E3_un_fallo_tecnico_a_mitad_de_camino_no_deja_datos_parciales` | CO089 E3 un fallo tecnico a mitad de camino no deja datos parciales | 1 | Pasa |
| `test_CO089_E3_avisa_al_cliente_que_el_cargo_se_revierte` | CO089 E3 avisa al cliente que el cargo se revierte | 1 | Pasa |
| `test_CO089_E3_el_saldo_que_ya_no_alcanza_tambien_reembolsa` | CO089 E3 el saldo que ya no alcanza tambien reembolsa | 1 | Pasa |
| `test_CO089_un_monto_distinto_del_cobrado_no_genera_pedido` | CO089 un monto distinto del cobrado no genera pedido | 1 | Pasa |
| `test_CO089_otro_carrito_cambiado_despues_de_confirmar_no_entra_al_pedido` | CO089 otro carrito cambiado despues de confirmar no entra al pedido | 1 | Pasa |

### `test_contratos_07_invitado.py`

Pruebas de contrato de la compra como invitado (`CU-TDA-INV`, plan 07 sexta parte).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO181_presenta_el_formulario_de_datos_del_invitado` | CO181 presenta el formulario de datos del invitado | 1 | Pasa |
| `test_CO181_A1_ofrece_iniciar_sesion` | CO181 A1 ofrece iniciar sesion | 1 | Pasa |
| `test_CO181_un_carrito_con_pre_venta_no_se_compra_como_invitado` | CO181 un carrito con pre venta no se compra como invitado | 1 | Pasa |
| `test_CO181_no_modifica_el_estado_del_sistema` | CO181 no modifica el estado del sistema | 1 | Pasa |
| `test_CO181_un_cliente_con_sesion_va_a_su_checkout` | CO181 un cliente con sesion va a su checkout | 1 | Pasa |
| `test_CO090_c_los_datos_quedan_asociados_al_checkout_sin_cambios_persistentes` | CO090 c los datos quedan asociados al checkout sin cambios persistentes | 1 | Pasa |
| `test_CO090_salida_el_resumen_con_envio_y_total_sin_canje` | CO090 salida el resumen con envio y total sin canje | 1 | Pasa |
| `test_CO090_E1_un_dato_ausente_o_invalido_se_resalta_y_se_conserva_lo_escrito` | CO090 E1 un dato ausente o invalido se resalta y se conserva lo escrito | 4 | Pasa |
| `test_CO090_E2_un_producto_sin_stock_vuelve_al_carrito` | CO090 E2 un producto sin stock vuelve al carrito | 1 | Pasa |
| `test_CO090_A1_si_el_correo_es_de_una_cuenta_sugiere_iniciar_sesion` | CO090 A1 si el correo es de una cuenta sugiere iniciar sesion | 1 | Pasa |
| `test_CO091_emite_la_solicitud_de_cobro_sin_cambios_en_el_dominio` | CO091 emite la solicitud de cobro sin cambios en el dominio | 1 | Pasa |
| `test_CO091_sin_datos_declarados_vuelve_al_formulario` | CO091 sin datos declarados vuelve al formulario | 1 | Pasa |
| `test_CO089_invitado_el_pedido_queda_asociado_al_correo_y_no_a_un_usuario` | CO089 invitado el pedido queda asociado al correo y no a un usuario | 1 | Pasa |
| `test_CO089_invitado_no_se_acreditan_ni_debitan_puntos` | CO089 invitado no se acreditan ni debitan puntos | 1 | Pasa |
| `test_CO089_invitado_el_stock_baja_y_el_carrito_de_sesion_se_vacia` | CO089 invitado el stock baja y el carrito de sesion se vacia | 1 | Pasa |
| `test_CO089_invitado_la_confirmacion_va_al_correo_declarado` | CO089 invitado la confirmacion va al correo declarado | 1 | Pasa |
| `test_CO089_invitado_queda_en_la_auditoria_con_su_correo` | CO089 invitado queda en la auditoria con su correo | 1 | Pasa |
| `test_CO089_invitado_E3_rechazo_conserva_los_datos_del_formulario` | CO089 invitado E3 rechazo conserva los datos del formulario | 1 | Pasa |

### `test_frontera_mercadopago.py`

Frontera con MercadoPago (B-07-031).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_frontera_mp_la_preferencia_lleva_la_referencia_y_redirige_al_init_point` | Frontera mp la preferencia lleva la referencia y redirige al init point | 1 | Pasa |
| `test_frontera_mp_sin_respuesta_no_cobra_y_vuelve_al_carrito` | Frontera mp sin respuesta no cobra y vuelve al carrito | 1 | Pasa |
| `test_frontera_mp_sin_credencial_no_inicia_el_cobro` | Frontera mp sin credencial no inicia el cobro | 1 | Pasa |
| `test_frontera_mp_el_aviso_se_confirma_consultando_el_pago` | Frontera mp el aviso se confirma consultando el pago | 1 | Pasa |
| `test_frontera_mp_un_aviso_por_parametros_tambien_se_lee` | Frontera mp un aviso por parametros tambien se lee | 1 | Pasa |
| `test_frontera_mp_un_pago_que_la_api_no_confirma_no_genera_nada` | Frontera mp un pago que la api no confirma no genera nada | 1 | Pasa |
| `test_frontera_mp_un_pago_pendiente_o_de_otro_tema_se_acusa_sin_efecto` | Frontera mp un pago pendiente o de otro tema se acusa sin efecto | 1 | Pasa |
| `test_frontera_mp_un_pago_rechazado_registra_el_rechazo` | Frontera mp un pago rechazado registra el rechazo | 1 | Pasa |
| `test_frontera_mp_E3_pide_el_reembolso_del_pago` | Frontera mp E3 pide el reembolso del pago | 1 | Pasa |
| `test_frontera_mp_sin_credencial_ninguna_llamada_sale` | Frontera mp sin credencial ninguna llamada sale | 1 | Pasa |
| `test_frontera_mp_un_aviso_sin_pago_es_invalido` | Frontera mp un aviso sin pago es invalido | 1 | Pasa |
| `test_frontera_mp_un_cuerpo_ilegible_sin_parametros_no_es_un_pago` | Frontera mp un cuerpo ilegible sin parametros no es un pago | 1 | Pasa |
| `test_frontera_mp_el_reembolso_rechazado_se_informa` | Frontera mp el reembolso rechazado se informa | 1 | Pasa |
| `test_frontera_mp_la_preferencia_usa_direcciones_absolutas` | Frontera mp la preferencia usa direcciones absolutas | 1 | Pasa |
| `test_frontera_una_pasarela_desconocida_no_existe` | Frontera una pasarela desconocida no existe | 1 | Pasa |
| `test_frontera_mercadopago_se_elige_por_su_clave` | Frontera mercadopago se elige por su clave | 1 | Pasa |

### `test_retiro_en_local.py`

Retiro en el local (plan 07, octava parte).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO087_con_retiro_el_envio_cuesta_cero_y_no_se_pide_direccion` | CO087 con retiro el envio cuesta cero y no se pide direccion | 1 | Pasa |
| `test_CO087_la_modalidad_no_toca_el_perfil` | CO087 la modalidad no toca el perfil | 1 | Pasa |
| `test_CO087_se_puede_volver_a_envio_a_domicilio_antes_de_confirmar` | CO087 se puede volver a envio a domicilio antes de confirmar | 1 | Pasa |
| `test_CO090_D4_el_invitado_no_puede_retirar` | CO090 D4 el invitado no puede retirar | 1 | Pasa |
| `test_CO088_el_cobro_congela_el_retiro_sin_envio` | CO088 el cobro congela el retiro sin envio | 1 | Pasa |
| `test_CO089_el_pedido_nace_para_retirar_sin_direccion_ni_envio` | CO089 el pedido nace para retirar sin direccion ni envio | 1 | Pasa |
| `test_CO089_D4_un_cobro_de_retiro_sin_cuenta_no_genera_pedido` | CO089 D4 un cobro de retiro sin cuenta no genera pedido | 1 | Pasa |
| `test_D4_la_base_no_admite_un_pedido_para_retirar_sin_cuenta_o_con_envio` | D4 la base no admite un pedido para retirar sin cuenta o con envio | 1 | Pasa |
| `test_CO092_el_pedido_armado_pasa_a_en_el_local_y_nunca_a_empaquetado` | CO092 el pedido armado pasa a en el local y nunca a empaquetado | 1 | Pasa |
| `test_CO092_cada_unidad_entra_al_stock_en_local_como_pedido_para_retirar` | CO092 cada unidad entra al stock en local como pedido para retirar | 1 | Pasa |
| `test_CO092_avisa_que_esta_listo_para_retirar` | CO092 avisa que esta listo para retirar | 1 | Pasa |
| `test_CO092_avanzar_dos_veces_no_duplica_los_articulos` | CO092 avanzar dos veces no duplica los articulos | 1 | Pasa |
| `test_CO092_las_lineas_no_cambian_al_pasar_a_en_el_local` | CO092 las lineas no cambian al pasar a en el local | 1 | Pasa |
| `test_el_pedido_para_retirar_muestra_su_modalidad_al_cliente_y_al_administrador` | El pedido para retirar muestra su modalidad al cliente y al administrador | 1 | Pasa |
| `test_la_opcion_2_en_un_pedido_para_retirar_lo_devuelve_al_armado` | La opcion 2 en un pedido para retirar lo devuelve al armado | 1 | Pasa |
| `test_el_demorado_de_un_pedido_para_retirar_entra_como_para_retirar` | El demorado de un pedido para retirar entra como para retirar | 1 | Pasa |
| `test_CO227_entregar_todo_retira_cada_articulo_disponible_del_pedido` | CO227 entregar todo retira cada articulo disponible del pedido | 1 | Pasa |
| `test_CO227_E1_si_un_articulo_cambio_no_se_entrega_ninguno` | CO227 E1 si un articulo cambio no se entrega ninguno | 1 | Pasa |
| `test_acceso_el_cliente_no_entrega_su_propio_pedido` | Acceso el cliente no entrega su propio pedido | 1 | Pasa |
| `test_CO218_la_ficha_muestra_el_origen_y_el_acceso_a_entregar_todo` | CO218 la ficha muestra el origen y el acceso a entregar todo | 1 | Pasa |
| `test_CO154_D3_lo_no_retirado_vuelve_al_stock_con_su_valor_en_puntos` | CO154 D3 lo no retirado vuelve al stock con su valor en puntos | 1 | Pasa |
| `test_CO154_D3_una_unidad_pagada_con_puntos_devuelve_sus_puntos` | CO154 D3 una unidad pagada con puntos devuelve sus puntos | 1 | Pasa |
| `test_CO154_el_despacho_diferido_tambien_vuelve_con_reembolso` | CO154 el despacho diferido tambien vuelve con reembolso | 1 | Pasa |
| `test_CO154_correr_dos_veces_no_reembolsa_dos_veces` | CO154 correr dos veces no reembolsa dos veces | 1 | Pasa |
| `test_CO154_el_aviso_previo_dice_que_vuelve_con_reembolso` | CO154 el aviso previo dice que vuelve con reembolso | 1 | Pasa |
| `test_CO185_lo_retirado_se_puede_reclamar_desde_el_retiro` | CO185 lo retirado se puede reclamar desde el retiro | 1 | Pasa |
| `test_CO099_el_plazo_de_lo_retirado_corre_desde_el_retiro` | CO099 el plazo de lo retirado corre desde el retiro | 1 | Pasa |
| `test_el_estado_de_reclamo_ofrece_el_boton_en_el_pedido_retirado` | El estado de reclamo ofrece el boton en el pedido retirado | 1 | Pasa |
| `test_concurrencia_dos_mostradores_que_entregan_el_mismo_pedido_registran_una_vez` | Concurrencia dos mostradores que entregan el mismo pedido registran una vez | 1 | Pasa |

---

## ventas — `apps/ventas`

### `test_concurrencia_ventas.py`

`CO-082` bajo concurrencia real (RNF-06).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO082_el_ultimo_ejemplar_vendido_a_la_vez_en_dos_cajas_y_en_la_tienda` | CO082 el ultimo ejemplar vendido a la vez en dos cajas y en la tienda | 1 | Pasa |

### `test_contratos_06_ventas.py`

Pruebas de contrato del mostrador (`CU-VTA-REG`, plan 06).

| Prueba | Qué hace | Casos | Resultado |
| --- | --- | ---: | --- |
| `test_CO078_abre_un_ticket_en_blanco_sin_tocar_el_dominio` | CO078 abre un ticket en blanco sin tocar el dominio | 1 | Pasa |
| `test_CO078_sin_productos_con_stock_no_se_abre` | CO078 sin productos con stock no se abre | 1 | Pasa |
| `test_CO079_a_agrega_el_item_y_el_stock_no_cambia` | CO079 a agrega el item y el stock no cambia | 1 | Pasa |
| `test_CO079_un_codigo_exacto_agrega_directo` | CO079 un codigo exacto agrega directo | 3 | Pasa |
| `test_CO079_un_texto_que_no_es_codigo_lista_coincidencias_sin_agregar` | CO079 un texto que no es codigo lista coincidencias sin agregar | 1 | Pasa |
| `test_CO079_repetir_un_producto_suma_la_cantidad` | CO079 repetir un producto suma la cantidad | 1 | Pasa |
| `test_CO079_E1_un_producto_sin_stock_no_se_agrega` | CO079 E1 un producto sin stock no se agrega | 1 | Pasa |
| `test_CO079_no_se_agrega_mas_que_el_stock` | CO079 no se agrega mas que el stock | 1 | Pasa |
| `test_CO079_una_pre_venta_no_se_vende_en_el_local` | CO079 una pre venta no se vende en el local | 1 | Pasa |
| `test_CO080_a_se_retira_el_item` | CO080 a se retira el item | 1 | Pasa |
| `test_CO080_si_estaba_cubierto_el_canje_se_va_sin_tocar_lotes` | CO080 si estaba cubierto el canje se va sin tocar lotes | 1 | Pasa |
| `test_CO081_b_se_asocia_el_cliente_por_su_codigo` | CO081 b se asocia el cliente por su codigo | 1 | Pasa |
| `test_CO081_tambien_por_correo` | CO081 tambien por correo | 1 | Pasa |
| `test_CO081_sin_un_cliente_activo_no_se_vincula` | CO081 sin un cliente activo no se vincula | 3 | Pasa |
| `test_CO081_no_hay_cambios_persistentes` | CO081 no hay cambios persistentes | 1 | Pasa |
| `test_CO103_mostrador_el_item_queda_cubierto_y_el_total_baja` | CO103 mostrador el item queda cubierto y el total baja | 1 | Pasa |
| `test_CO103_mostrador_ningun_lote_cambia` | CO103 mostrador ningun lote cambia | 1 | Pasa |
| `test_CO103_mostrador_E2_saldo_insuficiente_no_cubre` | CO103 mostrador E2 saldo insuficiente no cubre | 1 | Pasa |
| `test_CO103_mostrador_sin_cliente_no_hay_canje` | CO103 mostrador sin cliente no hay canje | 1 | Pasa |
| `test_CO104_mostrador_el_item_vuelve_a_su_precio` | CO104 mostrador el item vuelve a su precio | 1 | Pasa |
| `test_CO082_a_crea_el_pedido_con_sus_lineas_y_la_transaccion` | CO082 a crea el pedido con sus lineas y la transaccion | 1 | Pasa |
| `test_CO082_b_el_pedido_queda_asociado_al_cliente` | CO082 b el pedido queda asociado al cliente | 1 | Pasa |
| `test_CO082_c_canal_presencial_y_nace_despachado` | CO082 c canal presencial y nace despachado | 1 | Pasa |
| `test_CO082_c_precio_congelado_y_canje_registrado` | CO082 c precio congelado y canje registrado | 1 | Pasa |
| `test_CO082_c_la_transaccion_tiene_el_medio_el_subtotal_monetario_y_aprobado` | CO082 c la transaccion tiene el medio el subtotal monetario y aprobado | 1 | Pasa |
| `test_CO082_c_el_stock_baja_y_el_que_llega_a_cero_pasa_a_agotado` | CO082 c el stock baja y el que llega a cero pasa a agotado | 1 | Pasa |
| `test_CO082_c_debita_los_lotes_que_vencen_antes` | CO082 c debita los lotes que vencen antes | 1 | Pasa |
| `test_CO082_c_acredita_el_reintegro_de_lo_pagado_en_dinero` | CO082 c acredita el reintegro de lo pagado en dinero | 1 | Pasa |
| `test_CO082_queda_en_la_auditoria_con_el_detalle` | CO082 queda en la auditoria con el detalle | 1 | Pasa |
| `test_CO082_el_ticket_queda_vacio_y_se_muestra_el_comprobante` | CO082 el ticket queda vacio y se muestra el comprobante | 1 | Pasa |
| `test_CO082_sin_cliente_no_hay_puntos_ni_asociacion` | CO082 sin cliente no hay puntos ni asociacion | 1 | Pasa |
| `test_CO082_todo_cubierto_con_puntos_registra_la_transaccion_en_cero` | CO082 todo cubierto con puntos registra la transaccion en cero | 1 | Pasa |
| `test_CO082_con_importe_hay_que_elegir_el_medio_de_pago` | CO082 con importe hay que elegir el medio de pago | 1 | Pasa |
| `test_CO082_si_el_stock_se_perdio_no_se_vende_nada` | CO082 si el stock se perdio no se vende nada | 1 | Pasa |
| `test_CO082_si_el_saldo_cambio_no_se_confirma` | CO082 si el saldo cambio no se confirma | 1 | Pasa |
| `test_acceso_el_cliente_recibe_403_en_el_mostrador` | Acceso el cliente recibe 403 en el mostrador | 5 | Pasa |
| `test_acceso_el_administrador_tambien_vende` | Acceso el administrador tambien vende | 1 | Pasa |
| `test_acceso_sin_sesion_va_al_ingreso` | Acceso sin sesion va al ingreso | 1 | Pasa |

---

## Scripts de `scripts/demo/`

Las pruebas de resistencia que no entran en la suite. Corren sobre la base de la demostración; cómo se preparan está en [`CASOS_DE_PRUEBA.md`](CASOS_DE_PRUEBA.md).

| Script | Qué hace | Casos de prueba |
| --- | --- | --- |
| `ajustes_demo.py` | Ajustes de la demostración: los de producción, con los archivos subidos aparte. | — |
| `ataques.py` | Acto 3 · Ataques contra el sistema real, cada uno con su veredicto. | CP-13, CP-14, CP-15, CP-16, CP-17, CP-18, CP-19, CP-20 |
| `caida_base.py` | D6-04 · La base de datos se cae con el servidor andando, y vuelve. | CP-24 |
| `carreras.py` | Acto 4 · Concurrencia con hilos reales contra PostgreSQL. | CP-05, CP-08 |
| `ensayo.py` | El ensayo completo de la demostración, o la verificación rápida de la mañana. | — |
| `entorno.py` | Lo común a las herramientas de la demostración (plan 00). | — |
| `enviar_novedades.py` | Correos de novedades de editorial, armados con los datos de Ivrea. Sólo desarrollo. | — |
| `escalones.py` | D5-03 · Hasta dónde llega: la carga sube por escalones hasta que el p95 pasa 2 s o hay errores. | — |
| `linea_base.py` | D5-01 · Línea base: tiempos de respuesta con un solo usuario (RNF-02). | CP-26 |
| `llm_falso.py` | D6-02 · Un modelo de lenguaje que responde basura, para ver qué hace el sistema. | CP-09, CP-10 |
| `locustfile.py` | Acto 5 · Carga con sesiones reales de los tres roles (RNF-07, RNF-02). | CP-27 |
| `manejar.py` | `manage.py` con el entorno de la demostración. | — |
| `modelo_caido.py` | D6-01 y D6-02 · El modelo de lenguaje caído o respondiendo basura. | CP-07, CP-09, CP-10 |
| `mutacion.py` | D1-03 · Pruebas de mutación con mutmut, dentro de un contenedor Linux. | CP-01 |
| `poblar.py` | Puebla `longbox_demo` con un volumen realista y reproducible (plan 00, apartado 2). | — |
| `presentacion.py` | Deja una base de desarrollo limpia para una presentación, con el catálogo real de Ivrea. | — |
| `presentacion_carga.py` | La mitad de `presentacion.py` que corre dentro de Django. | — |
| `raspar_ivrea.py` | Raspa el catálogo público de series de Ivrea a un Excel, con sus portadas. | — |
| `raspar_portadas_tomos.py` | Baja la portada de cada tomo desde la galería PORTADAS de cada serie de Ivrea. | — |
| `respaldo.py` | D6-06 · Respaldo y restauración, según `docs/despliegue/RESPALDOS.md`. | CP-23 |
| `restaurar.py` | Vuelve `longbox_demo` al punto de partida en un comando (plan 00, apartado 2). | — |
| `rutas_protegidas.py` | D3-01 · RNF-03: cada ruta protegida, pedida con el rol equivocado, responde 403. | CP-12 |
| `sabotaje.py` | D1-02 · Sabotaje controlado: rompe algo a propósito y muestra que la suite lo detecta. | CP-01 |
