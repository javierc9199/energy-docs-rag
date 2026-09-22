---
title: "Procedimiento de limpieza de módulos — PFV Los Almendros"
doc_type: procedure
synthetic: true
---

# Procedimiento de limpieza de módulos fotovoltaicos

> Documento ficticio creado para un proyecto de demostración.

## 1. Medición de la suciedad

La planta dispone de dos estaciones de medida de suciedad, cada una con una pareja de células de referencia: una se limpia a diario y la otra se deja ensuciar de forma natural. El **ratio de suciedad** es la pérdida relativa de la célula sucia frente a la limpia, promediada en las horas centrales del día.

## 2. Criterio de activación de la limpieza

Se programa una campaña de limpieza cuando el ratio de suciedad supera el **3 %** de forma sostenida durante 5 días, o cuando la previsión económica indica que la energía recuperada en los siguientes 30 días supera el coste de la campaña.

Tras un episodio de calima o polvo sahariano, la pérdida puede superar el 8 % en pocos días. En ese caso se valora una limpieza extraordinaria sin esperar al periodo de 5 días, salvo que haya previsión de lluvia superior a 5 mm en las 72 horas siguientes, ya que la lluvia realiza una limpieza parcial gratuita.

## 3. Métodos de limpieza

### 3.1 Limpieza en seco con robot

Es el método preferente. Los robots de limpieza en seco recorren cada fila con un cepillo de microfibra rotativo sin consumo de agua. Rendimiento orientativo: 1 MWp por robot y jornada.

La limpieza en seco no es eficaz contra excrementos de aves ni contra suciedad cementada por rocío. Esos puntos se tratan con limpieza manual localizada.

### 3.2 Limpieza con agua

Se utiliza agua desmineralizada con una conductividad inferior a 10 µS/cm para evitar depósitos de cal. La presión en la boquilla no debe superar 40 bar y nunca se proyecta agua a menos de 30 cm del módulo.

La limpieza con agua solo se realiza con temperatura de módulo inferior a 40 °C, para evitar el choque térmico sobre el vidrio. En verano esto obliga a trabajar al amanecer o de noche.

### 3.3 Productos prohibidos

Está prohibido el uso de detergentes, disolventes, cepillos metálicos o abrasivos. Dañan el recubrimiento antirreflectante del vidrio y anulan la garantía del fabricante del módulo.

## 4. Seguridad

Las limpiezas nocturnas requieren iluminación de la zona de trabajo y comunicación permanente con el centro de control. Los seguidores de la zona a limpiar se colocan en posición horizontal desde el SCADA antes de empezar, y se bloquea el paso a seguimiento automático durante la campaña.
