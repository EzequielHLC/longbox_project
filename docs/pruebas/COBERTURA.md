> **Tipo: Fotografía.** Tomada el 2026-09-22, del repositorio y no de memoria.
> **Generado por `scripts/generar_cobertura.py`.** No lo edites: la próxima corrida lo pisa.
> Se reemplaza entero. Si algo está mal acá, anotalo en la bitácora del módulo.

# Cobertura de contratos

Qué prueba lleva el código de qué contrato. **Es la única fuente de esta correspondencia**: los
demás documentos enlazan acá en vez de repetirla.

Sale de cruzar los contratos de `.contexto-ia/contratos/` con los nombres de función
`test_CO###_…` de la suite. La convención que lo hace posible está en
[`ESPECIFICACION.md`](ESPECIFICACION.md), apartado 2.

**Qué mide y qué no.** Mide que existe una prueba que *dice* verificar el contrato. No mide que
lo verifique entero: un contrato con tres postcondiciones y una sola prueba figura acá igual que
uno con todas cubiertas. Decidir si un contrato está verificado exige leer sus postcondiciones al
lado de sus pruebas, y ese juicio vive en [`../ESTADO.md`](../ESTADO.md). La cobertura de líneas
es otra puerta y su número también vive ahí.

---

## Resumen

| | |
| --- | ---: |
| Contratos especificados | 218 |
| Con al menos una prueba que lleva su código | 19 |
| Sin ninguna | 199 |
| Pruebas de contrato en la suite | 98 |

---

## Por archivo de contratos

### `00-transversales.md` — Transversales

18 contratos · 2 con prueba · 16 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-005` | confirmarPrecioManual | — | — |
| `CO-016` | ejecutarCicloMonitoreoCasilla | — | — |
| `CO-017` | aprobarCorreoParaProcesamiento | — | — |
| `CO-018` | descartarCorreo | — | — |
| `CO-025` | cerrarSesionDeRevision | — | — |
| `CO-031` | revertirPrecioManual | — | — |
| `CO-053` | confirmarCambioDeMargenGlobal | — | — |
| `CO-074` | enviarPedidoConsolidado — *contrato de operación interna* | — | — |
| `CO-077` | notificarReposicionASuscriptores — *contrato de operación interna* | — | — |
| `CO-087` | declararDireccionDeEnvio | — | — |
| `CO-089` | registrarResultadoDePago | — | — |
| `CO-103` | aplicarCanjeDePuntosAItem | — | — |
| `CO-104` | revertirCanjeDePuntosDeItem | — | — |
| `CO-122` | regenerarEnlaceDeActivacion | 5 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-137` | registrarEditorial | — | — |
| `CO-156` | cancelarOperacion | 1 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-157` | consultarColaDeCorreos | — | — |
| `CO-158` | abrirFichaDeCorreo | — | — |

### `01-alta-editorial.md` — 01 Alta Editorial

24 contratos · 0 con prueba · 24 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-001` | iniciarLoteEditorial | — | — |
| `CO-002` | declararCabeceraLote | — | — |
| `CO-003` | agregarItemLote | — | — |
| `CO-004` | fijarPrecioManualItem | — | — |
| `CO-006` | confirmarLote | — | — |
| `CO-007` | declararCalculadoraLote | — | — |
| `CO-008` | sobrescribirCotizacion | — | — |
| `CO-009` | agregarItemLoteImportado | — | — |
| `CO-010` | fijarPrecioFinalManual | — | — |
| `CO-011` | ejecutarCicloVigilanciaPreventa | — | — |
| `CO-012` | ejecutarCicloEscaladoPorInaccion | — | — |
| `CO-013` | confirmarIngresoDeLote | — | — |
| `CO-014` | solicitarRegistroDeDemora | — | — |
| `CO-015` | confirmarRegistroDeDemora | — | — |
| `CO-019` | reprocesarCorreo | — | — |
| `CO-020` | editarBorrador | — | — |
| `CO-021` | marcarCampoRevisado | — | — |
| `CO-022` | confirmarBorrador | — | — |
| `CO-023` | confirmarBorradoresEnLote | — | — |
| `CO-024` | rechazarBorrador | — | — |
| `CO-026` | solicitarCancelacionDePreventaEnLote | — | — |
| `CO-027` | confirmarCancelacionDePreventaEnLote | — | — |
| `CO-159` | consultarColaDeBorradores | — | — |
| `CO-160` | abrirBorrador | — | — |

