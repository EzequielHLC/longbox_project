> **Tipo: Bitácora.** Se anexa, no se reescribe.

# Bitácora — `15` Reportes

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-15-001 · Qué cuenta como venta en los reportes

**Tipo:** Agregado · **Fecha:** 2026-10-22 · **Alcance:** `CU-REP-GEN`, `CO-204`
**Estado:** Abierta — decidido en el plan 15 (ambigüedades 1 a 4)

**Qué apareció.**
Los cinco reportes de `CO-204` consolidan «ventas», «productos vendidos» y «solicitudes activas»
sin decir qué entra en cada uno, y el sistema tiene pedidos cancelados, líneas canceladas con
reembolso, líneas pagadas con puntos, devoluciones y costo de envío.

**Qué dice la especificación.**
> «Ventas Totales, Ventas por Canal (físico / online), Productos más Vendidos, Movimientos de
> Puntos y Solicitudes de Reposición Activas» (`CU-REP-GEN`, paso 2). Nada más sobre su contenido.

**Qué se hizo.**
- Una venta es un pedido no cancelado, por su fecha; una línea cancelada con reembolso no cuenta.
- El envío va en su propia columna y no suma al importe de mercadería.
- Una línea pagada con puntos cuenta como unidad vendida y no suma importe.
- Los reembolsos de devoluciones resueltas van en su propia columna, por la fecha de resolución.
- Las solicitudes de reposición son las que siguen en espera hoy, creadas dentro del rango.
- El canal «físico» es el mostrador; un pedido online con retiro en el local es online.

**Qué habría que cambiar.**
`CO-204`, salida: describir el contenido de cada reporte con estos criterios.
