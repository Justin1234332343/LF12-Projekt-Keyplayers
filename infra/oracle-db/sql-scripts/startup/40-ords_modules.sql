ALTER SESSION SET CONTAINER=FREEPDB1;
ALTER SESSION SET CURRENT_SCHEMA = PROJEKT_LF12;

-- ============================================================
-- Modul lf12.v1 — Business-Endpunkte auf den PL/SQL-Packages
-- Base-URL: http://ords:8080/ords/projekt_lf12/api/v1/
--
-- Benutzt denselben Retry-Mechanismus wie 20-ords_enable.sql:
-- Falls ORDS_METADATA.ORDS noch nicht existiert (ORDS noch nicht
-- gestartet), wird ein DBMS_SCHEDULER-Job angelegt, der jede
-- Minute erneut versucht, das Modul zu registrieren.
-- ============================================================

DECLARE
  v_pkg INTEGER;
  v_job_action CLOB := q'[
DECLARE
  v_ok INTEGER := 0;
  PROCEDURE define_modules IS
  BEGIN
    BEGIN
      ORDS.DELETE_MODULE(p_module_name => 'lf12.v1');
    EXCEPTION WHEN OTHERS THEN NULL;
    END;

    ORDS.DEFINE_MODULE(
      p_module_name    => 'lf12.v1',
      p_base_path      => '/api/v1/',
      p_items_per_page => 25,
      p_status         => 'PUBLISHED'
    );

    -- POST /api/v1/firmen/komplett/
    ORDS.DEFINE_TEMPLATE(p_module_name => 'lf12.v1', p_pattern => 'firmen/komplett/');
    ORDS.DEFINE_HANDLER(
      p_module_name   => 'lf12.v1',
      p_pattern       => 'firmen/komplett/',
      p_method        => 'POST',
      p_source_type   => 'plsql/block',
      p_source        => q'~
DECLARE
    v_body      CLOB    := :body_text;
    v_firma_id  INTEGER;
BEGIN
    pkg_firma.create_firma_mit_ansprechpartner(
        p_firma_name        => JSON_VALUE(v_body, '$.firma_name'),
        p_rechnungsadresse  => JSON_VALUE(v_body, '$.rechnungsadresse'),
        p_email_rechnung    => JSON_VALUE(v_body, '$.email_rechnungsversand'),
        p_kommentar         => JSON_VALUE(v_body, '$.kommentar'),
        p_ap_vorname        => JSON_VALUE(v_body, '$.ap_vorname'),
        p_ap_nachname       => JSON_VALUE(v_body, '$.ap_nachname'),
        p_ap_email          => JSON_VALUE(v_body, '$.ap_email'),
        p_ap_telefon        => JSON_VALUE(v_body, '$.ap_telefon'),
        p_ap_position       => JSON_VALUE(v_body, '$.ap_position'),
        p_out_firma_id      => v_firma_id
    );
    :status_code := 201;
    htp.prn('{"firma_id":' || v_firma_id || '}');
EXCEPTION WHEN OTHERS THEN
    :status_code := 400;
    htp.prn('{"error":"' || REPLACE(SQLERRM, '"', '''') || '"}');
END;~'
    );

    -- POST /api/v1/kurse/komplett/
    ORDS.DEFINE_TEMPLATE(p_module_name => 'lf12.v1', p_pattern => 'kurse/komplett/');
    ORDS.DEFINE_HANDLER(
      p_module_name   => 'lf12.v1',
      p_pattern       => 'kurse/komplett/',
      p_method        => 'POST',
      p_source_type   => 'plsql/block',
      p_source        => q'~
DECLARE
    v_body    CLOB    := :body_text;
    v_kurs_id INTEGER;
BEGIN
    pkg_kurs.create_kurs_mit_terminen(
        p_kurs_name        => JSON_VALUE(v_body, '$.kurs_name'),
        p_kurs_typ         => JSON_VALUE(v_body, '$.kurs_typ'),
        p_kurs_ort         => NVL(JSON_VALUE(v_body, '$.kurs_ort'), 'online (MS Teams)'),
        p_datum_beginn     => TO_DATE(JSON_VALUE(v_body, '$.kurs_datum_beginn'), 'YYYY-MM-DD'),
        p_datum_ende       => TO_DATE(JSON_VALUE(v_body, '$.kurs_datum_ende'),   'YYYY-MM-DD'),
        p_zeitraum         => JSON_VALUE(v_body, '$.kurs_zeitraum'),
        p_tage             => TO_NUMBER(JSON_VALUE(v_body, '$.kurs_tage')),
        p_kommentar        => JSON_VALUE(v_body, '$.kommentar'),
        p_seminaragenda_id => TO_NUMBER(JSON_VALUE(v_body, '$.seminaragenda_id')),
        p_termine_json     => JSON_QUERY(v_body, '$.termine'),
        p_out_kurs_id      => v_kurs_id
    );
    :status_code := 201;
    htp.prn('{"kurs_id":' || v_kurs_id || '}');
EXCEPTION WHEN OTHERS THEN
    :status_code := 400;
    htp.prn('{"error":"' || REPLACE(SQLERRM, '"', '''') || '"}');
END;~'
    );

    -- GET /api/v1/kurse/:kurs_id/detail
    ORDS.DEFINE_TEMPLATE(p_module_name => 'lf12.v1', p_pattern => 'kurse/:kurs_id/detail');
    ORDS.DEFINE_HANDLER(
      p_module_name   => 'lf12.v1',
      p_pattern       => 'kurse/:kurs_id/detail',
      p_method        => 'GET',
      p_source_type   => 'plsql/block',
      p_source        => q'~
DECLARE
    v_json CLOB;
BEGIN
    v_json := pkg_kurs.get_kurs_detail_json(p_kurs_id => :kurs_id);
    IF v_json IS NULL THEN
        :status_code := 404;
        htp.prn('{"error":"Kurs nicht gefunden"}');
    ELSE
        :status_code := 200;
        htp.prn(v_json);
    END IF;
END;~'
    );

    -- PUT /api/v1/angebote/:angebot_id/status
    ORDS.DEFINE_TEMPLATE(p_module_name => 'lf12.v1', p_pattern => 'angebote/:angebot_id/status');
    ORDS.DEFINE_HANDLER(
      p_module_name   => 'lf12.v1',
      p_pattern       => 'angebote/:angebot_id/status',
      p_method        => 'PUT',
      p_source_type   => 'plsql/block',
      p_source        => q'~
DECLARE
    v_body        CLOB    := :body_text;
    v_rechnung_id INTEGER;
    v_tage        INTEGER := NVL(TO_NUMBER(JSON_VALUE(v_body, '$.zahltermin_tage')), 30);
BEGIN
    pkg_angebot.update_status(
        p_angebot_id      => :angebot_id,
        p_neuer_status    => JSON_VALUE(v_body, '$.status'),
        p_zahltermin_tage => v_tage,
        p_out_rechnung_id => v_rechnung_id
    );
    :status_code := 200;
    IF v_rechnung_id IS NOT NULL THEN
        htp.prn('{"success":true,"rechnungsnummer":' || v_rechnung_id || '}');
    ELSE
        htp.prn('{"success":true}');
    END IF;
EXCEPTION WHEN OTHERS THEN
    :status_code := 400;
    htp.prn('{"error":"' || REPLACE(SQLERRM, '"', '''') || '"}');
END;~'
    );

    -- POST /api/v1/rechnungen/:rechnungsnummer/zahlung/
    ORDS.DEFINE_TEMPLATE(p_module_name => 'lf12.v1', p_pattern => 'rechnungen/:rechnungsnummer/zahlung/');
    ORDS.DEFINE_HANDLER(
      p_module_name   => 'lf12.v1',
      p_pattern       => 'rechnungen/:rechnungsnummer/zahlung/',
      p_method        => 'POST',
      p_source_type   => 'plsql/block',
      p_source        => q'~
DECLARE
    v_body       CLOB    := :body_text;
    v_zahlung_id INTEGER;
BEGIN
    pkg_rechnung.zahlung_erfassen(
        p_rechnungsnummer => :rechnungsnummer,
        p_betrag          => TO_NUMBER(JSON_VALUE(v_body, '$.betrag')),
        p_methode         => JSON_VALUE(v_body, '$.zahlungsmethode'),
        p_out_zahlung_id  => v_zahlung_id
    );
    :status_code := 201;
    htp.prn('{"zahlung_id":' || v_zahlung_id || '}');
EXCEPTION WHEN OTHERS THEN
    :status_code := 400;
    htp.prn('{"error":"' || REPLACE(SQLERRM, '"', '''') || '"}');
END;~'
    );

    -- PUT /api/v1/teilnehmer/:teilnehmerid/status
    ORDS.DEFINE_TEMPLATE(p_module_name => 'lf12.v1', p_pattern => 'teilnehmer/:teilnehmerid/status');
    ORDS.DEFINE_HANDLER(
      p_module_name   => 'lf12.v1',
      p_pattern       => 'teilnehmer/:teilnehmerid/status',
      p_method        => 'PUT',
      p_source_type   => 'plsql/block',
      p_source        => q'~
DECLARE
    v_body CLOB := :body_text;
BEGIN
    pkg_teilnehmer.update_status(
        p_teilnehmerid => :teilnehmerid,
        p_status_id    => TO_NUMBER(JSON_VALUE(v_body, '$.status_id'))
    );
    :status_code := 200;
    htp.prn('{"success":true}');
EXCEPTION WHEN OTHERS THEN
    :status_code := 400;
    htp.prn('{"error":"' || REPLACE(SQLERRM, '"', '''') || '"}');
END;~'
    );

    COMMIT;
    v_ok := 1;
  EXCEPTION WHEN OTHERS THEN
    v_ok := 0;
  END define_modules;
BEGIN
  define_modules;
  INSERT INTO APPINFO.ORDS_ENABLE_STATUS(ok) VALUES (v_ok);
  COMMIT;
  IF v_ok = 1 THEN
    DBMS_SCHEDULER.DROP_JOB('APPINFO.ORDS_MODULES_RETRY');
  END IF;
END;
]';

BEGIN
  SELECT COUNT(*) INTO v_pkg
  FROM all_objects
  WHERE owner = 'ORDS_METADATA'
    AND object_name = 'ORDS'
    AND object_type = 'PACKAGE';

  IF v_pkg = 0 THEN
    -- ORDS noch nicht installiert → Retry-Job anlegen
    BEGIN
      DBMS_SCHEDULER.DROP_JOB('APPINFO.ORDS_MODULES_RETRY', TRUE);
    EXCEPTION WHEN OTHERS THEN NULL;
    END;

    DBMS_SCHEDULER.CREATE_JOB(
      job_name        => 'APPINFO.ORDS_MODULES_RETRY',
      job_type        => 'PLSQL_BLOCK',
      job_action      => v_job_action,
      start_date      => SYSTIMESTAMP + INTERVAL '45' SECOND,
      repeat_interval => 'FREQ=MINUTELY;INTERVAL=1',
      enabled         => TRUE,
      auto_drop       => FALSE
    );
  ELSE
    -- ORDS ist da → sofort definieren
    DECLARE
      v_ok INTEGER := 0;
      PROCEDURE define_modules IS
      BEGIN
        BEGIN
          ORDS.DELETE_MODULE(p_module_name => 'lf12.v1');
        EXCEPTION WHEN OTHERS THEN NULL;
        END;

        ORDS.DEFINE_MODULE(
          p_module_name    => 'lf12.v1',
          p_base_path      => '/api/v1/',
          p_items_per_page => 25,
          p_status         => 'PUBLISHED'
        );

        ORDS.DEFINE_TEMPLATE(p_module_name => 'lf12.v1', p_pattern => 'firmen/komplett/');
        ORDS.DEFINE_HANDLER(
          p_module_name   => 'lf12.v1',
          p_pattern       => 'firmen/komplett/',
          p_method        => 'POST',
          p_source_type   => 'plsql/block',
          p_source        => q'[
DECLARE
    v_body      CLOB    := :body_text;
    v_firma_id  INTEGER;
BEGIN
    pkg_firma.create_firma_mit_ansprechpartner(
        p_firma_name        => JSON_VALUE(v_body, '$.firma_name'),
        p_rechnungsadresse  => JSON_VALUE(v_body, '$.rechnungsadresse'),
        p_email_rechnung    => JSON_VALUE(v_body, '$.email_rechnungsversand'),
        p_kommentar         => JSON_VALUE(v_body, '$.kommentar'),
        p_ap_vorname        => JSON_VALUE(v_body, '$.ap_vorname'),
        p_ap_nachname       => JSON_VALUE(v_body, '$.ap_nachname'),
        p_ap_email          => JSON_VALUE(v_body, '$.ap_email'),
        p_ap_telefon        => JSON_VALUE(v_body, '$.ap_telefon'),
        p_ap_position       => JSON_VALUE(v_body, '$.ap_position'),
        p_out_firma_id      => v_firma_id
    );
    :status_code := 201;
    htp.prn('{"firma_id":' || v_firma_id || '}');
EXCEPTION WHEN OTHERS THEN
    :status_code := 400;
    htp.prn('{"error":"' || REPLACE(SQLERRM, '"', '''') || '"}');
END;]'
        );

        ORDS.DEFINE_TEMPLATE(p_module_name => 'lf12.v1', p_pattern => 'kurse/komplett/');
        ORDS.DEFINE_HANDLER(
          p_module_name   => 'lf12.v1',
          p_pattern       => 'kurse/komplett/',
          p_method        => 'POST',
          p_source_type   => 'plsql/block',
          p_source        => q'[
DECLARE
    v_body    CLOB    := :body_text;
    v_kurs_id INTEGER;
BEGIN
    pkg_kurs.create_kurs_mit_terminen(
        p_kurs_name        => JSON_VALUE(v_body, '$.kurs_name'),
        p_kurs_typ         => JSON_VALUE(v_body, '$.kurs_typ'),
        p_kurs_ort         => NVL(JSON_VALUE(v_body, '$.kurs_ort'), 'online (MS Teams)'),
        p_datum_beginn     => TO_DATE(JSON_VALUE(v_body, '$.kurs_datum_beginn'), 'YYYY-MM-DD'),
        p_datum_ende       => TO_DATE(JSON_VALUE(v_body, '$.kurs_datum_ende'),   'YYYY-MM-DD'),
        p_zeitraum         => JSON_VALUE(v_body, '$.kurs_zeitraum'),
        p_tage             => TO_NUMBER(JSON_VALUE(v_body, '$.kurs_tage')),
        p_kommentar        => JSON_VALUE(v_body, '$.kommentar'),
        p_seminaragenda_id => TO_NUMBER(JSON_VALUE(v_body, '$.seminaragenda_id')),
        p_termine_json     => JSON_QUERY(v_body, '$.termine'),
        p_out_kurs_id      => v_kurs_id
    );
    :status_code := 201;
    htp.prn('{"kurs_id":' || v_kurs_id || '}');
EXCEPTION WHEN OTHERS THEN
    :status_code := 400;
    htp.prn('{"error":"' || REPLACE(SQLERRM, '"', '''') || '"}');
END;]'
        );

        ORDS.DEFINE_TEMPLATE(p_module_name => 'lf12.v1', p_pattern => 'kurse/:kurs_id/detail');
        ORDS.DEFINE_HANDLER(
          p_module_name   => 'lf12.v1',
          p_pattern       => 'kurse/:kurs_id/detail',
          p_method        => 'GET',
          p_source_type   => 'plsql/block',
          p_source        => q'[
DECLARE
    v_json CLOB;
BEGIN
    v_json := pkg_kurs.get_kurs_detail_json(p_kurs_id => :kurs_id);
    IF v_json IS NULL THEN
        :status_code := 404;
        htp.prn('{"error":"Kurs nicht gefunden"}');
    ELSE
        :status_code := 200;
        htp.prn(v_json);
    END IF;
END;]'
        );

        ORDS.DEFINE_TEMPLATE(p_module_name => 'lf12.v1', p_pattern => 'angebote/:angebot_id/status');
        ORDS.DEFINE_HANDLER(
          p_module_name   => 'lf12.v1',
          p_pattern       => 'angebote/:angebot_id/status',
          p_method        => 'PUT',
          p_source_type   => 'plsql/block',
          p_source        => q'[
DECLARE
    v_body        CLOB    := :body_text;
    v_rechnung_id INTEGER;
    v_tage        INTEGER := NVL(TO_NUMBER(JSON_VALUE(v_body, '$.zahltermin_tage')), 30);
BEGIN
    pkg_angebot.update_status(
        p_angebot_id      => :angebot_id,
        p_neuer_status    => JSON_VALUE(v_body, '$.status'),
        p_zahltermin_tage => v_tage,
        p_out_rechnung_id => v_rechnung_id
    );
    :status_code := 200;
    IF v_rechnung_id IS NOT NULL THEN
        htp.prn('{"success":true,"rechnungsnummer":' || v_rechnung_id || '}');
    ELSE
        htp.prn('{"success":true}');
    END IF;
EXCEPTION WHEN OTHERS THEN
    :status_code := 400;
    htp.prn('{"error":"' || REPLACE(SQLERRM, '"', '''') || '"}');
END;]'
        );

        ORDS.DEFINE_TEMPLATE(p_module_name => 'lf12.v1', p_pattern => 'rechnungen/:rechnungsnummer/zahlung/');
        ORDS.DEFINE_HANDLER(
          p_module_name   => 'lf12.v1',
          p_pattern       => 'rechnungen/:rechnungsnummer/zahlung/',
          p_method        => 'POST',
          p_source_type   => 'plsql/block',
          p_source        => q'[
DECLARE
    v_body       CLOB    := :body_text;
    v_zahlung_id INTEGER;
BEGIN
    pkg_rechnung.zahlung_erfassen(
        p_rechnungsnummer => :rechnungsnummer,
        p_betrag          => TO_NUMBER(JSON_VALUE(v_body, '$.betrag')),
        p_methode         => JSON_VALUE(v_body, '$.zahlungsmethode'),
        p_out_zahlung_id  => v_zahlung_id
    );
    :status_code := 201;
    htp.prn('{"zahlung_id":' || v_zahlung_id || '}');
EXCEPTION WHEN OTHERS THEN
    :status_code := 400;
    htp.prn('{"error":"' || REPLACE(SQLERRM, '"', '''') || '"}');
END;]'
        );

        ORDS.DEFINE_TEMPLATE(p_module_name => 'lf12.v1', p_pattern => 'teilnehmer/:teilnehmerid/status');
        ORDS.DEFINE_HANDLER(
          p_module_name   => 'lf12.v1',
          p_pattern       => 'teilnehmer/:teilnehmerid/status',
          p_method        => 'PUT',
          p_source_type   => 'plsql/block',
          p_source        => q'[
DECLARE
    v_body CLOB := :body_text;
BEGIN
    pkg_teilnehmer.update_status(
        p_teilnehmerid => :teilnehmerid,
        p_status_id    => TO_NUMBER(JSON_VALUE(v_body, '$.status_id'))
    );
    :status_code := 200;
    htp.prn('{"success":true}');
EXCEPTION WHEN OTHERS THEN
    :status_code := 400;
    htp.prn('{"error":"' || REPLACE(SQLERRM, '"', '''') || '"}');
END;]'
        );

        COMMIT;
        v_ok := 1;
      EXCEPTION WHEN OTHERS THEN
        v_ok := 0;
      END define_modules;
    BEGIN
      define_modules;
      INSERT INTO APPINFO.ORDS_ENABLE_STATUS(ok) VALUES (v_ok);
      COMMIT;
    END;
  END IF;
END;
/
