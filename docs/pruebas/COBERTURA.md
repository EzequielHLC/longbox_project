> **Tipo: Fotografía.** Tomada el 2026-10-28, del repositorio y no de memoria.
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
| Con al menos una prueba que lleva su código | 219 |
| Sin ninguna | 0 |
| Pruebas de contrato en la suite | 1080 |

---

## Por archivo de contratos

### `00-transversales.md` — Transversales

18 contratos · 18 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-005` | confirmarPrecioManual | 3 | `apps/catalog/tests/test_contratos_01_alta_lotes.py` |
| `CO-017` | aprobarCorreoParaProcesamiento | 12 | `apps/suppliers/tests/test_concurrencia_correos.py`, `apps/suppliers/tests/test_contratos_04_proveedores.py` |
| `CO-019` | reprocesarCorreo | 5 | `apps/suppliers/tests/test_contratos_04_proveedores.py` |
| `CO-025` | cerrarSesionDeRevision | 6 | `apps/catalog/tests/test_contratos_01_revision.py` |
| `CO-031` | restaurarPrecioCalculado | 4 | `apps/catalog/tests/test_contratos_03_pricing.py` |
| `CO-053` | confirmarCambioDeMargenGlobal | 4 | `apps/accounts/tests/test_parametros_de_seguridad.py`, `apps/catalog/tests/test_contratos_03_pricing.py`, `apps/tienda/tests/test_contratos_07_carrito.py` |
| `CO-074` | enviarPedidoConsolidado — *contrato de operación interna* | 2 | `apps/restock/tests/test_contratos_05_restock.py`, `apps/suppliers/tests/test_pedidos_a_proveedor.py` |
| `CO-077` | notificarReposicionASuscriptores — *contrato de operación interna* | 8 | `apps/restock/tests/test_contratos_05_restock.py`, `apps/suppliers/tests/test_pedidos_a_proveedor.py` |
| `CO-086` | fusionarCarritoDeSesion | 4 | `apps/tienda/tests/test_contratos_07_carrito.py`, `apps/tienda/tests/test_tope_de_reservas.py` |
| `CO-087` | declararDireccionDeEnvio | 9 | `apps/almacen/tests/test_contratos_18_almacen.py`, `apps/tienda/tests/test_contratos_07_compra.py`, `apps/tienda/tests/test_retiro_en_local.py` |
| `CO-089` | registrarResultadoDePago | 41 | `apps/almacen/tests/test_contratos_18_almacen.py`, `apps/suppliers/tests/test_pedidos_a_proveedor.py`, `apps/tienda/tests/test_barra_envio.py`, `apps/tienda/tests/test_concurrencia_compra.py`, `apps/tienda/tests/test_contratos_07_compra.py`, `apps/tienda/tests/test_contratos_07_invitado.py`, `apps/tienda/tests/test_retiro_en_local.py` |
| `CO-103` | aplicarCanjeDePuntosAItem | 12 | `apps/tienda/tests/test_contratos_07_compra.py`, `apps/ventas/tests/test_contratos_06_ventas.py` |
| `CO-104` | revertirCanjeDePuntosDeItem | 2 | `apps/tienda/tests/test_contratos_07_compra.py`, `apps/ventas/tests/test_contratos_06_ventas.py` |
| `CO-122` | regenerarEnlaceDeActivacion | 5 | `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-137` | registrarEditorial | 4 | `apps/catalog/tests/test_concurrencia_catalogos.py`, `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-141` | registrarTipoDeMaterial | 1 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-144` | registrarFormato | 2 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-156` | cancelarOperacion | 14 | `apps/accounts/tests/test_contratos_11_baja.py`, `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`, `apps/almacen/tests/test_contratos_18_almacen.py`, `apps/catalog/tests/test_contratos_02_catalogo.py`, `apps/catalog/tests/test_contratos_03_ofertas.py`, `apps/catalog/tests/test_contratos_03_pricing.py`, `apps/catalog/tests/test_contratos_17_catalogos.py`, `apps/pedidos/tests/test_contratos_01_preventa.py`, `apps/pedidos/tests/test_contratos_08_demora.py`, `apps/suppliers/tests/test_contratos_04_proveedores.py` |

### `01-alta-editorial.md` — 01 Alta Editorial

24 contratos · 24 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-001` | iniciarLoteEditorial | 3 | `apps/catalog/tests/test_contratos_01_alta_lotes.py` |
| `CO-002` | declararCabeceraLote | 4 | `apps/catalog/tests/test_contratos_01_alta_lotes.py` |
| `CO-003` | agregarItemLote | 9 | `apps/catalog/tests/test_carreras_de_unicidad.py`, `apps/catalog/tests/test_contratos_01_alta_lotes.py`, `apps/catalog/tests/test_portadas_rnf05.py`, `apps/suppliers/tests/test_pedidos_a_proveedor.py` |
| `CO-004` | fijarPrecioManualItem | 1 | `apps/catalog/tests/test_contratos_01_alta_lotes.py` |
| `CO-006` | confirmarLote | 4 | `apps/catalog/tests/test_contratos_01_alta_lotes.py` |
| `CO-007` | declararCalculadoraLote | 2 | `apps/catalog/tests/test_contratos_01_alta_lotes.py` |
| `CO-008` | sobrescribirCotizacion | 1 | `apps/catalog/tests/test_contratos_01_alta_lotes.py` |
| `CO-009` | agregarItemLoteImportado | 3 | `apps/catalog/tests/test_contratos_01_alta_lotes.py`, `apps/catalog/tests/test_portadas_rnf05.py` |
| `CO-010` | fijarPrecioFinalManual | 1 | `apps/catalog/tests/test_contratos_01_alta_lotes.py` |
| `CO-011` | ejecutarCicloVigilanciaPreventa | 5 | `apps/pedidos/tests/test_contratos_01_preventa.py` |
| `CO-012` | ejecutarCicloEscaladoPorInaccion | 3 | `apps/pedidos/tests/test_contratos_01_preventa.py` |
| `CO-013` | confirmarIngresoDeLote | 16 | `apps/pedidos/tests/test_contratos_01_preventa.py`, `apps/restock/tests/test_contratos_05_restock.py`, `apps/suppliers/tests/test_pedidos_a_proveedor.py` |
| `CO-014` | solicitarRegistroDeDemora | 4 | `apps/pedidos/tests/test_contratos_01_preventa.py` |
| `CO-015` | confirmarRegistroDeDemora | 7 | `apps/pedidos/tests/test_contratos_01_preventa.py`, `apps/pedidos/tests/test_demora_de_varios_tomos.py` |
| `CO-016` | ejecutarCicloMonitoreoCasilla | 11 | `apps/suppliers/tests/test_monitoreo_casilla.py` |
| `CO-020` | editarBorrador | 5 | `apps/catalog/tests/test_contratos_01_revision.py`, `apps/catalog/tests/test_portadas_rnf05.py` |
| `CO-021` | marcarCampoRevisado | 1 | `apps/catalog/tests/test_contratos_01_revision.py` |
| `CO-022` | confirmarBorrador | 7 | `apps/catalog/tests/test_contratos_01_revision.py`, `apps/catalog/tests/test_revision_borradores.py` |
| `CO-023` | confirmarBorradoresEnLote | 1 | `apps/catalog/tests/test_contratos_01_revision.py` |
| `CO-024` | rechazarBorrador | 2 | `apps/catalog/tests/test_contratos_01_revision.py` |
| `CO-026` | solicitarCancelacionDePreventaEnLote | 2 | `apps/pedidos/tests/test_contratos_01_preventa.py` |
| `CO-027` | confirmarCancelacionDePreventaEnLote | 6 | `apps/pedidos/tests/test_contratos_01_preventa.py`, `apps/puntos/tests/test_descuento_de_ganados.py` |
| `CO-159` | consultarColaDeBorradores | 3 | `apps/catalog/tests/test_contratos_01_revision.py` |
| `CO-160` | abrirBorrador | 1 | `apps/catalog/tests/test_contratos_01_revision.py` |

### `02-catalogo.md` — 02 Catálogo

22 contratos · 22 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-028` | registrarProductoNoEditorial | 14 | `apps/catalog/tests/test_carreras_de_unicidad.py`, `apps/catalog/tests/test_contratos_02_producto.py`, `apps/catalog/tests/test_portadas_rnf05.py` |
| `CO-029` | confirmarAltaPeseAHomonimo | 2 | `apps/catalog/tests/test_contratos_02_producto.py` |
| `CO-030` | editarProducto | 13 | `apps/catalog/tests/test_carreras_de_unicidad.py`, `apps/catalog/tests/test_contratos_02_producto.py`, `apps/catalog/tests/test_portadas_rnf05.py` |
| `CO-032` | confirmarEdicionPeseAColision | 2 | `apps/catalog/tests/test_contratos_02_producto.py` |
| `CO-033` | solicitarBajaDeProducto | 3 | `apps/catalog/tests/test_contratos_02_producto.py` |
| `CO-034` | confirmarBajaDeProducto | 9 | `apps/catalog/tests/test_contratos_02_producto.py` |
| `CO-035` | solicitarReactivacionDeProducto | 2 | `apps/catalog/tests/test_contratos_02_producto.py` |
| `CO-036` | confirmarReactivacionDeProducto | 5 | `apps/catalog/tests/test_contratos_02_producto.py` |
| `CO-037` | exportarInventario | 3 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-038` | registrarGrupoDeEtiqueta | 2 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-039` | editarGrupoDeEtiqueta | 2 | `apps/catalog/tests/test_contratos_02_catalogo.py`, `apps/catalog/tests/test_filtros_publicos_de_etiquetas.py` |
| `CO-040` | solicitarBajaDeGrupoDeEtiqueta | 1 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-041` | confirmarBajaDeGrupoDeEtiqueta | 2 | `apps/catalog/tests/test_contratos_02_catalogo.py`, `apps/catalog/tests/test_filtros_publicos_de_etiquetas.py` |
| `CO-042` | registrarEtiqueta | 3 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-043` | editarEtiqueta | 4 | `apps/catalog/tests/test_contratos_02_catalogo.py`, `apps/catalog/tests/test_filtros_publicos_de_etiquetas.py` |
| `CO-044` | solicitarBajaDeEtiqueta | 1 | `apps/catalog/tests/test_contratos_02_catalogo.py` |
| `CO-045` | confirmarBajaDeEtiqueta | 3 | `apps/catalog/tests/test_contratos_02_catalogo.py`, `apps/catalog/tests/test_filtros_publicos_de_etiquetas.py` |
| `CO-161` | abrirEdicionDeProducto | 3 | `apps/catalog/tests/test_contratos_02_producto.py` |
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

13 contratos · 13 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-018` | descartarCorreo | 2 | `apps/suppliers/tests/test_contratos_04_proveedores.py` |
| `CO-060` | registrarProveedor | 5 | `apps/suppliers/tests/test_concurrencia_proveedores.py`, `apps/suppliers/tests/test_contratos_04_padron.py` |
| `CO-061` | editarProveedor | 6 | `apps/suppliers/tests/test_contratos_04_padron.py` |
| `CO-062` | confirmarCambioDeCorreoComercial | 2 | `apps/suppliers/tests/test_contratos_04_padron.py` |
| `CO-063` | solicitarBajaDeProveedor | 2 | `apps/suppliers/tests/test_contratos_04_padron.py` |
| `CO-064` | confirmarBajaDeProveedor | 5 | `apps/suppliers/tests/test_contratos_04_padron.py` |
| `CO-065` | solicitarReactivacionDeProveedor | 2 | `apps/suppliers/tests/test_contratos_04_padron.py` |
| `CO-066` | confirmarReactivacionDeProveedor | 8 | `apps/suppliers/tests/test_contratos_04_padron.py` |
| `CO-157` | consultarColaDeCorreos | 2 | `apps/suppliers/tests/test_contratos_04_proveedores.py` |
| `CO-158` | abrirFichaDeCorreo | 2 | `apps/suppliers/tests/test_contratos_04_proveedores.py` |
| `CO-171` | abrirEdicionDeProveedor | 1 | `apps/suppliers/tests/test_contratos_04_padron.py` |
| `CO-172` | consultarProveedores | 5 | `apps/suppliers/tests/test_contratos_04_padron.py` |
| `CO-173` | consultarFichaDeProveedor | 4 | `apps/suppliers/tests/test_contratos_04_padron.py` |

