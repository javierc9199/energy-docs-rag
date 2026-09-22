---
title: "Protocolo de pruebas de puesta en marcha — PFV Los Almendros"
doc_type: protocol
synthetic: true
---

# Protocolo de pruebas de puesta en marcha

> Documento ficticio creado para un proyecto de demostración.

## 1. Objeto

Este protocolo define las pruebas que deben superarse antes de la recepción provisional de la planta. Las pruebas se ejecutan por bloque de potencia y sus resultados se registran en las hojas de prueba del anexo.

## 2. Pruebas en frío (sin tensión de red)

### 2.1 Continuidad y polaridad de strings

Se verifica la polaridad de cada string en la caja de string antes de insertar los fusibles. Un string con polaridad invertida puede dañar el resto de strings conectados en paralelo.

### 2.2 Tensión en circuito abierto (Voc)

Se mide la tensión en circuito abierto de cada string y se compara con el valor teórico corregido por temperatura de módulo. La tolerancia admisible es de ±3 %. Una desviación mayor suele indicar un módulo de menos en el string o un diodo de bypass defectuoso.

### 2.3 Resistencia de aislamiento

Se mide el aislamiento de cada string respecto a tierra con megóhmetro a 1.000 V DC durante 1 minuto. El valor mínimo aceptable es de 40 MΩ por string en la puesta en marcha. Este criterio es más exigente que el umbral de alarma E101 del inversor, que se activa por debajo de 50 kΩ para el campo completo.

### 2.4 Resistencia de puesta a tierra

La resistencia de la red de tierras de cada estación de potencia debe ser inferior a 10 Ω. La de la subestación debe ser inferior a 1 Ω.

## 3. Pruebas en caliente

### 3.1 Curvas I-V

Se trazan las curvas I-V de una muestra del 5 % de los strings de cada bloque con irradiancia superior a 700 W/m². La potencia medida, corregida a condiciones estándar, no debe ser inferior al 97 % de la potencia nominal del string.

### 3.2 Prueba funcional del inversor

Se verifican el arranque, la parada, la respuesta a consignas de potencia activa y reactiva del controlador de planta y la actuación de las protecciones de tensión y frecuencia.

### 3.3 Prueba funcional de seguidores

Se comprueba el seguimiento, el backtracking y la orden de posición de defensa desde el SCADA en el 100 % de las filas.

## 4. Prueba de rendimiento

La prueba de rendimiento dura 7 días consecutivos con la planta a plena disponibilidad. El Performance Ratio medido durante la prueba, corregido por temperatura, debe ser igual o superior al 80,5 %. Si durante la prueba la disponibilidad cae por debajo del 98 %, la prueba se reinicia.

Se excluyen del cálculo los periodos con limitación de potencia por orden del operador del sistema y los periodos con irradiancia inferior a 200 W/m².

## 5. Criterios de recepción

La recepción provisional se firma cuando se han superado todas las pruebas y no queda ninguna reserva de categoría A (que afecte a la seguridad o a la producción). Las reservas de categoría B deben resolverse en un plazo de 90 días desde la recepción provisional.
