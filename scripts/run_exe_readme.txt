CYPHERpc.exe – jak spustit
===========================

1) Složka dist\ po buildu obsahuje CYPHERpc.exe

2) Vedle exe dej soubor .env:
   - zkopíruj .env.example → .env
   - volitelně doplň OPENAI_API_KEY nebo XAI_API_KEY

3) Dvojklik na CYPHERpc.exe
   - bez klíče = demo režim
   - s klíčem = plné AI

4) GUI:
   CYPHERpc.exe --gui

Build znovu:
  .\scripts\build_exe.ps1
  nebo build_exe.bat