### `05-restock.md` — 05 Restock

11 contratos · 11 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-067` | ejecutarCicloDePropuestaDeRestock | 4 | `apps/restock/tests/test_contratos_05_restock.py` |
| `CO-068` | generarPropuestaDeRestock | 3 | `apps/restock/tests/test_contratos_05_restock.py` |
| `CO-069` | ajustarCantidadDeLinea | 4 | `apps/restock/tests/test_contratos_05_restock.py` |
| `CO-070` | eliminarLineaDePropuesta | 1 | `apps/restock/tests/test_contratos_05_restock.py` |
| `CO-071` | agregarProductoAPropuesta | 1 | `apps/restock/tests/test_contratos_05_restock.py` |
| `CO-072` | despacharPedidoAProveedor | 5 | `apps/restock/tests/test_contratos_05_restock.py`, `apps/suppliers/tests/test_pantallas_pedidos.py`, `apps/suppliers/tests/test_pedidos_a_proveedor.py` |
| `CO-073` | descartarProveedorDePropuesta | 2 | `apps/restock/tests/test_contratos_05_restock.py` |
| `CO-075` | suscribirseAReposicion | 5 | `apps/restock/tests/test_contratos_05_restock.py`, `apps/suppliers/tests/test_pedidos_a_proveedor.py` |
| `CO-076` | cancelarSuscripcionDeReposicion | 2 | `apps/restock/tests/test_avisos_de_la_cuenta.py`, `apps/restock/tests/test_contratos_05_restock.py` |
| `CO-174` | consultarPropuestaDeRestock | 2 | `apps/restock/tests/test_contratos_05_restock.py` |
| `CO-175` | consultarLineasDeProveedor | 1 | `apps/restock/tests/test_contratos_05_restock.py` |

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
| `CO-083` | agregarProductoAlCarrito | 21 | `apps/core/tests/test_tienda_quinta_parte.py`, `apps/suppliers/tests/test_pedidos_a_proveedor.py`, `apps/tienda/tests/test_concurrencia_carrito.py`, `apps/tienda/tests/test_contratos_07_carrito.py`, `apps/tienda/tests/test_tope_de_reservas.py` |
| `CO-084` | modificarCantidadDeLinea | 8 | `apps/core/tests/test_tienda_quinta_parte.py`, `apps/tienda/tests/test_contratos_07_carrito.py` |
| `CO-085` | eliminarLineaDelCarrito | 3 | `apps/core/tests/test_tienda_quinta_parte.py`, `apps/tienda/tests/test_contratos_07_carrito.py` |
| `CO-088` | confirmarPedido | 8 | `apps/tienda/tests/test_contratos_07_compra.py`, `apps/tienda/tests/test_retiro_en_local.py` |
| `CO-090` | declararDatosDeInvitado | 6 | `apps/tienda/tests/test_contratos_07_invitado.py`, `apps/tienda/tests/test_retiro_en_local.py` |
| `CO-091` | confirmarPedidoDeInvitado | 2 | `apps/tienda/tests/test_contratos_07_invitado.py` |
| `CO-176` | consultarCatalogoPublico | 11 | `apps/core/tests/test_contratos_07_tienda.py`, `apps/core/tests/test_tienda_quinta_parte.py` |
| `CO-177` | consultarFichaPublicaDeProducto | 3 | `apps/core/tests/test_contratos_07_tienda.py` |
| `CO-178` | consultarCarrito | 6 | `apps/tienda/tests/test_contratos_07_carrito.py`, `apps/tienda/tests/test_tope_de_reservas.py` |
| `CO-179` | procederAlPago | 7 | `apps/tienda/tests/test_contratos_07_compra.py`, `apps/tienda/tests/test_tope_de_reservas.py` |
| `CO-180` | iniciarCheckout | 4 | `apps/tienda/tests/test_contratos_07_compra.py` |
| `CO-181` | iniciarCompraComoInvitado | 5 | `apps/tienda/tests/test_contratos_07_invitado.py` |

### `08-gestion-de-pedidos.md` — 08 Gestión de Pedidos

10 contratos · 10 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-092` | avanzarEstadoDePedido | 20 | `apps/pedidos/tests/test_acceso_y_concurrencia_pedidos.py`, `apps/pedidos/tests/test_contratos_08_pedidos.py`, `apps/tienda/tests/test_retiro_en_local.py` |
| `CO-093` | confirmarAvancePeseADecisionPendiente | 1 | `apps/pedidos/tests/test_contratos_08_pedidos.py` |
| `CO-094` | seleccionarOpcionAnteDemora | 2 | `apps/pedidos/tests/test_contratos_08_demora.py` |
| `CO-095` | confirmarOpcionAnteDemora | 8 | `apps/almacen/tests/test_contratos_18_almacen.py`, `apps/pedidos/tests/test_contratos_08_demora.py` |
| `CO-096` | ejecutarCicloDeVencimientoDeVentanaDeDecision | 3 | `apps/pedidos/tests/test_contratos_08_demora.py` |
| `CO-097` | ejecutarCicloDeCompensacionPorRetraso | 6 | `apps/pedidos/tests/test_contratos_08_demora.py` |
| `CO-098` | confirmarCancelacionDeArticuloDemorado | 7 | `apps/pedidos/tests/test_contratos_08_demora.py`, `apps/puntos/tests/test_descuento_de_ganados.py` |
| `CO-182` | consultarPedidos | 8 | `apps/pedidos/tests/test_contratos_08_pedidos.py` |
| `CO-183` | consultarDetalleDePedido | 4 | `apps/pedidos/tests/test_contratos_08_pedidos.py` |
| `CO-184` | consultarOpcionesAnteDemora | 5 | `apps/pedidos/tests/test_contratos_08_demora.py` |

### `09-devoluciones.md` — 09 Devoluciones

7 contratos · 7 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-099` | registrarCasoDeDevolucion | 21 | `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`, `apps/devoluciones/tests/test_contratos_09_devoluciones.py`, `apps/tienda/tests/test_retiro_en_local.py` |
| `CO-100` | resolverCasoConCambio | 13 | `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`, `apps/devoluciones/tests/test_contratos_09_devoluciones.py` |
| `CO-101` | resolverCasoConReembolsoEnPuntos | 13 | `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`, `apps/devoluciones/tests/test_contratos_09_devoluciones.py` |
| `CO-102` | rechazarCasoDeDevolucion | 5 | `apps/devoluciones/tests/test_contratos_09_devoluciones.py` |
| `CO-185` | iniciarSolicitudDeDevolucion | 9 | `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`, `apps/devoluciones/tests/test_contratos_09_devoluciones.py`, `apps/tienda/tests/test_retiro_en_local.py` |
| `CO-186` | consultarCasosDeDevolucion | 3 | `apps/devoluciones/tests/test_contratos_09_devoluciones.py` |
| `CO-187` | consultarDetalleDeCasoDeDevolucion | 1 | `apps/devoluciones/tests/test_contratos_09_devoluciones.py` |

### `10-puntos.md` — 10 Puntos

6 contratos · 6 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-105` | ejecutarCicloDeCaducidadDePuntos | 12 | `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py` |
| `CO-106` | registrarAjusteManualDePuntos | 12 | `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py` |
| `CO-188` | consultarPuntos | 7 | `apps/puntos/tests/test_contratos_10_puntos.py` |
| `CO-189` | filtrarMovimientosDePuntos | 4 | `apps/puntos/tests/test_contratos_10_puntos.py` |
| `CO-190` | confirmarSeleccionDeCanje | 1 | `apps/tienda/tests/test_contratos_07_compra.py` |
| `CO-191` | consultarPuntosDeCliente | 3 | `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py` |

### `11-cuenta-de-cliente.md` — 11 Cuenta de Cliente

11 contratos · 11 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-107` | registrarCuentaDeCliente | 8 | `apps/accounts/tests/test_carreras_de_unicidad.py`, `apps/accounts/tests/test_contratos_11_registro.py` |
| `CO-108` | actualizarDatosPersonales | 5 | `apps/accounts/tests/test_contratos_11_cuenta.py` |
| `CO-109` | solicitarCambioDeCorreo | 6 | `apps/accounts/tests/test_contratos_11_cuenta.py` |
| `CO-110` | confirmarCambioDeCorreo | 7 | `apps/accounts/tests/test_contratos_11_cuenta.py` |
| `CO-111` | cambiarContrasena | 4 | `apps/accounts/tests/test_contratos_11_cuenta.py` |
| `CO-112` | solicitarBajaDeCuentaPropia | 7 | `apps/accounts/tests/test_contratos_11_baja.py` |
| `CO-113` | confirmarBajaDeCuentaPropia | 12 | `apps/accounts/tests/test_contratos_11_baja.py` |
| `CO-192` | consultarPanelDeCuenta | 7 | `apps/accounts/tests/test_contratos_11_cuenta.py`, `apps/tienda/tests/test_retiro_en_local.py` |
| `CO-193` | consultarDetalleDePedidoPropio | 4 | `apps/accounts/tests/test_contratos_11_cuenta.py` |
| `CO-194` | consultarCuentasDeCliente | 4 | `apps/accounts/tests/test_contratos_11_cuenta_de_cliente.py` |
| `CO-195` | consultarFichaDeCliente | 5 | `apps/accounts/tests/test_contratos_11_cuenta_de_cliente.py` |

### `12-autenticacion.md` — 12 Autenticación

7 contratos · 7 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-114` | iniciarSesion | 13 | `apps/accounts/tests/test_contratos_12_autenticacion.py`, `apps/accounts/tests/test_parametros_de_seguridad.py` |
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
| `CO-120` | registrarUsuarioDelSistema | 12 | `apps/accounts/tests/test_carreras_de_unicidad.py`, `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-121` | modificarUsuarioDelSistema | 12 | `apps/accounts/tests/test_carreras_de_unicidad.py`, `apps/accounts/tests/test_concurrencia_ultimo_administrador.py`, `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-123` | confirmarBajaDeUsuario | 12 | `apps/accounts/tests/test_concurrencia_ultimo_administrador.py`, `apps/accounts/tests/test_contratos_11_baja.py`, `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
| `CO-124` | confirmarReactivacionDeUsuario | 13 | `apps/accounts/tests/test_contratos_11_baja.py`, `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py` |
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
| `CO-126` | confirmarCierreDeCaja | 12 | `apps/caja/tests/test_concurrencia_caja.py`, `apps/caja/tests/test_contratos_14_caja.py` |
| `CO-127` | exportarCierreDeCaja | 2 | `apps/caja/tests/test_contratos_14_caja.py` |
| `CO-203` | solicitarCierreDeCaja | 6 | `apps/caja/tests/test_contratos_14_caja.py` |

### `15-reportes.md` — 15 Reportes

2 contratos · 2 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-128` | exportarReporte | 3 | `apps/reportes/tests/test_contratos_15_reportes.py` |
| `CO-204` | generarReporteOperativo | 12 | `apps/reportes/tests/test_contratos_15_reportes.py` |

### `16-auditoria.md` — 16 Auditoría

