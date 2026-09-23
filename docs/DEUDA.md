> **Tipo: Fotografía.** Tomada el **2026-09-22**.
> Se reemplaza entera. No contiene reglas ni justificaciones de diseño.

# Deuda

La diferencia entre lo que el documento de análisis especifica y lo que el sistema hace. Y las
decisiones transversales que todavía no se tomaron.

Es el complemento de `ESTADO.md`: aquél dice cuánto se avanzó, éste dice qué separa al código de
la especificación.

---

## Decisiones transversales abiertas

Mientras sigan abiertas, lo que depende de ellas no avanza. Una decisión que bloquea a varios
módulos no se resuelve dentro del primero que la necesita.

| Ítem | Decisión pendiente | Qué bloquea | Desde |
| --- | --- | --- | --- |
| `ALLOWED_HOSTS` | La puerta de configuración de despliegue tiene una advertencia (`security.W020`) porque el host de producción no está decidido | El estado `Verificado` para **todo** caso de uso, por más que sus contratos estén verificados. Hoy son ocho los que dependen sólo de esto | 2026-09-14 |
| **P-05** · mecanismo de procesos periódicos | El sistema declara seis operaciones disparadas por el Temporizador y no existe ninguna forma de dispararlas. Es una decisión de implementación y no de dominio: qué mecanismo, con qué garantía de no ejecutar dos veces lo mismo, y cómo se prueba sin esperar el reloj | El ciclo de `CO-016`, el ciclo de `CO-155`, `CU-ALT-TRA`, `CU-RST-NOT`, `CU-PTS-CAD` y `CU-STK-VEN` | — |
| Dónde viven los parámetros de seguridad | `CO-114` declara que el bloqueo se levanta «por el período parametrizado» y que la expiración por inactividad sale «según `ConfiguracionSistema`». En el código son constantes de `config/settings/base.py`. Resuelto en B-12-001: mandan el contrato y **sólo dos** valores son parametrizables —la expiración y el período de bloqueo—; los 5 intentos son fijos por CO-114. Falta construirlo | La sección **Seguridad** de `CU-CFG-PAR`, y la mitad de `CO-114` que nombra a `ConfiguracionSistema` | — |
| Pedido como dependencia raíz | No es una decisión de diseño abierta sino un orden de construcción a fijar: el concepto Pedido no existe todavía | Los módulos **07, 08, 09, 10 y 14** enteros, más `CU-ALT-DEM`, `CU-ALT-CAN`, `CU-CLI-BAJ`, `CU-CLI-HIS` y el módulo **18** | — |
| `04_RESUMEN.md` | `MODELO_DE_DOMINIO.md` remite a él dos veces —para los supuestos, las inconsistencias y «cuatro operaciones con contrato pausado por ambigüedad»— y el archivo no está en el repositorio. Ninguno de los 218 contratos aparece marcado como pausado | Saber cuáles son esas cuatro operaciones. Hasta que aparezcan, se las cuenta como contratos normales | 2026-09-14 |

**Cuatro decisiones se cerraron desde la fotografía anterior** y salen de esta tabla:

- **Nombre de las pruebas.** Las de contrato se agregan junto a las descriptivas, en archivos
  `test_contratos_NN_*.py`. Aplicado en los módulos 12 y 13 y es el patrón para los 16 restantes.
- **`docs/pruebas/COBERTURA.md`.** Existe, lo genera `scripts/generar_cobertura.py` sobre el
  esquema `CU-MOD-AAA` / `CO-###`, y es la única fuente de qué prueba cubre qué contrato.
- **Dónde viven los generadores.** `scripts/`, dentro del repositorio y fuera de `.gitignore`.
- **Referencias a documentación que ya no existe.** Los documentos de `/docs/modulos/` y
  `/docs/diseno/` no se reponen; las nueve citas del código se reemplazaron por el caso de uso
  correspondiente y por `TOKENS_VISUALES.md` (R-13-001).

