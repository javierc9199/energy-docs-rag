---
title: "Códigos de alarma SCADA — Inversores y seguidores"
doc_type: procedure
synthetic: true
---

# Códigos de alarma SCADA — Inversores Solvanta SV-3150 y seguidores TrakLine

> Documento ficticio creado para un proyecto de demostración.

Las alarmas se clasifican en tres niveles: **E** (error, el equipo se detiene), **W** (aviso, el equipo sigue funcionando con limitaciones) e **I** (información). Las alarmas de nivel E se consideran críticas y activan el aviso al técnico de guardia.

## 1. Alarmas de inversor

### E101 — Fallo de aislamiento DC

La resistencia de aislamiento del campo fotovoltaico respecto a tierra es inferior a 50 kΩ. El inversor no se conecta a red mientras persista el fallo.

**Causas habituales:** conector dañado o mal crimpado, cable pelado por roedores, humedad en una caja de string tras lluvia.

**Actuación:**
1. Verificar si la alarma aparece solo por la mañana con rocío y desaparece al secarse. En ese caso, programar inspección sin urgencia.
2. Si persiste con tiempo seco, abrir las entradas DC del inversor una a una para localizar la caja de string afectada.
3. Medir el aislamiento de cada string de la caja con megóhmetro a 1.000 V. Un string con menos de 1 MΩ se considera defectuoso.

### E204 — Sobretensión de red

La tensión de red supera el 110 % de la nominal durante más de 0,2 segundos. El inversor se desconecta y se reconecta automáticamente tras 3 minutos si la tensión vuelve al rango normal.

**Actuación:** si se repite más de 5 veces en un día, comprobar con la distribuidora o el operador de la subestación si hay una incidencia en la red, y revisar la toma del transformador.

### E310 — Fallo de ventilador

Uno o más ventiladores del sistema de refrigeración no alcanzan la velocidad de consigna. El inversor se detiene para evitar sobrecalentamiento.

**Actuación:** sustituir el ventilador afectado con el repuesto del almacén. El tiempo típico de sustitución es de 45 minutos.

### E312 — Sobretemperatura

La temperatura interna supera el límite de seguridad o la temperatura ambiente supera 60 °C. El inversor se desconecta.

**Actuación:** comprobar filtros de aire, ventiladores y obstrucciones en las rejillas. Revisar si la alarma W402 había aparecido en los días anteriores.

### W402 — Reducción de potencia por temperatura

El inversor está limitando su potencia porque la temperatura ambiente supera 50 °C o la temperatura interna es elevada. No es un fallo, pero su aparición frecuente con temperaturas ambiente moderadas indica filtros de aire obstruidos.

**Actuación:** si aparece más de tres veces en una semana con temperatura ambiente inferior a 40 °C, adelantar la sustitución de filtros de aire.

### W405 — Desequilibrio de corriente entre entradas DC

La corriente de una entrada DC se desvía más de un 15 % de la media del resto de entradas. Suele indicar un fusible de string fundido, suciedad localizada o un seguidor bloqueado en posición distinta al resto.

## 2. Alarmas de seguidor

### E501 — Seguidor en posición de defensa por viento

El anemómetro de planta ha registrado una velocidad media de viento superior a 60 km/h durante 3 segundos o ráfagas superiores a 75 km/h. Todos los seguidores pasan a la posición de defensa (stow) en horizontal.

**Actuación:** ninguna. Los seguidores vuelven a seguimiento automáticamente cuando el viento medio baja de 45 km/h durante 10 minutos.

### E520 — Sobreconsumo de motor

El consumo del motor de un seguidor supera el 130 % del valor nominal. Suele deberse a falta de engrase, a un obstáculo mecánico o a un rodamiento dañado.

**Actuación:** inspeccionar el seguidor, revisar engrase de rodamientos y reductora. Si el sobreconsumo persiste tras el engrase, sustituir el motor.

### W530 — Pérdida de comunicación con el seguidor

El controlador de fila no responde al controlador de bloque durante más de 10 minutos. El seguidor queda en su última posición.
