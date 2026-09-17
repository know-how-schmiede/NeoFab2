# Entwicklungs- und Installationsstand

Version 0.1.0 ist ein Projektgerüst ohne startfähige Webanwendung.
Es gibt noch keine Abhängigkeiteninstallation, Migrationen oder Dienste.

Das Repository kann als normaler Entwicklungsbenutzer in PowerShell geprüft werden:

```powershell
Set-Location C:\Data\GitHub\NeoFab2
Get-Content src\neofab2\version.py
git status --short
```

Erwartet: `__version__ = "0.1.0"` und die lokalen Änderungen des Projektstarts.
Falls der Checkout anders liegt, den Pfad in `Set-Location` entsprechend ändern.

Python-Laufzeit, Abhängigkeiten und Datenbank werden mit dem nächsten
Arbeitspaket festgelegt. Anschließend werden hier konkrete Installations-,
Start- und Prüfbefehle ergänzt. Produktionsbetrieb ist noch nicht geprüft.

[Skriptübersicht](../script/README.md) · [Architektur](architecture.md)
