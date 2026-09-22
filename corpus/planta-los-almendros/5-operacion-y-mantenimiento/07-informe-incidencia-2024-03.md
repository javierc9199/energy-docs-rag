---
title: "Informe de incidencia INC-2024-017 — Fusibles fundidos en bloque 12"
doc_type: incident_report
date: "2024-03-21"
synthetic: true
---

# Informe de incidencia INC-2024-017 — Fusibles de string fundidos en el bloque 12

> Documento ficticio creado para un proyecto de demostración.

## 1. Resumen

Entre el 4 y el 18 de marzo de 2024 se fundieron 23 fusibles de string de 20 A en las cajas de string CB-12.03, CB-12.07 y CB-12.08 del bloque de potencia 12. La pérdida de producción estimada fue de 7,4 MWh, por lo que se clasificó como incidencia mayor.

## 2. Detección

El SCADA generó repetidamente la alarma W405 de desequilibrio de corriente en las entradas DC 5, 11 y 12 del inversor del bloque 12. El técnico de guardia verificó en campo los fusibles fundidos y los sustituyó, pero la alarma reapareció en los días siguientes en las mismas cajas.

## 3. Análisis de causa raíz

La termografía de las cajas afectadas mostró puntos calientes superiores a 85 °C en los portafusibles. Al desmontarlos se encontraron conectores de string con el crimpado defectuoso: la sección de contacto era insuficiente, lo que elevaba la resistencia de la unión y calentaba el fusible hasta su fusión sin que hubiera sobrecorriente real.

Todos los conectores defectuosos pertenecían al mismo lote de montaje, instalado por una única cuadrilla durante la construcción.

**Causa raíz:** crimpado defectuoso de conectores durante la construcción, no detectado en la puesta en marcha porque el protocolo solo exigía termografía de una muestra de cajas de string.

## 4. Acciones correctivas

1. Sustitución de los 23 fusibles y de 68 conectores del lote afectado.
2. Termografía del 100 % de las cajas de string del bloque 12 y de los bloques 11 y 13, montados por la misma cuadrilla. Se encontraron y sustituyeron 9 conectores adicionales en el bloque 13.
3. Reclamación al contratista EPC dentro del periodo de garantía.

## 5. Acciones preventivas

- Se modifica el plan de mantenimiento para realizar termografía semestral de las cajas de string en lugar de anual.
- Se propone añadir al protocolo de puesta en marcha la termografía del 100 % de las cajas de string bajo carga, en lugar de una muestra.
- Se incrementa el stock mínimo de fusibles de string de 20 A de 40 a 60 unidades.
