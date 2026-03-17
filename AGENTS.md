# AGENTS.md

Archivo operativo unico para agentes AI en Dragofactu.

Este archivo no reemplaza la documentacion principal: la consolida para evitar divergencias.

## Orden de lectura obligatorio

1. `CLAUDE.md`  
Contexto operativo esencial, stack, estado del proyecto, comandos y patrones.

2. `MEMORIA_LARGO_PLAZO.md`  
Historial de sesiones, decisiones tecnicas y trazabilidad de cambios.

3. `PLAN_FRONTEND.md`  
Plan y estado detallado del frontend web (fases 19-25).

## Reglas de trabajo

1. No asumir contenido: leer archivos antes de modificar.
2. No romper produccion: backend desplegado en Railway, cambios con cuidado y tests.
3. Mantener contratos API: backend como fuente de verdad para desktop y web.
4. Commits pequenos y trazables: una feature/fix por commit.
5. Documentar cambios sustanciales en formato consistente:
- `CLAUDE.md` (resumen operativo)
- `MEMORIA_LARGO_PLAZO.md` (registro historico)
- `PLAN_FRONTEND.md` (si afecta frontend)

## Definition of Done minima

1. Codigo funcional y sin regresiones obvias.
2. Validacion tecnica ejecutada:
- Backend: `cd backend && python -m pytest tests/ -v`
- Frontend: `cd frontend && npm run type-check && npm run build`
- E2E base: `cd frontend && npm run test:e2e`
3. Documentacion actualizada en los archivos anteriores cuando aplique.
4. Sin artefactos generados en el repo (`.pyc`, `.DS_Store`, build cache, secretos).

## Higiene y seguridad del repositorio

1. No versionar secretos ni archivos de entorno reales.
2. Mantener `.env.example` como plantilla publica.
3. No versionar llaves privadas, tokens, certificados o credenciales.
4. No versionar binarios generados por ejecucion local.

## Notas de arquitectura

1. Convivencia legacy/modular:
- `dragofactu_complete.py` existe por compatibilidad/historial.
- Preferir desarrollo sobre estructura modular `dragofactu/` y no ampliar monolito salvo necesidad.

2. Modo hibrido desktop:
- Si hay acceso a datos en desktop, considerar modo local/remoto y cache offline.

3. Multi-tenancy:
- Respetar `company_id` y filtros por tenant en backend.
