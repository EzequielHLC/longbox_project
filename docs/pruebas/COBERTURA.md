> **Tipo: Fotografía.** Tomada el 2026-10-12, del repositorio y no de memoria.
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
| Contratos especificados | 219 |
| Con al menos una prueba que lleva su código | 140 |
| Sin ninguna | 79 |
| Pruebas de contrato en la suite | 624 |

---

## Por archivo de contratos

### `00-transversales.md` — Transversales

18 contratos · 14 con prueba · 4 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-005` | confirmarPrecioManual | — | — |
| `CO-017` | aprobarCorreoParaProcesamiento | 11 | `apps/suppliers/tests/test_concurrencia_correos.py`, `apps/suppliers/tests/test_contratos_04_proveedores.py` |
| `CO-019` | reprocesarCorreo | 5 | `apps/suppliers/tests/test_contratos_04_proveedores.py` |
| `CO-025` | cerrarSesionDeRevision | — | — |
| `CO-031` | restaurarPrecioCalculado | 4 | `apps/catalog/tests/test_contratos_03_pricing.py` |
| `CO-053` | confirmarCambioDeMargenGlobal | 3 | `apps/catalog/tests/test_contratos_03_pricing.py`, `apps/tienda/tests/test_contratos_07_carrito.py` |
| `CO-074` | enviarPedidoConsolidado — *contrato de operación interna* | — | — |
| `CO-077` | notificarReposicionASuscriptores — *contrato de operación interna* | — | — |
| `CO-086` | fusionarCarritoDeSesion | 3 | `apps/tienda/tests/test_contratos_07_carrito.py` |
| `CO-087` | declararDireccionDeEnvio | 5 | `apps/tienda/tests/test_contratos_07_compra.py` |
| `CO-089` | registrarResultadoDePago | 37 | `apps/tienda/tests/test_barra_envio.py`, `apps/tienda/tests/test_concurrencia_compra.py`, `apps/tienda/tests/test_contratos_07_compra.py`, `apps/tienda/tests/test_contratos_07_invitado.py` |
| `CO-103` | aplicarCanjeDePuntosAItem | 12 | `apps/tienda/tests/test_contratos_07_compra.py`, `apps/ventas/tests/test_contratos_06_ventas.py` |
| `CO-104` | revertirCanjeDePuntosDeItem | 2 | `apps/tienda/tests/test_contratos_07_compra.py`, `apps/ventas/tests/test_contratos_06_ventas.py` |
| `CO-122` | regenerarEnlaceDeActivacion | 5 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-137` | registrarEditorial | 4 | `apps/catalog/tests/test_concurrencia_catalogos.py`, `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-141` | registrarTipoDeMaterial | 1 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-144` | registrarFormato | 2 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-156` | cancelarOperacion | 12 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`, `apps/catalog/tests/test_contratos_02_catalogo.py`, `apps/catalog/tests/test_contratos_03_ofertas.py`, `apps/catalog/tests/test_contratos_03_pricing.py`, `apps/catalog/tests/test_contratos_17_catalogos.py`, `apps/pedidos/tests/test_contratos_01_preventa.py`, `apps/pedidos/tests/test_contratos_08_demora.py`, `apps/suppliers/tests/test_contratos_04_proveedores.py` |

### `01-alta-editorial.md` — 01 Alta Editorial

24 contratos · 7 con prueba · 17 sin.

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
| `CO-011` | ejecutarCicloVigilanciaPreventa | 5 | `apps/pedidos/tests/test_contratos_01_preventa.py` |
| `CO-012` | ejecutarCicloEscaladoPorInaccion | 3 | `apps/pedidos/tests/test_contratos_01_preventa.py` |
| `CO-013` | confirmarIngresoDeLote | 14 | `apps/pedidos/tests/test_contratos_01_preventa.py` |
| `CO-014` | solicitarRegistroDeDemora | 4 | `apps/pedidos/tests/test_contratos_01_preventa.py` |
| `CO-015` | confirmarRegistroDeDemora | 5 | `apps/pedidos/tests/test_contratos_01_preventa.py` |
| `CO-016` | ejecutarCicloMonitoreoCasilla | — | — |
| `CO-020` | editarBorrador | — | — |
| `CO-021` | marcarCampoRevisado | — | — |
| `CO-022` | confirmarBorrador | — | — |
| `CO-023` | confirmarBorradoresEnLote | — | — |
| `CO-024` | rechazarBorrador | — | — |
| `CO-026` | solicitarCancelacionDePreventaEnLote | 2 | `apps/pedidos/tests/test_contratos_01_preventa.py` |
| `CO-027` | confirmarCancelacionDePreventaEnLote | 5 | `apps/pedidos/tests/test_contratos_01_preventa.py` |
| `CO-159` | consultarColaDeBorradores | — | — |
| `CO-160` | abrirBorrador | — | — |

### `02-catalogo.md` — 02 Catálogo

22 contratos · 13 con prueba · 9 sin.

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
| `CO-037` | exportarInventario | 3 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-038` | registrarGrupoDeEtiqueta | 2 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-039` | editarGrupoDeEtiqueta | 1 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-040` | solicitarBajaDeGrupoDeEtiqueta | 1 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-041` | confirmarBajaDeGrupoDeEtiqueta | 1 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-042` | registrarEtiqueta | 3 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-043` | editarEtiqueta | 3 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-044` | solicitarBajaDeEtiqueta | 1 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-045` | confirmarBajaDeEtiqueta | 2 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-161` | abrirEdicionDeProducto | — | — |
| `CO-162` | consultarInventario | 2 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-163` | consultarFichaDeProducto | 2 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-164` | consultarGruposDeEtiqueta | 1 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-165` | consultarEtiquetasDeGrupo | 1 | `apps/catalog/tests/test_contratos_02_catalogo.py` |

### `03-pricing.md` — 03 Pricing

17 contratos · 17 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-047` | solicitarModificacionDePrecioDeReferencia | 3 | `apps/catalog/tests/test_contratos_03_pricing.py` |
| `CO-048` | confirmarModificacionDePrecioDeReferencia | 5 | `apps/catalog/tests/test_contratos_03_pricing.py`, `apps/tienda/tests/test_contratos_07_carrito.py` |
| `CO-049` | registrarCombinacionDePrecioDeReferencia | 4 | `apps/catalog/tests/test_contratos_03_pricing.py` |
| `CO-050` | solicitarBajaDeCombinacionDePrecio | 1 | `apps/catalog/tests/test_contratos_03_pricing.py` |
| `CO-051` | confirmarBajaDeCombinacionDePrecio | 1 | `apps/catalog/tests/test_contratos_03_pricing.py` |
| `CO-052` | simularCambioDeMargenGlobal | 3 | `apps/catalog/tests/test_contratos_03_pricing.py` |
| `CO-054` | registrarOferta | 12 | `apps/catalog/tests/test_concurrencia_ofertas.py`, `apps/catalog/tests/test_contratos_03_ofertas.py` |
| `CO-055` | confirmarOfertaConTopeMinimo | 1 | `apps/catalog/tests/test_contratos_03_ofertas.py` |
| `CO-056` | editarOferta | 5 | `apps/catalog/tests/test_contratos_03_ofertas.py` |
| `CO-057` | solicitarBajaDeOferta | 2 | `apps/catalog/tests/test_contratos_03_ofertas.py` |
| `CO-058` | confirmarBajaDeOferta | 3 | `apps/catalog/tests/test_contratos_03_ofertas.py` |
| `CO-059` | ejecutarCicloDeVigenciaDeOfertas | 2 | `apps/catalog/tests/test_contratos_03_ofertas.py` |
| `CO-166` | consultarTablaDePrecios | 1 | `apps/catalog/tests/test_contratos_03_pricing.py` |
| `CO-167` | consultarMargenGlobal | 1 | `apps/catalog/tests/test_contratos_03_pricing.py` |
| `CO-168` | abrirEdicionDeOferta | 2 | `apps/catalog/tests/test_contratos_03_ofertas.py` |
| `CO-169` | consultarOfertas | 3 | `apps/catalog/tests/test_contratos_03_ofertas.py` |
| `CO-170` | consultarFichaDeOferta | 2 | `apps/catalog/tests/test_contratos_03_ofertas.py` |

### `04-proveedores.md` — 04 Proveedores

13 contratos · 4 con prueba · 9 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-018` | descartarCorreo | 2 | `apps/suppliers/tests/test_contratos_04_proveedores.py` |
| `CO-060` | registrarProveedor | 1 | `apps/suppliers/tests/test_concurrencia_proveedores.py` |
| `CO-061` | editarProveedor | — | — |
| `CO-062` | confirmarCambioDeCorreoComercial | — | — |
| `CO-063` | solicitarBajaDeProveedor | — | — |
| `CO-064` | confirmarBajaDeProveedor | — | — |
| `CO-065` | solicitarReactivacionDeProveedor | — | — |
| `CO-066` | confirmarReactivacionDeProveedor | — | — |
| `CO-157` | consultarColaDeCorreos | 2 | `apps/suppliers/tests/test_contratos_04_proveedores.py` |
| `CO-158` | abrirFichaDeCorreo | 2 | `apps/suppliers/tests/test_contratos_04_proveedores.py` |
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

5 contratos · 5 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-078` | abrirVentaPresencial | 2 | `apps/ventas/tests/test_contratos_06_ventas.py` |
| `CO-079` | agregarItemAlTicket | 7 | `apps/ventas/tests/test_contratos_06_ventas.py` |
| `CO-080` | quitarItemDelTicket | 2 | `apps/ventas/tests/test_contratos_06_ventas.py` |
| `CO-081` | vincularCuentaDeCliente | 4 | `apps/ventas/tests/test_contratos_06_ventas.py` |
| `CO-082` | confirmarVentaPresencial | 16 | `apps/ventas/tests/test_concurrencia_ventas.py`, `apps/ventas/tests/test_contratos_06_ventas.py` |

### `07-tienda-online.md` — 07 Tienda Online

