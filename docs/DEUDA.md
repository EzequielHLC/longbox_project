> **Tipo: Fotografía.** Tomada el **2026-09-14**.
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
| Nombre de las pruebas | **Resuelta el 2026-09-14**: las pruebas de contrato se agregan junto a las descriptivas, en archivos `test_contratos_NN_*.py`, y las existentes no se renombran. Queda abierto si las descriptivas se retiran cuando su contrato quede verificado, o si conviven | Nada. Se aplicó en los módulos 12 y 13 y es el patrón para los 16 restantes | Resuelta |
| `ALLOWED_HOSTS` | La puerta de configuración de despliegue tiene una advertencia (`security.W020`) porque el host de producción no está decidido. Es la única que separa a `CU-AUT-FIN` y `CU-USR-ELI` del estado `Verificado` | El estado `Verificado` para **todo** caso de uso, por más que sus contratos estén verificados | 2026-09-14 |
| `docs/pruebas/COBERTURA.md` | No existe, y `.scripts/generar_cobertura.py` lo arma extrayendo `CU-\d+` de los docstrings: es el esquema viejo de 63 CU, que ya no está en el código. Hay que decidir si se adapta el script al esquema `CU-MOD-AAA` y a los códigos `CO-###` | El único archivo donde vive «qué contrato está cubierto por qué prueba» | 2026-09-14 (migración de la numeración) |
| `04_RESUMEN.md` | `MODELO_DE_DOMINIO.md` remite a él dos veces —para los supuestos, las inconsistencias y «cuatro operaciones con contrato pausado por ambigüedad»— y el archivo no está en el repositorio. Ninguno de los 218 contratos aparece marcado como pausado en `.contexto-ia/` | Saber cuáles son esas cuatro operaciones. Hasta que aparezcan, se las está contando como contratos normales en el recuento de más abajo | 2026-09-14 |
| `.contexto-ia/dss/` | La carpeta no existe. `CLAUDE.md` manda abrir `dss/NN-modulo.md` junto con la ficha y los contratos; el generador no la produce y hay un `.scripts/exportar_dss.py` aparte que sí genera diagramas. Hay que decidir cuál de los dos es la fuente | El paso 1 del flujo «antes de programar un módulo» | — |
| Dónde viven los parámetros del sistema | CO-114 declara que el bloqueo se levanta «por el período parametrizado» y que la expiración por inactividad sale «según `ConfiguracionSistema`». En el código los tres valores son constantes en `config/settings/base.py` (`LOGIN_INTENTOS_MAXIMOS`, `LOGIN_BLOQUEO_MINUTOS`, `SESSION_COOKIE_AGE`) | `CU-CFG-PAR` completo, y la verificación de CO-114 y CO-115 | — |
| Pedido como dependencia raíz | No es una decisión de diseño abierta sino un orden de construcción a fijar: el concepto Pedido no existe todavía | Los módulos **07, 08, 09, 10 y 14** enteros, más `CU-ALT-DEM`, `CU-ALT-CAN`, `CU-CLI-BAJ`, `CU-CLI-HIS` y el módulo **18** | — |
| Dónde viven los generadores | `CLAUDE.md` documenta `scripts/generar_contexto.py`; el directorio real es `.scripts/`, y está listado en `.gitignore`. Los cuatro generadores no viajan con el repositorio | Que otra máquina pueda regenerar `.contexto-ia/` | Commit que renombró el directorio |
| Referencias a documentación que ya no existe | El código cita nueve veces dos rutas que desaparecieron en la reorganización: `/docs/modulos/gestion_usuarios.md` (5), `/docs/modulos/proveedores.md` (1) y `/docs/diseno/sistema-visual.md` (3, en las tres cáscaras de plantilla). Hay que decidir si se reponen esos documentos o si las citas se reemplazan por el caso de uso y por `TOKENS_VISUALES.md` | Que se pueda reconstruir por qué se tomó cada agregado del módulo 13 y del pipeline de novedades. El razonamiento no está en ninguna otra parte del repositorio | Reorganización de la documentación |

---

## Conceptos especificados sin implementar

Fuente: `.contexto-ia/MODELO_DE_DOMINIO.md`, que declara **39 conceptos — 19 construidos y 20
planificados** — contrastados contra las 19 clases `models.Model` del código.

