"""
Configuración de la instalación.

Cada cliente recibe su propia instalación de Prisma con el enfoque que le corresponde.
El enfoque se elige aquí (o con la variable de entorno PRISMA_ENFOQUE) antes de instalar:

    "general"     → versión general: sirve para cualquier organización (la que viene por defecto)
    "territorio"  → enfoque territorial (desarrollo rural, gobiernos locales, organizaciones sociales)
    "cadena"      → enfoque empresarial: empresa compradora de cacao y café
    "industrial"  → enfoque empresarial: empresa industrial con planta y logística

Para cambiarlo en una instalación ya creada hay que borrar prisma_territorial.db (se pierden los datos).
"""
import os

ENFOQUE = os.environ.get("PRISMA_ENFOQUE", "general")