12 contratos · 12 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-083` | agregarProductoAlCarrito | 14 | `apps/core/tests/test_tienda_quinta_parte.py`, `apps/tienda/tests/test_concurrencia_carrito.py`, `apps/tienda/tests/test_contratos_07_carrito.py` |
| `CO-084` | modificarCantidadDeLinea | 7 | `apps/core/tests/test_tienda_quinta_parte.py`, `apps/tienda/tests/test_contratos_07_carrito.py` |
| `CO-085` | eliminarLineaDelCarrito | 3 | `apps/core/tests/test_tienda_quinta_parte.py`, `apps/tienda/tests/test_contratos_07_carrito.py` |
| `CO-088` | confirmarPedido | 7 | `apps/tienda/tests/test_contratos_07_compra.py` |
| `CO-090` | declararDatosDeInvitado | 5 | `apps/tienda/tests/test_contratos_07_invitado.py` |
| `CO-091` | confirmarPedidoDeInvitado | 2 | `apps/tienda/tests/test_contratos_07_invitado.py` |
| `CO-176` | consultarCatalogoPublico | 11 | `apps/core/tests/test_contratos_07_tienda.py`, `apps/core/tests/test_tienda_quinta_parte.py` |
| `CO-177` | consultarFichaPublicaDeProducto | 3 | `apps/core/tests/test_contratos_07_tienda.py` |
| `CO-178` | consultarCarrito | 5 | `apps/tienda/tests/test_contratos_07_carrito.py` |
| `CO-179` | procederAlPago | 6 | `apps/tienda/tests/test_contratos_07_compra.py` |
| `CO-180` | iniciarCheckout | 4 | `apps/tienda/tests/test_contratos_07_compra.py` |
| `CO-181` | iniciarCompraComoInvitado | 5 | `apps/tienda/tests/test_contratos_07_invitado.py` |

### `08-gestion-de-pedidos.md` — 08 Gestión de Pedidos

10 contratos · 10 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-092` | avanzarEstadoDePedido | 15 | `apps/pedidos/tests/test_acceso_y_concurrencia_pedidos.py`, `apps/pedidos/tests/test_contratos_08_pedidos.py` |
| `CO-093` | confirmarAvancePeseADecisionPendiente | 1 | `apps/pedidos/tests/test_contratos_08_pedidos.py` |
| `CO-094` | seleccionarOpcionAnteDemora | 2 | `apps/pedidos/tests/test_contratos_08_demora.py` |
| `CO-095` | confirmarOpcionAnteDemora | 6 | `apps/pedidos/tests/test_contratos_08_demora.py` |
| `CO-096` | ejecutarCicloDeVencimientoDeVentanaDeDecision | 3 | `apps/pedidos/tests/test_contratos_08_demora.py` |
| `CO-097` | ejecutarCicloDeCompensacionPorRetraso | 6 | `apps/pedidos/tests/test_contratos_08_demora.py` |
| `CO-098` | confirmarCancelacionDeArticuloDemorado | 6 | `apps/pedidos/tests/test_contratos_08_demora.py` |
| `CO-182` | consultarPedidos | 8 | `apps/pedidos/tests/test_contratos_08_pedidos.py` |
| `CO-183` | consultarDetalleDePedido | 4 | `apps/pedidos/tests/test_contratos_08_pedidos.py` |
| `CO-184` | consultarOpcionesAnteDemora | 5 | `apps/pedidos/tests/test_contratos_08_demora.py` |

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

6 contratos · 3 con prueba · 3 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-105` | ejecutarCicloDeCaducidadDePuntos | — | — |
| `CO-106` | registrarAjusteManualDePuntos | — | — |
| `CO-188` | consultarPuntos | 7 | `apps/puntos/tests/test_contratos_10_puntos.py` |
| `CO-189` | filtrarMovimientosDePuntos | 4 | `apps/puntos/tests/test_contratos_10_puntos.py` |
| `CO-190` | confirmarSeleccionDeCanje | 1 | `apps/tienda/tests/test_contratos_07_compra.py` |
| `CO-191` | consultarPuntosDeCliente | — | — |

### `11-cuenta-de-cliente.md` — 11 Cuenta de Cliente

11 contratos · 8 con prueba · 3 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-107` | registrarCuentaDeCliente | — | — |
| `CO-108` | actualizarDatosPersonales | 5 | `apps/accounts/tests/test_contratos_11_cuenta.py` |
| `CO-109` | solicitarCambioDeCorreo | 6 | `apps/accounts/tests/test_contratos_11_cuenta.py` |
| `CO-110` | confirmarCambioDeCorreo | 7 | `apps/accounts/tests/test_contratos_11_cuenta.py` |
| `CO-111` | cambiarContrasena | 4 | `apps/accounts/tests/test_contratos_11_cuenta.py` |
| `CO-112` | solicitarBajaDeCuentaPropia | — | — |
| `CO-113` | confirmarBajaDeCuentaPropia | — | — |
| `CO-192` | consultarPanelDeCuenta | 5 | `apps/accounts/tests/test_contratos_11_cuenta.py` |
| `CO-193` | consultarDetalleDePedidoPropio | 4 | `apps/accounts/tests/test_contratos_11_cuenta.py` |
| `CO-194` | consultarCuentasDeCliente | 4 | `apps/accounts/tests/test_contratos_11_cuenta_de_cliente.py` |
| `CO-195` | consultarFichaDeCliente | 5 | `apps/accounts/tests/test_contratos_11_cuenta_de_cliente.py` |

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

11 contratos · 11 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-120` | registrarUsuarioDelSistema | 11 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-121` | modificarUsuarioDelSistema | 11 | `apps/accounts/tests/test_concurrencia_ultimo_administrador.py`, `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-123` | confirmarBajaDeUsuario | 7 | `apps/accounts/tests/test_concurrencia_ultimo_administrador.py`, `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-124` | confirmarReactivacionDeUsuario | 8 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-125` | confirmarEliminacionDeCuentaPendiente | 8 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-197` | abrirEdicionDeUsuario | 1 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-198` | solicitarBajaDeUsuario | 2 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-199` | solicitarReactivacionDeUsuario | 2 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-200` | solicitarEliminacionDeCuentaPendiente | 1 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-201` | consultarCuentasDePersonal | 2 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-202` | consultarFichaDeUsuario | 7 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |

### `14-caja.md` — 14 Caja

3 contratos · 3 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-126` | confirmarCierreDeCaja | 11 | `apps/caja/tests/test_concurrencia_caja.py`, `apps/caja/tests/test_contratos_14_caja.py` |
| `CO-127` | exportarCierreDeCaja | 2 | `apps/caja/tests/test_contratos_14_caja.py` |
| `CO-203` | solicitarCierreDeCaja | 6 | `apps/caja/tests/test_contratos_14_caja.py` |

### `15-reportes.md` — 15 Reportes

2 contratos · 0 con prueba · 2 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-128` | exportarReporte | — | — |
| `CO-204` | generarReporteOperativo | — | — |

### `16-auditoria.md` — 16 Auditoría

3 contratos · 3 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-129` | exportarLogDeAuditoria | 2 | `apps/core/tests/test_contratos_16_auditoria.py` |
| `CO-205` | consultarLogDeAuditoria | 3 | `apps/core/tests/test_contratos_16_auditoria.py` |
| `CO-206` | consultarDetalleDeEntradaDeAuditoria | 1 | `apps/core/tests/test_contratos_16_auditoria.py` |

### `17-configuracion-del-sistema.md` — 17 Configuración del Sistema

27 contratos · 23 con prueba · 4 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-130` | actualizarParametrosOperacionales | 8 | `apps/catalog/tests/test_parametros_compra.py` |
| `CO-131` | actualizarIdentidadVisual | 8 | `apps/core/tests/test_contratos_17_contenido.py` |
| `CO-132` | agregarBanner | 2 | `apps/core/tests/test_contratos_17_contenido.py` |
| `CO-133` | editarBanner | 4 | `apps/core/tests/test_contratos_17_contenido.py` |
| `CO-134` | eliminarBanner | 2 | `apps/core/tests/test_contratos_17_contenido.py` |
| `CO-135` | publicarContenidoDeFaq | 4 | `apps/core/tests/test_contratos_17_contenido.py` |
| `CO-136` | confirmarPublicacionDeFaqVacia | 1 | `apps/core/tests/test_contratos_17_contenido.py` |
| `CO-138` | editarEditorial | 4 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-139` | solicitarBajaDeEditorial | 2 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-140` | confirmarBajaDeEditorial | 4 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-142` | editarTipoDeMaterial | 4 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-145` | editarFormato | 3 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-146` | declararFormatosDeTipo | 3 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-147` | solicitarBajaDeFormato | 1 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-148` | confirmarBajaDeFormato | 2 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-149` | ejecutarDiagnosticoDelModelo | — | — |
| `CO-150` | verificarDisponibilidadDelModelo | — | — |
| `CO-207` | consultarParametrosOperacionales | — | — |
| `CO-208` | consultarIdentidadVisual | 1 | `apps/core/tests/test_contratos_17_contenido.py` |
| `CO-209` | consultarBanners | 1 | `apps/core/tests/test_contratos_17_contenido.py` |
| `CO-210` | consultarContenidoDeFaq | 1 | `apps/core/tests/test_contratos_17_contenido.py` |
| `CO-211` | consultarEditoriales | 1 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-212` | consultarTiposDeMaterial | 1 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-213` | consultarFormatos | 1 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-214` | consultarConfiguracionDeDiagnostico | — | — |
| `CO-220` | solicitarBajaDeTipoDeMaterial | 1 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-221` | confirmarBajaDeTipoDeMaterial | 2 | `apps/catalog/tests/test_contratos_17_catalogos.py` |

### `18-stock-almacenado-en-local.md` — 18 Stock Almacenado en Local

10 contratos · 0 con prueba · 10 sin.

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
| `CO-227` | confirmarRetiroEnLocal | — | — |

---

## Prueba por prueba

Cada contrato con sus pruebas, por nombre. El nombre dice qué postcondición verifica cada una, que es lo que hace consultable la trazabilidad sin abrir un archivo.

**`CO-011` · ejecutarCicloVigilanciaPreventa**

- `test_CO011_avisa_las_proximas_y_las_de_hoy_sin_cambiar_nada` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO011_correr_dos_veces_el_mismo_dia_no_repite_avisos` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO011_el_temporizador_corre_los_ciclos_de_la_preventa_y_la_demora` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO011_fuera_del_horizonte_o_sin_preventas_no_avisa` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO011_una_demorada_cuya_fecha_estimada_paso_se_recuerda_una_vez` — `apps/pedidos/tests/test_contratos_01_preventa.py`

**`CO-012` · ejecutarCicloEscaladoPorInaccion**

- `test_CO012_escala_lo_vencido_sin_ingreso_ni_demora_y_lo_audita` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO012_escala_una_vez_por_dia_mientras_siga_sin_resolver` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO012_no_escala_lo_que_tiene_demora_registrada` — `apps/pedidos/tests/test_contratos_01_preventa.py`

**`CO-013` · confirmarIngresoDeLote**

- `test_CO013_A1_un_faltante_vencido_se_demora_con_la_cascada_de_CO015` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO013_E3_un_producto_que_falla_queda_en_preventa_y_los_demas_siguen` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO013_confirmar_ingreso_activa_productos_y_pasa_pedidos_a_pendiente_de_armado` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO013_el_articulo_de_despacho_diferido_llega_disponible_y_cierra_la_compensacion` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO013_la_pantalla_agrupa_por_fecha_y_editorial` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO013_la_pantalla_rechaza_unidades_invalidas` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO013_la_revision_dice_que_faltante_se_demora_y_cual_no_cambia` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO013_lo_recibido_cubre_las_reservas_en_orden_de_compra` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO013_no_saltea_una_reserva_que_no_alcanza` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO013_por_la_pantalla_se_revisa_y_despues_se_confirma` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO013_rechaza_unidades_negativas` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO013_un_faltante_que_todavia_no_vence_no_cambia` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO013_un_pedido_con_otra_preventa_sigue_esperando` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO013_un_producto_que_ya_no_esta_en_preventa_se_informa` — `apps/pedidos/tests/test_contratos_01_preventa.py`

