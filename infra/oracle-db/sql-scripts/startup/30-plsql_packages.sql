ALTER SESSION SET CONTAINER=FREEPDB1;
ALTER SESSION SET CURRENT_SCHEMA = PROJEKT_LF12;

-- ============================================================
-- PKG_FIRMA
-- Firma anlegen (inkl. erstem Ansprechpartner in einer Transaktion)
-- ============================================================
CREATE OR REPLACE PACKAGE pkg_firma AS
    PROCEDURE create_firma_mit_ansprechpartner(
        p_firma_name           IN firma.firma_name%TYPE,
        p_rechnungsadresse     IN firma.rechnungsadresse%TYPE,
        p_email_rechnung       IN firma.email_rechnungsversand%TYPE,
        p_kommentar            IN firma.kommentar%TYPE,
        p_ap_vorname           IN ansprechpartner.vorname%TYPE,
        p_ap_nachname          IN ansprechpartner.nachname%TYPE,
        p_ap_email             IN ansprechpartner.email%TYPE,
        p_ap_telefon           IN ansprechpartner.telefonnummer%TYPE,
        p_ap_position          IN ansprechpartner.positionFirma%TYPE,
        p_out_firma_id         OUT firma.firma_id%TYPE
    );
END pkg_firma;
/

CREATE OR REPLACE PACKAGE BODY pkg_firma AS
    PROCEDURE create_firma_mit_ansprechpartner(
        p_firma_name           IN firma.firma_name%TYPE,
        p_rechnungsadresse     IN firma.rechnungsadresse%TYPE,
        p_email_rechnung       IN firma.email_rechnungsversand%TYPE,
        p_kommentar            IN firma.kommentar%TYPE,
        p_ap_vorname           IN ansprechpartner.vorname%TYPE,
        p_ap_nachname          IN ansprechpartner.nachname%TYPE,
        p_ap_email             IN ansprechpartner.email%TYPE,
        p_ap_telefon           IN ansprechpartner.telefonnummer%TYPE,
        p_ap_position          IN ansprechpartner.positionFirma%TYPE,
        p_out_firma_id         OUT firma.firma_id%TYPE
    ) IS
        v_firma_id firma.firma_id%TYPE;
    BEGIN
        INSERT INTO firma (firma_name, rechnungsadresse, email_rechnungsversand, kommentar)
        VALUES (p_firma_name, p_rechnungsadresse, p_email_rechnung, p_kommentar)
        RETURNING firma_id INTO v_firma_id;

        INSERT INTO ansprechpartner (firma_id, vorname, nachname, email, telefonnummer, positionFirma)
        VALUES (v_firma_id, p_ap_vorname, p_ap_nachname, p_ap_email, p_ap_telefon, p_ap_position);

        COMMIT;
        p_out_firma_id := v_firma_id;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END create_firma_mit_ansprechpartner;
END pkg_firma;
/


-- ============================================================
-- PKG_KURS
-- Kurs anlegen mit mehreren Terminen (JSON-Array) in einer Transaktion
-- ============================================================
CREATE OR REPLACE PACKAGE pkg_kurs AS
    PROCEDURE create_kurs_mit_terminen(
        p_kurs_name       IN kurs.kurs_name%TYPE,
        p_kurs_typ        IN kurs.kurs_typ%TYPE,
        p_kurs_ort        IN kurs.kurs_ort%TYPE,
        p_datum_beginn    IN kurs.kurs_datum_beginn%TYPE,
        p_datum_ende      IN kurs.kurs_datum_ende%TYPE,
        p_zeitraum        IN kurs.kurs_zeitraum%TYPE,
        p_tage            IN kurs.kurs_tage%TYPE,
        p_kommentar       IN kurs.kommentar%TYPE,
        p_seminaragenda_id IN kurs.seminaragenda_id%TYPE,
        p_termine_json    IN CLOB,
        p_out_kurs_id     OUT kurs.kurs_id%TYPE
    );

    FUNCTION get_kurs_detail_json(p_kurs_id IN kurs.kurs_id%TYPE) RETURN CLOB;
END pkg_kurs;
/