`.contexto-ia/dss/` también sale: la carpeta existe, la mantiene el responsable y el generador no
la toca ni la produce.

---

## Conceptos especificados sin implementar

Fuente: `.contexto-ia/MODELO_DE_DOMINIO.md`, contrastado contra las clases `models.Model` del
código.

**`EnlaceActivacion` y `TokenRecuperacion` dejaron de ser deuda.** Se construyeron el 2026-09-22
con sus tres estados —Vigente, Consumido, Vencido— y las seis postcondiciones que dependían de
ellos se afirman ahora literalmente. El modelo de dominio todavía los declara `<<planificado>>`:
es una enmienda pendiente anotada en B-12-003, y hasta que llegue el recuento del documento y el
del código no coinciden.

Los 18 planificados que quedan:

| Concepto | Área | Módulo que lo introduce | Conceptos que dependen de él |
| --- | --- | --- | --- |
| `Pedido` | A5 Comercio | 07 Tienda Online (`canal` cubre también 06 Ventas Presenciales) | `LineaPedido`, `TransaccionPago` |
| `LineaPedido` | A5 Comercio | 07 Tienda Online | `CasoDevolucion`, `ArticuloRetenido` |
| `TransaccionPago` | A5 Comercio | 07 Tienda Online | `CierreDeCaja` |
| `Carrito` | A5 Comercio | 07 Tienda Online | `LineaCarrito` |
| `LineaCarrito` | A5 Comercio | 07 Tienda Online | — |
| `CasoDevolucion` | A5 Comercio | 09 Devoluciones | `DevolucionFisica` |
| `DevolucionFisica` | A5 Comercio | 09 Devoluciones | — |
| `ArticuloRetenido` | A5 Comercio | 18 Stock Almacenado en Local | — |
| `CierreDeCaja` | A5 Comercio | 14 Caja | — |
| `LotePuntos` | A6 Fidelización | 10 Puntos | `MovimientoPuntos`, y el saldo derivado de I-18 |
| `MovimientoPuntos` | A6 Fidelización | 10 Puntos | — |
| `PropuestaRestock` | A4 Pipeline | 05 Restock | `LineaPropuestaRestock` |
| `LineaPropuestaRestock` | A4 Pipeline | 05 Restock | — |
| `SuscripcionReposicion` | A3 Producto | 05 Restock | — |
| `Oferta` | A2 Clasificación | 03 Pricing | — |
| `Banner` | A7 Parámetros | 17 Configuración del Sistema | — |
| `ContenidoFAQ` | A7 Parámetros | 17 Configuración del Sistema | — |
| `IdentidadVisual` | A7 Parámetros | 17 Configuración del Sistema | — |

**`Pedido` es la raíz.** De sus dos dependientes directos cuelgan otros cinco, y hasta que exista
no avanzan los módulos 07, 08, 09, 10, 14 y 18, ni `CU-ALT-DEM`, `CU-ALT-CAN`, `CU-CLI-BAJ` ni
`CU-CLI-HIS`. Es el orden de construcción que el modelo hace visible.

---

## Contratos sin prueba

Operaciones especificadas cuya postcondición nadie verifica todavía. El detalle contrato por
contrato está en [pruebas/COBERTURA.md](pruebas/COBERTURA.md), que es su domicilio; acá va sólo
lo que no cabe ahí.

**Faltan 199 de 218.** Los 19 restantes se reparten en 18 verificados y 1 parcial, y son todos de
los módulos `12` y `13`.

**El recuento por archivo cambió de sentido en esta fotografía.** Hasta la corrida anterior,
`contratos/18-stock-almacenado-en-local.md` tenía 68 contratos, de los cuales sólo cuatro eran del
módulo; ahora tiene 9. Los contratos se archivan por sus Referencias Cruzadas y los que cruzan
módulos viven en `contratos/00-transversales.md`, que son 18. El recuento por archivo dice por fin
algo sobre el módulo.

### El único parcial: la postcondición nombra algo que el sistema no tiene

