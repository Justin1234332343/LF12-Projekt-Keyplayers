-- Läuft bei JEDEM Containerstart. Legt den User nur an, wenn er fehlt.
WHENEVER SQLERROR EXIT SQL.SQLCODE
ALTER SESSION SET CONTAINER = FREEPDB1;

DECLARE
  v_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO v_count FROM dba_users WHERE username = 'PROJEKT_LF12';
  IF v_count = 0 THEN
    EXECUTE IMMEDIATE q'[
      CREATE USER PROJEKT_LF12 IDENTIFIED BY "MeinSicheresPasswort123"
      DEFAULT TABLESPACE USERS
      QUOTA UNLIMITED ON USERS
    ]';
    -- Für Dev gewünscht:
    EXECUTE IMMEDIATE 'GRANT DBA TO PROJEKT_LF12';
    -- Falls du lieber minimal willst, stattdessen gezielte Privilegien vergeben.
  ELSE
    -- Passwort bei Bedarf „re-syncen“ (optional):
    EXECUTE IMMEDIATE 'ALTER USER PROJEKT_LF12 IDENTIFIED BY "MeinSicheresPasswort123"';
  END IF;
END;
/