CREATE OR REPLACE PACKAGE BODY pkg_kurs AS

    PROCEDURE create_kurs_mit_terminen(
        p_kurs_name       IN kurs.kurs_name%TYPE,
        p_kurs_typ        IN kurs.kurs_typ%TYPE,
        p_kurs_ort        IN kurs.kurs_ort%TYPE,
        p_datum_beginn    IN kurs.kurs_datum_beginn%TYPE,
        p_datum_ende      IN kurs.kurs_datum_ende%TYPE,
        p_zeitraum        IN kurs.kurs_zeitraum%TYPE,
        p_tage            IN kurs.kurs_tage%TYPE,
        p_kommentar       IN kurs.kommentar%TYPE,
        p_seminaragenda_id IN kurs.seminaragenda_id%TYPE,
        p_termine_json    IN CLOB,
        p_out_kurs_id     OUT kurs.kurs_id%TYPE
    ) IS
        v_kurs_id kurs.kurs_id%TYPE;
    BEGIN
        INSERT INTO kurs (
            kurs_name, kurs_typ, kurs_ort,
            kurs_datum_beginn, kurs_datum_ende,
            kurs_zeitraum, kurs_tage, kommentar, seminaragenda_id
        ) VALUES (
            p_kurs_name, p_kurs_typ, p_kurs_ort,
            p_datum_beginn, p_datum_ende,
            p_zeitraum, p_tage, p_kommentar, p_seminaragenda_id
        ) RETURNING kurs_id INTO v_kurs_id;

        -- Termine aus JSON-Array einfügen
        -- Erwartet: [{"datum":"YYYY-MM-DD","start":"YYYY-MM-DD HH24:MI:SS","ende":"YYYY-MM-DD HH24:MI:SS"}, ...]
        INSERT INTO kurs_termine (kurs_id, datum, uhrzeit_start, uhrzeit_ende)
        SELECT
            v_kurs_id,
            TO_DATE(jt.datum, 'YYYY-MM-DD'),
            TO_TIMESTAMP(jt.start_zeit, 'YYYY-MM-DD HH24:MI:SS'),
            TO_TIMESTAMP(jt.ende_zeit,  'YYYY-MM-DD HH24:MI:SS')
        FROM JSON_TABLE(p_termine_json, '$[*]'
            COLUMNS (
                datum      VARCHAR2(20) PATH '$.datum',
                start_zeit VARCHAR2(30) PATH '$.start',
                ende_zeit  VARCHAR2(30) PATH '$.ende'
            )
        ) jt;

        COMMIT;
        p_out_kurs_id := v_kurs_id;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END create_kurs_mit_terminen;

    FUNCTION get_kurs_detail_json(p_kurs_id IN kurs.kurs_id%TYPE) RETURN CLOB IS
        v_result CLOB;
    BEGIN
        SELECT JSON_OBJECT(
            'kurs_id'          VALUE k.kurs_id,
            'kurs_name'        VALUE k.kurs_name,
            'kurs_typ'         VALUE k.kurs_typ,
            'kurs_ort'         VALUE k.kurs_ort,
            'kurs_datum_beginn' VALUE TO_CHAR(k.kurs_datum_beginn, 'YYYY-MM-DD'),
            'kurs_datum_ende'  VALUE TO_CHAR(k.kurs_datum_ende,   'YYYY-MM-DD'),
            'kurs_zeitraum'    VALUE k.kurs_zeitraum,
            'kurs_tage'        VALUE k.kurs_tage,
            'kommentar'        VALUE k.kommentar,
            'seminaragenda'    VALUE (
                SELECT JSON_OBJECT(
                    'id'      VALUE s.seminaragenda_id,
                    'titel'   VALUE s.titel,
                    'version' VALUE TO_CHAR(s.seminaragenda_version, 'YYYY-MM-DD')
                    ABSENT ON NULL
                )
                FROM seminaragenda s
                WHERE s.seminaragenda_id = k.seminaragenda_id
            ),
            'termine' VALUE (
                SELECT JSON_ARRAYAGG(
                    JSON_OBJECT(
                        'terminid'      VALUE t.terminid,
                        'datum'         VALUE TO_CHAR(t.datum, 'YYYY-MM-DD'),
                        'uhrzeit_start' VALUE TO_CHAR(t.uhrzeit_start, 'HH24:MI'),
                        'uhrzeit_ende'  VALUE TO_CHAR(t.uhrzeit_ende,  'HH24:MI')
                    ) ORDER BY t.datum
                )
                FROM kurs_termine t
                WHERE t.kurs_id = k.kurs_id
            )
            ABSENT ON NULL
        )
        INTO v_result
        FROM kurs k
        WHERE k.kurs_id = p_kurs_id;

        RETURN v_result;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN NULL;
    END get_kurs_detail_json;

END pkg_kurs;
/


-- ============================================================
-- PKG_ANGEBOT
-- Angebot-Status aktualisieren; bei 'angenommen' automatisch Rechnung anlegen
-- ============================================================
CREATE OR REPLACE PACKAGE pkg_angebot AS
    PROCEDURE update_status(
        p_angebot_id     IN angebot.angebot_id%TYPE,
        p_neuer_status   IN angebot.angebot_status%TYPE,
        p_zahltermin_tage IN INTEGER DEFAULT 30,
        p_out_rechnung_id OUT rechnung.rechnungsnummer%TYPE
    );
END pkg_angebot;
/