**`CO-014` · solicitarRegistroDeDemora**

- `test_CO014_A3_sin_pedidos_lo_dice` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO014_E1_la_fecha_estimada_debe_ser_posterior_a_hoy` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO014_informa_pedidos_y_clientes_sin_registrar_nada` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO014_rechaza_lo_ya_demorado_lo_vencido_y_lo_que_no_es_preventa` — `apps/pedidos/tests/test_contratos_01_preventa.py`

**`CO-015` · confirmarRegistroDeDemora**

- `test_CO015_A1_sin_fecha_estimada_el_aviso_la_omite` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO015_A3_sin_pedidos_registra_la_demora_sin_avisos` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO015_E2_un_pedido_que_falla_no_frena_a_los_demas` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO015_confirmar_demora_marca_el_producto_y_transiciona_los_pedidos` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO015_el_servicio_rechaza_una_fecha_estimada_que_no_es_futura` — `apps/pedidos/tests/test_contratos_01_preventa.py`

**`CO-017` · aprobarCorreoParaProcesamiento**

- `test_CO017_E1_la_segunda_aprobacion_encuentra_el_correo_tomado` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO017_E1_un_correo_ya_tomado_por_otro_no_se_vuelve_a_procesar` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO017_E4_si_el_servicio_no_responde_el_correo_falla_y_queda_en_la_cola` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO017_E4_si_no_identifica_ningun_producto_el_correo_falla` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO017_aprobar_pasa_el_correo_de_pendiente_a_procesado` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO017_crea_un_borrador_por_producto_con_sus_asociaciones` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO017_dos_aprobaciones_simultaneas_procesan_una_sola_vez` — `apps/suppliers/tests/test_concurrencia_correos.py`
- `test_CO017_el_resumen_informa_generados_omitidos_y_reparos` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO017_la_operacion_queda_auditada` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO017_no_acepta_get` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO017_por_la_direccion_real_con_rol_cajero_no_procesa` — `apps/suppliers/tests/test_contratos_04_proveedores.py`

**`CO-018` · descartarCorreo**

- `test_CO018_E3_sin_motivo_no_se_descarta` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO018_descartar_registra_estado_motivo_y_responsable` — `apps/suppliers/tests/test_contratos_04_proveedores.py`

**`CO-019` · reprocesarCorreo**

- `test_CO019_la_ficha_ofrece_reprocesar_solo_si_corresponde` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO019_queda_auditado` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO019_reemplaza_solo_los_borradores_abiertos` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO019_si_la_extraccion_falla_los_abiertos_se_conservan` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO019_un_correo_pendiente_no_se_reprocesa` — `apps/suppliers/tests/test_contratos_04_proveedores.py`

**`CO-026` · solicitarCancelacionDePreventaEnLote**

- `test_CO026_informa_reservas_por_cliente_y_los_puntos_a_reembolsar` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO026_sin_reservas_lo_dice_con_cero` — `apps/pedidos/tests/test_contratos_01_preventa.py`

**`CO-027` · confirmarCancelacionDePreventaEnLote**

- `test_CO027_E1_si_falla_un_reembolso_no_queda_nada` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO027_cancela_reservas_reembolsa_en_puntos_y_cancela_el_producto` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO027_incluye_las_reservas_ya_demoradas` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO027_no_se_cancela_lo_que_no_esta_en_preventa` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO027_sin_reservas_solo_cambia_el_estado` — `apps/pedidos/tests/test_contratos_01_preventa.py`

**`CO-031` · restaurarPrecioCalculado**

- `test_CO031_no_aplica_a_un_producto_que_ya_sigue_su_fuente` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO031_un_importado_a_mano_vuelve_al_margen_vigente_desde_su_base` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO031_un_nacional_a_mano_vuelve_a_la_tabla_y_se_vincula` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO031_un_nacional_que_perdio_su_fila_se_vuelve_a_vincular` — `apps/catalog/tests/test_contratos_03_pricing.py`

**`CO-037` · exportarInventario**

- `test_CO037_el_cajero_no_exporta_por_la_direccion_real` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO037_el_cajero_no_ve_la_opcion_de_exportar` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO037_exportar_inventario_trae_las_filas_del_listado_filtrado` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-038` · registrarGrupoDeEtiqueta**

- `test_CO038_E1_la_colision_enlaza_el_grupo_existente` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO038_registrar_grupo_lo_crea_activo_y_auditado` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-039` · editarGrupoDeEtiqueta**

- `test_CO039_reactivar_el_grupo_no_reactiva_sus_etiquetas` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-040` · solicitarBajaDeGrupoDeEtiqueta**

- `test_CO040_solicitar_baja_de_grupo_informa_etiquetas_y_productos` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-041` · confirmarBajaDeGrupoDeEtiqueta**

- `test_CO041_la_baja_del_grupo_alcanza_a_sus_etiquetas_y_conserva_las_asignaciones` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-042` · registrarEtiqueta**

- `test_CO042_E1_la_colision_es_dentro_del_grupo_y_enlaza_la_existente` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO042_no_se_crea_en_un_grupo_dado_de_baja` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO042_registrar_etiqueta_la_crea_activa_en_su_grupo` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-043` · editarEtiqueta**

- `test_CO043_E3_no_se_reactiva_dentro_de_un_grupo_dado_de_baja` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO043_mover_la_etiqueta_conserva_sus_asignaciones_y_su_estado` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO043_reactivar_moviendola_a_un_grupo_activo` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-044` · solicitarBajaDeEtiqueta**

- `test_CO044_solicitar_baja_de_etiqueta_informa_sus_productos` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-045` · confirmarBajaDeEtiqueta**

- `test_CO045_confirmar_baja_de_etiqueta_la_retira_y_conserva_sus_asignaciones` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO045_la_edicion_del_producto_la_presenta_marcada_y_no_la_pierde` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-047` · solicitarModificacionDePrecioDeReferencia**

- `test_CO047_E1_un_precio_no_mayor_que_cero_se_rechaza` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO047_sin_vinculados_informa_que_solo_afecta_a_la_tabla` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO047_solicitar_modificacion_informa_el_alcance_sin_cambiar_nada` — `apps/catalog/tests/test_contratos_03_pricing.py`

**`CO-048` · confirmarModificacionDePrecioDeReferencia**

- `test_CO048_confirmar_modificacion_actualiza_las_lineas_y_el_carrito_avisa` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO048_confirmar_propaga_a_los_vinculados_y_respeta_las_excepciones` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO048_el_informe_cuenta_lo_mismo_que_se_propaga` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO048_no_toca_el_precio_base` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO048_no_toca_las_lineas_de_otros_productos` — `apps/tienda/tests/test_contratos_07_carrito.py`

**`CO-049` · registrarCombinacionDePrecioDeReferencia**