3 contratos · 3 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-129` | exportarLogDeAuditoria | 2 | `apps/core/tests/test_contratos_16_auditoria.py` |
| `CO-205` | consultarLogDeAuditoria | 3 | `apps/core/tests/test_contratos_16_auditoria.py` |
| `CO-206` | consultarDetalleDeEntradaDeAuditoria | 1 | `apps/core/tests/test_contratos_16_auditoria.py` |

### `17-configuracion-del-sistema.md` — 17 Configuración del Sistema

27 contratos · 27 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-130` | actualizarParametrosOperacionales | 19 | `apps/accounts/tests/test_parametros_de_seguridad.py`, `apps/catalog/tests/test_parametros_compra.py`, `apps/devoluciones/tests/test_contratos_09_devoluciones.py`, `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py` |
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
| `CO-149` | ejecutarDiagnosticoDelModelo | 9 | `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py` |
| `CO-150` | verificarDisponibilidadDelModelo | 3 | `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py` |
| `CO-207` | consultarParametrosOperacionales | 1 | `apps/accounts/tests/test_parametros_de_seguridad.py` |
| `CO-208` | consultarIdentidadVisual | 1 | `apps/core/tests/test_contratos_17_contenido.py` |
| `CO-209` | consultarBanners | 1 | `apps/core/tests/test_contratos_17_contenido.py` |
| `CO-210` | consultarContenidoDeFaq | 1 | `apps/core/tests/test_contratos_17_contenido.py` |
| `CO-211` | consultarEditoriales | 1 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-212` | consultarTiposDeMaterial | 1 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-213` | consultarFormatos | 1 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-214` | consultarConfiguracionDeDiagnostico | 2 | `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py` |
| `CO-220` | solicitarBajaDeTipoDeMaterial | 1 | `apps/catalog/tests/test_contratos_17_catalogos.py` |
| `CO-221` | confirmarBajaDeTipoDeMaterial | 2 | `apps/catalog/tests/test_contratos_17_catalogos.py` |

### `18-stock-almacenado-en-local.md` — 18 Stock Almacenado en Local

10 contratos · 10 con prueba · 0 sin.

| Contrato | Operación | Pruebas | Dónde |
| --- | --- | ---: | --- |
| `CO-151` | confirmarDespachoDeStockAlmacenado | 5 | `apps/almacen/tests/test_contratos_18_almacen.py` |
| `CO-152` | confirmarDespachoFisico | 2 | `apps/almacen/tests/test_contratos_18_almacen.py` |
| `CO-153` | modificarPlazoDeRetencion | 3 | `apps/almacen/tests/test_contratos_18_almacen.py` |
| `CO-154` | ejecutarCicloDeVencimientoDeRetencion | 12 | `apps/almacen/tests/test_contratos_18_almacen.py`, `apps/puntos/tests/test_descuento_de_ganados.py`, `apps/tienda/tests/test_retiro_en_local.py` |
| `CO-155` | sincronizarCotizaciones | 2 | `apps/tienda/tests/test_cobros_abandonados.py` |
| `CO-215` | consultarStockAlmacenadoPropio | 2 | `apps/almacen/tests/test_contratos_18_almacen.py` |
| `CO-216` | solicitarDespachoDeStockAlmacenado | 3 | `apps/almacen/tests/test_contratos_18_almacen.py` |
| `CO-217` | consultarStockAlmacenado | 1 | `apps/almacen/tests/test_contratos_18_almacen.py` |
| `CO-218` | consultarFichaDeArticuloRetenido | 3 | `apps/almacen/tests/test_contratos_18_almacen.py`, `apps/tienda/tests/test_retiro_en_local.py` |
| `CO-227` | confirmarRetiroEnLocal | 4 | `apps/almacen/tests/test_contratos_18_almacen.py`, `apps/tienda/tests/test_retiro_en_local.py` |

---

## Prueba por prueba

Cada contrato con sus pruebas, por nombre. El nombre dice qué postcondición verifica cada una, que es lo que hace consultable la trazabilidad sin abrir un archivo.

**`CO-001` · iniciarLoteEditorial**

- `test_CO001_a_b_c_el_lote_nacional_queda_con_su_creador_origen_y_fecha` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO001_abrir_la_pantalla_no_crea_ningun_lote` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO001_c_el_origen_importado_queda_fijado` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`

**`CO-002` · declararCabeceraLote**

- `test_CO002_b_la_cabecera_asocia_editorial_tipo_y_formato` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO002_c_la_fecha_de_llegada_declarada_queda_en_el_lote` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO002_salida_el_precio_de_la_combinacion_completa_o_nada` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO002_sin_cabecera_el_lote_es_mixto_y_no_asocia_nada` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`

**`CO-003` · agregarItemLote**

- `test_CO003_E_un_repetido_por_isbn_dice_el_criterio` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO003_E_un_repetido_por_la_combinacion_no_guarda_nada_y_dice_con_cual_choca` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO003_c_el_estado_sigue_a_la_fecha_de_llegada` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO003_c_el_precio_sale_de_la_tabla_y_el_producto_queda_asociado` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO003_c_sin_combinacion_en_la_tabla_el_precio_es_el_declarado` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO003_c_sin_portada_queda_con_imagen_pendiente` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO003_el_tomo_cargado_mientras_tanto_se_excluye_como_duplicado` — `apps/catalog/tests/test_carreras_de_unicidad.py`
- `test_CO003_la_portada_del_lote_nacional_queda_en_webp_sin_el_original` — `apps/catalog/tests/test_portadas_rnf05.py`
- `test_CO003_una_preventa_del_lote_nace_sin_stock_y_su_cantidad_queda_pedida` — `apps/suppliers/tests/test_pedidos_a_proveedor.py`

**`CO-004` · fijarPrecioManualItem**

- `test_CO004_la_advertencia_sin_confirmar_no_cambia_nada` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`

**`CO-005` · confirmarPrecioManual**

- `test_CO005_b_c_confirmado_rompe_el_vinculo_y_fija_el_precio_a_mano` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO005_c_importado_confirmado_conserva_el_precio_base_calculado` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO005_la_auditoria_del_lote_registra_los_precios_a_mano` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`

**`CO-006` · confirmarLote**

- `test_CO006_E1_un_duplicado_del_catalogo_se_excluye_con_motivo_y_el_resto_se_crea` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO006_a_b_c_cada_item_es_un_producto_con_sus_asociaciones_y_valores` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO006_importado_guarda_precio_base_y_costo_en_origen` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO006_una_unica_entrada_de_auditoria_consolidada` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`

**`CO-007` · declararCalculadoraLote**

- `test_CO007_c_la_calculadora_y_el_margen_quedan_congelados_en_el_lote` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO007_cambiar_el_margen_despues_no_cambia_el_lote` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`

**`CO-008` · sobrescribirCotizacion**

- `test_CO008_c_la_cotizacion_declarada_reemplaza_a_la_del_servicio` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`

**`CO-009` · agregarItemLoteImportado**

- `test_CO009_A3_sin_imagen_se_registra_con_imagen_pendiente` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO009_c_precio_base_y_final_salen_del_cre_y_del_margen` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`
- `test_CO009_la_portada_del_lote_importado_queda_en_webp_sin_el_original` — `apps/catalog/tests/test_portadas_rnf05.py`

**`CO-010` · fijarPrecioFinalManual**

- `test_CO010_la_advertencia_sin_confirmar_no_cambia_nada` — `apps/catalog/tests/test_contratos_01_alta_lotes.py`

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
- `test_CO013_lo_confirmado_en_preventas_por_llegar_se_descuenta_del_pedido` — `apps/suppliers/tests/test_pedidos_a_proveedor.py`
- `test_CO013_lo_que_sobra_al_llegar_una_preventa_avisa_a_los_suscriptores` — `apps/restock/tests/test_contratos_05_restock.py`
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
- `test_CO015_el_que_ya_no_admite_la_demora_queda_afuera_y_los_demas_siguen` — `apps/pedidos/tests/test_demora_de_varios_tomos.py`
- `test_CO015_el_servicio_rechaza_una_fecha_estimada_que_no_es_futura` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO015_varios_tomos_cada_uno_con_su_fecha_y_su_auditoria` — `apps/pedidos/tests/test_demora_de_varios_tomos.py`

**`CO-016` · ejecutarCicloMonitoreoCasilla**

- `test_CO016_E1_un_remitente_no_registrado_no_se_encola_y_el_ciclo_sigue` — `apps/suppliers/tests/test_monitoreo_casilla.py`
- `test_CO016_E3_sin_conexion_avisa_al_administrador_y_no_encola` — `apps/suppliers/tests/test_monitoreo_casilla.py`
- `test_CO016_I16_correr_dos_veces_no_encola_dos_veces` — `apps/suppliers/tests/test_monitoreo_casilla.py`
- `test_CO016_corre_en_el_temporizador` — `apps/suppliers/tests/test_monitoreo_casilla.py`
- `test_CO016_el_boton_de_la_cola_encola_sin_esperar_la_frecuencia` — `apps/suppliers/tests/test_monitoreo_casilla.py`
- `test_CO016_encola_lo_de_un_proveedor_habilitado_sin_procesarlo` — `apps/suppliers/tests/test_monitoreo_casilla.py`
- `test_CO016_escuchar_al_bot_vigila_la_casilla` — `apps/suppliers/tests/test_monitoreo_casilla.py`
- `test_CO016_respeta_la_frecuencia_configurada` — `apps/suppliers/tests/test_monitoreo_casilla.py`
- `test_CO016_revisar_casilla_saltea_la_frecuencia` — `apps/suppliers/tests/test_monitoreo_casilla.py`
- `test_CO016_revisar_casilla_si_corresponde_respeta_la_frecuencia` — `apps/suppliers/tests/test_monitoreo_casilla.py`
- `test_CO016_sin_casilla_configurada_no_hace_nada` — `apps/suppliers/tests/test_monitoreo_casilla.py`

**`CO-017` · aprobarCorreoParaProcesamiento**

- `test_CO017_E1_la_segunda_aprobacion_encuentra_el_correo_tomado` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO017_E1_un_correo_ya_tomado_por_otro_no_se_vuelve_a_procesar` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO017_E4_si_el_servicio_no_responde_el_correo_falla_y_queda_en_la_cola` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO017_E4_si_no_identifica_ningun_producto_el_correo_falla` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO017_E4_un_correo_bien_clasificado_que_no_es_de_novedades_no_falla` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
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

**`CO-020` · editarBorrador**

- `test_CO020_a_CO025_otro_rol_no_resuelve_borradores` — `apps/catalog/tests/test_contratos_01_revision.py`
- `test_CO020_completar_los_bloqueantes_lo_pasa_a_pendiente` — `apps/catalog/tests/test_contratos_01_revision.py`
- `test_CO020_la_portada_que_se_le_carga_a_un_borrador_queda_en_webp` — `apps/catalog/tests/test_portadas_rnf05.py`
- `test_CO020_los_atributos_y_el_stock_inicial_pasan_a_lo_declarado` — `apps/catalog/tests/test_contratos_01_revision.py`
- `test_CO020_si_sigue_faltando_un_bloqueante_sigue_incompleto` — `apps/catalog/tests/test_contratos_01_revision.py`

**`CO-021` · marcarCampoRevisado**

- `test_CO021_el_campo_pasa_a_revisado` — `apps/catalog/tests/test_contratos_01_revision.py`

**`CO-022` · confirmarBorrador**

- `test_CO022_E3_un_bloqueante_vacio_bloquea` — `apps/catalog/tests/test_contratos_01_revision.py`
- `test_CO022_E7_el_tomo_confirmado_mientras_tanto_se_informa_como_duplicado` — `apps/catalog/tests/test_revision_borradores.py`
- `test_CO022_E7_la_colision_se_bloquea_antes_de_crear_y_enlaza_la_ficha` — `apps/catalog/tests/test_contratos_01_revision.py`
- `test_CO022_E7_por_combinacion_lo_dice` — `apps/catalog/tests/test_contratos_01_revision.py`
- `test_CO022_crea_el_producto_con_los_valores_del_borrador` — `apps/catalog/tests/test_contratos_01_revision.py`
- `test_CO022_la_segunda_decision_sigue_en_la_misma_sesion` — `apps/catalog/tests/test_contratos_01_revision.py`
- `test_CO022_precondicion_confianza_baja_sin_revisar_bloquea` — `apps/catalog/tests/test_contratos_01_revision.py`

**`CO-023` · confirmarBorradoresEnLote**

