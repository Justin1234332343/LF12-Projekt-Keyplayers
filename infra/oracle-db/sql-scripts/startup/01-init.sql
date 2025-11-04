-- 1) In PDB wechseln
ALTER SESSION SET CONTAINER=FREEPDB1;

-- 2) Marker-Schema + Tabelle (falls noch nicht vorhanden)
BEGIN
  EXECUTE IMMEDIATE 'CREATE USER appinfo IDENTIFIED BY "Tmp#1" QUOTA UNLIMITED ON users';
  EXECUTE IMMEDIATE 'GRANT CONNECT, RESOURCE TO appinfo';
EXCEPTION
  WHEN OTHERS THEN
    -- ORA-01920: user name conflicts with another user or role name
    IF SQLCODE != -1920 THEN RAISE; END IF;
END;
/
BEGIN
  EXECUTE IMMEDIATE 'CREATE TABLE appinfo.init_done (flag NUMBER PRIMARY KEY)';
EXCEPTION
  WHEN OTHERS THEN
    -- ORA-00955: name is already used by an existing object
    IF SQLCODE != -955 THEN RAISE; END IF;
END;
/

-- 3) Nur beim ersten Mal dein langes Schema-SQL ausführen
DECLARE
  v NUMBER;
BEGIN
  SELECT COUNT(*) INTO v FROM appinfo.init_done WHERE flag = 1;
  IF v = 0 THEN
    -- dein vorhandenes Skript aufrufen:
    @/opt/oracle/scripts/startup/sql_schema.sql

    INSERT INTO appinfo.init_done(flag) VALUES (1);
    COMMIT;
  END IF;
END;
/
