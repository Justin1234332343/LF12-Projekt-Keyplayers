-- 020-ords_enable_with_retry.sql
ALTER SESSION SET CONTAINER=FREEPDB1;

-- ORA-06598 vermeiden: INHERIT PRIVILEGES-Grants (idempotent)
BEGIN EXECUTE IMMEDIATE 'GRANT INHERIT PRIVILEGES ON USER SYS TO ORDS_METADATA';     EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'GRANT INHERIT PRIVILEGES ON USER SYSTEM TO ORDS_METADATA';  EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'GRANT INHERIT PRIVILEGES ON USER PROJEKT_LF12 TO ORDS_METADATA'; EXCEPTION WHEN OTHERS THEN NULL; END;
/

-- Hilfstabelle für Status (idempotent)
BEGIN
  EXECUTE IMMEDIATE 'CREATE TABLE APPINFO.ORDS_ENABLE_STATUS (ok NUMBER, dt TIMESTAMP DEFAULT SYSTIMESTAMP)';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -955 THEN RAISE; END IF; END;
/

DECLARE
  v_pkg INTEGER;
BEGIN
  -- Ist das ORDS-Package da?
  SELECT COUNT(*) INTO v_pkg
  FROM all_objects
  WHERE owner='ORDS_METADATA' AND object_name='ORDS' AND object_type='PACKAGE';

  IF v_pkg = 0 THEN
    -- ORDS noch nicht installiert -> Retry-Job anlegen/erneuern
    BEGIN
      DBMS_SCHEDULER.DROP_JOB('APPINFO.ORDS_ENABLE_RETRY', TRUE);
    EXCEPTION WHEN OTHERS THEN NULL; END;

    DBMS_SCHEDULER.CREATE_JOB (
      job_name        => 'APPINFO.ORDS_ENABLE_RETRY',
      job_type        => 'PLSQL_BLOCK',
      job_action      => q'[
        DECLARE
          v_ok INTEGER := 0;
          PROCEDURE enable_all IS
          BEGIN
            ORDS.ENABLE_SCHEMA(
              p_enabled             => TRUE,
              p_schema              => 'PROJEKT_LF12',
              p_url_mapping_type    => 'BASE_PATH',
              p_url_mapping_pattern => 'projekt_lf12',
              p_auto_rest_auth      => FALSE
            );

            FOR t IN (SELECT table_name FROM all_tables WHERE owner='PROJEKT_LF12') LOOP
              BEGIN
                ORDS.ENABLE_OBJECT(
                  p_enabled      => TRUE,
                  p_schema       => 'PROJEKT_LF12',
                  p_object       => t.table_name,
                  p_object_type  => 'TABLE',
                  p_object_alias => LOWER(t.table_name)
                );
              EXCEPTION WHEN OTHERS THEN NULL;
              END;
            END LOOP;

            COMMIT;
            v_ok := 1;
          EXCEPTION WHEN OTHERS THEN
            v_ok := 0;
          END;
        BEGIN
          enable_all;
          INSERT INTO APPINFO.ORDS_ENABLE_STATUS(ok) VALUES (v_ok);
          COMMIT;
          IF v_ok = 1 THEN
            DBMS_SCHEDULER.DROP_JOB('APPINFO.ORDS_ENABLE_RETRY');
          END IF;
        END;
      ]',
      start_date      => SYSTIMESTAMP + INTERVAL '30' SECOND,
      repeat_interval => 'FREQ=MINUTELY;INTERVAL=1',
      enabled         => TRUE,
      auto_drop       => FALSE
    );

  ELSE
    -- ORDS ist da -> sofort enablen (idempotent)
    ORDS.ENABLE_SCHEMA(
      p_enabled             => TRUE,
      p_schema              => 'PROJEKT_LF12',
      p_url_mapping_type    => 'BASE_PATH',
      p_url_mapping_pattern => 'projekt_lf12',
      p_auto_rest_auth      => FALSE
    );

    FOR t IN (SELECT table_name FROM all_tables WHERE owner='PROJEKT_LF12') LOOP
      BEGIN
        ORDS.ENABLE_OBJECT(
          p_enabled      => TRUE,
          p_schema       => 'PROJEKT_LF12',
          p_object       => t.table_name,
          p_object_type  => 'TABLE',
          p_object_alias => LOWER(t.table_name)
        );
      EXCEPTION WHEN OTHERS THEN NULL;
      END;
    END LOOP;

    INSERT INTO APPINFO.ORDS_ENABLE_STATUS(ok) VALUES (1);
    COMMIT;
  END IF;
END;
/