### `02-catalogo.md` — 02 Catálogo

23 contratos · 0 con prueba · 23 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-028` | registrarProductoNoEditorial | — | — |
| `CO-029` | confirmarAltaPeseAHomonimo | — | — |
| `CO-030` | editarProducto | — | — |
| `CO-032` | confirmarEdicionPeseAColision | — | — |
| `CO-033` | solicitarBajaDeProducto | — | — |
| `CO-034` | confirmarBajaDeProducto | — | — |
| `CO-035` | solicitarReactivacionDeProducto | — | — |
| `CO-036` | confirmarReactivacionDeProducto | — | — |
| `CO-037` | exportarInventario | — | — |
| `CO-038` | registrarGrupoDeEtiqueta | — | — |
| `CO-039` | editarGrupoDeEtiqueta | — | — |
| `CO-040` | solicitarBajaDeGrupoDeEtiqueta | — | — |
| `CO-041` | confirmarBajaDeGrupoDeEtiqueta | — | — |
| `CO-042` | registrarEtiqueta | — | — |
| `CO-043` | editarEtiqueta | — | — |
| `CO-044` | solicitarBajaDeEtiqueta | — | — |
| `CO-045` | confirmarBajaDeEtiqueta | — | — |
| `CO-046` | moverEtiquetaDeGrupo | — | — |
| `CO-161` | abrirEdicionDeProducto | — | — |
| `CO-162` | consultarInventario | — | — |
| `CO-163` | consultarFichaDeProducto | — | — |
| `CO-164` | consultarGruposDeEtiqueta | — | — |
| `CO-165` | consultarEtiquetasDeGrupo | — | — |

### `03-pricing.md` — 03 Pricing

17 contratos · 0 con prueba · 17 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-047` | solicitarModificacionDePrecioDeReferencia | — | — |
| `CO-048` | confirmarModificacionDePrecioDeReferencia | — | — |
| `CO-049` | registrarCombinacionDePrecioDeReferencia | — | — |
| `CO-050` | solicitarBajaDeCombinacionDePrecio | — | — |
| `CO-051` | confirmarBajaDeCombinacionDePrecio | — | — |
| `CO-052` | simularCambioDeMargenGlobal | — | — |
| `CO-054` | registrarOferta | — | — |
| `CO-055` | confirmarOfertaConTopeMinimo | — | — |
| `CO-056` | editarOferta | — | — |
| `CO-057` | solicitarBajaDeOferta | — | — |
| `CO-058` | confirmarBajaDeOferta | — | — |
| `CO-059` | ejecutarCicloDeVigenciaDeOfertas | — | — |
| `CO-166` | consultarTablaDePrecios | — | — |
| `CO-167` | consultarMargenGlobal | — | — |
| `CO-168` | abrirEdicionDeOferta | — | — |
| `CO-169` | consultarOfertas | — | — |
| `CO-170` | consultarFichaDeOferta | — | — |

### `04-proveedores.md` — 04 Proveedores

