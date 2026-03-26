# PLAN_DESKTOP_UI_PARITY.md

> Ultima actualizacion: 2026-03-26
> Estado: En ejecucion (aprobado)
> Objetivo: Lograr paridad visual y de experiencia entre Desktop (PySide6) y Web App (React) sin perder modo offline.

---

## 1) Objetivo y criterio de exito

### Objetivo principal
Conseguir que la app desktop sea visualmente equivalente a la web app desplegada, con el mismo lenguaje de interfaz, navegacion, jerarquia visual, componentes y feedback de estado.

### Criterio de exito (Definition of Match)
Se considera paridad alcanzada cuando:

1. Navegacion principal desktop refleja el mismo arbol de secciones que web.
2. Cada pantalla desktop tiene estructura y comportamiento UI equivalente a su pantalla web.
3. Tokens visuales (color, espaciado, radio, tipografia, estados) son consistentes entre clientes.
4. No hay regresion funcional en modo local/remoto/offline.
5. Checklist de paridad por modulo esta en verde.

---

## 2) Alcance

### En alcance

1. Shell de aplicacion desktop (sidebar/header/content) con estructura equivalente a web.
2. Refactor visual de componentes base (botones, inputs, tablas, dialogs, badges, cards, toasts).
3. Paridad UI por modulo:
- Dashboard
- Clients
- Products
- Suppliers
- Documents
- Inventory
- Workers
- Diary
- Reminders
- Reports
- Audit
- Settings
- Admin
4. Estados UX equivalentes:
- loading
- empty
- error
- success
- offline/cache/sync
5. Validacion visual y funcional por fase.

### Fuera de alcance (de momento)

1. Reescritura completa de logica de negocio backend.
2. Cambios de contrato API sin necesidad.
3. Rebranding radical distinto al lenguaje visual actual web.

---

## 3) Decision tecnica de runtime

### Situacion actual
El launcher de escritorio prioriza actualmente el entrypoint monolitico (`dragofactu_complete.py`) antes que el modular.

### Decision adoptada
Trabajar en enfoque modular como destino final y controlar compatibilidad legacy durante la migracion.

### Regla operativa
1. Todo desarrollo nuevo de UI debe caer en `dragofactu/` modular.
2. El monolito queda en mantenimiento minimo solo para no romper arranque actual hasta switch final.
3. El switch de prioridad de entrypoint se ejecuta cuando la cobertura de modulos en modular cumpla los checkpoints definidos.

---

## 4) Fases de ejecucion (checkpoints)

## Fase 0 - Baseline y contrato de paridad

### Objetivo
Congelar referencia web y matriz de comparacion desktop/web.

### Entregables
1. Inventario de pantallas web objetivo y equivalente desktop.
2. Matriz de gap por pantalla (layout, componentes, interacciones, estados).
3. Checklist de paridad versionada en este archivo.

### Checkpoint de cierre
1. Existe matriz completa por modulo.
2. Existe criterio de aceptacion por pantalla.
3. Existe orden de implementacion confirmado.

### Estado de ejecucion Fase 0 (2026-03-26)

- Estado: COMPLETADA
- Evidencia estructurada: `docs/desktop_ui_parity_phase0_matrix.csv`
- Fuentes base usadas para inventario:
	- Web shell/routes: `frontend/src/components/layout/sidebar.tsx`, `frontend/src/App.tsx`
	- Desktop modular: `dragofactu/ui/views/main_window.py`
	- Desktop legacy: `dragofactu_complete.py`

### Inventario baseline desktop vs web

1. Cobertura web objetivo (13 superficies):
- `/`
- `/clients`
- `/products`
- `/suppliers`
- `/documents` (lista/nuevo/detalle)
- `/inventory`
- `/workers`
- `/diary`
- `/reminders`
- `/reports`
- `/audit`
- `/settings`
- `/admin`

2. Cobertura desktop modular actual (wired en ventana principal):
- Dashboard
- Documents
- Clients
- Inventory
- Diary

3. Cobertura desktop legacy actual (tabs/diaglogos):
- Dashboard
- Clients
- Products
- Documents
- Inventory
- Diary
- Workers
- Settings (dialog)
- Reminders (parcial en dashboard)
- Reports (parcial como accion/export)

### Gaps detectados (priorizados)

1. Criticos:
- Shell de navegacion desktop no replica estructura web (sidebar/header/routing).
- Faltan modulos dedicados equivalentes a web: Products (modular), Suppliers, Reminders, Reports, Audit.