**Los 19 construidos del modelo coinciden uno a uno con los 19 modelos de Django.** No hay
concepto marcado como construido que falte en el código, ni modelo en el código que el documento
no declare. La correspondencia es exacta.

Los 20 planificados son la deuda de dominio completa:

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
| `EnlaceActivacion` | A1 Personas y acceso | 13 Gestión de Usuarios | — |
| `TokenRecuperacion` | A1 Personas y acceso | 12 Autenticación | — |
| `Banner` | A7 Parámetros | 17 Configuración del Sistema | — |
| `ContenidoFAQ` | A7 Parámetros | 17 Configuración del Sistema | — |
| `IdentidadVisual` | A7 Parámetros | 17 Configuración del Sistema | — |

**`Pedido` es la raíz.** De sus dos dependientes directos cuelgan otros cinco, y hasta que exista
no avanzan los módulos 07, 08, 09, 10, 14 y 18, ni `CU-ALT-DEM`, `CU-ALT-CAN`, `CU-CLI-BAJ` ni
`CU-CLI-HIS`. Es el orden de construcción que el modelo hace visible.

**Dos planificados tienen sustituto funcionando en el código, y aun así son deuda.**
`EnlaceActivacion` y `TokenRecuperacion` están resueltos hoy con tokens firmados de Django y
vigencias propias en `apps/accounts/tokens.py`, sin tabla. El modelo los declara conceptos porque
cuatro casos de uso los tratan como objetos con estado propio y hay que distinguir tres razones de
rechazo —vigente, consumido, vencido—: `CU-AUT-ACT` valida las tres, `CU-USR-MOD` A1 y
`CU-USR-REA` A2 regeneran el enlace invalidando el anterior, y `CU-AUT-REC` E1 distingue «ya
utilizado» de «expirado». Un token firmado distingue válido de inválido y no más que eso, así que
la postcondición que declara el cambio de estado no tiene hoy sujeto sobre el cual declararse.

---

## Contratos sin prueba

Operaciones especificadas cuya postcondición nadie verifica todavía. Se obtiene comparando los
códigos de contrato con los nombres de prueba.

**Faltan 199 de 218.** El pase de verificación del 2026-09-14 cubrió los módulos `12` Autenticación
y `13` Gestión de Usuarios —los dos únicos con todos sus casos de uso construidos— con 94 pruebas
nuevas nombradas por su contrato. El resto de la suite sigue nombrada en castellano descriptivo,
sin declarar qué postcondición verifica.

| Archivo de contratos | Contratos | Verificados | Parciales | Incumplidos | Sin prueba |
| --- | --- | --- | --- | --- | --- |
| `contratos/01-alta-editorial.md` | 27 | 0 | 0 | 0 | 27 |
| `contratos/02-catalogo.md` | 19 | 0 | 0 | 0 | 19 |
| `contratos/03-pricing.md` | 13 | 0 | 0 | 0 | 13 |
| `contratos/04-proveedores.md` | 7 | 0 | 0 | 0 | 7 |
| `contratos/05-restock.md` | 11 | 0 | 0 | 0 | 11 |
| `contratos/06-ventas-presenciales.md` | 5 | 0 | 0 | 0 | 5 |
| `contratos/07-tienda-online.md` | 9 | 0 | 0 | 0 | 9 |
| `contratos/08-gestion-de-pedidos.md` | 7 | 0 | 0 | 0 | 7 |
| `contratos/09-devoluciones.md` | 4 | 0 | 0 | 0 | 4 |
| `contratos/10-puntos.md` | 4 | 0 | 0 | 0 | 4 |
| `contratos/11-cuenta-de-cliente.md` | 7 | 0 | 0 | 0 | 7 |
| **`contratos/12-autenticacion.md`** | 6 | **2** | 4 | 0 | **0** |
| **`contratos/13-gestion-de-usuarios.md`** | 6 | **3** | 2 | 1 | **0** |
| `contratos/14-caja.md` | 2 | 0 | 0 | 0 | 2 |
| `contratos/15-reportes.md` | 1 | 0 | 0 | 0 | 1 |
| `contratos/16-auditoria.md` | 1 | 0 | 0 | 0 | 1 |
| `contratos/17-configuracion-del-sistema.md` | 21 | 0 | 0 | 0 | 21 |
| `contratos/18-stock-almacenado-en-local.md` | 68 | **5** | 0 | 2 | 61 |
| **Total** | **218** | **10** | **6** | **3** | **199** |