10 contratos · 0 con prueba · 10 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-060` | registrarProveedor | — | — |
| `CO-061` | editarProveedor | — | — |
| `CO-062` | confirmarCambioDeCorreoComercial | — | — |
| `CO-063` | solicitarBajaDeProveedor | — | — |
| `CO-064` | confirmarBajaDeProveedor | — | — |
| `CO-065` | solicitarReactivacionDeProveedor | — | — |
| `CO-066` | confirmarReactivacionDeProveedor | — | — |
| `CO-171` | abrirEdicionDeProveedor | — | — |
| `CO-172` | consultarProveedores | — | — |
| `CO-173` | consultarFichaDeProveedor | — | — |

### `05-restock.md` — 05 Restock

11 contratos · 0 con prueba · 11 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-067` | ejecutarCicloDePropuestaDeRestock | — | — |
| `CO-068` | generarPropuestaDeRestock | — | — |
| `CO-069` | ajustarCantidadDeLinea | — | — |
| `CO-070` | eliminarLineaDePropuesta | — | — |
| `CO-071` | agregarProductoAPropuesta | — | — |
| `CO-072` | despacharPedidoAProveedor | — | — |
| `CO-073` | descartarProveedorDePropuesta | — | — |
| `CO-075` | suscribirseAReposicion | — | — |
| `CO-076` | cancelarSuscripcionDeReposicion | — | — |
| `CO-174` | consultarPropuestaDeRestock | — | — |
| `CO-175` | consultarLineasDeProveedor | — | — |

### `06-ventas-presenciales.md` — 06 Ventas Presenciales

5 contratos · 0 con prueba · 5 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-078` | abrirVentaPresencial | — | — |
| `CO-079` | agregarItemAlTicket | — | — |
| `CO-080` | quitarItemDelTicket | — | — |
| `CO-081` | vincularCuentaDeCliente | — | — |
| `CO-082` | confirmarVentaPresencial | — | — |

### `07-tienda-online.md` — 07 Tienda Online

13 contratos · 0 con prueba · 13 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-083` | agregarProductoAlCarrito | — | — |
| `CO-084` | modificarCantidadDeLinea | — | — |
| `CO-085` | eliminarLineaDelCarrito | — | — |
| `CO-086` | fusionarCarritoDeSesion | — | — |
| `CO-088` | confirmarPedido | — | — |
| `CO-090` | declararDatosDeInvitado | — | — |
| `CO-091` | confirmarPedidoDeInvitado | — | — |
| `CO-176` | consultarCatalogoPublico | — | — |
| `CO-177` | consultarFichaPublicaDeProducto | — | — |
| `CO-178` | consultarCarrito | — | — |
| `CO-179` | procederAlPago | — | — |
| `CO-180` | iniciarCheckout | — | — |
| `CO-181` | iniciarCompraComoInvitado | — | — |

### `08-gestion-de-pedidos.md` — 08 Gestión de Pedidos

10 contratos · 0 con prueba · 10 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-092` | avanzarEstadoDePedido | — | — |
| `CO-093` | confirmarAvancePeseADecisionPendiente | — | — |
| `CO-094` | seleccionarOpcionAnteDemora | — | — |
| `CO-095` | confirmarOpcionAnteDemora | — | — |
| `CO-096` | ejecutarCicloDeVencimientoDeVentanaDeDecision | — | — |
| `CO-097` | ejecutarCicloDeCompensacionPorRetraso | — | — |
| `CO-098` | confirmarCancelacionDeArticuloDemorado | — | — |
| `CO-182` | consultarPedidos | — | — |
| `CO-183` | consultarDetalleDePedido | — | — |
| `CO-184` | consultarOpcionesAnteDemora | — | — |

### `09-devoluciones.md` — 09 Devoluciones

7 contratos · 0 con prueba · 7 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-099` | registrarCasoDeDevolucion | — | — |
| `CO-100` | resolverCasoConCambio | — | — |
| `CO-101` | resolverCasoConReembolsoEnPuntos | — | — |
| `CO-102` | rechazarCasoDeDevolucion | — | — |
| `CO-185` | iniciarSolicitudDeDevolucion | — | — |
| `CO-186` | consultarCasosDeDevolucion | — | — |
| `CO-187` | consultarDetalleDeCasoDeDevolucion | — | — |

### `10-puntos.md` — 10 Puntos