- `test_CO049_E1_la_combinacion_existente_se_enlaza_y_no_se_registra` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO049_E2_una_combinacion_imposible_se_rechaza` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO049_E3_un_precio_no_mayor_que_cero_se_rechaza` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO049_registrar_combinacion_crea_la_fila_y_no_toca_productos` — `apps/catalog/tests/test_contratos_03_pricing.py`

**`CO-050` · solicitarBajaDeCombinacionDePrecio**

- `test_CO050_solicitar_baja_cuenta_todos_los_vinculados` — `apps/catalog/tests/test_contratos_03_pricing.py`

**`CO-051` · confirmarBajaDeCombinacionDePrecio**

- `test_CO051_confirmar_baja_desvincula_y_conserva_precio_y_marca` — `apps/catalog/tests/test_contratos_03_pricing.py`

**`CO-052` · simularCambioDeMargenGlobal**

- `test_CO052_A1_todos_a_mano_avisa_que_no_afecta_a_ninguno` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO052_simular_informa_el_impacto_sin_cambiar_nada` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO052_sin_importados_la_precondicion_no_se_cumple` — `apps/catalog/tests/test_contratos_03_pricing.py`

**`CO-053` · confirmarCambioDeMargenGlobal**

- `test_CO053_confirmar_cambio_de_margen_actualiza_las_lineas` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO053_confirmar_recalcula_desde_el_precio_base_con_decimal_exacto` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO053_no_toca_a_los_nacionales` — `apps/catalog/tests/test_contratos_03_pricing.py`

**`CO-054` · registrarOferta**

- `test_CO054_A1_un_tipo_sin_productos_registra_con_aviso` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO054_E1_el_vencimiento_tiene_que_ser_futuro` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO054_E2_no_cuentan_las_dadas_de_baja_ni_las_de_otro_alcance` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO054_E2_rechaza_el_solapamiento_con_el_nombre_y_el_periodo` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO054_E3_un_monto_que_supera_el_precio_pide_confirmacion_y_no_registra` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO054_con_inicio_futuro_queda_programada_y_no_descuenta_todavia` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO054_dos_ofertas_solapadas_registradas_a_la_vez_dejan_una` — `apps/catalog/tests/test_concurrencia_ofertas.py`
- `test_CO054_el_inicio_no_puede_pasar_al_vencimiento` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO054_no_toca_el_precio_guardado_del_producto` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO054_por_tipo_se_asocia_al_tipo_y_alcanza_a_sus_productos` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO054_rechaza_un_porcentaje_de_cien` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO054_registrar_con_inicio_hoy_la_deja_activa_y_aplicada_en_los_dos_canales` — `apps/catalog/tests/test_contratos_03_ofertas.py`

**`CO-055` · confirmarOfertaConTopeMinimo**

- `test_CO055_confirmar_registra_y_deja_en_un_peso_a_los_que_no_alcanzan` — `apps/catalog/tests/test_contratos_03_ofertas.py`

**`CO-056` · editarOferta**

- `test_CO056_A1_reducir_el_alcance_restaura_a_los_que_quedan_afuera` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO056_E1_un_solapamiento_no_actualiza_ningun_campo` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO056_cambiar_el_valor_de_una_activa_actualiza_precio_carrito_y_log` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO056_mover_el_inicio_al_futuro_la_vuelve_programada` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO056_sin_cambios_no_audita` — `apps/catalog/tests/test_contratos_03_ofertas.py`

**`CO-057` · solicitarBajaDeOferta**

- `test_CO057_E1_una_vencida_informa_que_ya_expiro_y_no_registra_nada` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO057_el_informe_cuenta_productos_con_descuento_y_carritos` — `apps/catalog/tests/test_contratos_03_ofertas.py`

**`CO-058` · confirmarBajaDeOferta**

- `test_CO058_confirmar_la_deja_dada_de_baja_y_restaura_precio_y_carritos` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO058_una_dada_de_baja_no_se_reactiva_ni_se_audita_dos_veces` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO058_una_programada_tambien_se_da_de_baja` — `apps/catalog/tests/test_contratos_03_ofertas.py`

**`CO-059` · ejecutarCicloDeVigenciaDeOfertas**

- `test_CO059_activa_las_programadas_y_vence_las_activas_con_su_entrada` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO059_correrlo_dos_veces_no_duplica_nada` — `apps/catalog/tests/test_contratos_03_ofertas.py`

**`CO-060` · registrarProveedor**

- `test_CO060_doble_envio_del_alta_deja_uno_y_avisa_sin_error` — `apps/suppliers/tests/test_concurrencia_proveedores.py`

**`CO-078` · abrirVentaPresencial**

- `test_CO078_abre_un_ticket_en_blanco_sin_tocar_el_dominio` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO078_sin_productos_con_stock_no_se_abre` — `apps/ventas/tests/test_contratos_06_ventas.py`

**`CO-079` · agregarItemAlTicket**

- `test_CO079_E1_un_producto_sin_stock_no_se_agrega` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO079_a_agrega_el_item_y_el_stock_no_cambia` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO079_no_se_agrega_mas_que_el_stock` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO079_repetir_un_producto_suma_la_cantidad` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO079_un_codigo_exacto_agrega_directo` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO079_un_texto_que_no_es_codigo_lista_coincidencias_sin_agregar` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO079_una_pre_venta_no_se_vende_en_el_local` — `apps/ventas/tests/test_contratos_06_ventas.py`

**`CO-080` · quitarItemDelTicket**

- `test_CO080_a_se_retira_el_item` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO080_si_estaba_cubierto_el_canje_se_va_sin_tocar_lotes` — `apps/ventas/tests/test_contratos_06_ventas.py`

**`CO-081` · vincularCuentaDeCliente**

- `test_CO081_b_se_asocia_el_cliente_por_su_codigo` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO081_no_hay_cambios_persistentes` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO081_sin_un_cliente_activo_no_se_vincula` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO081_tambien_por_correo` — `apps/ventas/tests/test_contratos_06_ventas.py`

**`CO-082` · confirmarVentaPresencial**

- `test_CO082_a_crea_el_pedido_con_sus_lineas_y_la_transaccion` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO082_b_el_pedido_queda_asociado_al_cliente` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO082_c_acredita_el_reintegro_de_lo_pagado_en_dinero` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO082_c_canal_presencial_y_nace_despachado` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO082_c_debita_los_lotes_que_vencen_antes` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO082_c_el_stock_baja_y_el_que_llega_a_cero_pasa_a_agotado` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO082_c_la_transaccion_tiene_el_medio_el_subtotal_monetario_y_aprobado` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO082_c_precio_congelado_y_canje_registrado` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO082_con_importe_hay_que_elegir_el_medio_de_pago` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO082_el_ticket_queda_vacio_y_se_muestra_el_comprobante` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO082_el_ultimo_ejemplar_vendido_a_la_vez_en_dos_cajas_y_en_la_tienda` — `apps/ventas/tests/test_concurrencia_ventas.py`
- `test_CO082_queda_en_la_auditoria_con_el_detalle` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO082_si_el_saldo_cambio_no_se_confirma` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO082_si_el_stock_se_perdio_no_se_vende_nada` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO082_sin_cliente_no_hay_puntos_ni_asociacion` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO082_todo_cubierto_con_puntos_registra_la_transaccion_en_cero` — `apps/ventas/tests/test_contratos_06_ventas.py`

**`CO-083` · agregarProductoAlCarrito**

- `test_CO083_A1_la_pre_venta_se_reserva_sin_tope_de_stock` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_E1_la_cantidad_no_pasa_del_stock_y_se_informa_el_maximo` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_agregar_desde_la_tarjeta_responde_json_con_las_unidades` — `apps/core/tests/test_tienda_quinta_parte.py`
- `test_CO083_desde_la_tarjeta_el_tope_de_stock_se_avisa_igual` — `apps/core/tests/test_tienda_quinta_parte.py`
- `test_CO083_dos_pestanas_que_agregan_a_la_vez_dejan_una_linea_con_la_suma` — `apps/tienda/tests/test_concurrencia_carrito.py`
- `test_CO083_el_cliente_crea_un_carrito_persistente_asociado_a_su_cuenta` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_el_invitado_crea_un_carrito_de_sesion_con_la_linea` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_el_personal_no_agrega_desde_la_tarjeta` — `apps/core/tests/test_tienda_quinta_parte.py`
- `test_CO083_no_toca_el_producto_ni_se_audita` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_rechaza_una_cantidad_que_no_es_al_menos_uno` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_si_ya_estaba_suma_a_la_misma_linea` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_un_producto_fuera_de_la_tienda_responde_404` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_un_producto_sin_stock_no_se_agrega` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_volver_a_una_direccion_externa_se_ignora` — `apps/tienda/tests/test_contratos_07_carrito.py`

**`CO-084` · modificarCantidadDeLinea**

- `test_CO084_A1_en_pre_venta_no_hay_tope` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO084_E1_no_pasa_del_stock` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO084_E2_menos_de_uno_se_rechaza_y_la_linea_no_cambia` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO084_cambiar_la_cantidad_devuelve_el_carrito_recalculado` — `apps/core/tests/test_tienda_quinta_parte.py`
- `test_CO084_la_linea_de_otro_carrito_responde_404` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO084_la_linea_queda_con_la_cantidad_declarada` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO084_sin_stock_suficiente_se_topea_y_se_avisa` — `apps/core/tests/test_tienda_quinta_parte.py`

**`CO-085` · eliminarLineaDelCarrito**

- `test_CO085_la_linea_de_otro_carrito_responde_404` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO085_la_linea_deja_de_existir_y_el_producto_sigue_igual` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO085_quitar_devuelve_el_carrito_sin_la_linea` — `apps/core/tests/test_tienda_quinta_parte.py`

**`CO-086` · fusionarCarritoDeSesion**

- `test_CO086_con_carrito_propio_suma_con_tope_y_elimina_el_de_sesion` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO086_el_personal_que_inicia_sesion_descarta_el_carrito_de_invitado` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO086_sin_carrito_propio_el_de_sesion_pasa_a_la_cuenta` — `apps/tienda/tests/test_contratos_07_carrito.py`

**`CO-087` · declararDireccionDeEnvio**

- `test_CO087_devuelve_el_costo_de_envio` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO087_la_direccion_del_checkout_pasa_a_la_declarada` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO087_la_direccion_del_perfil_no_se_modifica` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO087_sin_numero_de_calle_no_se_declara` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO087_una_direccion_incoherente_no_se_declara` — `apps/tienda/tests/test_contratos_07_compra.py`

**`CO-088` · confirmarPedido**

- `test_CO088_A2_con_todo_cubierto_y_envio_gratis_confirma_sin_pasarela` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO088_A2_no_ocurre_si_hay_que_pagar_el_envio` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO088_con_total_mayor_que_cero_emite_la_solicitud_de_cobro_con_su_referencia` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO088_con_total_mayor_que_cero_no_cambia_el_dominio` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO088_congela_lineas_precios_direccion_y_canje` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO088_sin_direccion_completa_no_confirma` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO088_un_canje_que_el_saldo_ya_no_cubre_pide_revisar` — `apps/tienda/tests/test_contratos_07_compra.py`

**`CO-089` · registrarResultadoDePago**

