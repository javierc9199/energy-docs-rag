---
title: "Manual de Operación y Mantenimiento — PFV Los Almendros"
doc_type: manual
revision: "Rev. 3"
synthetic: true
---

# Manual de Operación y Mantenimiento — Planta Fotovoltaica Los Almendros

> Documento ficticio creado para un proyecto de demostración. No describe ninguna planta real.

## 1. Descripción general de la planta

La Planta Fotovoltaica Los Almendros tiene una potencia pico instalada de 50,4 MWp y una potencia nominal de acceso de 43,2 MWn. Está compuesta por 91.644 módulos bifaciales NovaPanel NP-550B de 550 Wp, agrupados en strings de 28 módulos y montados sobre 1.091 seguidores a un eje TrakLine 1P con orientación norte-sur.

La planta se divide en 14 bloques de potencia. Cada bloque dispone de una estación de potencia con un inversor central Solvanta SV-3150 y un transformador de 3.150 kVA a 30 kV. La energía se evacúa a través de una subestación elevadora 30/132 kV propiedad de la planta.

La relación DC/AC de diseño es de 1,17. El sistema de monitorización SCADA registra datos con una resolución de 5 minutos y los agrega a nivel horario para el cálculo de indicadores.

## 2. Organización y responsabilidades

El equipo de operación en planta está formado por un jefe de planta, dos técnicos eléctricos y un técnico de mantenimiento mecánico. El centro de control remoto supervisa la planta 24 horas al día, 365 días al año.

Cualquier intervención en equipos de media tensión requiere un recurso preventivo presente y la aplicación del procedimiento de consignación descrito en el apartado 6. Las intervenciones en baja tensión DC en horas de irradiancia se consideran trabajos en tensión y solo pueden realizarlas técnicos con habilitación específica.

## 3. Indicadores clave de rendimiento (KPIs)

Los indicadores contractuales de la planta son los siguientes:

- **Performance Ratio (PR)**: objetivo anual del 82,0 %, calculado con irradiancia en plano del módulo corregida por temperatura. Un PR mensual inferior al 78 % obliga a abrir un análisis de causa raíz.
- **Disponibilidad técnica**: objetivo del 99,0 %. Se calcula como el cociente entre las horas en que el inversor está disponible con irradiancia superior a 50 W/m² y el total de horas con irradiancia superior a ese umbral.
- **Tiempo de respuesta ante alarma crítica**: menos de 4 horas desde la notificación del centro de control.
- **Tiempo de resolución de fallo de inversor**: menos de 48 horas, salvo espera de repuestos.

Las pérdidas por indisponibilidad se imputan al mantenedor cuando la causa es un fallo de equipo o un incumplimiento del plan de mantenimiento, y al propietario cuando la causa es una restricción de red o una orden del operador del sistema.

## 4. Mantenimiento preventivo

### 4.1 Calendario de mantenimiento preventivo

| Equipo | Tarea | Frecuencia |
|---|---|---|
| Módulos | Inspección visual de roturas, delaminación y puntos calientes | Trimestral |
| Módulos | Termografía aérea con dron | Anual (primavera) |
| Módulos | Limpieza | Según umbral de suciedad (ver documento de limpieza) |
| Inversores | Limpieza y sustitución de filtros de aire | Trimestral |
| Inversores | Revisión de apriete de conexiones de potencia | Anual |
| Inversores | Verificación de ventiladores y sistema de refrigeración | Semestral |
| Seguidores | Engrase de rodamientos y reductora | Semestral |
| Seguidores | Verificación de consumo de motores | Semestral |
| Cajas de string | Revisión de fusibles y termografía | Semestral |
| Transformadores | Análisis de aceite (gases disueltos) | Anual |
| Subestación | Revisión de protecciones | Anual |

### 4.2 Termografía

La termografía anual se realiza con irradiancia superior a 600 W/m² y viento inferior a 25 km/h. Se clasifican como anomalías de severidad alta las diferencias de temperatura superiores a 20 °C respecto a las células adyacentes, y deben corregirse en un plazo máximo de 30 días.

### 4.3 Inversores

La sustitución de filtros de aire del inversor Solvanta SV-3150 debe realizarse cada tres meses, o antes si la alarma W402 de reducción de potencia por temperatura aparece más de tres veces en una semana. El detalle de alarmas y actuaciones está en el documento de códigos de alarma.

## 5. Mantenimiento correctivo

Todo fallo se registra en el sistema de gestión de mantenimiento con un código de incidencia. Los fallos que afecten a más de un bloque de potencia o que provoquen una pérdida estimada superior a 5 MWh se tratan como incidencias mayores y requieren un informe de incidencia con análisis de causa raíz en un plazo de 10 días hábiles.

El stock mínimo de repuestos en almacén incluye: 2 ventiladores de inversor, 1 tarjeta de control de inversor, 60 fusibles de string de 20 A (ampliado desde 40 tras la incidencia INC-2024-017), 1 motor de seguidor y 30 conectores MC4 compatibles.

## 6. Seguridad y consignación

Antes de intervenir en un inversor se aplican las cinco reglas de oro: corte efectivo de todas las fuentes de tensión, bloqueo y señalización de los elementos de corte, verificación de ausencia de tensión, puesta a tierra y en cortocircuito, y delimitación de la zona de trabajo.

En el lado DC, la apertura del seccionador del inversor no elimina la tensión en los strings mientras haya irradiancia. Para trabajar en una caja de string es obligatorio abrir sus fusibles y medir ausencia de tensión en cada entrada.