6 contratos · 0 con prueba · 6 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-105` | ejecutarCicloDeCaducidadDePuntos | — | — |
| `CO-106` | registrarAjusteManualDePuntos | — | — |
| `CO-188` | consultarPuntos | — | — |
| `CO-189` | filtrarMovimientosDePuntos | — | — |
| `CO-190` | confirmarSeleccionDeCanje | — | — |
| `CO-191` | consultarPuntosDeCliente | — | — |

### `11-cuenta-de-cliente.md` — 11 Cuenta de Cliente

11 contratos · 0 con prueba · 11 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-107` | registrarCuentaDeCliente | — | — |
| `CO-108` | actualizarDatosPersonales | — | — |
| `CO-109` | solicitarCambioDeCorreo | — | — |
| `CO-110` | confirmarCambioDeCorreo | — | — |
| `CO-111` | cambiarContrasena | — | — |
| `CO-112` | solicitarBajaDeCuentaPropia | — | — |
| `CO-113` | confirmarBajaDeCuentaPropia | — | — |
| `CO-192` | consultarPanelDeCuenta | — | — |
| `CO-193` | consultarDetalleDePedidoPropio | — | — |
| `CO-194` | consultarCuentasDeCliente | — | — |
| `CO-195` | consultarFichaDeCliente | — | — |

### `12-autenticacion.md` — 12 Autenticación

7 contratos · 7 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-114` | iniciarSesion | 11 | `apps/accounts/tests/test_contratos_12_autenticacion.py` |
| `CO-115` | extenderSesion | 2 | `apps/accounts/tests/test_contratos_12_autenticacion.py` |
| `CO-116` | cerrarSesion | 3 | `apps/accounts/tests/test_contratos_12_autenticacion.py` |
| `CO-117` | solicitarRecuperacionDeContrasena | 6 | `apps/accounts/tests/test_contratos_12_autenticacion.py` |
| `CO-118` | establecerNuevaContrasena | 9 | `apps/accounts/tests/test_contratos_12_autenticacion.py` |
| `CO-119` | activarCuenta | 9 | `apps/accounts/tests/test_contratos_12_autenticacion.py` |
| `CO-196` | abrirEnlaceDeActivacion | 2 | `apps/accounts/tests/test_contratos_12_autenticacion.py` |

### `13-gestion-de-usuarios.md` — 13 Gestión de Usuarios

11 contratos · 10 con prueba · 1 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-120` | registrarUsuarioDelSistema | 11 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-121` | modificarUsuarioDelSistema | 9 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-123` | confirmarBajaDeUsuario | 6 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-124` | confirmarReactivacionDeUsuario | 8 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-125` | confirmarEliminacionDeCuentaPendiente | 8 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-197` | abrirEdicionDeUsuario | 1 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-198` | solicitarBajaDeUsuario | 2 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-199` | solicitarReactivacionDeUsuario | 2 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-200` | solicitarEliminacionDeCuentaPendiente | 1 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-201` | consultarCuentasDePersonal | 2 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-202` | consultarFichaDeUsuario | — | — |

### `14-caja.md` — 14 Caja

3 contratos · 0 con prueba · 3 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-126` | confirmarCierreDeCaja | — | — |
| `CO-127` | exportarCierreDeCaja | — | — |
| `CO-203` | solicitarCierreDeCaja | — | — |

### `15-reportes.md` — 15 Reportes

2 contratos · 0 con prueba · 2 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-128` | exportarReporte | — | — |
| `CO-204` | generarReporteOperativo | — | — |

### `16-auditoria.md` — 16 Auditoría