- `test_CO089_E2_el_rechazo_queda_en_la_auditoria` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_E2_el_rechazo_se_informa_con_el_mensaje_de_la_pasarela` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_E2_un_pago_rechazado_no_modifica_nada` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_E3_avisa_al_cliente_que_el_cargo_se_revierte` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_E3_el_saldo_que_ya_no_alcanza_tambien_reembolsa` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_E3_stock_perdido_mientras_se_pagaba_no_deja_nada_y_reembolsa` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_E3_un_fallo_tecnico_a_mitad_de_camino_no_deja_datos_parciales` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_a_crea_el_pedido_con_una_linea_por_linea_del_carrito_y_la_transaccion` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_a_el_carrito_queda_vaciado` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_b_asociaciones_del_pedido` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_c_acredita_los_puntos_de_lo_pagado_en_dinero_sin_el_envio` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_c_debita_los_lotes_de_caducidad_mas_proxima_primero` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_c_el_precio_unitario_queda_congelado` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_c_el_stock_baja_y_el_que_llega_a_cero_pasa_a_agotado` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_c_la_direccion_queda_copiada_y_no_sigue_al_perfil` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_c_la_linea_cubierta_guarda_el_valor_de_su_canje` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_c_la_transaccion_queda_aprobada_con_referencia_y_monto` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_c_numero_unico_canal_online_y_pendiente_de_armado` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_con_pre_venta_nace_esperando_stock_y_la_linea_reservada` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_dos_pagos_aprobados_del_ultimo_ejemplar_generan_un_solo_pedido` — `apps/tienda/tests/test_concurrencia_compra.py`
- `test_CO089_el_mismo_aviso_repetido_en_paralelo_genera_un_solo_pedido` — `apps/tienda/tests/test_concurrencia_compra.py`
- `test_CO089_el_mismo_saldo_canjeado_en_dos_compras_a_la_vez_se_gasta_una_sola_vez` — `apps/tienda/tests/test_concurrencia_compra.py`
- `test_CO089_envia_la_confirmacion_despues_del_commit` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_invitado_E3_rechazo_conserva_los_datos_del_formulario` — `apps/tienda/tests/test_contratos_07_invitado.py`
- `test_CO089_invitado_el_pedido_queda_asociado_al_correo_y_no_a_un_usuario` — `apps/tienda/tests/test_contratos_07_invitado.py`
- `test_CO089_invitado_el_stock_baja_y_el_carrito_de_sesion_se_vacia` — `apps/tienda/tests/test_contratos_07_invitado.py`
- `test_CO089_invitado_la_confirmacion_va_al_correo_declarado` — `apps/tienda/tests/test_contratos_07_invitado.py`
- `test_CO089_invitado_no_se_acreditan_ni_debitan_puntos` — `apps/tienda/tests/test_contratos_07_invitado.py`
- `test_CO089_invitado_queda_en_la_auditoria_con_su_correo` — `apps/tienda/tests/test_contratos_07_invitado.py`
- `test_CO089_la_confirmacion_lleva_el_enlace_de_seguimiento` — `apps/tienda/tests/test_barra_envio.py`
- `test_CO089_la_pantalla_de_resultado_muestra_el_numero_y_el_estado` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_los_puntos_acreditados_redondean_hacia_abajo` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_otro_carrito_cambiado_despues_de_confirmar_no_entra_al_pedido` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_queda_registrado_en_la_auditoria_con_el_actor` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_un_aviso_repetido_no_genera_un_segundo_pedido` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_un_correo_caido_no_deshace_el_pedido` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_un_monto_distinto_del_cobrado_no_genera_pedido` — `apps/tienda/tests/test_contratos_07_compra.py`

**`CO-090` · declararDatosDeInvitado**

- `test_CO090_A1_si_el_correo_es_de_una_cuenta_sugiere_iniciar_sesion` — `apps/tienda/tests/test_contratos_07_invitado.py`
- `test_CO090_E1_un_dato_ausente_o_invalido_se_resalta_y_se_conserva_lo_escrito` — `apps/tienda/tests/test_contratos_07_invitado.py`
- `test_CO090_E2_un_producto_sin_stock_vuelve_al_carrito` — `apps/tienda/tests/test_contratos_07_invitado.py`
- `test_CO090_c_los_datos_quedan_asociados_al_checkout_sin_cambios_persistentes` — `apps/tienda/tests/test_contratos_07_invitado.py`
- `test_CO090_salida_el_resumen_con_envio_y_total_sin_canje` — `apps/tienda/tests/test_contratos_07_invitado.py`

**`CO-091` · confirmarPedidoDeInvitado**

- `test_CO091_emite_la_solicitud_de_cobro_sin_cambios_en_el_dominio` — `apps/tienda/tests/test_contratos_07_invitado.py`
- `test_CO091_sin_datos_declarados_vuelve_al_formulario` — `apps/tienda/tests/test_contratos_07_invitado.py`

**`CO-092` · avanzarEstadoDePedido**

- `test_CO092_E1_un_estado_automatico_no_se_avanza_a_mano` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_E2_con_decision_pendiente_advierte_y_no_avanza` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_c_armado_no_toca_las_lineas` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_c_el_estado_pasa_al_unico_siguiente` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_c_empaquetado_y_despachado_avanzan_las_lineas_disponibles` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_c_las_lineas_demoradas_no_avanzan` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_dos_administradores_que_avanzan_a_la_vez_avanzan_un_solo_paso` — `apps/pedidos/tests/test_acceso_y_concurrencia_pedidos.py`
- `test_CO092_el_cliente_recibe_la_notificacion` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_el_invitado_recibe_la_notificacion_en_su_correo` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_la_confirmacion_muestra_el_estado_actual_y_el_siguiente` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_no_se_saltea_un_paso_si_el_pedido_cambio_en_otra_pantalla` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_queda_en_la_auditoria_con_el_estado_anterior_y_el_nuevo` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_queda_una_transicion_en_la_linea_de_tiempo` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_un_correo_caido_no_deshace_el_avance` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_un_pedido_despachado_no_tiene_siguiente` — `apps/pedidos/tests/test_contratos_08_pedidos.py`

**`CO-093` · confirmarAvancePeseADecisionPendiente**

- `test_CO093_avanza_y_los_pendientes_conservan_su_estado` — `apps/pedidos/tests/test_contratos_08_pedidos.py`

**`CO-094` · seleccionarOpcionAnteDemora**

- `test_CO094_pide_confirmar_con_la_consecuencia_sin_registrar` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO094_una_opcion_que_no_corresponde_se_rechaza` — `apps/pedidos/tests/test_contratos_08_demora.py`

**`CO-095` · confirmarOpcionAnteDemora**

- `test_CO095_al_llegar_el_articulo_pausado_el_pedido_pasa_a_pendiente_de_armado` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO095_con_la_ventana_vencida_se_rechaza_en_el_servidor` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO095_despacho_diferido_empaqueta_lo_disponible_y_el_pedido` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO095_el_despacho_no_arrastra_al_articulo_diferido` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO095_no_se_decide_dos_veces` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO095_pausar_registra_la_decision_y_el_pedido_sigue_esperando` — `apps/pedidos/tests/test_contratos_08_demora.py`

**`CO-096` · ejecutarCicloDeVencimientoDeVentanaDeDecision**

- `test_CO096_cierra_las_ventanas_vencidas_y_avisa_al_administrador` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO096_mira_la_decision_y_no_el_estado` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO096_no_repite_ni_toca_las_vigentes` — `apps/pedidos/tests/test_contratos_08_demora.py`

**`CO-097` · ejecutarCicloDeCompensacionPorRetraso**

- `test_CO097_E1_un_articulo_que_llego_o_se_cancelo_no_acredita` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO097_E2_un_acumulador_en_el_tope_y_abierto_se_cierra_sin_acreditar` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO097_E3_sin_acumuladores_no_hace_nada` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO097_acredita_el_5_por_ciento_por_semana_cumplida` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO097_correr_dos_veces_o_antes_de_la_semana_no_acredita_de_mas` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO097_el_tope_del_25_por_ciento_cierra_el_acumulador` — `apps/pedidos/tests/test_contratos_08_demora.py`

**`CO-098` · confirmarCancelacionDeArticuloDemorado**

- `test_CO098_E1_si_falla_no_queda_nada_y_avisa_al_administrador` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO098_cancelado_el_articulo_sale_del_historial_activo` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO098_cancelar_reembolsa_el_valor_en_puntos_y_no_toca_el_stock` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO098_con_envio_gratis_el_pedido_cancelado_solo_devuelve_el_articulo` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO098_pagado_con_puntos_devuelve_los_mismos_puntos` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO098_un_pedido_sin_otros_articulos_se_cancela_y_devuelve_el_envio` — `apps/pedidos/tests/test_contratos_08_demora.py`

**`CO-103` · aplicarCanjeDePuntosAItem**

- `test_CO103_E1_no_hay_canje_parcial_entre_dos_lineas` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO103_E1_saldo_insuficiente_no_cubre_y_lo_informa` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO103_E2_se_verifica_con_el_precio_de_hoy` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO103_la_linea_de_otro_carrito_responde_404` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO103_la_linea_queda_cubierta_y_el_total_baja_su_precio` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO103_los_puntos_requeridos_redondean_hacia_arriba` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO103_mostrador_E2_saldo_insuficiente_no_cubre` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO103_mostrador_el_item_queda_cubierto_y_el_total_baja` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO103_mostrador_ningun_lote_cambia` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO103_mostrador_sin_cliente_no_hay_canje` — `apps/ventas/tests/test_contratos_06_ventas.py`
- `test_CO103_ningun_lote_de_puntos_se_modifica_ni_se_audita` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO103_sin_saldo_no_hay_canje` — `apps/tienda/tests/test_contratos_07_compra.py`

**`CO-104` · revertirCanjeDePuntosDeItem**

- `test_CO104_la_linea_vuelve_a_su_precio_sin_tocar_lotes` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO104_mostrador_el_item_vuelve_a_su_precio` — `apps/ventas/tests/test_contratos_06_ventas.py`

**`CO-108` · actualizarDatosPersonales**

- `test_CO108_c_los_atributos_modificados_pasan_a_los_declarados` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO108_el_correo_no_se_cambia_desde_aca` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO108_guardar_sin_cambios_no_audita` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO108_queda_en_la_auditoria_con_el_actor` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO108_una_direccion_incoherente_no_cambia_nada` — `apps/accounts/tests/test_contratos_11_cuenta.py`