Los cinco verificados del archivo del módulo 18 son contratos de consulta que pertenecen al módulo
13: `CO-156`, `CO-196`, `CO-197`, `CO-200` y `CO-201`. Es la consecuencia práctica del problema de
archivado que se explica más abajo.

### Los 6 parciales: la postcondición nombra un concepto que no existe

| Contrato | Qué no se puede afirmar | Qué sí se afirma en su lugar |
| --- | --- | --- |
| `CO-114` | «expiración por inactividad **según `ConfiguracionSistema`**» | Que la sesión nace con una expiración por inactividad finita |
| `CO-117` | «(a) se creó tr : `TokenRecuperacion`», «tr → Usuario» | Que el enlace llega a la dirección de la cuenta activa, y que un correo sin cuenta no produce ningún efecto |
| `CO-118` | «(c) tr.estado pasó de Vigente a Consumido» | Que el mismo enlace no admite un segundo uso |
| `CO-119` | «(c) `EnlaceActivacion`.estado pasó de Vigente a Consumido» | Ídem |
| `CO-120` | «(a) se creó ea : `EnlaceActivacion`», «(b) ea → u» | Que el enlace se envió al correo del nuevo usuario |
| `CO-122` | «(a) se creó uno nuevo», «(c) el anterior pasó a Vencido» | Que llega un enlace nuevo y que el anterior deja de servir |

Las seis dependen de construir `EnlaceActivacion` y `TokenRecuperacion`, dos de los 20 conceptos
planificados. Registradas en `bitacora/12-autenticacion.md`, B-12-002.

### Los 3 incumplidos: el sistema hace otra cosa que la declarada

| Contrato | La postcondición declarada | Lo que hace el sistema | Registrado en |
| --- | --- | --- | --- |
| `CO-124` | «u.rol quedó con el valor declarado», y la auditoría incluye el rol asignado | Conserva el rol anterior; la auditoría registra sólo el cambio de estado | B-13-002 |
| `CO-199` | Presentar el rol «permitiendo modificarlo antes de confirmar» | Lo presenta como texto, sin control editable | B-13-002 |
| `CO-198` | E1: la solicitud de baja del último Administrador se bloquea | La pantalla se ofrece; el rechazo llega recién al confirmar | B-13-003 |

Las tres están escritas como prueba y marcadas `xfail(strict=True)`: si alguna empezara a pasar, la
suite falla y avisa en vez de dejar un xfail viejo pasando desapercibido.

`CO-202` `consultarFichaDeUsuario` queda entre los 199 sin prueba por otro motivo: no hay pantalla
de ficha de usuario que ejercer. El listado y el formulario de edición cubren lo que el CU pide
mostrar, y decidir si eso alcanza es una de las ambigüedades de
`docs/planes/13-gestion-de-usuarios.md`.

---

## Invariantes declaradas sin garantía en la base

`MODELO_DE_DOMINIO.md` declara 23 invariantes. Seis de ellas (I-18 a I-23) recaen sobre conceptos
planificados y no se pueden evaluar todavía. De las 17 restantes, **todas están implementadas**:
ninguna invariante sobre concepto construido quedó sin código que la sostenga.

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

**No hay ni una `CheckConstraint` en todo el proyecto** (`grep -rn "CheckConstraint" apps/`
devuelve cero). Las nueve invariantes de unicidad están en la base; las cuatro de valor y de
coherencia de estado, no.

I-09 es la más expuesta de las cuatro, porque es la única que toca dinero: nada en la base impide
hoy un `Producto.objects.update(precio=0)` ni un importe negativo. I-12 es la segunda, porque el
resguardo del último Administrador vive en el servicio y no en el modelo: cualquier baja que no
pase por la vista lo esquiva.

**Las dos verificaciones a mano que `CLAUDE.md` pide antes de cerrar un módulo se hicieron, y las
dos dan bien.**

- `manage.py migrate --check` sobre la base de desarrollo sale en 0: no hay migraciones sin
  aplicar.
- Las 12 restricciones de unicidad existen en PostgreSQL y las 12 son índices `UNIQUE`.

La segunda confirma el falso negativo contra el que `CLAUDE.md` advierte, y con una proporción
mayor que la esperada: **de las 12, sólo 3 figuran además en `pg_constraint`.** Las otras 9 —las
siete definidas sobre `Lower(...)` más las dos con `condition=` (`producto_unico_por_codigo_de_barras`
y `producto_editorial_unico_por_isbn`)— existen únicamente como índice. Buscarlas donde están las
demás devuelve «no existe» sobre nueve restricciones que sí están puestas:

