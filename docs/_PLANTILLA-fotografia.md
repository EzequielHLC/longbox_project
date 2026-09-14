# Título de la fotografía

> **Tomada el AAAA-MM-DD**, del repositorio y no de memoria.
> Describe un momento. **Se reemplaza entera, no se actualiza por partes.**

---

## Qué es un documento de tipo Fotografía

Un documento que describe **cómo están las cosas hoy**. Caduca: dentro de un mes va a estar mal, y
eso no es un defecto sino su naturaleza. Por eso lleva fecha arriba de todo y por eso se reemplaza
completo en vez de parchearse.

Las tres que existen son `ESTADO.md` (avance por caso de uso), `DEUDA.md` (diferencia entre lo
especificado y lo construido) y `ESTRUCTURA.md` (el árbol del repositorio, que vive en
`.contexto-ia/` por ser material de orientación).

### Qué puede contener

- Cifras, conteos, porcentajes, fechas
- El estado de cada caso de uso, módulo o entidad
- Qué falta, qué sobra, qué está a medias
- Enlaces a los documentos normativos que describen lo que se está midiendo

### Qué no puede contener

- **Ninguna regla nueva.** Si al escribirla aparece una regla —"el dinero es Decimal", "esta
  pantalla pertenece al modo operativo"— esa regla está mal ubicada: va a `CLAUDE.md` si es de
  trabajo, o al documento de análisis si es del sistema. Una regla dentro de una fotografía
  desaparece cuando la foto se reemplaza.
- **Justificaciones de diseño.** Van a la bitácora.
- **Nada que ya viva en otro archivo.** Se enlaza, no se copia. Un dato duplicado en dos
  fotografías diverge en la primera semana.

---

## Estructura sugerida

Adaptala. Lo único obligatorio es la fecha arriba y que no aparezcan reglas.

### Resumen

Dos o tres frases sobre el momento que la foto captura. Qué cambió respecto de la anterior, si
algo cambió de forma relevante.

### El cuerpo

Tablas, preferentemente. Una fotografía se consulta buscando un dato puntual, no se lee de
corrido. Si una sección necesita tres párrafos de prosa para explicarse, probablemente sea una
regla disfrazada y no pertenece acá.

| Cosa | Estado | Observación |
| --- | --- | --- |
| … | … | … |

### Lo que la foto no cubre

Sé explícito con los huecos. Una fotografía que omite lo que no pudo medir se lee como si eso no
existiera, y es peor que decir que no se sabe.

---

## Escala de estado

Cuando la fotografía informe avance, usá siempre estos valores. Que sean pocos y fijos es lo que
hace comparables dos fotos de fechas distintas.

| Valor | Significa |
| --- | --- |
| `Pendiente` | No se empezó |
| `En curso` | Se está trabajando ahora |
| `Construido, sin verificar` | El código existe y la suite pasa, pero nadie comprobó que cumpla las postcondiciones de sus contratos |
| `Verificado` | Pasó las siete puertas, incluida la de contratos |
| `Parcial` | Terminado en parte, con la limitación anotada en la observación |
| `Bloqueado` | No puede avanzar. La observación dice qué lo bloquea |

**`Construido, sin verificar` no es una etiqueta transitoria.** Es el estado real de todo lo que se
escribió antes de que existieran los contratos, y decirlo así es más honesto que llamarlo
terminado. La cola de trabajo que genera es legítima y conviene que se vea.