- `test_CO023_confirma_los_elegibles_y_no_toca_los_excluidos` — `apps/catalog/tests/test_contratos_01_revision.py`

**`CO-024` · rechazarBorrador**

- `test_CO024_pasa_a_rechazado_con_motivo_sesion_y_responsable` — `apps/catalog/tests/test_contratos_01_revision.py`
- `test_CO024_precondicion_sin_motivo_no_rechaza` — `apps/catalog/tests/test_contratos_01_revision.py`

**`CO-025` · cerrarSesionDeRevision**

- `test_CO025_E5_un_envio_fallido_no_revierte_los_productos` — `apps/catalog/tests/test_contratos_01_revision.py`
- `test_CO025_E6_sin_confirmaciones_no_se_envia_nada` — `apps/catalog/tests/test_contratos_01_revision.py`
- `test_CO025_cierra_la_sesion_con_el_resultado_por_proveedor` — `apps/catalog/tests/test_contratos_01_revision.py`
- `test_CO025_encadena_CO074_con_su_entrada_por_proveedor` — `apps/catalog/tests/test_contratos_01_revision.py`
- `test_CO025_la_entrada_del_cierre_trae_el_resumen` — `apps/catalog/tests/test_contratos_01_revision.py`
- `test_CO025_precondicion_sin_sesion_abierta_no_registra_cierre` — `apps/catalog/tests/test_contratos_01_revision.py`

**`CO-026` · solicitarCancelacionDePreventaEnLote**

- `test_CO026_informa_reservas_por_cliente_y_los_puntos_a_reembolsar` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO026_sin_reservas_lo_dice_con_cero` — `apps/pedidos/tests/test_contratos_01_preventa.py`

**`CO-027` · confirmarCancelacionDePreventaEnLote**

- `test_CO027_E1_si_falla_un_reembolso_no_queda_nada` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO027_cancela_reservas_reembolsa_en_puntos_y_cancela_el_producto` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO027_incluye_las_reservas_ya_demoradas` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO027_la_cancelacion_en_lote_descuenta_lo_que_gano_cada_reserva` — `apps/puntos/tests/test_descuento_de_ganados.py`
- `test_CO027_no_se_cancela_lo_que_no_esta_en_preventa` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO027_sin_reservas_solo_cambia_el_estado` — `apps/pedidos/tests/test_contratos_01_preventa.py`

**`CO-028` · registrarProductoNoEditorial**

- `test_CO028_E1_falta_un_obligatorio_no_registra_y_conserva_lo_escrito` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO028_E2_el_homonimo_advierte_con_enlace_y_no_registra_sin_confirmar` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO028_E3_el_codigo_ajeno_enlaza_la_ficha_en_conflicto` — `apps/catalog/tests/test_carreras_de_unicidad.py`
- `test_CO028_E3_el_codigo_tomado_mientras_se_validaba_bloquea_y_enlaza` — `apps/catalog/tests/test_carreras_de_unicidad.py`
- `test_CO028_E3_la_portada_del_alta_que_perdio_no_queda_en_el_almacenamiento` — `apps/catalog/tests/test_carreras_de_unicidad.py`
- `test_CO028_E3_un_codigo_ajeno_bloquea_aunque_se_confirme` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO028_crea_el_producto_con_sus_atributos_y_asociaciones` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO028_el_alta_no_la_hace_otro_rol` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO028_la_portada_del_alta_no_editorial_queda_en_webp_sin_el_original` — `apps/catalog/tests/test_portadas_rnf05.py`
- `test_CO028_precondicion_el_precio_es_mayor_que_cero` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO028_precondicion_el_stock_no_es_negativo` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO028_precondicion_el_tipo_tiene_que_ser_del_rubro` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO028_sin_codigo_declarado_se_genera_uno_unico` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO028_una_portada_gif_se_rechaza_y_no_registra` — `apps/catalog/tests/test_portadas_rnf05.py`

**`CO-029` · confirmarAltaPeseAHomonimo**

- `test_CO029_E1_un_faltante_sigue_bloqueando_aunque_se_confirme` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO029_confirmado_el_homonimo_se_crea_con_las_postcondiciones_de_CO028` — `apps/catalog/tests/test_contratos_02_producto.py`

**`CO-030` · editarProducto**

- `test_CO030_E1_un_obligatorio_vacio_no_actualiza` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO030_E1_una_clasificacion_de_otro_rubro_no_actualiza` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO030_E2_el_codigo_de_barras_ajeno_enlaza_la_ficha_y_el_criterio` — `apps/catalog/tests/test_carreras_de_unicidad.py`
- `test_CO030_E2_el_codigo_de_barras_tomado_mientras_se_validaba_no_actualiza` — `apps/catalog/tests/test_carreras_de_unicidad.py`
- `test_CO030_E2_el_isbn_tomado_mientras_se_validaba_no_actualiza` — `apps/catalog/tests/test_carreras_de_unicidad.py`
- `test_CO030_E2_la_colision_bloqueante_informa_con_enlace_y_no_actualiza` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO030_E3_la_colision_no_bloqueante_pide_confirmacion` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO030_cambiar_un_precio_vinculado_cumple_CO005` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO030_la_edicion_no_la_hace_otro_rol` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO030_la_portada_que_reemplaza_queda_en_webp_sin_el_original` — `apps/catalog/tests/test_portadas_rnf05.py`
- `test_CO030_los_atributos_cambian_y_la_auditoria_guarda_el_par` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO030_precondicion_un_descatalogado_se_edita` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO030_se_forman_y_rompen_las_asociaciones` — `apps/catalog/tests/test_contratos_02_producto.py`

**`CO-031` · restaurarPrecioCalculado**

- `test_CO031_no_aplica_a_un_producto_que_ya_sigue_su_fuente` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO031_un_importado_a_mano_vuelve_al_margen_vigente_desde_su_base` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO031_un_nacional_a_mano_vuelve_a_la_tabla_y_se_vincula` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO031_un_nacional_que_perdio_su_fila_se_vuelve_a_vincular` — `apps/catalog/tests/test_contratos_03_pricing.py`

**`CO-032` · confirmarEdicionPeseAColision**

- `test_CO032_confirmada_la_colision_se_cumplen_las_postcondiciones_de_CO030` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO032_precondicion_un_tomo_no_admite_la_confirmacion` — `apps/catalog/tests/test_contratos_02_producto.py`

**`CO-033` · solicitarBajaDeProducto**

- `test_CO033_E2_un_cancelado_por_editorial_se_rechaza` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO033_el_informe_trae_las_cuatro_categorias_y_la_accion` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO033_pedir_el_informe_no_modifica_nada` — `apps/catalog/tests/test_contratos_02_producto.py`

**`CO-034` · confirmarBajaDeProducto**

- `test_CO034_CO036_baja_y_reactivacion_no_las_hace_otro_rol` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO034_E1_sin_referencias_la_baja_procede_igual` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO034_deja_de_verse_en_el_catalogo_publico_y_la_busqueda` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO034_el_carrito_queda_no_disponible_y_el_cliente_se_entera` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO034_el_estado_pasa_a_descatalogado` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO034_la_oferta_exclusiva_queda_dada_de_baja_y_la_del_tipo_lo_deja_de_alcanzar` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO034_las_suscripciones_quedan_canceladas` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO034_los_pedidos_activos_no_se_modifican` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO034_una_sola_entrada_con_el_impacto_resuelto` — `apps/catalog/tests/test_contratos_02_producto.py`

**`CO-035` · solicitarReactivacionDeProducto**

- `test_CO035_E1_un_cancelado_por_editorial_se_rechaza` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO035_el_resumen_no_modifica_nada` — `apps/catalog/tests/test_contratos_02_producto.py`

**`CO-036` · confirmarReactivacionDeProducto**

- `test_CO036_E2_la_fecha_vencida_queda_sin_efecto_y_se_informa` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO036_el_material_para_adultos_sigue_sujeto_a_su_indicador` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO036_la_entrada_guarda_el_estado_anterior_y_el_nuevo` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO036_no_se_restituyen_suscripciones_ni_ofertas` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO036_vuelve_activo_y_visible_con_su_identidad` — `apps/catalog/tests/test_contratos_02_producto.py`

**`CO-037` · exportarInventario**

- `test_CO037_el_cajero_no_exporta_por_la_direccion_real` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO037_el_cajero_no_ve_la_opcion_de_exportar` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO037_exportar_inventario_trae_las_filas_del_listado_filtrado` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-038` · registrarGrupoDeEtiqueta**

- `test_CO038_E1_la_colision_enlaza_el_grupo_existente` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO038_registrar_grupo_lo_crea_activo_y_auditado` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-039` · editarGrupoDeEtiqueta**

- `test_CO039_el_grupo_reactivado_vuelve_a_ofrecer_las_etiquetas_activas` — `apps/catalog/tests/test_filtros_publicos_de_etiquetas.py`
- `test_CO039_reactivar_el_grupo_no_reactiva_sus_etiquetas` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-040` · solicitarBajaDeGrupoDeEtiqueta**

- `test_CO040_solicitar_baja_de_grupo_informa_etiquetas_y_productos` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-041` · confirmarBajaDeGrupoDeEtiqueta**

- `test_CO041_el_grupo_dado_de_baja_y_sus_etiquetas_dejan_de_ofrecerse_en_la_tienda` — `apps/catalog/tests/test_filtros_publicos_de_etiquetas.py`
- `test_CO041_la_baja_del_grupo_alcanza_a_sus_etiquetas_y_conserva_las_asignaciones` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-042` · registrarEtiqueta**

- `test_CO042_E1_la_colision_es_dentro_del_grupo_y_enlaza_la_existente` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO042_no_se_crea_en_un_grupo_dado_de_baja` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO042_registrar_etiqueta_la_crea_activa_en_su_grupo` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-043` · editarEtiqueta**

- `test_CO043_E3_no_se_reactiva_dentro_de_un_grupo_dado_de_baja` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO043_la_etiqueta_reactivada_vuelve_a_ofrecerse_en_la_tienda` — `apps/catalog/tests/test_filtros_publicos_de_etiquetas.py`
- `test_CO043_mover_la_etiqueta_conserva_sus_asignaciones_y_su_estado` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO043_reactivar_moviendola_a_un_grupo_activo` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-044` · solicitarBajaDeEtiqueta**

- `test_CO044_solicitar_baja_de_etiqueta_informa_sus_productos` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-045` · confirmarBajaDeEtiqueta**

- `test_CO045_confirmar_baja_de_etiqueta_la_retira_y_conserva_sus_asignaciones` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO045_la_edicion_del_producto_la_presenta_marcada_y_no_la_pierde` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO045_la_etiqueta_dada_de_baja_deja_de_ofrecerse_en_la_tienda` — `apps/catalog/tests/test_filtros_publicos_de_etiquetas.py`

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
- `test_CO053_desde_parametros_el_margen_global_se_cambia_en_su_pantalla` — `apps/accounts/tests/test_parametros_de_seguridad.py`
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

- `test_CO060_E1_un_obligatorio_vacio_no_procede` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO060_E2_un_dato_repetido_en_cualquier_estado_enlaza_la_ficha` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO060_crea_el_proveedor_activo_normalizado_y_habilitado` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO060_doble_envio_del_alta_deja_uno_y_avisa_sin_error` — `apps/suppliers/tests/test_concurrencia_proveedores.py`
- `test_CO060_el_procesamiento_apagado_queda_apagado` — `apps/suppliers/tests/test_contratos_04_padron.py`

**`CO-061` · editarProveedor**

- `test_CO061_CO064_CO066_otro_rol_no_modifica_el_padron` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO061_E1_un_obligatorio_vacio_no_procede` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO061_E2_el_dato_de_otro_proveedor_se_informa_con_enlace` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO061_la_auditoria_guarda_cada_par_anterior_y_nuevo` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO061_los_atributos_cambian_y_la_modificacion_queda_con_el_instante` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO061_se_forman_y_rompen_editorial_y_tipo` — `apps/suppliers/tests/test_contratos_04_padron.py`

**`CO-062` · confirmarCambioDeCorreoComercial**

- `test_CO062_confirmado_el_correo_anterior_deja_de_ser_remitente_y_el_nuevo_pasa_a_serlo` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO062_sin_la_advertencia_confirmada_el_correo_no_cambia` — `apps/suppliers/tests/test_contratos_04_padron.py`