| Restricción | En `pg_indexes` | En `pg_constraint` |
| --- | --- | --- |
| Las 7 sobre `Lower(...)` | sí, `UNIQUE` | **no** |
| Las 2 con `condition=` | sí, `UNIQUE` | **no** |
| `producto_editorial_unico_por_clave`, `precio_unico_por_editorial_tipo_y_formato`, `confianza_unica_por_campo_del_borrador` | sí, `UNIQUE` | sí |

---

## Código sin contrato

Lo inverso, y suele ser más grave: comportamiento que existe en el código y que ningún contrato
declara. Cada fila es o un contrato que falta escribir, o funcionalidad que sobra.

| Dónde | Qué hace | Qué falta |
| --- | --- | --- |
| `apps/core/georef.py`, `apps/core/paises.py`, ruta `core:localidades`, comandos `sincronizar_georef` y `sincronizar_paises` | Mantiene los catálogos de provincias, localidades y códigos telefónicos de país desde servicios públicos, con caché y respaldo local versionado en `apps/core/datos/`, y los sirve al autocompletado del registro de Cliente | Ningún contrato los declara. CO-155 contrata la sincronización de **cotizaciones** y nada más; CO-107 `registrarCuentaDeCliente` no menciona de dónde salen localidad y provincia. Falta el contrato de sincronización de catálogos geográficos, o su declaración dentro de CO-107 |
| `apps/core/integraciones.py` | Única puerta de salida HTTP del proyecto, con política de tres capas: caché, servicio en vivo, respaldo local. Es lo que permite que la fixture `sin_red` corte la red entera parcheando un punto | La política de degradación está declarada sólo para cotizaciones, dentro de las Excepciones de CO-155. Para el resto de los catálogos no hay contrato que diga qué pasa cuando el servicio no responde |
| `apps/core/views.py::PanelAdministracionView` y `core/templates/core/panel.html` | Tablero de entrada del Administrador: cuentas por rol y por estado, proveedores que alimentan el pipeline de novedades, últimas entradas del log de auditoría | Ningún contrato declara un tablero. CO-205 contrata la consulta del log, que es otra cosa: acá hay cifras agregadas que nadie especificó, y `CU-REP-GEN` —el CU que sí habla de cifras— está pendiente |
| `apps/core/views.py::TerminosView` y `core/templates/core/terminos.html` | Sirve el texto de términos y condiciones que el registro de Cliente obliga a aceptar | CO-107 declara la aceptación y el campo `fecha_aceptacion_politica`, pero ningún contrato declara la publicación del documento ni qué pasa cuando el texto cambia después de que alguien lo aceptó |
| `apps/core/management/commands/respaldar_base.py` y `docs/despliegue/RESPALDOS.md` | Respaldo de la base con rotación, invocable a mano o por tarea programada | Ningún contrato lo declara, y no hay ningún caso de uso de operación del sistema donde ubicarlo. Puede ser correcto que quede fuera del alcance funcional; hoy eso no está dicho en ninguna parte |
| `apps/suppliers/muestras.py` y el banco de muestras de `DiagnosticoLLMView` | Fabrica correos de novedades de mentira para probar el modelo de lenguaje contra contenido conocido | CO-149 `ejecutarDiagnosticoDelModelo` contrata el diagnóstico, pero no dice si el contenido de prueba lo provee el sistema o lo pega el Administrador. Hoy el sistema trae un banco propio |
| `apps/suppliers/management/commands/ingerir_correos.py` y `extraer_novedades.py` | Disparan a mano la ingesta y la extracción que CO-016 especifica como ciclo automático del Temporizador del Sistema | No es código sin contrato sino contrato sin código: CO-016 `ejecutarCicloMonitoreoCasilla` no existe todavía y los comandos ocupan su lugar. Está anotado así en `ESTADO.md` (`CU-ALT-NOV`, Parcial) |