**`CO-109` · solicitarCambioDeCorreo**

- `test_CO109_E1_un_correo_con_cuenta_se_rechaza_y_ofrece_recuperar` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO109_a_se_crea_un_token_de_cambio_de_correo` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO109_con_la_contrasena_equivocada_no_se_emite_nada` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO109_el_correo_de_la_cuenta_no_cambia` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO109_el_enlace_va_al_correo_nuevo` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO109_un_pedido_nuevo_vence_el_anterior` — `apps/accounts/tests/test_contratos_11_cuenta.py`

**`CO-110` · confirmarCambioDeCorreo**

- `test_CO110_abrir_el_enlace_no_cambia_nada` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO110_c_el_correo_pasa_al_nuevo_y_el_token_queda_consumido` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO110_el_correo_anterior_recibe_un_aviso` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO110_queda_en_la_auditoria` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO110_si_otra_cuenta_tomo_el_correo_en_el_medio_no_se_cambia` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO110_un_enlace_usado_no_sirve_dos_veces` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO110_un_enlace_vencido_no_sirve` — `apps/accounts/tests/test_contratos_11_cuenta.py`

**`CO-111` · cambiarContrasena**

- `test_CO111_c_la_credencial_pasa_al_hash_nuevo` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO111_con_la_contrasena_actual_equivocada_no_cambia_nada` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO111_la_sesion_actual_sigue_y_las_otras_se_cierran` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO111_queda_en_la_auditoria` — `apps/accounts/tests/test_contratos_11_cuenta.py`

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
- `test_CO121_dos_administradores_que_se_sacan_el_rol_a_la_vez_dejan_uno` — `apps/accounts/tests/test_concurrencia_ultimo_administrador.py`
- `test_CO121_la_ultima_modificacion_queda_con_el_instante` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO121_los_atributos_pasan_de_su_valor_anterior_al_declarado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO121_no_se_puede_quitar_el_rol_al_ultimo_administrador` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO121_registra_los_valores_anterior_y_nuevo_de_cada_campo` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO121_sin_cambiar_el_rol_la_sesion_del_usuario_sigue_viva` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO121_un_correo_que_ya_es_de_otra_cuenta_no_actualiza` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO121_una_cuenta_inactiva_no_admite_modificacion` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO121_una_cuenta_inactiva_no_cambia_aunque_se_envie_el_formulario` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO121_y_CO123_cruzados_dejan_uno` — `apps/accounts/tests/test_concurrencia_ultimo_administrador.py`

**`CO-122` · regenerarEnlaceDeActivacion**

- `test_CO122_el_correo_de_activacion_fue_reenviado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO122_el_enlace_anterior_deja_de_admitir_uso` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO122_el_enlace_anterior_pasa_de_vigente_a_vencido` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO122_registra_el_reenvio_en_auditoria` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO122_se_creo_un_enlace_nuevo_con_vigencia_de_48_horas` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`

**`CO-123` · confirmarBajaDeUsuario**

- `test_CO123_dos_administradores_que_se_dan_de_baja_a_la_vez_dejan_uno` — `apps/accounts/tests/test_concurrencia_ultimo_administrador.py`
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

**`CO-126` · confirmarCierreDeCaja**

- `test_CO126_E1_no_hay_segundo_cierre_en_el_dia` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO126_E2_sin_movimientos_no_hay_cierre` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO126_a_se_crea_el_cierre` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO126_b_el_cierre_queda_asociado_a_las_transacciones_incluidas` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO126_c_fecha_totales_y_cuentas` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO126_c_las_incluidas_pasan_a_incluidas_en_cierre` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO126_c_las_pendientes_y_rechazadas_quedan_fuera` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO126_dos_cierres_a_la_vez_dejan_uno_solo_con_cada_transaccion_una_vez` — `apps/caja/tests/test_concurrencia_caja.py`
- `test_CO126_la_base_no_admite_dos_cierres_de_la_misma_fecha` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO126_lo_vendido_despues_entra_en_el_cierre_siguiente` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO126_queda_en_la_auditoria_con_los_totales` — `apps/caja/tests/test_contratos_14_caja.py`

**`CO-127` · exportarCierreDeCaja**

- `test_CO127_el_csv_trae_cada_transaccion_y_los_totales` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO127_queda_en_la_auditoria` — `apps/caja/tests/test_contratos_14_caja.py`

**`CO-129` · exportarLogDeAuditoria**

- `test_CO129_exportar_trae_todo_el_filtro_y_no_solo_la_pagina` — `apps/core/tests/test_contratos_16_auditoria.py`
- `test_CO129_las_celdas_no_se_interpretan_como_formulas` — `apps/core/tests/test_contratos_16_auditoria.py`

**`CO-130` · actualizarParametrosOperacionales**

- `test_CO130_b_la_configuracion_queda_asociada_al_administrador` — `apps/catalog/tests/test_parametros_compra.py`
- `test_CO130_guardar_sin_cambios_no_deja_entradas` — `apps/catalog/tests/test_parametros_compra.py`
- `test_CO130_la_pantalla_muestra_la_seccion_de_compra_online` — `apps/catalog/tests/test_parametros_compra.py`
- `test_CO130_los_parametros_de_la_compra_pasan_a_los_declarados` — `apps/catalog/tests/test_parametros_compra.py`
- `test_CO130_los_valores_operativos_no_cambian_al_guardar_la_compra` — `apps/catalog/tests/test_parametros_compra.py`
- `test_CO130_solo_se_audita_lo_que_cambio` — `apps/catalog/tests/test_parametros_compra.py`
- `test_CO130_un_valor_fuera_de_rango_no_se_guarda` — `apps/catalog/tests/test_parametros_compra.py`
- `test_CO130_una_entrada_de_auditoria_por_cada_parametro_modificado` — `apps/catalog/tests/test_parametros_compra.py`

**`CO-131` · actualizarIdentidadVisual**

- `test_CO131_E1_un_hex_invalido_no_aplica_ningun_cambio` — `apps/core/tests/test_contratos_17_contenido.py`
- `test_CO131_E2_una_imagen_invalida_se_descarta_y_no_aplica_nada` — `apps/core/tests/test_contratos_17_contenido.py`
- `test_CO131_actualizar_identidad_aplica_a_la_tienda_y_audita_lo_anterior` — `apps/core/tests/test_contratos_17_contenido.py`
- `test_CO131_el_fondo_puede_ser_una_imagen` — `apps/core/tests/test_contratos_17_contenido.py`
- `test_CO131_el_nombre_y_el_correo_son_obligatorios` — `apps/core/tests/test_contratos_17_contenido.py`
- `test_CO131_la_imagen_del_ingreso_se_procesa_y_se_audita` — `apps/core/tests/test_contratos_17_contenido.py`
- `test_CO131_la_tienda_carga_la_hoja_sin_cambiar_el_backoffice` — `apps/core/tests/test_contratos_17_contenido.py`
- `test_CO131_quitar_el_logo_y_la_imagen_del_ingreso_vuelve_a_lo_predeterminado` — `apps/core/tests/test_contratos_17_contenido.py`

**`CO-132` · agregarBanner**

- `test_CO132_E1_una_imagen_invalida_no_agrega_nada` — `apps/core/tests/test_contratos_17_contenido.py`
- `test_CO132_agregar_banner_lo_pone_al_final_procesado_y_publicado` — `apps/core/tests/test_contratos_17_contenido.py`

**`CO-133` · editarBanner**

- `test_CO133_E1_imagen_invalida_no_registra_tampoco_la_posicion` — `apps/core/tests/test_contratos_17_contenido.py`
- `test_CO133_la_posicion_fuera_de_rango_se_rechaza` — `apps/core/tests/test_contratos_17_contenido.py`
- `test_CO133_mover_un_banner_reajusta_a_los_demas` — `apps/core/tests/test_contratos_17_contenido.py`
- `test_CO133_reemplazar_la_imagen_conserva_la_posicion_y_borra_la_anterior` — `apps/core/tests/test_contratos_17_contenido.py`

**`CO-134` · eliminarBanner**

- `test_CO134_eliminar_reajusta_y_conserva_el_orden_relativo` — `apps/core/tests/test_contratos_17_contenido.py`
- `test_CO134_sin_confirmacion_no_hay_eliminacion` — `apps/core/tests/test_contratos_17_contenido.py`

**`CO-135` · publicarContenidoDeFaq**

- `test_CO135_el_markdown_se_publica_sin_html_crudo` — `apps/core/tests/test_contratos_17_contenido.py`
- `test_CO135_la_vista_previa_no_publica` — `apps/core/tests/test_contratos_17_contenido.py`
- `test_CO135_publicar_reemplaza_el_contenido_y_queda_en_la_tienda` — `apps/core/tests/test_contratos_17_contenido.py`
- `test_CO135_vacio_no_publica_sin_confirmacion` — `apps/core/tests/test_contratos_17_contenido.py`

**`CO-136` · confirmarPublicacionDeFaqVacia**

- `test_CO136_confirmar_la_faq_vacia_la_deja_en_blanco` — `apps/core/tests/test_contratos_17_contenido.py`

**`CO-137` · registrarEditorial**

- `test_CO137_E1_la_colision_enlaza_la_existente_con_su_estado_y_no_registra` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO137_E2_un_nombre_vacio_tras_normalizar_se_rechaza` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO137_registrar_editorial_la_crea_activa_normalizada_y_auditada` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO137_y_CO141_doble_envio_del_alta_deja_uno_y_avisa_sin_error` — `apps/catalog/tests/test_concurrencia_catalogos.py`

**`CO-138` · editarEditorial**

- `test_CO138_E1_la_colision_no_registra_el_cambio` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO138_editar_editorial_corrige_el_nombre_y_conserva_sus_asociaciones` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO138_la_modificacion_no_da_de_baja` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO138_reactivar_la_vuelve_a_ofrecer_en_los_formularios` — `apps/catalog/tests/test_contratos_17_catalogos.py`

**`CO-139` · solicitarBajaDeEditorial**

- `test_CO139_la_precondicion_exige_que_este_activa` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO139_solicitar_baja_de_editorial_informa_las_tres_cantidades_sin_cambiar_nada` — `apps/catalog/tests/test_contratos_17_catalogos.py`

