> **Tipo: Normativo.** Define cómo se respalda y se restaura. El resultado de la última
> verificación es una fotografía y va al final, fechado.

# Plan de respaldos

Qué se respalda, cada cuánto, dónde queda y cómo se verifica que sirve.

**Un respaldo que nunca se restauró no es un respaldo.** La única prueba de que un respaldo
funciona es haberlo restaurado, y por eso este plan incluye una verificación periódica y no sólo
una rutina de copia.

---

## Qué se respalda

| Qué | Por qué | Se pierde si falta |
| --- | --- | --- |
| Base de datos | Es el sistema | Todo |
| `media/` | Portadas, evidencias de devolución, banners, correos originales archivados | Los archivos subidos. **No se regeneran**: la evidencia de un reclamo y el correo original de un proveedor son únicos |
| `.env` | Credenciales y configuración del entorno | El despliegue no arranca |

**Lo que no se respalda, a propósito:** el código y las migraciones viven en el repositorio, los
archivos derivados se regeneran, y `venv/` se reconstruye desde `requirements.txt`.

---

## Rutina

| | |
| --- | --- |
| Frecuencia | Diaria |
| Disparador | `respaldos/respaldo-diario.ps1`, como tarea programada |
| Destino | `respaldos/` |
| Retención | *(a definir: cuántos diarios, cuántos semanales)* |
| Fuera del repositorio | Sí. `respaldos/` está en `.gitignore` |

El comando de Django que produce el volcado es `respaldar_base`. El script de Windows lo invoca y
se ocupa de la rotación; **la lógica del respaldo vive en el comando y no en el script**, para que
se pueda ejecutar a mano y desde cualquier sistema.

---

## Verificación

Un respaldo se considera verificado cuando **se restauró sobre una base vacía y el sistema
arrancó contra ella**. No alcanza con que el archivo exista y pese lo esperado.

| Paso | Qué se comprueba |
| --- | --- |
| 1 | El archivo del día existe y no está vacío |
| 2 | Se restaura sobre una base vacía, sin errores |
| 3 | Las migraciones están todas aplicadas en la base restaurada |
| 4 | El sistema arranca y una pantalla que lee datos los muestra |
| 5 | Un archivo de `media/` referenciado desde la base existe en el respaldo |

El paso 5 es el que se olvida: la base y los archivos se respaldan por separado, y un respaldo de
base sin sus archivos deja el sistema arrancando con las imágenes rotas.

**Frecuencia de la verificación:** *(a definir)*. Lo importante es que sea periódica y que quede
registrada abajo.

---

## Restauración

*(Pasos concretos: dónde se toma el archivo, con qué comando se restaura, qué hay que hacer con
`media/` y con `.env`, y cómo se comprueba que quedó bien.)*

---

## Última verificación

| | |
| --- | --- |
| Fecha | — |
| Resultado | — |
| Observaciones | — |