| Contrato | Qué no se puede afirmar | Qué sí se afirma en su lugar | Registrado en |
| --- | --- | --- | --- |
| `CO-114` | «expiración por inactividad **según `ConfiguracionSistema`**» | Que la sesión nace con una expiración por inactividad finita, y que el bloqueo por intentos se levanta solo | B-12-001 |

**Los otros cinco parciales se cerraron.** `CO-117`, `CO-118`, `CO-119`, `CO-120` y `CO-122` lo
eran porque sus postcondiciones nombraban `TokenRecuperacion` y `EnlaceActivacion`, que no
existían como tabla. Los dos conceptos se construyeron y las cinco postcondiciones se afirman
ahora literalmente (B-12-003).

### Los tres incumplidos se cerraron

`CO-124`, `CO-199` y `CO-198` declaraban cosas que el sistema no hacía, y sus pruebas estaban en
`xfail(strict=True)`. Los dos desvíos se resolvieron a favor del contrato y las cuatro pruebas
pasan:

| Contrato | Qué se construyó | Registrado en |
| --- | --- | --- |
| `CO-124` | La reactivación recibe el rol y la auditoría lo registra como par —anterior y nuevo— | B-13-002 |
| `CO-199` | La pantalla de reactivación presenta el rol con un desplegable, no como texto | B-13-002 |
| `CO-198` | La solicitud de baja del último Administrador se bloquea en el `GET`, no sólo al confirmar | B-13-003 |

**No queda ningún `xfail` en la suite.**

`CO-202` `consultarFichaDeUsuario` queda entre los 199 sin prueba por otro motivo: no hay pantalla
de ficha de usuario que ejercer. Es la misma situación de `CO-195` `consultarFichaDeCliente`, y
los dos casos de uso quedan `Parcial` por eso.

---

## Consistencia de la especificación consigo misma

Resultado del chequeo que `scripts/generar_contexto.py` corre sobre tres fuentes —los contratos
volcados, `dss/inventario_operaciones.md` y los DSS— comparando **por nombre de operación**. El
chequeo informa y no corrige: un generador que ajusta lo que encuentra deja de ser un volcado.

Las tres fuentes declaran **218 operaciones cada una** y se corresponden casi por completo. Lo que
no cierra:

| Qué | Cuántas | Cuáles |
| --- | --- | --- |
| Operaciones del inventario que ningún DSS declara | 2 | `notificarReposicionASuscriptores`, `sincronizarCotizaciones` |
| Operaciones declaradas en un DSS y ausentes del inventario | 2 | `cancelarRegistroDeDemora` (DSS del módulo 01), `cancelarSeleccion` (DSS del módulo 08) |

Las dos primeras son operaciones internas o de Temporizador, que no tienen actor que las inicie y
por eso ningún diagrama de secuencia las dibuja. Puede ser correcto que falten; hoy no está dicho
en ninguna parte.

**Y una afirmación del inventario que no se sostiene.** Su cabecera dice que «las operaciones se
numeran `OP-nnn` y cada una tiene exactamente un contrato `C-nnn` con el mismo número». **No se
cumple en 202 de las 218**: `abrirBorrador` es `OP-023` y su contrato es `CO-160`;
`abrirEdicionDeUsuario` es `OP-161` y su contrato es `CO-197`.

No es que las operaciones estén mal: es la afirmación la que está mal. El vínculo que sí funciona
es el **nombre**, y por él las tres fuentes se corresponden. Convendría enmendar esa frase del
inventario antes de que alguien la use para buscar un contrato por su número y encuentre otro.

---

## Invariantes declaradas sin garantía en la base

`MODELO_DE_DOMINIO.md` declara 23 invariantes. Seis (I-18 a I-23) recaen sobre conceptos
planificados y no se pueden evaluar todavía. De las 17 restantes, **todas están implementadas**.

