# Bitácora — `18` Stock Almacenado en Local

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-18-001 · Sesenta y cuatro contratos de otros módulos quedan archivados bajo el módulo 18

**Tipo:** Corrección · **Fecha:** 2026-09-14 · **Alcance:** `CO-155` a `CO-218`, todos los módulos
**Estado:** Abierta

**Qué apareció.**
`.contexto-ia/contratos/18-stock-almacenado-en-local.md` contiene 68 contratos. Sólo cuatro son del
módulo: `CO-151` a `CO-154`. Los otros 64 —de `CO-155` a `CO-218`— son operaciones de consulta y
de apertura de pantalla que pertenecen a todos los módulos del sistema:

| Contrato | A qué módulo pertenece |
| --- | --- |
| `CO-155 sincronizarCotizaciones` | 01 Alta Editorial (lo consume `CO-007`) |
| `CO-157 consultarColaDeCorreos` | 04 Proveedores |
| `CO-162 consultarInventario` | 02 Catálogo |
| `CO-172 consultarProveedores` | 04 Proveedores |
| `CO-176 consultarCatalogoPublico` | 07 Tienda Online |
| `CO-194 consultarCuentasDeCliente` | 11 Cuenta de Cliente |
| `CO-205 consultarLogDeAuditoria` | 16 Auditoría |
| … | … |

La causa es de estructura del documento, no del generador: en el documento de análisis esos
contratos vienen **después** del último encabezado de módulo, así que `generar_contexto.py` los
atribuye al módulo que estaba abierto, que es el 18. El script hace lo correcto con lo que recibe.

Lo que sí conviene saber es que **la verificación del generador no lo detecta**. Busca fichas sin
contrato, contratos sin ficha, módulos vacíos y huecos en la numeración. Acá no hay hueco alguno
—la numeración corre de `CO-001` a `CO-218` sin saltos— y la corrida del 2026-09-14 informó «Sin
observaciones».

**Qué dice la especificación.**
El documento agrupa los contratos por módulo con encabezados de la forma «Módulos NN: Nombre». A
partir de `CO-155` no hay encabezado nuevo, así que el capítulo de contratos de consulta queda
dentro del módulo 18 por posición y no por contenido. Cada contrato **sí** declara a qué caso de
uso pertenece, en su campo «Referencias Cruzadas»: la información está, pero no en el lugar por el
que se busca.

**Qué se hizo.**
Nada. `.contexto-ia/` no se edita a mano y la corrección no se aplica ahí: lo que hay que cambiar
es el documento. Se anotó acá, y el recuento por archivo de `docs/DEUDA.md` lleva la aclaración
para que nadie lea «68 contratos del módulo 18».

**Qué habría que cambiar.**
En el documento de análisis, abrir un encabezado de capítulo propio antes de `CO-155` —las
operaciones de consulta son transversales y no pertenecen a ningún módulo— o repartir cada
contrato bajo el encabezado del módulo que le corresponde. La primera opción es menos trabajo y
más fiel: `CO-156 cancelarOperacion` aparece referenciado por 15 casos de uso de 8 módulos
distintos, así que no hay un módulo al que mudarlo.

Como consecuencia, convendría que `generar_contexto.py` avise cuando un contrato se archiva en un
módulo que ninguno de sus casos de uso referenciados habita. Hoy eso no se chequea y es
exactamente el error que se coló.