2. Altos:
- Documents desktop no separa claramente flujo lista/nuevo/detalle como web.
- Settings/Admin desktop no estan como superficies equivalentes (pagina), sino parcial/dialog.
- Workers modular existe pero no esta integrado en la navegacion principal modular.

3. Medios:
- Diferencias de densidad visual, jerarquia y comportamiento de tablas/filtros en modulos ya presentes.

### Criterios de aceptacion por pantalla (contrato binario)

Para cada modulo se considera aprobado solo si cumple todos:

1. Navegacion: entrada visible en mismo orden funcional que web (segun rol).
2. Jerarquia: misma estructura de bloques principales (header, acciones, filtros, tabla/lista, detalles).
3. Componentes: equivalencia visual de botones, campos, tablas, badges, dialogs.
4. Estados: loading, empty, error y success consistentes.
5. Acciones: mismas acciones primarias/secundarias en ubicacion equivalente.
6. Feedback: mensajes y confirmaciones con severidad y tono equivalente.
7. Accesibilidad operativa: foco visible y navegacion por teclado usable.
8. i18n: etiquetas del modulo en es/en/de sin regresion.
9. Permisos: visibilidad/acciones por rol respetadas.
10. Integridad: no rompe modo local/remoto/offline.

### Orden de implementacion confirmado tras baseline

1. Fase 1: Design Tokens + componentes base.
2. Fase 2: Shell de aplicacion (sidebar/header/content).
3. Fase 3: Core (Dashboard, Clients, Products, Suppliers, Documents).
4. Fase 4: Operativos (Inventory, Workers, Diary, Reminders).
5. Fase 5: Analiticos/Admin (Reports, Audit, Settings, Admin).
6. Fase 6: Offline UX parity.
7. Fase 7: Switch final a modular y estabilizacion.

---

## Fase 1 - Design Tokens y componentes base

### Objetivo
Unificar sistema visual desktop con tokens equivalentes a web.

### Entregables
1. Tokens desktop documentados y aplicados globalmente.
2. Componentes base desktop alineados con web:
- button
- input/select/textarea
- badge
- card
- dialog
- table + pagination
- toast/alerts
3. Estados hover/focus/disabled/error consistentes.

### Checkpoint de cierre
1. Pantalla demo interna de componentes desktop validada.
2. Contrastes y estados minimos verificados.

### Avance inicial Fase 1 (2026-03-26)

1. Activado stylesheet global en runtime modular via `dragofactu/main.py`.
2. Eliminado override local de estilos en `dragofactu/ui/views/main_window.py` para evitar divergencia de tokens.
3. Ajustados tokens base en `dragofactu/ui/styles.py` para acercarlos al sistema web (base font y radio medio).
4. Pendiente para cierre Fase 1:
- Demo de componentes equivalente y validada.
- Verificacion final de estados hover/focus/disabled/error en formularios y tablas.

---

## Fase 2 - Shell de aplicacion

### Objetivo
Eliminar diferencias estructurales de navegacion.

### Entregables
1. Sidebar desktop equivalente a web (orden, iconos, estado activo, colapso).
2. Header equivalente (contexto de pagina, usuario, acciones globales).
3. Area de contenido desacoplada para render por modulo.

### Checkpoint de cierre
1. Navegacion desktop replica arbol de rutas web.
2. No se rompen permisos por rol.

---

## Fase 3 - Modulos core (negocio diario)

### Objetivo
Alinear los modulos de uso mas frecuente.

### Orden
1. Dashboard
2. Clients
3. Products
4. Suppliers
5. Documents

### Checkpoint de cierre
1. Cada modulo pasa checklist visual + funcional.
2. Sin regresiones en CRUD ni estados de documento.

---

## Fase 4 - Modulos operativos

### Objetivo
Alinear operativa interna completa.

### Orden
1. Inventory
2. Workers
3. Diary
4. Reminders

### Checkpoint de cierre
1. Flujos principales operativos con UI equivalente.
2. Estados de warning/stock/prioridad consistentes.

---

## Fase 5 - Modulos analiticos y administracion

### Objetivo
Cerrar paridad de areas avanzadas.

### Orden
1. Reports
2. Audit
3. Settings
4. Admin

### Checkpoint de cierre
1. Dashboards/reportes con jerarquia visual alineada.
2. Ajustes/admin con controles y feedback equivalentes.

---

## Fase 6 - Offline UX parity

### Objetivo
Mantener ventaja offline desktop sin romper paridad UX.

### Entregables
1. Estados visuales claros para cache y cola pendiente.
2. Indicadores de reconexion/sincronizacion integrados en diseño.
3. Mensajeria consistente con web donde aplique.

