---
title: "Procedimiento de mantenimiento — Seguidores TrakLine 1P"
doc_type: procedure
synthetic: true
---

# Procedimiento de mantenimiento — Seguidores a un eje TrakLine 1P

> Documento ficticio creado para un proyecto de demostración.

## 1. Descripción del sistema

Los seguidores TrakLine 1P son seguidores horizontales a un eje con configuración de un módulo en vertical (1P). Cada fila soporta 84 módulos y está accionada por un motor de corriente continua de 24 V con reductora sin fin. El rango de giro es de ±55°.

Cada fila tiene un controlador autónomo alimentado por un pequeño panel propio y una batería, de modo que el seguidor puede ir a posición de defensa incluso sin alimentación de red. Los controladores de fila se comunican por radio con un controlador de bloque, que a su vez se conecta al SCADA.

## 2. Algoritmo de seguimiento y backtracking

El seguidor calcula la posición del sol a partir de la fecha, la hora y las coordenadas de la planta. A primera y última hora del día aplica **backtracking**: reduce el ángulo de inclinación para evitar que una fila sombree a la siguiente. Con la separación entre filas de Los Almendros (ratio de cobertura del terreno, GCR, de 0,38) el backtracking se activa con elevaciones solares inferiores a 25° aproximadamente.

En días completamente nublados, el controlador puede activar el modo difuso, que coloca los seguidores en horizontal para maximizar la captación de radiación difusa.

## 3. Posición de defensa por viento

Los seguidores pasan a posición de defensa (stow) en horizontal cuando la velocidad media del viento supera 60 km/h durante 3 segundos o cuando se registran ráfagas superiores a 75 km/h. Vuelven al seguimiento cuando el viento medio se mantiene por debajo de 45 km/h durante 10 minutos.

En caso de nieve acumulada, se utiliza la posición de máxima inclinación (55°) para facilitar el deslizamiento.

## 4. Mantenimiento preventivo semestral

1. **Engrase de rodamientos:** aplicar grasa de litio grado NLGI 2 en cada rodamiento hasta que asome grasa limpia por el retén. Cantidad orientativa: 5 g por rodamiento.
2. **Engrase de la reductora:** verificar el nivel de grasa de la reductora y completar si es necesario.
3. **Consumo del motor:** registrar el consumo durante un giro completo de este a oeste. El valor de referencia es de 1,8 A. Un consumo superior a 2,3 A (130 %) genera la alarma E520 y requiere inspección.
4. **Apriete de tornillería:** verificar par de apriete de las uniones de la viga de torsión a 90 N·m en una muestra del 10 % de las filas.
5. **Inclinómetro:** comparar el ángulo reportado por el controlador con una medida manual. La desviación admisible es de ±1°.
6. **Batería del controlador:** verificar tensión en reposo. Sustituir si es inferior a 12,2 V.

## 5. Averías frecuentes

| Síntoma | Causa probable | Actuación |
|---|---|---|
| Fila parada en posición distinta al resto | Fallo de motor o de controlador | Revisar alarma en SCADA; mover manualmente a stow si hay previsión de viento |
| Consumo del motor elevado | Falta de engrase, rodamiento dañado | Engrasar; sustituir rodamiento si persiste |
| Pérdida de comunicación | Batería del controlador agotada, antena dañada | Revisar batería y antena |
| Desviación de ángulo | Inclinómetro descalibrado | Recalibrar desde el software de configuración |

Una fila bloqueada en una posición distinta a la del resto provoca pérdidas por desalineación y puede generar la alarma W405 de desequilibrio de corriente en el inversor.