Lo que no es uniforme es **dónde** vive cada una, y ahí hay una diferencia que importa: una
restricción que vive en la base la respeta cualquier camino de escritura; una que vive en
`clean()` o en un validador sólo la respeta el camino que llama a `full_clean()`, es decir un
`ModelForm`. Un `save()` directo, un `update()` de queryset, una migración de datos o el shell la
esquivan.

| Invariante | Dónde vive hoy | La respeta cualquier escritura |
| --- | --- | --- |
| I-01 código único e inmutable | `unique=True` + `Producto.save()` | Sí |
| I-03 ISBN único salvo vacío | `UniqueConstraint` condicional | Sí |
| I-04 tupla de edición única | `UniqueConstraint` sobre `clave_edicion` | Sí |
| I-07 precio único por terna | `UniqueConstraint` | Sí |
| I-08 etiqueta única dentro del grupo | `UniqueConstraint(Lower("nombre"), "grupo")` | Sí |
| I-10 correo de cuenta único | `unique=True` | Sí |
| I-15 correo comercial único | `UniqueConstraint(Lower(…))` | Sí |
| I-16 un mensaje se encola una vez | `unique=True` sobre `message_id` | Sí |
| I-17 una confianza por campo | `UniqueConstraint` | Sí |
| I-02 todo producto tiene rubro | `Producto.save()` lanza `ProductoAbstractoError` | Sí |
| I-13 el log no se modifica ni se borra | `save()` y `delete()` lanzan `RegistroAuditoriaError` | Sí |
| I-14 una sola `ConfiguracionSistema` | `save()` fija la clave, `delete()` bloqueado | Sí |
| I-11 sólo una cuenta Activa inicia sesión | backend de autenticación + `is_active` derivado en `save()` | Sí |
| **I-05** tipo del mismo rubro que el producto | `clean()` | **No** |
| **I-06** no editorial sin Pre-venta ni Cancelado | `clean()` | **No** |
| **I-09** ningún importe negativo, ningún precio cero | `MinValueValidator` | **No** |
| **I-12** siempre un Administrador activo | servicio de `accounts`, invocado desde las vistas | **No** |

**No hay ni una `CheckConstraint` en todo el proyecto.** Las nueve invariantes de unicidad están
en la base; las cuatro de valor y de coherencia de estado, no.

I-09 es la más expuesta, porque es la única que toca dinero: nada en la base impide hoy un
`Producto.objects.update(precio=0)` ni un importe negativo. I-12 es la segunda, porque el
resguardo del último Administrador vive en el servicio y no en el modelo.

**El retiro del admin de Django cerró una puerta, no la puerta.** El admin permitía editar el rol
y el estado de cualquier cuenta desde una grilla, sin pasar por el servicio que sostiene I-12
(B-13-005). Con él afuera esa vía ya no existe, pero un `update()` de queryset o el shell siguen
esquivando las cuatro. Lo que las cerraría de verdad es la restricción en la base.

**Las dos verificaciones a mano que `CLAUDE.md` pide se hicieron, y las dos dan bien.**

- `manage.py migrate --check` sobre la base de desarrollo sale en 0: no hay migraciones sin
  aplicar. Las dos migraciones nuevas de este pase —`accounts.0007` y `core.0017`— se aplicaron.
- Las restricciones de unicidad existen en PostgreSQL y son índices `UNIQUE`.

De las 12, **sólo 3 figuran además en `pg_constraint`.** Las otras 9 —las siete definidas sobre
`Lower(...)` más las dos con `condition=`— existen únicamente como índice. Buscarlas donde están
las demás devuelve «no existe» sobre nueve restricciones que sí están puestas. Es el falso
negativo contra el que `CLAUDE.md` advierte.

---

## Código sin contrato

Comportamiento que existe en el código y que ningún contrato declara. Cada fila es o un contrato
que falta escribir, o funcionalidad que sobra.

