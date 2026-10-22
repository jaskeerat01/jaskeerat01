# Bank of Baroda Breach Report

## Threat Actor Profile: Triple X

Triple X is a ransomware group that emerged in May 2026, specializing in the exfiltration of sensitive data to extort victims. The group employs a double-extortion model and maintains a leak site on the Tor network to publish stolen data, primarily targeting financial institutions and professional services firms.

### Key Insights
- Employs double-extortion tactics, threatening public release of stolen data to pressure victims into payment.
- Primarily targets financial institutions and professional services firms.
- Gains initial access through brute-force attacks on RDP services and exploitation of valid accounts.
- Uses command and scripting interpreters for lateral movement within compromised networks.
- Impairs security tooling and deletes backups to obstruct recovery efforts.

### TTPs Utilized by Triple X

**Discovery**
- [T1046 – Network Service Discovery](https://attack.mitre.org/techniques/T1046/)

**Credential Access**
- [T1110 – Brute Force](https://attack.mitre.org/techniques/T1110/)

**Execution**
- [T1059 – Command and Scripting Interpreter](https://attack.mitre.org/techniques/T1059/)

**Persistence**
- [T1547 – Boot or Logon Autostart Execution](https://attack.mitre.org/techniques/T1547/)
- [T1078 – Valid Accounts](https://attack.mitre.org/techniques/T1078/)

**Lateral Movement**
- [T1021.001 – Remote Desktop Protocol](https://attack.mitre.org/techniques/T1021/001/)

**Impact**
- [T1490 – Inhibit System Recovery](https://attack.mitre.org/techniques/T1490/)
- [T1486 – Data Encrypted for Impact](https://attack.mitre.org/techniques/T1486/)

### Recent History
| Victim | Date |
|---|---|
| Law Offices US (immigrationonline.com) | 13 June 2026 |
| Bank of Indonesia (leak) | 21 May 2026 |

---

## Breach Analysis

Exposed/exfiltrated document categories reportedly include:
- Scanned account opening forms
- Scanned NetBanking registration forms
- Audit Reports of various zones
- Scanned Aadhaar Cards, Voter Cards
- Digital signer executable file

**Exposure path:**
`Index of /bankofbaroda.bank.in/AuditBhopalZone2021-22/Shared Documents/General/`

---

## Observation: CamScanner Usage

A notable point of concern is the continued use of the CamScanner app for document scanning by government-linked entities in 2023 and 2024, despite the app having been flagged and pulled from India's official app stores back in June 2020 over data security concerns.
