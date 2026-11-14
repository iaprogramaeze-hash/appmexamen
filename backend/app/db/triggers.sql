-- analisis.txt 1.6 [CORREGIDO]: updated_at NO puede vivir en DEFAULT porque
-- DEFAULT sólo se evalúa al INSERT y la columna queda congelada. El trigger la
-- refresca en cada UPDATE, para cualquier cliente (API, migraciones, SQL directo).
CREATE OR REPLACE FUNCTION trg_set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Cada tabla con updated_at adjunta su propio trigger (lo materializa su
-- migración, una tabla por revisión):
--
--   CREATE TRIGGER set_updated_at BEFORE UPDATE ON {tabla}
--   FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();