| Dónde | Qué hace | Qué falta |
| --- | --- | --- |
| `TipoForm`, casilla `activo` | Da de baja un **tipo de material**, sacándolo de los desplegables de alta | Ningún contrato la declara. El módulo 17 tiene `CO-141 registrarTipoDeMaterial` y `CO-142 editarTipoDeMaterial`, y ahí se corta: no hay `solicitarBajaDeTipoDeMaterial` ni su confirmación. Editorial tiene su par (CO-139/140) y formato el suyo (CO-147/148); tipo no. **Es más grave que la casilla de B-17-002**: ahí el contrato existe y el código se aparta; acá el contrato no existe, y `Tipo` entra en la clave de unicidad del producto y en la tabla de precios de referencia |
| `apps/core/views.py::PanelAdministracionView` y `core/templates/core/panel.html` | Tablero de entrada del Administrador: cuentas por rol y por estado, proveedores que alimentan el pipeline, últimas entradas del log | Ningún contrato declara un tablero. `CO-205` contrata la consulta del log, que es otra cosa: acá hay cifras agregadas que nadie especificó. Hay un `CO-219` en camino para esto; hasta que aparezca en `.contexto-ia/` no hay contra qué escribir pruebas |
| `apps/core/views.py::PoliticaPrivacidadView` | Sirve el texto de la política de privacidad que el registro de Cliente obliga a aceptar | `CO-107` declara la aceptación y el campo `fecha_aceptacion_politica`, pero ningún contrato declara la publicación del documento ni qué pasa cuando el texto cambia después de que alguien lo aceptó |
| `apps/core/integraciones.py` | Única puerta de salida HTTP del proyecto, con política de tres capas: caché, servicio en vivo, respaldo local | La política de degradación está declarada sólo para cotizaciones, dentro de las Excepciones de `CO-155`. Para el resto de los catálogos no hay contrato que diga qué pasa cuando el servicio no responde |

### Las tareas de consola quedan fuera del modelo de casos de uso

Cuatro cosas que figuraban en esta tabla **salen de ella**, por la decisión de R-01-002: son
herramientas de operación y no casos de uso. No tienen ficha ni contrato, y eso es deliberado.

| Herramienta | Qué hace |
| --- | --- |
| `manage.py respaldar_base` | Respaldo de la base con rotación, invocable a mano o por tarea programada |
| `manage.py sincronizar_georef`, `sincronizar_paises` | Mantienen los catálogos de provincias, localidades y códigos telefónicos desde servicios públicos |
| `manage.py ingerir_correos`, `extraer_novedades` | Cargan correos desde `.eml` y disparan la extracción a mano |
| `manage.py crear_administrador_inicial` | Alta de la primera cuenta Administrador de una instalación nueva. No hay actor del sistema que pueda ejecutarla, porque el sistema todavía no tiene ninguna cuenta |

**La enmienda está pendiente**: un límite nuevo del sistema que declare esas tareas fuera del
modelo de casos de uso. Hasta que llegue a `.contexto-ia/`, lo que manda es la resolución
R-01-002. Es la única fila de esta sección que se resuelve enmendando el alcance y no escribiendo
un contrato.

**Dos aclaraciones sobre lo que ya no está acá.** `CO-016 ejecutarCicloMonitoreoCasilla` no es
código sin contrato sino **contrato sin código**: sigue pendiente y depende de P-05; que la
ingesta manual exista no lo reemplaza. Y el banco de muestras de `DiagnosticoLLMView` tampoco es
deuda: el paso 2 de `CU-CFG-LLM` ya declara que el contenido de prueba lo provee el sistema
(B-17-001).

---

## Entradas de bitácora

