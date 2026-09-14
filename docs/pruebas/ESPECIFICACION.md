> **Tipo: Normativo.** Define cómo se escribe una prueba en este proyecto. No dice qué está
> probado hoy: eso vive en `COBERTURA.md`, que es una fotografía.

# Especificación de pruebas

`CLAUDE.md` fija los umbrales. Este documento fija el método: qué se prueba, en qué capa, con qué
nombre y qué se exige en cada zona del sistema.

Una regla vale para todo lo que sigue. **La prueba existe para detectar que algo dejó de cumplirse,
no para acompañar al código.** Una prueba que se escribe mirando la implementación repite la
implementación, y entonces las dos se rompen juntas y en silencio. Por eso las pruebas de contrato
se escriben desde el contrato, sin abrir el archivo que lo implementa.

---

## 1. Las cinco capas

Cada una responde una pregunta distinta. Cubrir una no cubre a las otras, y la confusión más común
es creer que sí.

| Capa | Pregunta que responde | Toca la base | Toca HTTP |
| --- | --- | --- | --- |
| **Unidad** | ¿El cálculo da bien? | No | No |
| **Contrato** | ¿La operación deja el sistema como el contrato declara? | Sí | No |
| **Acceso** | ¿Puede ejercerla quien no debe? | Sí | Sí |
| **Flujo** | ¿El actor puede recorrer el caso de uso de punta a punta? | Sí | Sí |
| **Frontera** | ¿Qué pasa cuando el sistema externo se comporta mal? | Depende | Interceptado |

### Unidad

Para lógica que se puede aislar del framework: aritmética de precios, normalización de ISBN,
cálculo de puntos, resolución de duplicados. Se prueban contra una tabla de casos, sin base de
datos.

Es la capa más barata y la única que puede permitirse ser exhaustiva. Si una regla se puede probar
acá, no se prueba más arriba.

### Contrato

**Es la capa que sostiene la correspondencia entre el documento y el código**, y la que más
atención requiere. Está desarrollada en el apartado 3.

### Acceso

Verifica el control de acceso **por la dirección real de la operación, con el rol equivocado**.
Nunca llamando a la función interna: eso comprueba que la función valida, no que la operación esté
protegida, y son cosas distintas. Una operación puede tener la validación correcta en el servicio
y estar expuesta por una ruta que no pasa por ahí.

Toda operación que declara un rol en sus precondiciones necesita una prueba de esta capa.

### Flujo

Recorre el caso de uso completo como lo haría el actor, incluidos los pasos intermedios de
confirmación. Es la única capa que detecta que un paso quedó inalcanzable aunque su lógica esté
bien.

Una por caso de uso alcanza. No hace falta una por escenario alternativo: los alternativos se
cubren en la capa de contrato, que es más barata.

### Frontera

Para todo lo que sale del sistema: modelo de lenguaje, pasarela de pago, servicio de cotizaciones,
casilla de correo, envío de correo. **La red está cortada en las pruebas**; toda salida pasa por
una única puerta que las pruebas interceptan.

Lo que hay que probar acá no es el camino feliz, que es el fácil: es el catálogo de formas de
fallar. Un servicio externo que no responde, que responde tarde, que responde con basura, que
responde con la forma correcta y el contenido inventado, y que responde dos veces lo mismo.

**Una integración nueva que salga a la red por otro camino queda fuera de cobertura sin que nadie
lo note.** Es el fallo más silencioso del proyecto.

---

## 2. Cómo se nombra una prueba

El nombre es lo que hace consultable la trazabilidad sin leer código.

```
test_CO013_confirmar_ingreso_activa_productos_recibidos
     └────┘ └──────────────────────────────────────────┘
     contrato          qué verifica, en el lenguaje del dominio
```

Reglas:

- **Prueba de contrato: empieza por el código del contrato.** Con eso, "qué contratos no tienen
  prueba" es una búsqueda de texto y no una auditoría.
- **Las demás capas: empiezan por la capa.** `test_acceso_…`, `test_flujo_…`, `test_frontera_…`,
  o nada si es de unidad.
- **El resto del nombre describe el efecto esperado, no la acción.** `activa_productos_recibidos`,
  no `llama_a_confirmar_ingreso`. Si el nombre describe la llamada, la prueba probablemente esté
  verificando que el código corrió y no que el efecto ocurrió.
- **Una postcondición conflictiva, una prueba.** No agrupes cinco postcondiciones en un test: cuando
  falla, no sabés cuál.

---

## 3. La prueba de contrato

Un contrato declara precondiciones y postcondiciones en forma declarativa: qué instancias se
crearon, qué asociaciones se formaron o se rompieron, qué atributos cambiaron y de qué valor a qué
valor. **Eso ya es el cuerpo de la prueba.** No hay que diseñarlo, hay que transcribirlo.

### La estructura

1. **Montar el estado que las precondiciones describen.** Ni más ni menos. Si el contrato no exige
   que exista un pedido, no crees un pedido: estarías probando un escenario que el contrato no
   promete.