### Checkpoint de cierre
1. Pruebas de desconexion/reconexion superadas.
2. Operaciones pendientes visibles y comprensibles para usuario.

---

## Fase 7 - Switch final y estabilizacion

### Objetivo
Completar migracion de referencia y cerrar deuda legacy.

### Entregables
1. Ajuste de prioridad de entrypoint a modular (cuando cumpla cobertura).
2. Hardening final de estilos, accesibilidad y UX.
3. Documentacion sincronizada final.

### Checkpoint de cierre
1. Paridad validada en toda la matriz.
2. Sin regresiones funcionales criticas.
3. Merge listo con evidencia de pruebas.

---

## 5) Checklist de paridad por modulo

Usar esta checklist para cada modulo. Debe estar en verde antes de marcar fase como cerrada.

### Identidad visual

- [ ] Paleta de color equivalente
- [ ] Tipografia y pesos consistentes
- [ ] Espaciado y densidad equivalentes
- [ ] Radios/bordes/sombras equivalentes

### Estructura y layout

- [ ] Misma jerarquia de bloques
- [ ] Mismo orden de acciones principales/secundarias
- [ ] Responsive desktop (ventanas pequenas/medias/grandes) sin degradacion visual

### Componentes

- [ ] Tabla equivalente (cabecera, filas, hover, seleccion)
- [ ] Filtros/buscador equivalentes
- [ ] Formularios equivalentes (labels, validaciones, errores)
- [ ] Dialogos/confirmaciones equivalentes
- [ ] Badges/estados equivalentes

### Estados UX

- [ ] Loading state equivalente
- [ ] Empty state equivalente
- [ ] Error state equivalente
- [ ] Success feedback equivalente
- [ ] Offline/cache/sync state claro y consistente

### Integridad funcional

- [ ] CRUD principal estable
- [ ] Permisos por rol respetados
- [ ] Traducciones sin regresion (es/en/de)

---

## 6) Matriz de pruebas obligatorias

## A. Pruebas por cambio de UI desktop

1. Arranque desktop:
```bash
source venv/bin/activate
python3 dragofactu_complete.py
```

2. Flujo local y remoto del modulo afectado.
3. Verificar que no rompe cache offline ni operation queue.

## B. Pruebas de integracion (obligatorias por bloque)

1. Backend:
```bash
cd backend && python -m pytest tests/ -v
```

2. Frontend:
```bash
cd frontend && npm run type-check && npm run build
```

3. E2E base:
```bash
cd frontend && npm run test:e2e
```

## C. Pruebas de seguridad/auth si aplica

1. Login-refresh-logout web y desktop.
2. Sin secretos ni credenciales en logs.
3. Sin romper aislamiento multi-tenant (`company_id`).

---

## 7) Criterio de salida por fase

Una fase solo se marca como completada cuando:

1. Checklist del alcance en verde.
2. Tests obligatorios del bloque ejecutados.
3. Evidencia minima registrada (comandos y resultado resumen).
4. Documentacion actualizada en:
- `PLAN_DESKTOP_PYTHON.md`
- `CLAUDE.md`
- `MEMORIA_LARGO_PLAZO.md`

---

## 8) Riesgos y mitigaciones

1. Riesgo: Doble mantenimiento monolito/modular.
- Mitigacion: desarrollo nuevo solo modular + freeze funcional en legacy.

2. Riesgo: Regresion offline UX por foco visual.
- Mitigacion: fase dedicada offline parity + pruebas de reconexion.

3. Riesgo: Deriva entre web y desktop tras futuras features.
- Mitigacion: checklist de paridad como gate obligatorio por modulo.

4. Riesgo: Cambios UI que rompan permisos por rol.
- Mitigacion: validacion por roles en cada fase.

---

## 9) Estado de ejecucion

- [x] Plan aprobado por usuario
- [x] Archivo de plan/checkpoints/checklist/tests creado
- [x] Fase 0 iniciada
- [x] Fase 0 completada
- [x] Fase 1 iniciada
- [ ] Fase 2 iniciada
- [ ] Fase 3 iniciada
- [ ] Fase 4 iniciada
- [ ] Fase 5 iniciada
- [ ] Fase 6 iniciada
- [ ] Fase 7 iniciada

---

## 10) Notas para agentes

1. No asumir UI parity por intuicion: comparar siempre con web real.
2. No mezclar fases: cerrar una antes de abrir la siguiente.
3. No romper contratos API.
4. Commits pequenos por modulo/componente.
5. Mantener este archivo como fuente operativa de seguimiento.