**`CO-063` · solicitarBajaDeProveedor**

- `test_CO063_el_informe_trae_productos_propuestas_y_reversibilidad` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO063_pedir_el_informe_no_modifica_nada` — `apps/suppliers/tests/test_contratos_04_padron.py`

**`CO-064` · confirmarBajaDeProveedor**

- `test_CO064_el_habitual_de_la_editorial_tambien_marca_la_linea` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO064_la_propuesta_activa_marca_proveedor_inactivo` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO064_los_productos_conservan_su_proveedor` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO064_pasa_a_inactivo_y_el_correo_deja_de_ser_remitente` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO064_queda_auditada` — `apps/suppliers/tests/test_contratos_04_padron.py`

**`CO-065` · solicitarReactivacionDeProveedor**

- `test_CO065_no_modifica_nada` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO065_presenta_los_datos_vigentes_con_el_correo_destacado` — `apps/suppliers/tests/test_contratos_04_padron.py`

**`CO-066` · confirmarReactivacionDeProveedor**

- `test_CO066_E1_la_colision_se_informa_con_enlace_y_no_reactiva` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO066_E2_un_correo_mal_formado_se_rechaza` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO066_el_doble_envio_no_registra_dos_reactivaciones` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO066_el_procesamiento_queda_con_el_valor_declarado` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO066_la_reactivacion_limpia_la_marca_de_la_propuesta` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO066_los_productos_conservan_su_proveedor` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO066_pasa_a_activo_con_las_correcciones_y_vuelve_al_filtro` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO066_queda_auditada_con_las_correcciones` — `apps/suppliers/tests/test_contratos_04_padron.py`

**`CO-067` · ejecutarCicloDePropuestaDeRestock**

- `test_CO067_E1_sin_elegibles_no_genera_y_lo_registra_una_vez_por_semana` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO067_E3_con_una_pendiente_no_genera_otra_y_avisa` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO067_E4_se_abstiene_si_hubo_una_propuesta_en_la_semana` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO067_arma_la_propuesta_por_proveedor_con_la_cantidad_sugerida` — `apps/restock/tests/test_contratos_05_restock.py`

**`CO-068` · generarPropuestaDeRestock**

- `test_CO068_E1_sin_elegibles_igual_omite_el_ciclo_de_la_semana` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO068_E3_con_una_pendiente_se_rechaza` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO068_el_disparo_manual_genera_aunque_haya_una_reciente_y_omite_el_ciclo` — `apps/restock/tests/test_contratos_05_restock.py`

**`CO-069` · ajustarCantidadDeLinea**

- `test_CO069_ajustar_la_cantidad_conserva_los_suscriptores` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO069_guardar_cantidades_cambia_las_del_proveedor_de_una_vez` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO069_guardar_cantidades_es_todo_o_nada` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO069_guardar_cantidades_ignora_lineas_de_otro_proveedor` — `apps/restock/tests/test_contratos_05_restock.py`

**`CO-070` · eliminarLineaDePropuesta**

- `test_CO070_quitar_elimina_la_linea` — `apps/restock/tests/test_contratos_05_restock.py`

**`CO-071` · agregarProductoAPropuesta**

- `test_CO071_agregar_va_al_grupo_de_su_proveedor` — `apps/restock/tests/test_contratos_05_restock.py`

**`CO-072` · despacharPedidoAProveedor**

- `test_CO072_E2_si_el_correo_falla_el_proveedor_sigue_pendiente` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO072_despachar_envia_el_correo_y_marca_las_lineas` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO072_despachar_restock_registra_el_pedido_y_abre_la_preventa_de_lo_agotado` — `apps/suppliers/tests/test_pedidos_a_proveedor.py`
- `test_CO072_el_despacho_lleva_la_llegada_estimada` — `apps/suppliers/tests/test_pantallas_pedidos.py`
- `test_CO072_el_grupo_sin_proveedor_no_se_despacha` — `apps/restock/tests/test_contratos_05_restock.py`

**`CO-073` · descartarProveedorDePropuesta**

- `test_CO073_descartar_exige_motivo_y_cierra_si_era_el_ultimo` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO073_descartar_un_proveedor_no_afecta_a_los_demas` — `apps/restock/tests/test_contratos_05_restock.py`

**`CO-074` · enviarPedidoConsolidado — *contrato de operación interna***

- `test_CO074_E2_sin_correo_no_se_envia_y_se_registra` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO074_un_pedido_que_no_salio_no_queda_registrado` — `apps/suppliers/tests/test_pedidos_a_proveedor.py`

**`CO-075` · suscribirseAReposicion**

- `test_CO075_E1_no_registra_un_duplicado` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO075_E2_si_ya_hay_stock_no_se_suscribe` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO075_con_la_preventa_completa_se_puede_pedir_el_aviso` — `apps/suppliers/tests/test_pedidos_a_proveedor.py`
- `test_CO075_el_invitado_va_al_ingreso_y_el_personal_no_puede` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO075_suscribirse_desde_la_ficha_de_un_agotado` — `apps/restock/tests/test_contratos_05_restock.py`

**`CO-076` · cancelarSuscripcionDeReposicion**

- `test_CO076_cancelar_desde_la_cuenta_elimina_la_propia_sin_auditar` — `apps/restock/tests/test_avisos_de_la_cuenta.py`
- `test_CO076_cancelar_elimina_la_suscripcion_sin_auditar` — `apps/restock/tests/test_contratos_05_restock.py`

**`CO-077` · notificarReposicionASuscriptores — *contrato de operación interna***

- `test_CO077_A1_sin_suscriptores_no_registra_nada` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO077_E1_un_envio_que_falla_tres_veces_conserva_el_turno` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO077_E2_quien_cancela_no_cede_su_cupo` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO077_bajar_el_stock_no_avisa` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO077_con_mas_unidades_que_suscriptores_avisa_a_todos` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO077_el_articulo_que_vuelve_por_vencimiento_tambien_avisa` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO077_lo_que_llega_avisa_a_la_lista_de_espera` — `apps/suppliers/tests/test_pedidos_a_proveedor.py`
- `test_CO077_reponer_por_la_edicion_avisa_a_los_primeros_n` — `apps/restock/tests/test_contratos_05_restock.py`

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
- `test_CO082_c_canal_presencial_y_nace_vendido_en_el_local` — `apps/ventas/tests/test_contratos_06_ventas.py`
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

- `test_CO083_A1_la_pre_venta_se_reserva_sin_mirar_el_stock` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_A1_la_reserva_queda_en_el_maximo_por_cliente_y_se_avisa` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_E1_la_cantidad_no_pasa_del_stock_y_se_informa_el_maximo` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_agregar_desde_la_tarjeta_responde_json_con_las_unidades` — `apps/core/tests/test_tienda_quinta_parte.py`
- `test_CO083_con_el_cupo_lleno_no_se_reserva_y_se_dice` — `apps/suppliers/tests/test_pedidos_a_proveedor.py`
- `test_CO083_con_el_maximo_ya_reservado_no_agrega_y_lo_dice` — `apps/tienda/tests/test_tope_de_reservas.py`
- `test_CO083_desde_la_tarjeta_el_tope_de_stock_se_avisa_igual` — `apps/core/tests/test_tienda_quinta_parte.py`
- `test_CO083_dos_pestanas_que_agregan_a_la_vez_dejan_una_linea_con_la_suma` — `apps/tienda/tests/test_concurrencia_carrito.py`
- `test_CO083_el_cliente_crea_un_carrito_persistente_asociado_a_su_cuenta` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_el_invitado_crea_un_carrito_de_sesion_con_la_linea` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_el_personal_no_agrega_desde_la_tarjeta` — `apps/core/tests/test_tienda_quinta_parte.py`
- `test_CO083_el_tope_cuenta_lo_reservado_en_pedidos_en_curso` — `apps/tienda/tests/test_tope_de_reservas.py`
- `test_CO083_las_reservas_de_otro_cliente_no_cuentan` — `apps/tienda/tests/test_tope_de_reservas.py`
- `test_CO083_lo_cancelado_o_entregado_no_cuenta_como_reserva` — `apps/tienda/tests/test_tope_de_reservas.py`
- `test_CO083_no_toca_el_producto_ni_se_audita` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_rechaza_una_cantidad_que_no_es_al_menos_uno` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_si_ya_estaba_suma_a_la_misma_linea` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_un_activo_sigue_con_el_tope_del_stock_y_no_el_de_reserva` — `apps/tienda/tests/test_tope_de_reservas.py`
- `test_CO083_un_producto_fuera_de_la_tienda_responde_404` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_un_producto_sin_stock_no_se_agrega` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO083_volver_a_una_direccion_externa_se_ignora` — `apps/tienda/tests/test_contratos_07_carrito.py`

**`CO-084` · modificarCantidadDeLinea**

- `test_CO084_A1_el_maximo_sale_de_parametros` — `apps/tienda/tests/test_contratos_07_carrito.py`
- `test_CO084_A1_en_pre_venta_el_tope_es_el_maximo_por_reserva` — `apps/tienda/tests/test_contratos_07_carrito.py`
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
- `test_CO086_la_fusion_respeta_el_tope_contando_los_pedidos` — `apps/tienda/tests/test_tope_de_reservas.py`
- `test_CO086_sin_carrito_propio_el_de_sesion_pasa_a_la_cuenta` — `apps/tienda/tests/test_contratos_07_carrito.py`

**`CO-087` · declararDireccionDeEnvio**

- `test_CO087_con_retiro_el_envio_cuesta_cero_y_no_se_pide_direccion` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO087_devuelve_el_costo_de_envio` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO087_la_direccion_del_checkout_pasa_a_la_declarada` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO087_la_direccion_del_envio_no_toca_el_perfil` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO087_la_direccion_del_perfil_no_se_modifica` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO087_la_modalidad_no_toca_el_perfil` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO087_se_puede_volver_a_envio_a_domicilio_antes_de_confirmar` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO087_sin_numero_de_calle_no_se_declara` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO087_una_direccion_incoherente_no_se_declara` — `apps/tienda/tests/test_contratos_07_compra.py`

**`CO-088` · confirmarPedido**