CREATE OR REPLACE PACKAGE BODY pkg_angebot AS
    PROCEDURE update_status(
        p_angebot_id      IN angebot.angebot_id%TYPE,
        p_neuer_status    IN angebot.angebot_status%TYPE,
        p_zahltermin_tage IN INTEGER DEFAULT 30,
        p_out_rechnung_id OUT rechnung.rechnungsnummer%TYPE
    ) IS
        v_firma_id  angebot.firma_id%TYPE;
        v_kurs_id   angebot.kurs_id%TYPE;
        v_betrag    angebot.angebot_betrag%TYPE;
        v_rechnung_id rechnung.rechnungsnummer%TYPE;
    BEGIN
        UPDATE angebot
        SET angebot_status = p_neuer_status
        WHERE angebot_id = p_angebot_id
        RETURNING firma_id, kurs_id, angebot_betrag
        INTO v_firma_id, v_kurs_id, v_betrag;

        IF SQL%ROWCOUNT = 0 THEN
            RAISE_APPLICATION_ERROR(-20010, 'Angebot nicht gefunden: ' || p_angebot_id);
        END IF;

        -- Bei Annahme automatisch Rechnung erstellen
        IF p_neuer_status = 'angenommen' THEN
            INSERT INTO rechnung (kurs_id, angebot_id, firma_id, zahltermin, betrag_brutto)
            VALUES (v_kurs_id, p_angebot_id, v_firma_id, SYSDATE + p_zahltermin_tage, v_betrag)
            RETURNING rechnungsnummer INTO v_rechnung_id;
        END IF;

        COMMIT;
        p_out_rechnung_id := v_rechnung_id;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END update_status;
END pkg_angebot;
/


-- ============================================================
-- PKG_RECHNUNG
-- Zahlung erfassen und Rechnungsstatus aktualisieren
-- ============================================================
CREATE OR REPLACE PACKAGE pkg_rechnung AS
    PROCEDURE zahlung_erfassen(
        p_rechnungsnummer IN rechnung.rechnungsnummer%TYPE,
        p_betrag          IN zahlung.betrag%TYPE,
        p_methode         IN zahlung.zahlungsmethode%TYPE,
        p_out_zahlung_id  OUT zahlung.zahlung_id%TYPE
    );
END pkg_rechnung;
/

CREATE OR REPLACE PACKAGE BODY pkg_rechnung AS
    PROCEDURE zahlung_erfassen(
        p_rechnungsnummer IN rechnung.rechnungsnummer%TYPE,
        p_betrag          IN zahlung.betrag%TYPE,
        p_methode         IN zahlung.zahlungsmethode%TYPE,
        p_out_zahlung_id  OUT zahlung.zahlung_id%TYPE
    ) IS
        v_zahlung_id  zahlung.zahlung_id%TYPE;
        v_brutto      rechnung.betrag_brutto%TYPE;
        v_gezahlt     NUMBER(10,2);
    BEGIN
        INSERT INTO zahlung (rechnungsnummer, betrag, zahlungsmethode)
        VALUES (p_rechnungsnummer, p_betrag, p_methode)
        RETURNING zahlung_id INTO v_zahlung_id;

        -- Prüfen ob Rechnung vollständig bezahlt
        SELECT betrag_brutto INTO v_brutto
        FROM rechnung
        WHERE rechnungsnummer = p_rechnungsnummer;

        SELECT NVL(SUM(betrag), 0) INTO v_gezahlt
        FROM zahlung
        WHERE rechnungsnummer = p_rechnungsnummer;

        IF v_gezahlt >= v_brutto THEN
            UPDATE rechnung
            SET rechnung_status = 'bezahlt'
            WHERE rechnungsnummer = p_rechnungsnummer;
        END IF;

        COMMIT;
        p_out_zahlung_id := v_zahlung_id;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END zahlung_erfassen;
END pkg_rechnung;
/


-- ============================================================
-- PKG_TEILNEHMER
-- Teilnehmer-Status aktualisieren
-- ============================================================
CREATE OR REPLACE PACKAGE pkg_teilnehmer AS
    PROCEDURE update_status(
        p_teilnehmerid IN teilnehmer.teilnehmerid%TYPE,
        p_status_id    IN teilnehmer.status_id%TYPE
    );
END pkg_teilnehmer;
/

CREATE OR REPLACE PACKAGE BODY pkg_teilnehmer AS
    PROCEDURE update_status(
        p_teilnehmerid IN teilnehmer.teilnehmerid%TYPE,
        p_status_id    IN teilnehmer.status_id%TYPE
    ) IS
    BEGIN
        UPDATE teilnehmer
        SET status_id = p_status_id
        WHERE teilnehmerid = p_teilnehmerid;

        IF SQL%ROWCOUNT = 0 THEN
            RAISE_APPLICATION_ERROR(-20020, 'Teilnehmer nicht gefunden: ' || p_teilnehmerid);
        END IF;

        COMMIT;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END update_status;
END pkg_teilnehmer;
/