2. **Capturar el valor anterior** de todo atributo que la postcondición diga que cambia.
3. **Ejercer la operación una vez.**
4. **Afirmar cada postcondición por separado**, en el mismo orden en que el contrato las lista.

### Las tres categorías, y cómo se afirma cada una

| El contrato dice | La prueba afirma |
| --- | --- |
| (a) Se creó una instancia | Que existe, y que no existía antes |
| (b) Se formó o se rompió una asociación | Que la referencia apunta a lo que debe, y que la rota ya no apunta |
| (c) Un atributo pasó de X a Y | Que valía X antes y vale Y después. **Las dos mitades** |

La tercera es la que se hace mal más seguido. Afirmar sólo el valor final deja pasar el caso en que
el atributo ya valía Y desde el principio y la operación no hizo nada.

### Postcondiciones negativas

Varios contratos declaran explícitamente qué **no** debe cambiar. Que los pedidos activos no se
modifican al descatalogar un producto. Que el domicilio del perfil no se reescribe al declarar una
dirección de envío. Que el precio base no se toca al recalcular el precio final.

**Esas son obligatorias y son las que se rompen sin que nadie lo note**, porque ninguna prueba del
camino feliz las mira. Se afirman igual que las positivas: valor antes, valor después, iguales.

### Excepciones

Cada excepción declarada en el contrato es una prueba. Y lo que se afirma no es sólo que la
operación falle: es **qué quedó en el sistema después de que falló**. Un contrato que dice "se
revierten completamente todos los cambios" está pidiendo que la prueba verifique que no quedó nada
a medias, no que se haya lanzado un error.

### Operaciones sin postcondiciones

Las de consulta no cambian el estado, y esa es exactamente su prueba: ejercerla y afirmar que nada
cambió. Suena trivial y no lo es — es lo que detecta que alguien le agregó un efecto secundario a
una consulta.

---

## 4. Zonas de foco reforzado

Cuatro zonas donde el umbral de cobertura no alcanza y hay que cubrir también las ramas de error.

### Dinero y stock

- Aritmética decimal exacta, nunca punto flotante.
- Redondeo a la unidad monetaria, y **verificar dónde ocurre**: el coeficiente de importación
  conserva sus decimales intermedios porque multiplica a todos los ítems del lote, y recortarlo
  antes de aplicarlo arrastra el error a cada precio.
- Los valores congelados se prueban cambiando su fuente después de la operación y verificando que
  el valor congelado **no siguió** a la fuente.
- El stock se prueba en los bordes: llegar a cero, quedar en cero, volver de cero.

### Control de acceso

Ya está en el apartado 1. La regla que se olvida: **la prueba usa la dirección real, no la
función.**

### Concurrencia

Donde el sistema toma un bloqueo de registro. Lo que hay que provocar es la carrera, no simularla:
dos operaciones sobre el mismo dato, y afirmar que el resultado es uno de los dos estados válidos y
nunca un tercero.

Los casos que el sistema declara: stock perdido entre el carrito y el checkout, canje de puntos
sobre un lote que caduca, dos administradores resolviendo el mismo correo, aviso repetido de la
pasarela con la misma referencia.

### Idempotencia

Donde el sistema promete que repetir no duplica. Se prueba **ejerciendo la operación dos veces con
la misma entrada** y afirmando que el estado después de la segunda es idéntico al de la primera.

Los casos que el sistema declara: encolado de un correo por su identificador de mensaje, aviso de
pago por su referencia de pasarela, reprocesamiento de un correo ya procesado.

---

## 5. Datos de prueba

- **Cada prueba monta lo que necesita.** Una prueba que depende de datos que montó otra falla
  cuando la suite cambia de orden, y el diagnóstico es caro.
- **Los valores del dominio se escriben tal como el dominio los usa.** Precios con dos decimales,
  ISBN con dígito verificador válido, correos normalizados a minúsculas. Un dato de prueba
  imposible en producción prueba un camino que no existe.
- **Las fechas relativas al momento de la corrida**, no fijas. Una prueba con una fecha fija de
  vencimiento pasa hoy y falla el año que viene.
- **La red está cortada.** Si una prueba necesita una respuesta externa, la declara; no la busca.

---

## 6. Qué no se prueba

Decirlo evita discusiones y evita cobertura inflada que no significa nada.

- **El framework.** Que un campo obligatorio rechace un valor nulo es responsabilidad de quien
  escribió el framework.
- **Las migraciones, con pruebas.** Se verifican aplicándolas sobre la base de desarrollo, a mano,
  antes de cerrar el módulo. La suite crea una base temporal desde cero y puede quedar en verde con
  migraciones sin aplicar y las pantallas caídas.
- **El detalle visual.** Que un botón esté en su lugar no se prueba automáticamente. Que la
  operación que el botón dispara exista y esté protegida, sí.
- **Las justificaciones del contrato.** El campo Notas explica por qué una regla es como es. Es
  material de lectura, no una aserción.