- `test_CO088_A2_con_todo_cubierto_y_envio_gratis_confirma_sin_pasarela` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO088_A2_no_ocurre_si_hay_que_pagar_el_envio` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO088_con_total_mayor_que_cero_emite_la_solicitud_de_cobro_con_su_referencia` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO088_con_total_mayor_que_cero_no_cambia_el_dominio` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO088_congela_lineas_precios_direccion_y_canje` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO088_el_cobro_congela_el_retiro_sin_envio` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO088_sin_direccion_completa_no_confirma` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO088_un_canje_que_el_saldo_ya_no_cubre_pide_revisar` — `apps/tienda/tests/test_contratos_07_compra.py`

**`CO-089` · registrarResultadoDePago**

- `test_CO089_D4_un_cobro_de_retiro_sin_cuenta_no_genera_pedido` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO089_E2_el_rechazo_queda_en_la_auditoria` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_E2_el_rechazo_se_informa_con_el_mensaje_de_la_pasarela` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_E2_un_pago_rechazado_no_modifica_nada` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_E3_avisa_al_cliente_que_el_cargo_se_revierte` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_E3_el_saldo_que_ya_no_alcanza_tambien_reembolsa` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO089_E3_si_el_articulo_vencio_mientras_pagaba_se_reembolsa` — `apps/almacen/tests/test_contratos_18_almacen.py`
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
- `test_CO089_el_pedido_nace_para_retirar_sin_direccion_ni_envio` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO089_el_ultimo_lugar_del_cupo_pagado_dos_veces_se_rechaza_la_segunda` — `apps/suppliers/tests/test_pedidos_a_proveedor.py`
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
- `test_CO090_D4_el_invitado_no_puede_retirar` — `apps/tienda/tests/test_retiro_en_local.py`
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
- `test_CO092_avanzar_dos_veces_no_duplica_los_articulos` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO092_avisa_que_esta_listo_para_retirar` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO092_c_armado_no_toca_las_lineas` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_c_el_estado_pasa_al_unico_siguiente` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_c_empaquetado_y_despachado_avanzan_las_lineas_disponibles` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_c_las_lineas_demoradas_no_avanzan` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_cada_unidad_entra_al_stock_en_local_como_pedido_para_retirar` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO092_dos_administradores_que_avanzan_a_la_vez_avanzan_un_solo_paso` — `apps/pedidos/tests/test_acceso_y_concurrencia_pedidos.py`
- `test_CO092_el_cliente_recibe_la_notificacion` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_el_invitado_recibe_la_notificacion_en_su_correo` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_el_pedido_armado_pasa_a_en_el_local_y_nunca_a_empaquetado` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO092_la_confirmacion_muestra_el_estado_actual_y_el_siguiente` — `apps/pedidos/tests/test_contratos_08_pedidos.py`
- `test_CO092_las_lineas_no_cambian_al_pasar_a_en_el_local` — `apps/tienda/tests/test_retiro_en_local.py`
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
- `test_CO095_el_articulo_diferido_queda_retenido_uno_por_unidad` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO095_el_despacho_no_arrastra_al_articulo_diferido` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO095_el_pedido_muestra_el_articulo_en_el_local_y_deja_de_contar_como_demorado` — `apps/almacen/tests/test_contratos_18_almacen.py`
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
- `test_CO098_cancelar_el_demorado_descuenta_lo_que_gano` — `apps/puntos/tests/test_descuento_de_ganados.py`
- `test_CO098_cancelar_reembolsa_el_valor_en_puntos_y_no_toca_el_stock` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO098_con_envio_gratis_el_pedido_cancelado_solo_devuelve_el_articulo` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO098_pagado_con_puntos_devuelve_los_mismos_puntos` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO098_un_pedido_sin_otros_articulos_se_cancela_y_devuelve_el_envio` — `apps/pedidos/tests/test_contratos_08_demora.py`

**`CO-099` · registrarCasoDeDevolucion**

- `test_CO099_E1_los_dos_plazos_son_independientes` — `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`
- `test_CO099_E1_vencido_el_plazo_no_registra_nada` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO099_E2_un_articulo_con_un_caso_rechazado_no_admite_otro` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO099_E3_sin_fotos_no_registra_y_el_formulario_sigue_abierto` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO099_E4_un_archivo_que_no_es_imagen_se_descarta_con_el_problema_especifico` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO099_E4_un_formato_no_aceptado_se_rechaza` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO099_E4_una_foto_que_excede_el_tamano_maximo_se_rechaza` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO099_I19_la_base_no_admite_dos_casos_sobre_la_misma_linea` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO099_arrepentirse_abre_un_caso_por_linea_con_la_linea_entera_y_sin_fotos` — `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`
- `test_CO099_avisa_al_administrador_del_caso_nuevo` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO099_confirma_al_cliente_la_apertura` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO099_crea_el_caso_pendiente_con_sus_datos` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO099_el_arrepentimiento_es_solo_para_compras_online` — `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`
- `test_CO099_el_caso_queda_asociado_a_la_linea_reclamada` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO099_el_plazo_corre_desde_el_despacho_con_el_parametro_vigente` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO099_el_plazo_de_lo_retirado_corre_desde_el_retiro` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO099_guarda_cada_foto_convertida_a_webp_fuera_de_la_carpeta_publica` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO099_mas_de_cinco_fotos_no_se_admiten` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO099_registra_la_apertura_con_el_actor_y_el_momento` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO099_un_arrepentimiento_y_una_garantia_no_conviven_en_la_misma_linea` — `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`
- `test_CO099_un_pedido_de_otro_cliente_responde_404` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`

**`CO-100` · resolverCasoConCambio**

- `test_CO100_E1_la_pantalla_no_deja_elegir_un_producto_sin_stock` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO100_E1_sin_stock_no_registra_nada` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO100_avisa_al_cliente_con_el_reemplazo_y_las_instrucciones` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO100_el_arrepentimiento_no_admite_cambio_ni_en_el_servicio_ni_en_la_base` — `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`
- `test_CO100_el_caso_pasa_de_pendiente_a_resuelto_con_cambio` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO100_el_caso_queda_asociado_al_producto_de_reemplazo` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO100_el_reemplazo_que_llega_a_cero_pasa_a_agotado` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO100_el_reemplazo_queda_a_nombre_del_cliente_en_el_stock_en_local` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO100_el_reemplazo_tiene_que_ser_de_la_misma_editorial_y_formato` — `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`
- `test_CO100_el_stock_del_reemplazo_baja_una_unidad` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO100_no_toca_el_producto_reclamado_ni_los_puntos` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO100_registra_la_resolucion_con_el_tipo_el_administrador_y_el_momento` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO100_un_caso_que_ya_no_esta_pendiente_no_se_vuelve_a_resolver` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`

**`CO-101` · resolverCasoConReembolsoEnPuntos**

- `test_CO101_acredita_un_lote_de_reembolso_por_una_unidad_con_la_caducidad_estandar` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO101_arrepentirse_del_pedido_entero_reintegra_tambien_el_envio` — `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`
- `test_CO101_avisa_al_cliente_con_el_saldo_actualizado` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO101_descuenta_los_puntos_ganados_con_la_compra_y_no_toca_el_stock` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO101_el_arrepentimiento_se_reembolsa_por_el_medio_de_pago_y_vuelve_al_stock` — `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`
- `test_CO101_el_caso_pasa_de_pendiente_a_resuelto_con_reembolso` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO101_el_movimiento_de_acreditacion_queda_con_su_saldo_y_su_caso` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO101_el_reembolso_por_el_medio_descuenta_los_puntos_ganados` — `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`
- `test_CO101_en_el_mostrador_no_hay_reembolso_por_el_medio` — `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`
- `test_CO101_lo_pagado_con_puntos_vuelve_en_puntos_y_no_por_el_medio` — `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`
- `test_CO101_registra_la_resolucion_con_el_tipo_el_administrador_y_el_momento` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO101_un_caso_ya_resuelto_no_acredita_dos_veces` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO101_una_unidad_pagada_con_puntos_devuelve_su_parte_hacia_arriba` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`

**`CO-102` · rechazarCasoDeDevolucion**

- `test_CO102_avisa_al_cliente_con_el_motivo` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO102_el_caso_pasa_a_rechazado_con_el_motivo_declarado` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO102_no_acredita_puntos_ni_toca_el_stock` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO102_registra_el_rechazo_con_el_actor_y_el_momento` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO102_sin_motivo_no_registra_nada` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`

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

**`CO-105` · ejecutarCicloDeCaducidadDePuntos**

- `test_CO105_A1_sin_lotes_vencidos_no_invalida_ni_avisa_ni_registra` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO105_E1_un_lote_que_falla_queda_como_estaba_y_el_ciclo_sigue` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO105_E2_un_canje_abandonado_hace_mas_de_un_dia_no_difiere_la_caducidad` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO105_E2_un_lote_comprometido_en_un_canje_en_curso_no_se_modifica` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO105_avisa_a_cada_cliente_una_vez_con_sus_lotes_y_su_saldo` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO105_corre_en_el_temporizador` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO105_el_historial_muestra_el_debito_por_caducidad_con_su_saldo` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO105_el_lote_con_caducidad_alcanzada_pasa_a_vencido_con_disponible_cero` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO105_el_saldo_del_cliente_baja_en_lo_que_vencio` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO105_los_lotes_con_caducidad_futura_no_se_tocan` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO105_los_puntos_vencidos_no_se_recuperan_al_correr_otra_vez` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO105_registra_cada_lote_con_el_cliente_la_cantidad_y_la_fecha` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`

**`CO-106` · registrarAjusteManualDePuntos**

- `test_CO106_E1_un_debito_mayor_que_lo_libre_informa_el_maximo_y_no_registra` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO106_E2_sin_motivo_no_registra_y_conserva_lo_ingresado` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO106_avisa_al_cliente_el_tipo_la_cantidad_y_el_saldo` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO106_crea_el_movimiento_con_tipo_cantidad_motivo_y_saldo` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO106_el_debito_consume_lotes_por_caducidad_y_el_que_llega_a_cero_se_agota` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO106_el_debito_no_toca_lo_comprometido_en_un_canje` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO106_la_acreditacion_crea_un_lote_de_ajuste_manual_con_la_caducidad_estandar` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO106_la_cantidad_tiene_que_ser_mayor_que_cero` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO106_presenta_el_saldo_actualizado_al_administrador` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO106_registra_tipo_cantidad_saldos_motivo_y_administrador` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO106_una_cuenta_inactiva_no_admite_ajustes` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO106_volver_sin_confirmar_no_registra_nada` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`

**`CO-107` · registrarCuentaDeCliente**

- `test_CO107_E1_el_correo_registrado_mientras_se_validaba_avisa_sin_error` — `apps/accounts/tests/test_carreras_de_unicidad.py`
- `test_CO107_E1_un_correo_registrado_en_cualquier_estado_no_duplica` — `apps/accounts/tests/test_contratos_11_registro.py`
- `test_CO107_E2_contrasenas_invalidas_no_crean_y_conservan_lo_escrito` — `apps/accounts/tests/test_contratos_11_registro.py`
- `test_CO107_E3_sin_aceptar_la_politica_se_bloquea` — `apps/accounts/tests/test_contratos_11_registro.py`
- `test_CO107_crea_la_cuenta_de_cliente_activa_con_sus_datos` — `apps/accounts/tests/test_contratos_11_registro.py`
- `test_CO107_la_credencial_queda_con_hash_y_sal_unica` — `apps/accounts/tests/test_contratos_11_registro.py`
- `test_CO107_queda_con_sesion_y_con_la_entrada_de_auditoria` — `apps/accounts/tests/test_contratos_11_registro.py`
- `test_CO107_sin_puntos_ni_stock_almacenado` — `apps/accounts/tests/test_contratos_11_registro.py`

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

**`CO-112` · solicitarBajaDeCuentaPropia**

- `test_CO112_CO113_el_personal_no_entra` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO112_E1_E2_tambien_los_exige_la_confirmacion` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO112_E1_un_retenido_bloquea_y_dice_que_hacer` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO112_E2_una_decision_de_demora_pendiente_bloquea` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO112_el_informe_trae_las_cuatro_categorias_y_el_aviso` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO112_pedir_el_informe_no_modifica_nada` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO112_sin_sesion_va_al_ingreso` — `apps/accounts/tests/test_contratos_11_baja.py`

**`CO-113` · confirmarBajaDeCuentaPropia**