**`CO-140` · confirmarBajaDeEditorial**

- `test_CO140_confirmar_baja_de_editorial_la_desactiva_y_conserva_todo` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO140_confirmar_dos_veces_no_deja_dos_bajas` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO140_reactivarla_destraba_el_borrador` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO140_un_borrador_que_la_hereda_registra_un_reparo_y_no_se_confirma` — `apps/catalog/tests/test_contratos_17_catalogos.py`

**`CO-141` · registrarTipoDeMaterial**

- `test_CO141_registrar_tipo_con_su_rubro_y_su_clasificacion` — `apps/catalog/tests/test_contratos_17_catalogos.py`

**`CO-142` · editarTipoDeMaterial**

- `test_CO142_E2_no_cambia_el_rubro_de_un_tipo_con_productos` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO142_E4_no_deja_de_clasificarse_por_formato_con_combinaciones_en_uso` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO142_dejar_de_clasificarse_por_formato_rompe_sus_combinaciones` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO142_reactivar_el_tipo_lo_vuelve_a_ofrecer` — `apps/catalog/tests/test_contratos_17_catalogos.py`

**`CO-144` · registrarFormato**

- `test_CO144_registrar_formato_con_tipos_declarados` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO144_un_formato_que_aplica_a_todos_no_declara_tipos` — `apps/catalog/tests/test_contratos_17_catalogos.py`

**`CO-145` · editarFormato**

- `test_CO145_E3_no_deja_sin_declarar_un_tipo_en_uso` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO145_pasar_a_aplica_a_todos_rompe_los_tipos_declarados` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO145_reactivar_el_formato_lo_vuelve_a_ofrecer` — `apps/catalog/tests/test_contratos_17_catalogos.py`

**`CO-146` · declararFormatosDeTipo**

- `test_CO146_E5_no_se_quita_un_formato_en_uso` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO146_declarar_formatos_de_tipo_forma_y_rompe_combinaciones` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO146_no_ofrece_ni_toca_los_formatos_que_aplican_a_todos` — `apps/catalog/tests/test_contratos_17_catalogos.py`

**`CO-147` · solicitarBajaDeFormato**

- `test_CO147_solicitar_baja_de_formato_informa_las_tres_cantidades` — `apps/catalog/tests/test_contratos_17_catalogos.py`

**`CO-148` · confirmarBajaDeFormato**

- `test_CO148_confirmar_baja_de_formato_conserva_productos_filas_y_tipos` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO148_un_borrador_con_el_formato_dado_de_baja_no_se_confirma` — `apps/catalog/tests/test_contratos_17_catalogos.py`

**`CO-156` · cancelarOperacion**

- `test_CO156_abandonar_antes_de_confirmar_no_cambia_nada` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO156_abandonar_el_cambio_de_margen_lo_deja_como_estaba` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO156_abandonar_la_baja_de_grupo_o_etiqueta_no_cambia_nada` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO156_abandonar_la_baja_de_un_catalogo_no_cambia_nada` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO156_abandonar_la_baja_de_una_combinacion_no_cambia_nada` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO156_abandonar_la_confirmacion_no_cambia_el_producto` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO156_abandonar_la_confirmacion_no_cambia_el_proveedor` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO156_abandonar_la_modificacion_no_cambia_el_precio` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO156_cancelar_la_baja_no_cambia_nada` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO156_volver_desde_el_informe_de_demora_no_registra_nada` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO156_volver_desde_la_cancelacion_no_cambia_nada` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO156_volver_desde_la_confirmacion_no_registra_nada` — `apps/pedidos/tests/test_contratos_08_demora.py`

**`CO-157` · consultarColaDeCorreos**

- `test_CO157_consultar_la_cola_no_modifica_nada` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO157_por_la_direccion_real_con_rol_cajero_se_deniega` — `apps/suppliers/tests/test_contratos_04_proveedores.py`

**`CO-158` · abrirFichaDeCorreo**

- `test_CO158_abrir_la_ficha_muestra_el_contenido_y_no_modifica_nada` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO158_la_ficha_de_un_pendiente_ofrece_aprobar_y_descartar` — `apps/suppliers/tests/test_contratos_04_proveedores.py`

**`CO-162` · consultarInventario**

- `test_CO162_consultar_inventario_filtra_por_editorial` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO162_el_filtro_ofrece_las_etiquetas_inactivas_marcadas` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-163` · consultarFichaDeProducto**

- `test_CO163_la_ficha_dibuja_para_el_cajero_solo_sus_campos` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO163_los_indicadores_que_no_puede_calcular_se_declaran_no_disponibles` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-164` · consultarGruposDeEtiqueta**

- `test_CO164_consultar_grupos_lista_activos_e_inactivos_con_sus_etiquetas` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-165` · consultarEtiquetasDeGrupo**

- `test_CO165_consultar_etiquetas_de_grupo_paginadas_con_busqueda_y_estado` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-166` · consultarTablaDePrecios**

- `test_CO166_consultar_tabla_con_filtros_combinables` — `apps/catalog/tests/test_contratos_03_pricing.py`

**`CO-167` · consultarMargenGlobal**

- `test_CO167_consultar_margen_lo_expresa_como_porcentaje` — `apps/catalog/tests/test_contratos_03_pricing.py`

**`CO-168` · abrirEdicionDeOferta**

- `test_CO168_E2_vencida_o_dada_de_baja_no_abre_ni_guarda` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO168_abre_con_los_campos_actuales` — `apps/catalog/tests/test_contratos_03_ofertas.py`

**`CO-169` · consultarOfertas**

- `test_CO169_E1_sin_resultados_ofrece_limpiar_y_E2_sin_ofertas_ofrece_la_alta` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO169_filtra_por_estado_texto_y_fechas` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO169_lista_de_la_mas_reciente_a_la_mas_vieja_con_su_estado_por_fecha` — `apps/catalog/tests/test_contratos_03_ofertas.py`

**`CO-170` · consultarFichaDeOferta**

- `test_CO170_la_ficha_muestra_los_dos_precios_y_las_acciones_del_estado` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO170_una_vencida_es_de_solo_lectura` — `apps/catalog/tests/test_contratos_03_ofertas.py`

**`CO-176` · consultarCatalogoPublico**

- `test_CO176_E1_sin_resultados_ofrece_limpiar_los_filtros` — `apps/core/tests/test_contratos_07_tienda.py`
- `test_CO176_busqueda_tipo_editorial_etiqueta_y_precio` — `apps/core/tests/test_contratos_07_tienda.py`
- `test_CO176_con_parcial_responde_solo_los_resultados` — `apps/core/tests/test_tienda_quinta_parte.py`
- `test_CO176_descatalogados_cancelados_y_para_adultos_no_se_ven_bajo_ningun_filtro` — `apps/core/tests/test_contratos_07_tienda.py`
- `test_CO176_etiquetas_del_mismo_grupo_suman_y_de_grupos_distintos_restringen` — `apps/core/tests/test_tienda_quinta_parte.py`
- `test_CO176_los_estados_son_interruptores` — `apps/core/tests/test_tienda_quinta_parte.py`
- `test_CO176_los_filtros_de_estado` — `apps/core/tests/test_contratos_07_tienda.py`
- `test_CO176_por_defecto_activos_con_stock_de_lo_mas_nuevo_a_lo_mas_viejo` — `apps/core/tests/test_contratos_07_tienda.py`
- `test_CO176_proximos_a_llegar_ordena_por_la_fecha_vigente` — `apps/core/tests/test_tienda_quinta_parte.py`
- `test_CO176_se_pagina_de_a_24` — `apps/core/tests/test_contratos_07_tienda.py`
- `test_CO176_varios_tipos_a_la_vez_suman_productos` — `apps/core/tests/test_tienda_quinta_parte.py`

**`CO-177` · consultarFichaPublicaDeProducto**

- `test_CO177_la_ficha_ofrece_la_accion_de_su_estado` — `apps/core/tests/test_contratos_07_tienda.py`
- `test_CO177_un_producto_no_visible_responde_404` — `apps/core/tests/test_contratos_07_tienda.py`
- `test_CO177_volver_conserva_los_filtros` — `apps/core/tests/test_contratos_07_tienda.py`

**`CO-178` · consultarCarrito**

- `test_CO178_A1_el_carrito_vacio_ofrece_el_catalogo` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO178_A3_y_A4_la_disponibilidad_se_deriva_del_producto` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO178_A4_la_pre_venta_figura_siempre_disponible` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO178_la_consulta_no_modifica_nada` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO178_presenta_las_lineas_con_precio_subtotal_y_total` — `apps/tienda/tests/test_contratos_07_carrito.py`

**`CO-179` · procederAlPago**

- `test_CO179_con_todas_las_lineas_disponibles_transfiere_al_checkout` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO179_el_invitado_que_elige_comprar_como_invitado_va_al_formulario` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO179_el_invitado_sin_elegir_va_a_iniciar_sesion_y_vuelve_al_checkout` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO179_no_modifica_el_estado_del_sistema` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO179_stock_insuficiente_bloquea` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO179_una_linea_no_disponible_bloquea_y_vuelve_al_carrito` — `apps/tienda/tests/test_contratos_07_compra.py`

**`CO-180` · iniciarCheckout**

