
-- SQL Skipt zum erstellen eines Datenbank Nutzers.
-- Der Nutzer admin wird mit einem Passwort erstellt und kriegt Basisrechte.
-- Außerdem darf er auf die Tabellen 'Employees' und Departments' zugreifen und unendliche neue Tabellen erstellen.

-- In Powershell 'docker exec -it oracle-23ai-free bash' eingeben um mit dem CDB (Container Data base) zu verbinden.
-- Im SQLPlus Terminal direkt mit der PDB (Portable Data base) FREEPDB1 als system Nutzer verbinden: 'sqlplus system/MeinSicheresPasswort123@//localhost:1521/FREEPDB1'


CREATE USER admin IDENTIFIED BY BrineApple123;
GRANT CONNECT, RESOURCE TO admin;
GRANT UNLIMITED TABLESPACE TO admin;
GRANT SELECT ON SYSTEM.EMPLOYEES to admin;
GRANT SELECT ON SYSTEM.DEPARTMENTS to admin;