| Bitácora | Total | Abiertas | Tipos | Resueltas el |
| --- | ---: | ---: | --- | --- |
| `bitacora/01-alta-editorial.md` | 2 | 0 | 2 agregados | 2026-09-22 |
| `bitacora/02-catalogo.md` | 2 | 0 | 1 agregado, 1 corrección | 2026-09-22 |
| `bitacora/04-proveedores.md` | 3 | 0 | 3 agregados | 2026-09-22 |
| `bitacora/11-cuenta-de-cliente.md` | 1 | 0 | 1 agregado | 2026-09-22 |
| `bitacora/12-autenticacion.md` | 3 | 0 | 2 desvíos, 1 agregado | 2026-09-22 |
| `bitacora/13-gestion-de-usuarios.md` | 5 | 0 | 2 agregados, 2 desvíos, 1 corrección | 2026-09-22 |
| `bitacora/17-configuracion-del-sistema.md` | 2 | 0 | 1 agregado, 1 desvío | 2026-09-22 |
| `bitacora/18-stock-almacenado-en-local.md` | 1 | 0 | 1 corrección | 2026-09-22 |
| **Total** | **19** | **0** | | |

**Eran 17 y ahora son 19.** La fotografía anterior decía 16 y estaba mal: las entradas del
2026-09-14 fueron diecisiete. Las dos nuevas son `B-12-003` —los dos conceptos de enlace, que
aparecieron al construirlos— y `B-13-005` —el retiro del admin de Django—.

**Ninguna queda abierta**, y eso no quiere decir que el documento ya esté enmendado. Una entrada
resuelta puede dejar una enmienda pendiente, y siete lo hacen:

| Enmienda pendiente | De dónde sale | Qué toca |
| --- | --- | --- |
| Límite nuevo: las tareas de consola quedan fuera del modelo de casos de uso | R-01-002 | El capítulo de alcance |
| Los cinco catálogos no distinguen mayúsculas | R-02-002 | `MODELO_DE_DOMINIO.md` Área 2, e I-08 |
| `CO-120`: el correo no pertenece a ninguna cuenta **en cualquier estado** | R-13-004 | Precondición y E2 de `CO-120` |
| `CO-124`: pierde la precondición de colisión y la excepción E2 | R-13-004 | `CO-124` |
| `CO-125`: pierde la cita a I-14, que no tiene relación con inicios de sesión | R-13-004 | `CO-125` |
| `CO-149`: de dónde sale el contenido con el que se diagnostica | R-17-001 | Notas de `CO-149` |
| `EnlaceActivacion` y `TokenRecuperacion` pasan de `<<planificado>>` a `<<construido>>` | B-12-003 | `MODELO_DE_DOMINIO.md` Área 1 |

Hasta que cada enmienda llegue a `.contexto-ia/`, **manda la resolución de la bitácora** sobre el
texto volcado.

**Los cuatro desvíos se registraron después de tomados**, contra la regla que dice que un desvío
se consulta antes. No podían haberse consultado: el código es anterior a los contratos de los que
se aparta. Cada entrada lo aclara en su primer párrafo.

---

## Lo que esta fotografía no cubre

- **La columna de dependientes es la del modelo, no la de los contratos.** Se leyó de las
  asociaciones con multiplicidad de `MODELO_DE_DOMINIO.md`; un contrato podría necesitar un
  concepto sin que el modelo declare una asociación entre los dos, y eso no se buscó.
- **No se verificó el modelo contra las fichas.** Se lo tomó como fuente, que es lo que es.
- **«Código sin contrato» no es exhaustivo.** Se recorrieron las rutas de las cuatro apps, los
  comandos de gestión y los módulos de servicio. Lo que no se recorrió con el mismo detalle son
  las plantillas: una regla de negocio que viva sólo en un `{% if %}` no la encontraría este
  método. La baja de tipo de material apareció justamente por revisar un formulario, no una ruta.
- **El chequeo de consistencia compara nombres, no significados.** Dos operaciones con el mismo
  nombre en fuentes distintas se dan por la misma; que sus argumentos o su tipo coincidan no se
  comprueba.
- **La cobertura del 97 % no distingue camino feliz de rama de error.** El «foco reforzado» que
  `CLAUDE.md` pide sobre dinero, control de acceso, concurrencia y postcondiciones negativas no se
  midió aparte.
- **La deuda de las pantallas contra `TOKENS_VISUALES.md` no se midió.**
