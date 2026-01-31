# DRAGOFACTU - Sistema de Gestion Empresarial

**Version:** 1.0.0.7
**Estado:** Estable
**Stack:** Python 3.10+ / PySide6 / SQLAlchemy / SQLite

---

## Screenshots

<!-- TODO: Añadir screenshots actualizados -->

---

## Que es Dragofactu

ERP de escritorio para gestion empresarial:
- Facturacion (presupuestos, facturas, albaranes)
- Inventario con alertas de stock
- Gestion de clientes y proveedores
- Gestion de trabajadores y formacion
- Diario personal
- Multi-idioma (ES/EN/DE)

---

## Instalacion Rapida

```bash
# Clonar repositorio
git clone https://github.com/Copitx/Dragofactu.git
cd Dragofactu

# Ejecutar (instalacion automatica)
./start_dragofactu.sh
```

**Primera ejecucion:** El launcher preguntara donde instalar:
```
DRAGOFACTU - First Time Setup
Default installation directory: ~/.dragofactu
Use default location? [Y/n/custom path]:
```

**Credenciales por defecto:** `admin` / `admin123`

---

## Estructura del Proyecto

```
Dragofactu/                    # Codigo fuente (11MB)
├── start_dragofactu.sh        # Entry point
├── launch_dragofactu_fixed.py # Launcher configurable
├── dragofactu_complete.py     # App monolitica
├── dragofactu/                # Paquete modular
│   ├── models/                # SQLAlchemy ORM
│   ├── services/              # Logica de negocio
│   ├── ui/                    # PySide6 views
│   └── config/                # Configuracion
└── scripts/                   # Utilidades

~/.dragofactu/                 # Datos de usuario (separado)
├── venv/                      # Virtual environment
├── data/
│   └── dragofactu.db          # Base de datos
├── exports/                   # Exportaciones
└── attachments/               # Adjuntos
```

---

## Changelog

### v1.0.0.7 (2026-01-31) - Clean Repo Structure

**Limpieza del repositorio:**
- Reducido tamano de 457MB a 11MB
- Eliminado `venv/` del historial de git (commiteado por error)
- Creado `.gitignore` completo
- Eliminados 15 archivos obsoletos (launchers duplicados, backups, tests)

**Nuevo sistema de instalacion:**
- El launcher pregunta ubicacion en primera ejecucion
- Por defecto instala en `~/.dragofactu/`
- Codigo fuente separado de datos de usuario
- Configuracion guardada en `~/.dragofactu_config.json`

**Archivos eliminados:**
- `launch_dragofactu.py`, `launch_simple.py`, `launch_final.py`
- `simple_dragofactu_app.py`, `simple_dragofactu_app_fixed.py`
- `complete_dragofactu_app.py`, `dragofactu_complete_backup.py`
- `debug_main.py`, `test_*.py`, `run.py`, `start_fixed.py`
- `dashboard_view_fixed.py`, `inventory_view_fixed.py`

### v1.0.0.6 (2026-01-13) - UI Redesign

- Sistema de diseno Apple-inspired
- Clase `UIStyles` centralizada
- Paleta de colores consistente (#007AFF accent)
- Menus sin emojis + keyboard shortcuts
- Dashboard con metricas y quick actions

### v1.0.0.5 - Visual Interface

- Pequenos cambios en interfaz visual

### v1.0.0.4 - CRUD & Stability

- CRUD completo implementado
- Fix critico: Import error en `inventory_service.py`
- Fix: Syntax error en launcher
- Seguridad: Credenciales basadas en env vars
- Arquitectura: Launcher unificado

### v1.0.0.3 - Core Features

- Dashboard principal estable
- Gestion de clientes/productos/documentos
- Sistema multi-idioma
- Configuracion funcional

### v1.0.0.2 - Session Fix

- Fix critico: DetachedInstanceError en SQLAlchemy
- Pre-extraccion de datos de usuario en LoginDialog

### v1.0.0.1 - v1.0.0 - Initial Release

- Version inicial con estructura modular

---

## Funcionalidades

| Modulo | Estado | Descripcion |
|--------|--------|-------------|
| Dashboard | Estable | Metricas, acciones rapidas, docs recientes |
| Clientes | Estable | CRUD completo, busqueda, import/export |
| Productos | Estable | CRUD, control stock, alertas |
| Documentos | Estable | Presupuestos, facturas, albaranes |
| Inventario | Estable | Stock en tiempo real, movimientos |
| Diario | Estable | Notas diarias, etiquetas |
| Trabajadores | Estable | CRUD, cursos, formacion |
| Config | Estable | Preferencias, idioma, tema |

---

## Configuracion

### Variables de Entorno (.env)

```bash
DATABASE_URL=sqlite:///dragofactu.db
DEBUG=false
SECRET_KEY=tu-clave-secreta-32-chars
DEFAULT_LANGUAGE=es
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
```

### Ubicacion de Datos

El launcher usa `~/.dragofactu/` por defecto. Para cambiar:

```bash
# Eliminar config actual
rm ~/.dragofactu_config.json

# Ejecutar de nuevo (preguntara ubicacion)
./start_dragofactu.sh
```

---

## Desarrollo

```bash
# Activar entorno
source ~/.dragofactu/venv/bin/activate

# Ejecutar directamente
python3 dragofactu_complete.py

# Reset base de datos
rm ~/.dragofactu/data/dragofactu.db
python3 scripts/init_db.py
```

---

## Stack Tecnologico

- **GUI:** PySide6 (Qt6)
- **ORM:** SQLAlchemy 2.0
- **DB:** SQLite (dev) / PostgreSQL (prod)
- **Auth:** bcrypt + JWT
- **PDF:** ReportLab
- **i18n:** JSON translations (es/en/de)

---

## Licencia

MIT License

---

**Desarrollado por DRAGOFACTU Team**