3 contratos · 0 con prueba · 3 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-129` | exportarLogDeAuditoria | — | — |
| `CO-205` | consultarLogDeAuditoria | — | — |
| `CO-206` | consultarDetalleDeEntradaDeAuditoria | — | — |

### `17-configuracion-del-sistema.md` — 17 Configuración del Sistema

28 contratos · 0 con prueba · 28 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-130` | actualizarParametrosOperacionales | — | — |
| `CO-131` | actualizarIdentidadVisual | — | — |
| `CO-132` | agregarBanner | — | — |
| `CO-133` | reordenarBanner | — | — |
| `CO-134` | eliminarBanner | — | — |
| `CO-135` | publicarContenidoDeFaq | — | — |
| `CO-136` | confirmarPublicacionDeFaqVacia | — | — |
| `CO-138` | editarEditorial | — | — |
| `CO-139` | solicitarBajaDeEditorial | — | — |
| `CO-140` | confirmarBajaDeEditorial | — | — |
| `CO-141` | registrarTipoDeMaterial | — | — |
| `CO-142` | editarTipoDeMaterial | — | — |
| `CO-143` | confirmarCambioDeTabulacionDeFormato | — | — |
| `CO-144` | registrarFormato | — | — |
| `CO-145` | editarFormato | — | — |
| `CO-146` | declararFormatosDeTipo | — | — |
| `CO-147` | solicitarBajaDeFormato | — | — |
| `CO-148` | confirmarBajaDeFormato | — | — |
| `CO-149` | ejecutarDiagnosticoDelModelo | — | — |
| `CO-150` | verificarDisponibilidadDelModelo | — | — |
| `CO-207` | consultarParametrosOperacionales | — | — |
| `CO-208` | consultarIdentidadVisual | — | — |
| `CO-209` | consultarBanners | — | — |
| `CO-210` | consultarContenidoDeFaq | — | — |
| `CO-211` | consultarEditoriales | — | — |
| `CO-212` | consultarTiposDeMaterial | — | — |
| `CO-213` | consultarFormatos | — | — |
| `CO-214` | consultarConfiguracionDeDiagnostico | — | — |

### `18-stock-almacenado-en-local.md` — 18 Stock Almacenado en Local

9 contratos · 0 con prueba · 9 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-151` | confirmarDespachoDeStockAlmacenado | — | — |
| `CO-152` | confirmarDespachoFisico | — | — |
| `CO-153` | modificarPlazoDeRetencion | — | — |
| `CO-154` | ejecutarCicloDeVencimientoDeRetencion | — | — |
| `CO-155` | sincronizarCotizaciones | — | — |
| `CO-215` | consultarStockAlmacenadoPropio | — | — |
| `CO-216` | solicitarDespachoDeStockAlmacenado | — | — |
| `CO-217` | consultarStockAlmacenado | — | — |
| `CO-218` | consultarFichaDeArticuloRetenido | — | — |

---

## Prueba por prueba

Cada contrato con sus pruebas, por nombre. El nombre dice qué postcondición verifica cada una, que es lo que hace consultable la trazabilidad sin abrir un archivo.

**`CO-114` · iniciarSesion**

- `test_CO114_bloqueado_no_entra_ni_con_la_contrasena_correcta` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO114_credenciales_invalidas_crean_un_intento_fallido` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO114_credenciales_validas_establecen_sesion_con_el_nivel_del_rol` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO114_credenciales_validas_registran_el_inicio_en_auditoria` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO114_cuenta_inactiva_no_deja_rastro_de_inicio_en_auditoria` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO114_cuenta_inactiva_no_obtiene_sesion` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO114_el_bloqueo_se_levanta_solo_al_salir_los_intentos_de_la_ventana` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO114_el_intento_fallido_guarda_el_correo_tal_como_se_escribio` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO114_el_quinto_intento_registra_el_bloqueo_en_auditoria` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO114_la_sesion_nace_con_expiracion_por_inactividad` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO114_se_registra_el_intento_aunque_la_cuenta_no_exista` — `apps/accounts/tests/test_contratos_12_autenticacion.py`

**`CO-115` · extenderSesion**

- `test_CO115_extender_renueva_el_plazo_de_inactividad` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO115_sobre_una_sesion_vencida_la_extension_no_procede` — `apps/accounts/tests/test_contratos_12_autenticacion.py`

**`CO-116` · cerrarSesion**

