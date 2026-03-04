-- Activer le compte sa
ALTER LOGIN sa ENABLE;

-- Définir un mot de passe pour sa (choisis ton mot de passe)
ALTER LOGIN sa WITH PASSWORD = 'WaterQuality2026';

-- Activer l'authentification SQL Server + Windows
EXEC xp_instance_regwrite 
    N'HKEY_LOCAL_MACHINE', 
    N'Software\Microsoft\MSSQLServer\MSSQLServer',
    N'LoginMode', REG_DWORD, 2;
 