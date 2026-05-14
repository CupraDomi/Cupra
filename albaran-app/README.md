# Gestión de Albaranes — Maquinaria y Obras

Aplicación web interna para gestionar el alquiler de maquinaria de obra pública: albaranes, clientes y flota.

---

## Puesta en marcha

```bash
# 1. Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Poblar la base de datos con datos de ejemplo
python seed.py

# 3. Arrancar la aplicación
python run.py
# → http://localhost:5000
```

Para personalizar la empresa, edita `config.py` o define variables de entorno:
- `COMPANY_NAME`, `COMPANY_ADDRESS`, `COMPANY_PHONE`, `COMPANY_EMAIL`, `COMPANY_CIF`

---

## Sistema de códigos de máquina

### Formato: `CATEGORIA-VARIANTE-NNN`

- **CATEGORIA** — código de 2-3 letras (ver tabla abajo)
- **VARIANTE** — subtipo opcional (energía, tonelaje, potencia…)
- **NNN** — número secuencial de 3 dígitos por categoría (`001`, `002`…)

### Leyenda completa

| Código | Categoría | Variantes | Ejemplos |
|--------|-----------|-----------|---------|
| `AWP` | Plataforma Elevadora *(Aerial Work Platform)* | `D` = Diésel · `E` = Eléctrica | `AWP-D-001`, `AWP-E-003` |
| `FLT` | Carretilla Elevadora *(Forklift)* | `D` = Diésel · `E` = Eléctrica | `FLT-D-002`, `FLT-E-001` |
| `DMP` | Dúmper | `[N]T` = toneladas · `R-[N]T` = con raíles de vía | `DMP-6T-001`, `DMP-R-3T-001` |
| `EXC` | Excavadora | `[N]T` = toneladas de la máquina | `EXC-3T-001`, `EXC-20T-001` |
| `TLH` | Manipulador Telescópico *(Telehandler)* | `[N]M` = alcance máximo en metros | `TLH-17M-001`, `TLH-25M-001` |
| `RTH` | Martillo de Vía *(Rail Track Hammer)* | *(sin variante)* | `RTH-001`, `RTH-002` |
| `GEN` | Grupo Electrógeno | `[NNN]K` = potencia en kVA (3 dígitos, ceros a la izquierda) | `GEN-005K-001`, `GEN-045K-001`, `GEN-500K-001` |
| `TOL` | Herramienta / Accesorio *(Tool)* | etiqueta libre en mayúsculas | `TOL-COMPACTOR-001`, `TOL-PUMP-002` |

### Reglas de asignación

1. Cada categoría tiene su propia secuencia independiente.
2. El número siempre va con **3 dígitos** (`001`, no `1`).
3. En generadores, el kVA se rellena con ceros por la izquierda para que ordenen correctamente: `005K` < `045K` < `100K` < `500K`.
4. El código **nunca cambia** aunque la máquina se venda o retire; simplemente se marca como inactiva en las notas.

### Añadir una nueva categoría

1. Elige un prefijo de 2-4 letras no usado (revisa la tabla).
2. Añádelo a la lista `CATEGORIES` en `app/routes/dashboard.py` y `app/routes/machines.py`.
3. La secuencia empieza en `001` para esa categoría.
4. Actualiza esta tabla en el README.

---

## Sistema de códigos de cliente

### Formato: `C-ABBREV-NNN`

- `C` — prefijo fijo que identifica que es un cliente
- `ABBREV` — abreviatura de 3-6 letras en mayúsculas derivada del nombre
- `NNN` — número secuencial de 3 dígitos **por abreviatura**

### Reglas de derivación de la abreviatura

| Tipo | Regla | Ejemplo |
|------|-------|---------|
| Empresa | Primera palabra significativa del nombre (sin S.L., S.A., S.L.U., Grupo…) | Ferrovial Construcción S.A. → `FERRO` |
| Autónomo | Primer apellido | García Martínez, Pedro → `GARCIA` |

La aplicación sugiere la abreviatura automáticamente al escribir el nombre; el administrativo puede corregirla antes de guardar.

Si ya existe `C-GARCIA-001`, el siguiente García recibe `C-GARCIA-002`. Los códigos son únicos y no se reasignan.

### Ejemplos reales

| Cliente | Código |
|---------|--------|
| Ferrovial Construcción S.A. | `C-FERRO-001` |
| Acciona Infraestructuras S.A. | `C-ACCIONA-001` |
| García Martínez, Pedro (autónomo) | `C-GARCIA-001` |
| Vías y Construcciones S.L. | `C-VIAS-001` |
| Obras Públicas Levante S.L.U. | `C-OBRAS-001` |

---

## Albaranes

Numeración automática: `ALB-AAAA-NNNN` (año + 4 dígitos secuenciales).

### Modalidades de precio

| Modalidad | Cuándo usarla | Cómo funciona |
|-----------|---------------|---------------|
| **Precio cerrado** | Cuando se conoce la duración y se negocia un total fijo | Se introduce el total al crear el albarán; no cambia al cerrar |
| **Precio abierto** | Cuando la fecha de fin es incierta | Se introduce una tarifa (por día / semana / mes); el total se calcula al cerrar según la duración real |

---

## Estructura del proyecto

```
albaran-app/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Modelos SQLAlchemy
│   ├── pdf_generator.py     # Generación PDF con ReportLab
│   ├── routes/
│   │   ├── dashboard.py     # / — vista de flota
│   │   ├── machines.py      # /machines
│   │   ├── clients.py       # /clients
│   │   └── albaranes.py     # /albaranes
│   ├── templates/           # Jinja2
│   └── static/              # CSS + JS
├── seed.py                  # Datos de ejemplo
├── run.py                   # Punto de entrada
├── config.py                # Configuración
└── requirements.txt
```

---

## Autenticación

No implementada por ahora. La estructura está preparada para añadirla: todas las rutas pasan por blueprints registrados en el app factory (`app/__init__.py`), por lo que basta con añadir Flask-Login y decorar las rutas con `@login_required`.