- `test_CO113_E3_tres_intentos_bloquean_la_baja_y_no_el_ingreso` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO113_E3_una_contrasena_equivocada_no_avanza_y_no_revela_nada` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO113_E4_un_fallo_tecnico_revierte_todo` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO113_el_correo_no_se_puede_volver_a_registrar` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO113_el_historial_y_el_correo_se_conservan` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO113_la_cuenta_pasa_a_inactiva_y_vuelve_al_ingreso` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO113_la_entrada_trae_puntos_suscripciones_y_pedidos` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO113_los_pedidos_activos_no_se_modifican_y_siguen_avisando` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO113_los_puntos_quedan_en_cero_y_vencidos_con_su_debito` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO113_manda_la_confirmacion_al_correo` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO113_se_cierran_las_sesiones_en_todos_los_dispositivos` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO113_se_eliminan_las_suscripciones_y_las_lineas_del_carrito` — `apps/accounts/tests/test_contratos_11_baja.py`

**`CO-114` · iniciarSesion**

- `test_CO114_E1_el_bloqueo_dura_el_periodo_parametrizado` — `apps/accounts/tests/test_parametros_de_seguridad.py`
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
- `test_CO114_la_sesion_vence_por_inactividad_segun_el_parametro` — `apps/accounts/tests/test_parametros_de_seguridad.py`
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

- `test_CO120_E2_el_correo_dado_de_alta_mientras_se_validaba_avisa_sin_error` — `apps/accounts/tests/test_carreras_de_unicidad.py`
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

- `test_CO121_E2_el_correo_tomado_mientras_se_validaba_la_edicion_avisa_sin_error` — `apps/accounts/tests/test_carreras_de_unicidad.py`
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
- `test_CO123_el_administrador_da_de_baja_un_cliente_sin_quitarle_nada` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO123_el_estado_pasa_de_activo_a_inactivo` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO123_el_historial_del_usuario_se_conserva_integro` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO123_invalida_los_tokens_de_todos_los_dispositivos` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO123_la_baja_cierra_las_sesiones_del_cliente` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO123_la_cuenta_no_puede_volver_a_iniciar_sesion` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO123_la_ficha_ofrece_dar_de_baja_y_despues_reactivar` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO123_no_se_puede_dar_de_baja_al_ultimo_administrador` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO123_otro_rol_no_da_de_baja_un_cliente` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO123_reactivar_tras_la_baja_del_administrador_devuelve_sus_puntos` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO123_registra_la_baja_en_auditoria` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`

**`CO-124` · confirmarReactivacionDeUsuario**

- `test_CO124_el_cliente_vuelve_a_pendiente_con_un_enlace_nuevo` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO124_el_enlace_se_envia_al_correo_de_la_cuenta` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO124_el_estado_pasa_de_inactivo_a_pendiente_de_activacion` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO124_el_historial_del_usuario_se_conserva_integro` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO124_el_rol_queda_con_el_valor_declarado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO124_la_auditoria_incluye_el_rol_asignado` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO124_la_credencial_anterior_queda_invalidada` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO124_la_ficha_ofrece_reactivar_solo_si_esta_dado_de_baja` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO124_los_puntos_y_el_historial_no_vuelven_ni_se_pierden` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO124_otro_rol_no_reactiva_un_cliente` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO124_registra_la_reactivacion_en_auditoria` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO124_se_creo_un_enlace_de_activacion_con_48_horas` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO124_un_cliente_activo_no_se_reactiva` — `apps/accounts/tests/test_contratos_11_baja.py`

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
- `test_CO126_el_resumen_del_cierre_se_abre_con_sus_totales_y_sus_ventas` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO126_la_base_no_admite_dos_cierres_de_la_misma_fecha` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO126_lo_vendido_despues_entra_en_el_cierre_siguiente` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO126_queda_en_la_auditoria_con_los_totales` — `apps/caja/tests/test_contratos_14_caja.py`

**`CO-127` · exportarCierreDeCaja**

- `test_CO127_el_csv_trae_cada_transaccion_y_los_totales` — `apps/caja/tests/test_contratos_14_caja.py`
- `test_CO127_queda_en_la_auditoria` — `apps/caja/tests/test_contratos_14_caja.py`

**`CO-128` · exportarReporte**

- `test_CO128_el_csv_dice_lo_mismo_que_la_pantalla` — `apps/reportes/tests/test_contratos_15_reportes.py`
- `test_CO128_precondicion_sin_reporte_valido_no_exporta` — `apps/reportes/tests/test_contratos_15_reportes.py`
- `test_CO128_queda_en_el_log_con_tipo_rango_y_actor` — `apps/reportes/tests/test_contratos_15_reportes.py`

**`CO-129` · exportarLogDeAuditoria**

- `test_CO129_exportar_trae_todo_el_filtro_y_no_solo_la_pagina` — `apps/core/tests/test_contratos_16_auditoria.py`
- `test_CO129_las_celdas_no_se_interpretan_como_formulas` — `apps/core/tests/test_contratos_16_auditoria.py`

**`CO-130` · actualizarParametrosOperacionales**

- `test_CO130_E1_el_margen_del_cupo_no_pasa_del_50` — `apps/catalog/tests/test_parametros_compra.py`
- `test_CO130_E1_el_maximo_por_reserva_es_al_menos_uno` — `apps/catalog/tests/test_parametros_compra.py`
- `test_CO130_E1_el_plazo_bajo_el_piso_legal_se_rechaza_solo_y_los_demas_se_guardan` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO130_E2_otro_campo_invalido_no_guarda_nada_aunque_el_plazo_tambien_falle` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO130_E2_un_valor_fuera_de_rango_no_guarda_nada` — `apps/accounts/tests/test_parametros_de_seguridad.py`
- `test_CO130_b_la_configuracion_queda_asociada_al_administrador` — `apps/catalog/tests/test_parametros_compra.py`
- `test_CO130_el_aviso_previo_se_configura_en_parametros` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO130_el_margen_del_cupo_pasa_al_declarado_y_se_audita` — `apps/catalog/tests/test_parametros_compra.py`
- `test_CO130_el_maximo_por_reserva_pasa_al_declarado_y_se_audita` — `apps/catalog/tests/test_parametros_compra.py`
- `test_CO130_el_plazo_de_devolucion_pasa_al_declarado_y_queda_auditado` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO130_guardar_sin_cambios_no_deja_entradas` — `apps/catalog/tests/test_parametros_compra.py`
- `test_CO130_la_base_no_admite_un_plazo_bajo_el_piso_legal` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO130_la_pantalla_muestra_la_seccion_de_compra_online` — `apps/catalog/tests/test_parametros_compra.py`
- `test_CO130_la_seccion_seguridad_guarda_los_dos_valores_y_los_audita` — `apps/accounts/tests/test_parametros_de_seguridad.py`
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

**`CO-149` · ejecutarDiagnosticoDelModelo**

- `test_CO149_CO150_otro_rol_no_diagnostica` — `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py`
- `test_CO149_E1_sin_respuesta_tambien_queda_registrado` — `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py`
- `test_CO149_E2_E3_rechazos_distinguidos` — `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py`
- `test_CO149_E4_el_modelo_configurado_no_existe` — `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py`
- `test_CO149_E5_contenido_invalido_se_informa_como_reparo` — `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py`
- `test_CO149_E6_formato_ininterpretable_muestra_el_crudo` — `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py`
- `test_CO149_la_salida_trae_prompt_crudo_validacion_tiempo_y_version` — `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py`
- `test_CO149_no_modifica_el_catalogo_ni_genera_borradores` — `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py`
- `test_CO149_queda_en_el_log_con_la_configuracion_y_sin_la_credencial` — `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py`

**`CO-150` · verificarDisponibilidadDelModelo**

- `test_CO150_E1_a_E3_quedan_registrados` — `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py`
- `test_CO150_comprueba_sin_extraccion_y_queda_en_el_log` — `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py`
- `test_CO150_no_modifica_el_dominio` — `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py`

**`CO-151` · confirmarDespachoDeStockAlmacenado**

- `test_CO151_A1_pago_aprobado_genera_la_solicitud_con_su_transaccion` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO151_A1_pago_rechazado_no_genera_nada` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO151_E1_sin_direccion_no_se_confirma` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO151_el_cierre_de_caja_cuenta_el_envio_como_online` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO151_gratis_genera_la_solicitud_y_avisa_al_administrador` — `apps/almacen/tests/test_contratos_18_almacen.py`

**`CO-152` · confirmarDespachoFisico**

- `test_CO152_E1_si_un_articulo_cambio_no_se_registra_nada` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO152_despachar_la_solicitud_registra_cada_articulo_y_avisa` — `apps/almacen/tests/test_contratos_18_almacen.py`

**`CO-153` · modificarPlazoDeRetencion**

- `test_CO153_E1_E2_fecha_no_futura_o_motivo_vacio_se_rechazan` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO153_cambia_la_fecha_con_motivo_y_avisa_al_cliente` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO153_un_articulo_en_estado_final_no_tiene_plazo` — `apps/almacen/tests/test_contratos_18_almacen.py`

**`CO-154` · ejecutarCicloDeVencimientoDeRetencion**

- `test_CO154_A1_lo_vencido_con_envio_pendiente_se_extiende_tres_dias_cada_vez` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO154_D3_lo_no_retirado_vuelve_al_stock_con_su_valor_en_puntos` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO154_D3_una_unidad_pagada_con_puntos_devuelve_sus_puntos` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO154_E2_sin_articulos_elegibles_no_hace_nada` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO154_avisa_una_vez_por_fecha_lo_que_vence_en_los_dias_de_aviso` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO154_correr_dos_veces_no_reembolsa_dos_veces` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO154_el_aviso_previo_dice_que_vuelve_con_reembolso` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO154_el_despacho_diferido_tambien_vuelve_con_reembolso` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO154_el_temporizador_corre_el_ciclo` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO154_el_vencimiento_descuenta_lo_que_gano_la_unidad` — `apps/puntos/tests/test_descuento_de_ganados.py`
- `test_CO154_en_estado_final_no_se_toca` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO154_lo_vencido_disponible_vuelve_al_stock_con_su_valor_en_puntos` — `apps/almacen/tests/test_contratos_18_almacen.py`

**`CO-155` · sincronizarCotizaciones**

- `test_CO155_la_sincronizacion_guarda_el_respaldo_cuando_la_api_responde` — `apps/tienda/tests/test_cobros_abandonados.py`
- `test_CO155_y_los_cobros_abandonados_corren_en_el_temporizador` — `apps/tienda/tests/test_cobros_abandonados.py`

**`CO-156` · cancelarOperacion**

- `test_CO156_abandonar_antes_de_confirmar_no_cambia_nada` — `apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py`
- `test_CO156_abandonar_el_cambio_de_margen_lo_deja_como_estaba` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO156_abandonar_la_baja_de_grupo_o_etiqueta_no_cambia_nada` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO156_abandonar_la_baja_de_un_catalogo_no_cambia_nada` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO156_abandonar_la_baja_de_una_combinacion_no_cambia_nada` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO156_abandonar_la_baja_no_cambia_nada` — `apps/accounts/tests/test_contratos_11_baja.py`
- `test_CO156_abandonar_la_confirmacion_no_cambia_el_producto` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO156_abandonar_la_confirmacion_no_cambia_el_proveedor` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO156_abandonar_la_modificacion_no_cambia_el_precio` — `apps/catalog/tests/test_contratos_03_pricing.py`
- `test_CO156_cancelar_la_baja_no_cambia_nada` — `apps/catalog/tests/test_contratos_03_ofertas.py`
- `test_CO156_volver_desde_el_informe_de_demora_no_registra_nada` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO156_volver_desde_la_cancelacion_no_cambia_nada` — `apps/pedidos/tests/test_contratos_01_preventa.py`
- `test_CO156_volver_desde_la_confirmacion_no_registra_nada` — `apps/pedidos/tests/test_contratos_08_demora.py`
- `test_CO156_volver_sin_confirmar_el_envio_no_registra_nada` — `apps/almacen/tests/test_contratos_18_almacen.py`

**`CO-157` · consultarColaDeCorreos**

- `test_CO157_consultar_la_cola_no_modifica_nada` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO157_por_la_direccion_real_con_rol_cajero_se_deniega` — `apps/suppliers/tests/test_contratos_04_proveedores.py`

**`CO-158` · abrirFichaDeCorreo**

- `test_CO158_abrir_la_ficha_muestra_el_contenido_y_no_modifica_nada` — `apps/suppliers/tests/test_contratos_04_proveedores.py`
- `test_CO158_la_ficha_de_un_pendiente_ofrece_aprobar_y_descartar` — `apps/suppliers/tests/test_contratos_04_proveedores.py`

**`CO-159` · consultarColaDeBorradores**

- `test_CO159_CO160_consultar_no_modifica_nada_ni_abre_sesion` — `apps/catalog/tests/test_contratos_01_revision.py`
- `test_CO159_E1_sin_pendientes_lo_informa` — `apps/catalog/tests/test_contratos_01_revision.py`
- `test_CO159_lista_los_pendientes_con_confianza_reparos_estado_y_stock` — `apps/catalog/tests/test_contratos_01_revision.py`

