# TURF API – Go-Ideas
API ligera y optimizada para ejecutar análisis TURF (Total Unduplicated Reach & Frequency) a partir de cualquier combinación de SKUs seleccionada desde Excel u otra aplicación externa.

Esta API permite:
- Calcular **Reach** de forma automática.
- Calcular **Frequency** entre los productos elegidos.
- Calcular **Incremental Reach (Delta)** a medida que se agregan SKUs.
- Integrarse directamente con **Excel**, **Power BI**, **Google Sheets** o cualquier cliente HTTP.

La API está pensada para entregables a clientes donde ellos mismos pueden elegir SKUs y obtener resultados en tiempo real sin necesidad de Python local.

---

## 🚀 Características principales

- **Rápida**: FastAPI asegura respuestas en milisegundos.
- **Integración directa con Excel** mediante `WEBSERVICE()` o Power Query.
- **Sin costo**: puede correr localmente o en un servicio gratuito.
- **Seguro**: opcionalmente se puede activar autenticación JWT.
- **Ideal para simuladores** donde el cliente selecciona combinaciones de SKUs.

---

## 📁 Estructura del proyecto