**Una aclaración sobre lo que *no* entró en esta tabla.** Varias pantallas llevan en su docstring
la afirmación de que ningún caso de uso las describe —la reactivación de producto, la reactivación
de proveedor, la cola de correos, el diagnóstico del modelo, la consulta de cuentas de Cliente, la
eliminación de cuenta nunca activada—. Esas afirmaciones se escribieron contra el esquema anterior
de 63 casos de uso y **hoy son falsas**: el esquema vigente las describe en `CU-CAT-REA`,
`CU-PRV-REA`, `CU-PRV-COL`, `CU-CFG-LLM`, `CU-CLI-CON` y `CU-USR-ELI` respectivamente. No son
deuda de especificación sino comentarios vencidos. Están listadas una por una en el informe de la
migración y anotadas en las bitácoras de sus módulos.

---

## Entradas de bitácora sin resolver

Decisiones registradas durante la construcción que todavía no se llevaron al documento de
análisis. El detalle está en cada bitácora; acá va sólo la cuenta y las que llevan más tiempo
abiertas.

| Bitácora | Abiertas | Tipos | La más antigua |
| --- | --- | --- | --- |
| `bitacora/01-alta-editorial.md` | 2 | 2 agregados | B-01-001 (2026-09-14) |
| `bitacora/02-catalogo.md` | 2 | 1 agregado, 1 corrección | B-02-001 (2026-09-14) |
| `bitacora/04-proveedores.md` | 3 | 3 agregados | B-04-001 (2026-09-14) |
| `bitacora/11-cuenta-de-cliente.md` | 1 | 1 agregado | B-11-001 (2026-09-14) |
| `bitacora/12-autenticacion.md` | 2 | 1 desvío, 1 corrección | B-12-001 (2026-09-14) |
| `bitacora/13-gestion-de-usuarios.md` | 4 | 1 agregado, 2 desvíos, 1 corrección | B-13-001 (2026-09-14) |
| `bitacora/17-configuracion-del-sistema.md` | 2 | 1 agregado, 1 desvío | B-17-001 (2026-09-14) |
| `bitacora/18-stock-almacenado-en-local.md` | 1 | 1 corrección | B-18-001 (2026-09-14) |
| **Total** | **16** | 8 agregados, 4 desvíos, 4 correcciones | |

Todas nacieron el mismo día: son el registro de lo que apareció al reconciliar el código contra el
esquema vigente de casos de uso, no decisiones tomadas mientras se programaba. Las entradas
anteriores a esa reconciliación no existen —el proyecto llevaba meses de código sin bitácora—, y
eso no se puede recuperar leyendo el repositorio.

**Los cuatro desvíos se registraron después de tomados**, contra la regla que dice que un desvío se
consulta antes. No podían haberse consultado: el código es anterior a los contratos de los que se
aparta. Cada entrada lo aclara en su primer párrafo.

**Las cuatro entradas nuevas del 2026-09-14 salieron de escribir las pruebas de contrato**, no de
leer el código. Es la diferencia que la puerta de contratos hace: B-13-002 y B-13-003 son
divergencias que ninguna lectura del repositorio había encontrado en el pase anterior, porque el
código se lee coherente consigo mismo y sólo deja de serlo al lado del contrato.

---

## Lo que esta fotografía no cubre

- **La columna de dependientes es la del modelo, no la de los contratos.** Se leyó de las
  asociaciones con multiplicidad de `MODELO_DE_DOMINIO.md`; un contrato podría necesitar un
  concepto sin que el modelo declare una asociación entre los dos, y eso no se buscó.
- **No se verificó el modelo contra las fichas.** Se lo tomó como fuente, que es lo que es.
- **«Código sin contrato» no es exhaustivo.** Se recorrieron las rutas de las cuatro apps, los
  comandos de gestión y los módulos de servicio, y se contrastó cada uno contra los 218 contratos.
  Lo que no se recorrió con el mismo detalle son las plantillas: una regla de negocio que viva sólo
  en un `{% if %}` no la encontraría este método.
- **No se evaluó si un contrato existente está cumplido**, sólo si existe una prueba que lo
  declare. Un contrato puede estar implementado mal y esta fotografía no lo distinguiría de uno
  implementado bien: las dos cosas se ven igual desde acá, y ésa es exactamente la razón por la
  que existe la puerta de contratos.
- **La cobertura del 97 % no distingue camino feliz de rama de error.** El «foco reforzado» que
  `CLAUDE.md` pide sobre dinero, control de acceso, concurrencia y postcondiciones negativas no se
  midió aparte: haría falta leer qué cubre cada prueba, no cuántas líneas toca.
- **La deuda de las pantallas contra `TOKENS_VISUALES.md` no se midió.**
