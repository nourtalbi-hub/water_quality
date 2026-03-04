-- Vérifie si sa est activé (doit retourner is_disabled = 0)
SELECT name, is_disabled FROM sys.server_principals WHERE name = 'sa';
-- Vérifie si la base existe (doit retourner water_quality)
SELECT name FROM sys.databases WHERE name = 'water_quality';