- `test_CO180_E1_stock_perdido_por_compra_concurrente_vuelve_al_carrito` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO180_desde_el_monto_minimo_el_envio_es_gratis` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO180_no_modifica_el_estado_del_sistema` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO180_presenta_lineas_direccion_del_perfil_envio_y_subtotal` — `apps/tienda/tests/test_contratos_07_compra.py`

**`CO-181` · iniciarCompraComoInvitado**

- `test_CO181_A1_ofrece_iniciar_sesion` — `apps/tienda/tests/test_contratos_07_invitado.py`
- `test_CO181_no_modifica_el_estado_del_sistema` — `apps/tienda/tests/test_contratos_07_invitado.py`
- `test_CO181_presenta_el_formulario_de_datos_del_invitado` — `apps/tienda/tests/test_contratos_07_invitado.py`
- `test_CO181_un_carrito_con_pre_venta_no_se_compra_como_invitado` — `apps/tienda/tests/test_contratos_07_invitado.py`
- `test_CO181_un_cliente_con_sesion_va_a_su_checkout` — `apps/tienda/tests/test_contratos_07_invitado.py`

**`CO-182` · consultarPedidos**

- `test_CO182_E1_sin_resultados_informa_y_ofrece_limpiar` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO182_cada_fila_trae_cliente_o_invitado_canal_estado_y_total` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO182_filtra_por_estado_cliente_canal_y_demorados` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO182_filtra_por_rango_de_fechas` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO182_hace_las_mismas_consultas_con_pocos_o_muchos_pedidos` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO182_lista_los_pedidos_del_mas_reciente_al_mas_viejo` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO182_no_modifica_el_estado_del_sistema` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO182_un_filtro_invalido_se_ignora` — `apps/pedidos/tests/test_contratos_08_pedidos.py`

**`CO-183` · consultarDetalleDePedido**

- `test_CO183_en_un_estado_automatico_no_ofrece_avanzar` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO183_muestra_cliente_items_puntos_pago_y_linea_de_tiempo` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO183_no_modifica_el_estado_del_sistema` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO183_un_pedido_pagado_sólo_con_puntos_lo_dice` — `apps/pedidos/tests/test_contratos_08_pedidos.py`

**`CO-184` · consultarOpcionesAnteDemora**

- `test_CO184_E1_con_la_ventana_vencida_no_hay_opciones` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO184_con_otra_preventa_esperando_no_ofrece_recibir_lo_disponible` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO184_el_detalle_del_pedido_ofrece_elegir_que_hacer` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO184_muestra_el_articulo_sus_fechas_y_las_tres_opciones` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO184_sin_nada_para_despachar_no_ofrece_recibir_lo_disponible` — `apps/pedidos/tests/test_contratos_08_demora.py`

**`CO-188` · consultarPuntos**

- `test_CO188_A1_sin_puntos_saldo_cero_y_mensajes` — `apps/puntos/tests/test_contratos_10_puntos.py`
- `test_CO188_cada_lote_con_origen_monto_disponible_y_caducidad` — `apps/puntos/tests/test_contratos_10_puntos.py`
- `test_CO188_destaca_los_lotes_que_vencen_dentro_de_30_dias` — `apps/puntos/tests/test_contratos_10_puntos.py`
- `test_CO188_el_historial_descendente_con_saldo_resultante_y_su_pedido` — `apps/puntos/tests/test_contratos_10_puntos.py`
- `test_CO188_el_saldo_con_su_equivalencia_en_pesos` — `apps/puntos/tests/test_contratos_10_puntos.py`
- `test_CO188_no_modifica_el_estado_del_sistema` — `apps/puntos/tests/test_contratos_10_puntos.py`
- `test_CO188_no_muestra_los_puntos_de_otro_cliente` — `apps/puntos/tests/test_contratos_10_puntos.py`

**`CO-189` · filtrarMovimientosDePuntos**

- `test_CO189_E1_sin_resultados_informa_y_ofrece_limpiar` — `apps/puntos/tests/test_contratos_10_puntos.py`
- `test_CO189_filtra_por_rango_de_fechas` — `apps/puntos/tests/test_contratos_10_puntos.py`
- `test_CO189_filtra_por_tipo_y_muestra_el_total` — `apps/puntos/tests/test_contratos_10_puntos.py`
- `test_CO189_un_filtro_invalido_se_ignora` — `apps/puntos/tests/test_contratos_10_puntos.py`

**`CO-190` · confirmarSeleccionDeCanje**

- `test_CO190_A2_si_el_total_queda_en_cero_lo_informa_sin_cambiar_nada` — `apps/tienda/tests/test_contratos_07_compra.py`

**`CO-192` · consultarPanelDeCuenta**

- `test_CO192_E1_sin_pedidos_activos_informa_y_las_demas_secciones_siguen` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO192_el_historial_muestra_los_despachados` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO192_la_seccion_stock_en_local_no_se_muestra` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO192_muestra_los_pedidos_activos_del_cliente` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO192_no_modifica_el_estado_del_sistema` — `apps/accounts/tests/test_contratos_11_cuenta.py`

**`CO-193` · consultarDetalleDePedidoPropio**

- `test_CO193_el_pedido_de_otro_cliente_responde_404` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO193_muestra_items_precios_estados_alcanzados_y_sus_fechas` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO193_no_modifica_el_estado_del_sistema` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO193_un_pedido_activo_se_actualiza_solo_y_uno_despachado_no` — `apps/accounts/tests/test_contratos_11_cuenta.py`

**`CO-194` · consultarCuentasDeCliente**

- `test_CO194_A1_sin_coincidencias_lo_informa` — `apps/accounts/tests/test_contratos_11_cuenta_de_cliente.py`
- `test_CO194_E1_por_la_direccion_real_con_otro_rol_se_deniega` — `apps/accounts/tests/test_contratos_11_cuenta_de_cliente.py`
- `test_CO194_E1_sin_sesion_no_se_ve_el_padron` — `apps/accounts/tests/test_contratos_11_cuenta_de_cliente.py`
- `test_CO194_el_padron_lista_nombre_correo_estado_y_registro` — `apps/accounts/tests/test_contratos_11_cuenta_de_cliente.py`

**`CO-195` · consultarFichaDeCliente**

- `test_CO195_la_ficha_no_modifica_el_estado` — `apps/accounts/tests/test_contratos_11_cuenta_de_cliente.py`
- `test_CO195_la_ficha_no_ofrece_ninguna_modificacion` — `apps/accounts/tests/test_contratos_11_cuenta_de_cliente.py`
- `test_CO195_la_ficha_presenta_los_datos_que_declara_el_contrato` — `apps/accounts/tests/test_contratos_11_cuenta_de_cliente.py`
- `test_CO195_por_la_direccion_real_con_otro_rol_se_deniega` — `apps/accounts/tests/test_contratos_11_cuenta_de_cliente.py`
- `test_CO195_una_cuenta_de_personal_no_tiene_ficha_de_cliente` — `apps/accounts/tests/test_contratos_11_cuenta_de_cliente.py`

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

**`CO-202` · consultarFichaDeUsuario**

- `test_CO202_la_ficha_no_modifica_el_estado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO202_no_ofrece_la_baja_del_ultimo_administrador` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO202_por_la_direccion_real_con_rol_cajero_se_deniega` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO202_una_cuenta_activa_ofrece_modificar_y_dar_de_baja` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO202_una_cuenta_de_cliente_no_tiene_ficha_de_personal` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO202_una_cuenta_inactiva_ofrece_unicamente_reactivar` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO202_una_cuenta_pendiente_ofrece_reenviar_y_eliminar` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`

**`CO-203` · solicitarCierreDeCaja**

- `test_CO203_A1_lista_las_pendientes_de_verificacion_aparte` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO203_E2_sin_movimientos` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO203_avisa_lo_de_dias_anteriores_sin_cerrar` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO203_cuenta_las_compras_pagadas_solo_con_puntos` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO203_el_resumen_previo_totaliza_por_canal_y_por_medio` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO203_no_modifica_el_estado_del_sistema` — `apps/caja/tests/test_contratos_14_caja.py`

**`CO-205` · consultarLogDeAuditoria**

- `test_CO205_consultar_log_de_a_50_de_la_mas_reciente_a_la_mas_antigua` — `apps/core/tests/test_contratos_16_auditoria.py`
- `test_CO205_filtra_por_actor_accion_entidad_rol_y_fechas` — `apps/core/tests/test_contratos_16_auditoria.py`
- `test_CO205_un_rango_de_fechas_sin_entradas_lo_dice` — `apps/core/tests/test_contratos_16_auditoria.py`

**`CO-206` · consultarDetalleDeEntradaDeAuditoria**

- `test_CO206_el_detalle_presenta_la_entrada_completa` — `apps/core/tests/test_contratos_16_auditoria.py`

**`CO-208` · consultarIdentidadVisual**

- `test_CO208_consultar_identidad_presenta_los_valores_actuales` — `apps/core/tests/test_contratos_17_contenido.py`

**`CO-209` · consultarBanners**

- `test_CO209_consultar_banners_en_orden_con_la_vista_previa` — `apps/core/tests/test_contratos_17_contenido.py`

**`CO-210` · consultarContenidoDeFaq**

- `test_CO210_consultar_faq_presenta_lo_publicado_en_el_editor` — `apps/core/tests/test_contratos_17_contenido.py`

**`CO-211` · consultarEditoriales**

- `test_CO211_consultar_editoriales_lista_activas_e_inactivas_con_sus_productos` — `apps/catalog/tests/test_contratos_17_catalogos.py`

**`CO-212` · consultarTiposDeMaterial**

- `test_CO212_consultar_tipos_con_rubro_formatos_y_productos` — `apps/catalog/tests/test_contratos_17_catalogos.py`

**`CO-213` · consultarFormatos**

- `test_CO213_consultar_formatos_con_alcance_y_productos` — `apps/catalog/tests/test_contratos_17_catalogos.py`

**`CO-220` · solicitarBajaDeTipoDeMaterial**

- `test_CO220_solicitar_baja_de_tipo_cuenta_las_ofertas_vivas_del_tipo` — `apps/catalog/tests/test_contratos_17_catalogos.py`

**`CO-221` · confirmarBajaDeTipoDeMaterial**

- `test_CO221_confirmar_baja_de_tipo_conserva_sus_vinculos` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO221_un_borrador_que_hereda_el_tipo_no_se_confirma` — `apps/catalog/tests/test_contratos_17_catalogos.py`

---

## Lo que esta fotografía no cubre

- **No dice que un contrato esté verificado**, sólo que alguna prueba lleva su código. Una postcondición sin prueba no se distingue desde acá de una cubierta.
- **No mira las pruebas que no son de contrato.** Las de acceso, flujo, unidad y frontera no llevan código de contrato en el nombre, a propósito, y no entran en este recuento.
- **No mide cobertura de líneas.** Es otra puerta y su número vive en [`../ESTADO.md`](../ESTADO.md).
