---
title: "Requisitos técnicos de conexión a red y control de planta — PFV Los Almendros"
doc_type: specification
synthetic: true
---

# Requisitos técnicos de conexión a red y control de planta

> Documento ficticio creado para un proyecto de demostración. Los valores ilustran una especificación típica; no sustituyen a la normativa aplicable ni a los procedimientos de operación vigentes.

## 1. Punto de conexión

La planta se conecta a la red de transporte en la posición de 132 kV de la subestación colectora. La capacidad de acceso concedida es de 43,2 MW, que actúa como límite de inyección en el punto de conexión aunque la potencia instalada en inversores sea superior.

El marco regulatorio de referencia para el acceso y la conexión es el Real Decreto 1183/2020, y para la actividad de producción renovable el Real Decreto 413/2014.

## 2. Controlador de planta (PPC)

El controlador de planta (Power Plant Controller, PPC) mide en el punto de conexión y envía consignas a los 14 inversores para cumplir los requisitos de red. Sus funciones son:

- **Limitación de potencia activa:** mantiene la inyección por debajo de los 43,2 MW de capacidad de acceso y aplica las consignas de reducción que envía el operador del sistema.
- **Control de potencia reactiva:** en modo factor de potencia, modo potencia reactiva o modo control de tensión, según la consigna recibida.
- **Control de rampa:** limita la variación de potencia activa al 10 % de la potencia nominal por minuto en arranques y tras la retirada de una limitación.
- **Respuesta en frecuencia:** reduce la potencia activa cuando la frecuencia supera 50,2 Hz, con un estatismo del 5 %.

El PPC debe aplicar una nueva consigna de potencia activa en el punto de conexión en menos de 10 segundos.

## 3. Capacidad de potencia reactiva

En el punto de conexión, la planta debe poder operar con un factor de potencia entre 0,95 inductivo y 0,95 capacitivo cuando inyecta la potencia de acceso. Los inversores Solvanta SV-3150, con un factor de potencia ajustable entre 0,85 inductivo y 0,85 capacitivo, aportan margen suficiente para compensar la potencia reactiva consumida por los transformadores y el cableado de media tensión.

## 4. Huecos de tensión

La planta debe permanecer conectada ante huecos de tensión en el punto de conexión de hasta el 0 % de la tensión nominal durante 150 ms, inyectando corriente reactiva durante el hueco. Esta capacidad la aportan los inversores (función LVRT) y se verifica en la certificación de conformidad del módulo de generación.

## 5. Comunicaciones con el operador del sistema

La planta está adscrita a un centro de control de generación que recibe las consignas del operador del sistema y las transmite al PPC. La telemedida de potencia activa, potencia reactiva y tensión en el punto de conexión se envía en tiempo real con una resolución máxima de 12 segundos.

Las limitaciones de potencia ordenadas por el operador del sistema se registran en el SCADA con su hora de inicio y fin, porque la energía perdida por este motivo no computa como indisponibilidad imputable al mantenedor.