- `test_CO116_cerrar_sesion_invalida_el_token_del_dispositivo_actual` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO116_cerrar_sesion_no_afecta_las_sesiones_de_otros_dispositivos` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO116_cerrar_sesion_registra_el_cierre_en_auditoria` — `apps/accounts/tests/test_contratos_12_autenticacion.py`

**`CO-117` · solicitarRecuperacionDeContrasena**

- `test_CO117_la_respuesta_es_identica_exista_o_no_la_cuenta` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO117_se_creo_el_token_de_recuperacion_asociado_a_la_cuenta` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO117_un_correo_sin_cuenta_no_crea_ningun_token` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO117_un_correo_sin_cuenta_no_produce_ninguna_postcondicion` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO117_una_cuenta_activa_recibe_el_enlace_en_su_direccion` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO117_una_cuenta_inactiva_no_recibe_enlace` — `apps/accounts/tests/test_contratos_12_autenticacion.py`

**`CO-118` · establecerNuevaContrasena**

- `test_CO118_E2_una_contrasena_rechazada_no_consume_el_token` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO118_con_contrasenas_que_no_coinciden_el_enlace_no_se_consume` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO118_el_token_consumido_no_admite_un_segundo_uso` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO118_el_token_pasa_de_vigente_a_consumido` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO118_invalida_las_sesiones_en_todos_los_dispositivos` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO118_la_contrasena_anterior_queda_invalidada` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO118_la_credencial_pasa_del_hash_anterior_al_nuevo` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO118_registra_el_cambio_de_contrasena_en_auditoria` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO118_un_enlace_vencido_no_cambia_la_credencial` — `apps/accounts/tests/test_contratos_12_autenticacion.py`

**`CO-119` · activarCuenta**

- `test_CO119_E1_un_enlace_vencido_se_distingue_de_uno_ya_usado` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO119_E3_una_contrasena_rechazada_no_consume_el_enlace` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO119_el_enlace_no_admite_un_segundo_uso` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO119_el_enlace_pasa_de_vigente_a_consumido` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO119_la_credencial_pasa_de_nula_al_hash_de_la_elegida` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO119_la_cuenta_pasa_de_pendiente_de_activacion_a_activo` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO119_registra_la_activacion_en_auditoria` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO119_un_enlace_vencido_deja_la_cuenta_pendiente` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO119_una_contrasena_rechazada_no_consume_el_enlace` — `apps/accounts/tests/test_contratos_12_autenticacion.py`

**`CO-120` · registrarUsuarioDelSistema**

- `test_CO120_el_correo_queda_normalizado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO120_el_enlace_nace_vigente_y_con_48_horas` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO120_el_rol_queda_con_el_valor_declarado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO120_la_cuenta_nace_sin_credencial_utilizable` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO120_registra_el_alta_en_auditoria_con_el_rol_asignado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO120_se_creo_el_enlace_de_activacion_asociado_a_la_cuenta` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO120_se_creo_la_cuenta_en_pendiente_de_activacion` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO120_se_envio_el_enlace_al_correo_del_nuevo_usuario` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO120_un_correo_de_cuenta_activa_no_crea_la_cuenta` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO120_un_correo_de_cuenta_inactiva_no_crea_la_cuenta` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO120_un_correo_de_cuenta_pendiente_no_crea_la_cuenta` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`

**`CO-121` · modificarUsuarioDelSistema**

- `test_CO121_cambiar_el_rol_invalida_la_sesion_del_usuario_modificado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO121_la_ultima_modificacion_queda_con_el_instante` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO121_los_atributos_pasan_de_su_valor_anterior_al_declarado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO121_no_se_puede_quitar_el_rol_al_ultimo_administrador` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO121_registra_los_valores_anterior_y_nuevo_de_cada_campo` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO121_sin_cambiar_el_rol_la_sesion_del_usuario_sigue_viva` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO121_un_correo_que_ya_es_de_otra_cuenta_no_actualiza` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO121_una_cuenta_inactiva_no_admite_modificacion` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO121_una_cuenta_inactiva_no_cambia_aunque_se_envie_el_formulario` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`