**`CO-160` · abrirBorrador**

- `test_CO160_muestra_campos_confianzas_y_reparos` — `apps/catalog/tests/test_contratos_01_revision.py`

**`CO-161` · abrirEdicionDeProducto**

- `test_CO161_abrir_la_edicion_no_modifica_nada` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO161_el_importado_declara_su_costo_en_origen` — `apps/catalog/tests/test_contratos_02_producto.py`
- `test_CO161_muestra_los_campos_actuales_y_declara_los_inmutables` — `apps/catalog/tests/test_contratos_02_producto.py`

**`CO-162` · consultarInventario**

- `test_CO162_consultar_inventario_filtra_por_editorial` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO162_el_filtro_ofrece_las_etiquetas_inactivas_marcadas` — `apps/catalog/tests/test_contratos_02_catalogo.py`

**`CO-163` · consultarFichaDeProducto**

- `test_CO163_la_ficha_dibuja_para_el_cajero_solo_sus_campos` — `apps/catalog/tests/test_contratos_02_catalogo.py`
- `test_CO163_los_indicadores_internos_se_calculan` — `apps/catalog/tests/test_contratos_02_catalogo.py`

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

**`CO-171` · abrirEdicionDeProveedor**

- `test_CO171_muestra_los_campos_actuales_en_cualquier_estado` — `apps/suppliers/tests/test_contratos_04_padron.py`

**`CO-172` · consultarProveedores**

- `test_CO172_E1_sin_resultados` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO172_E2_sin_proveedores_ofrece_el_alta` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO172_filtra_por_estado_y_por_texto` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO172_lista_razon_social_correo_estado_y_productos` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO172_por_la_direccion_real_con_rol_cajero_se_deniega` — `apps/suppliers/tests/test_contratos_04_padron.py`

**`CO-173` · consultarFichaDeProveedor**

- `test_CO173_consultar_la_ficha_no_modifica_nada` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO173_contacto_productos_y_procesamiento_a_la_vista` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO173_el_historial_no_mezcla_pedidos_de_otro_proveedor` — `apps/suppliers/tests/test_contratos_04_padron.py`
- `test_CO173_el_historial_trae_los_pedidos_despachados` — `apps/suppliers/tests/test_contratos_04_padron.py`

**`CO-174` · consultarPropuestaDeRestock**

- `test_CO174_E1_sin_propuesta_lo_dice` — `apps/restock/tests/test_contratos_05_restock.py`
- `test_CO174_muestra_la_propuesta_por_proveedor` — `apps/restock/tests/test_contratos_05_restock.py`

**`CO-175` · consultarLineasDeProveedor**

- `test_CO175_lista_las_lineas_del_proveedor` — `apps/restock/tests/test_contratos_05_restock.py`

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
- `test_CO178_la_linea_que_pasa_el_tope_queda_marcada` — `apps/tienda/tests/test_tope_de_reservas.py`
- `test_CO178_presenta_las_lineas_con_precio_subtotal_y_total` — `apps/tienda/tests/test_contratos_07_carrito.py`

**`CO-179` · procederAlPago**

- `test_CO179_con_todas_las_lineas_disponibles_transfiere_al_checkout` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO179_el_invitado_que_elige_comprar_como_invitado_va_al_formulario` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO179_el_invitado_sin_elegir_va_a_iniciar_sesion_y_vuelve_al_checkout` — `apps/tienda/tests/test_contratos_07_compra.py`
- `test_CO179_la_reserva_hecha_en_otra_pestana_bloquea_el_pago` — `apps/tienda/tests/test_tope_de_reservas.py`
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

**`CO-185` · iniciarSolicitudDeDevolucion**

- `test_CO185_E1_vencido_el_plazo_informa_y_no_abre_el_formulario` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO185_E2_con_todos_los_articulos_reclamados_informa_el_caso_y_su_estado` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO185_con_sesion_el_cliente_ve_sus_compras_dentro_del_plazo` — `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`
- `test_CO185_lo_retirado_se_puede_reclamar_desde_el_retiro` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO185_no_ofrece_las_lineas_canceladas_ni_las_de_despacho_diferido` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO185_presenta_los_articulos_sin_reclamo_y_los_motivos_sin_modificar_nada` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO185_sin_sesion_el_numero_y_el_correo_de_la_compra_abren_el_pedido` — `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`
- `test_CO185_un_correo_que_no_coincide_no_revela_el_pedido` — `apps/devoluciones/tests/test_arrepentimiento_y_garantia.py`
- `test_CO185_un_pedido_sin_despachar_no_admite_reclamo` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`

**`CO-186` · consultarCasosDeDevolucion**

- `test_CO186_E2_sin_pendientes_muestra_el_panel_vacio_con_acceso_al_historial` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO186_el_historial_muestra_los_resueltos_y_los_rechazados` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`
- `test_CO186_lista_los_pendientes_mas_antiguos_primero_sin_modificar_nada` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`

**`CO-187` · consultarDetalleDeCasoDeDevolucion**

- `test_CO187_presenta_el_caso_con_sus_fotos_sin_modificar_nada` — `apps/devoluciones/tests/test_contratos_09_devoluciones.py`

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

**`CO-191` · consultarPuntosDeCliente**

- `test_CO191_la_ficha_del_cliente_lleva_a_sus_puntos` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO191_presenta_saldo_lotes_comprometido_y_movimientos_sin_modificar_nada` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`
- `test_CO191_una_cuenta_inactiva_no_admite_el_panel` — `apps/puntos/tests/test_contratos_10_caducidad_y_ajuste.py`

**`CO-192` · consultarPanelDeCuenta**

- `test_CO192_E1_sin_pedidos_activos_informa_y_las_demas_secciones_siguen` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO192_el_historial_muestra_los_despachados` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO192_el_pedido_en_el_local_sigue_en_curso_hasta_que_se_retira` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO192_la_direccion_del_historial_lleva_a_su_grupo` — `apps/accounts/tests/test_contratos_11_cuenta.py`
- `test_CO192_la_seccion_stock_en_local_se_muestra` — `apps/accounts/tests/test_contratos_11_cuenta.py`
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

**`CO-204` · generarReporteOperativo**

- `test_CO204_CO128_otro_rol_no_entra` — `apps/reportes/tests/test_contratos_15_reportes.py`
- `test_CO204_E1_el_rango_es_obligatorio` — `apps/reportes/tests/test_contratos_15_reportes.py`
- `test_CO204_E1_un_rango_invalido_no_procede` — `apps/reportes/tests/test_contratos_15_reportes.py`
- `test_CO204_E2_sin_datos_el_reporte_vacio_lo_dice` — `apps/reportes/tests/test_contratos_15_reportes.py`
- `test_CO204_mas_vendidos_filtra_por_categoria` — `apps/reportes/tests/test_contratos_15_reportes.py`
- `test_CO204_mas_vendidos_ordena_por_unidades_y_el_canje_no_suma` — `apps/reportes/tests/test_contratos_15_reportes.py`
- `test_CO204_movimientos_de_puntos_por_tipo_y_motivo` — `apps/reportes/tests/test_contratos_15_reportes.py`
- `test_CO204_no_modifica_nada` — `apps/reportes/tests/test_contratos_15_reportes.py`
- `test_CO204_solicitudes_de_reposicion_en_espera_del_rango` — `apps/reportes/tests/test_contratos_15_reportes.py`
- `test_CO204_ventas_por_canal_separa_fisico_y_online` — `apps/reportes/tests/test_contratos_15_reportes.py`
- `test_CO204_ventas_totales_consolida_por_dia` — `apps/reportes/tests/test_contratos_15_reportes.py`
- `test_CO204_ventas_totales_filtra_por_canal` — `apps/reportes/tests/test_contratos_15_reportes.py`

**`CO-205` · consultarLogDeAuditoria**

- `test_CO205_consultar_log_de_a_50_de_la_mas_reciente_a_la_mas_antigua` — `apps/core/tests/test_contratos_16_auditoria.py`
- `test_CO205_filtra_por_actor_accion_entidad_rol_y_fechas` — `apps/core/tests/test_contratos_16_auditoria.py`
- `test_CO205_un_rango_de_fechas_sin_entradas_lo_dice` — `apps/core/tests/test_contratos_16_auditoria.py`

**`CO-206` · consultarDetalleDeEntradaDeAuditoria**

- `test_CO206_el_detalle_presenta_la_entrada_completa` — `apps/core/tests/test_contratos_16_auditoria.py`

**`CO-207` · consultarParametrosOperacionales**

- `test_CO207_parametros_presenta_todas_las_secciones_sin_modificar_nada` — `apps/accounts/tests/test_parametros_de_seguridad.py`

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

**`CO-214` · consultarConfiguracionDeDiagnostico**

- `test_CO214_no_modifica_nada` — `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py`
- `test_CO214_presenta_la_configuracion_con_la_credencial_enmascarada` — `apps/suppliers/tests/test_contratos_17_diagnostico_llm.py`

**`CO-215` · consultarStockAlmacenadoPropio**

- `test_CO215_A1_sin_articulos_lo_dice` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO215_lista_lo_propio_con_lo_proximo_a_vencer_y_lo_pendiente_en_solo_lectura` — `apps/almacen/tests/test_contratos_18_almacen.py`

**`CO-216` · solicitarDespachoDeStockAlmacenado**

- `test_CO216_desde_el_monto_minimo_el_envio_es_gratis` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO216_no_se_puede_pedir_lo_de_otro_ni_lo_que_no_esta_disponible` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO216_resume_valor_costo_y_direccion_sin_registrar_nada` — `apps/almacen/tests/test_contratos_18_almacen.py`

**`CO-217` · consultarStockAlmacenado**

- `test_CO217_lista_todos_los_clientes_con_filtros` — `apps/almacen/tests/test_contratos_18_almacen.py`

**`CO-218` · consultarFichaDeArticuloRetenido**

- `test_CO218_el_cajero_no_ve_la_accion_del_plazo` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO218_la_ficha_muestra_el_origen_y_el_acceso_a_entregar_todo` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO218_la_ficha_muestra_origen_fechas_valor_e_historial` — `apps/almacen/tests/test_contratos_18_almacen.py`

**`CO-220` · solicitarBajaDeTipoDeMaterial**

- `test_CO220_solicitar_baja_de_tipo_cuenta_las_ofertas_vivas_del_tipo` — `apps/catalog/tests/test_contratos_17_catalogos.py`

**`CO-221` · confirmarBajaDeTipoDeMaterial**

- `test_CO221_confirmar_baja_de_tipo_conserva_sus_vinculos` — `apps/catalog/tests/test_contratos_17_catalogos.py`
- `test_CO221_un_borrador_que_hereda_el_tipo_no_se_confirma` — `apps/catalog/tests/test_contratos_17_catalogos.py`

**`CO-227` · confirmarRetiroEnLocal**

- `test_CO227_E1_lo_pendiente_de_despacho_no_se_retira` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO227_E1_si_un_articulo_cambio_no_se_entrega_ninguno` — `apps/tienda/tests/test_retiro_en_local.py`
- `test_CO227_el_retiro_registra_al_titular_sin_avisarle` — `apps/almacen/tests/test_contratos_18_almacen.py`
- `test_CO227_entregar_todo_retira_cada_articulo_disponible_del_pedido` — `apps/tienda/tests/test_retiro_en_local.py`

---

## Lo que esta fotografía no cubre

- **No dice que un contrato esté verificado**, sólo que alguna prueba lleva su código. Una postcondición sin prueba no se distingue desde acá de una cubierta.
- **No mira las pruebas que no son de contrato.** Las de acceso, flujo, unidad y frontera no llevan código de contrato en el nombre, a propósito, y no entran en este recuento.
- **No mide cobertura de líneas.** Es otra puerta y su número vive en [`../ESTADO.md`](../ESTADO.md).