**`CO-122` · regenerarEnlaceDeActivacion**

- `test_CO122_el_correo_de_activacion_fue_reenviado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO122_el_enlace_anterior_deja_de_admitir_uso` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO122_el_enlace_anterior_pasa_de_vigente_a_vencido` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO122_registra_el_reenvio_en_auditoria` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO122_se_creo_un_enlace_nuevo_con_vigencia_de_48_horas` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`

**`CO-123` · confirmarBajaDeUsuario**

- `test_CO123_el_estado_pasa_de_activo_a_inactivo` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO123_el_historial_del_usuario_se_conserva_integro` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO123_invalida_los_tokens_de_todos_los_dispositivos` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO123_la_cuenta_no_puede_volver_a_iniciar_sesion` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO123_no_se_puede_dar_de_baja_al_ultimo_administrador` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO123_registra_la_baja_en_auditoria` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`

**`CO-124` · confirmarReactivacionDeUsuario**

- `test_CO124_el_enlace_se_envia_al_correo_de_la_cuenta` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO124_el_estado_pasa_de_inactivo_a_pendiente_de_activacion` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO124_el_historial_del_usuario_se_conserva_integro` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO124_el_rol_queda_con_el_valor_declarado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO124_la_auditoria_incluye_el_rol_asignado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO124_la_credencial_anterior_queda_invalidada` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO124_registra_la_reactivacion_en_auditoria` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO124_se_creo_un_enlace_de_activacion_con_48_horas` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`

**`CO-125` · confirmarEliminacionDeCuentaPendiente**

- `test_CO125_el_correo_queda_disponible_para_un_alta_nueva` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO125_el_enlace_eliminado_ya_no_abre_nada` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO125_el_enlace_pendiente_queda_invalidado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO125_la_auditoria_se_escribe_antes_de_eliminar_el_registro` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO125_se_elimino_fisicamente_la_instancia` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO125_una_cuenta_activa_no_se_elimina` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO125_una_cuenta_inactiva_no_se_elimina` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO125_una_pendiente_que_ya_inicio_sesion_no_se_elimina` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`

**`CO-156` · cancelarOperacion**

- `test_CO156_abandonar_antes_de_confirmar_no_cambia_nada` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`

**`CO-196` · abrirEnlaceDeActivacion**

- `test_CO196_abrir_el_enlace_no_modifica_el_estado_del_sistema` — `apps/accounts/tests/test_contratos_12_autenticacion.py`
- `test_CO196_no_exige_sesion_iniciada` — `apps/accounts/tests/test_contratos_12_autenticacion.py`

**`CO-197` · abrirEdicionDeUsuario**

- `test_CO197_abrir_la_edicion_no_modifica_el_estado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`

**`CO-198` · solicitarBajaDeUsuario**

- `test_CO198_no_se_ofrece_sobre_el_ultimo_administrador` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO198_solicitar_la_baja_no_modifica_el_estado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`

**`CO-199` · solicitarReactivacionDeUsuario**

- `test_CO199_la_pantalla_permite_modificar_el_rol_antes_de_confirmar` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO199_solicitar_la_reactivacion_no_modifica_el_estado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`

**`CO-200` · solicitarEliminacionDeCuentaPendiente**

- `test_CO200_solicitar_la_eliminacion_no_modifica_el_estado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`

**`CO-201` · consultarCuentasDePersonal**

- `test_CO201_el_listado_no_modifica_el_estado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO201_el_listado_presenta_nombre_correo_rol_y_estado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`

---

## Lo que esta fotografía no cubre

- **No dice que un contrato esté verificado**, sólo que alguna prueba lleva su código. Una postcondición sin prueba no se distingue desde acá de una cubierta.
- **No mira las pruebas que no son de contrato.** Las de acceso, flujo, unidad y frontera no llevan código de contrato en el nombre, a propósito, y no entran en este recuento.
- **No mide cobertura de líneas.** Es otra puerta y su número vive en [`../ESTADO.md`](../ESTADO.md).
