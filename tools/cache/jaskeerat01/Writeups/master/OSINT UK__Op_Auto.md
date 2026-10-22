# OSINT UK CTF Challenge Writeup
**Operation:** Operation Auto  
**Target Focus:** Vehicle Intelligence & Infrastructure Enumeration  
**Status:** Completed (4/4 Flags Captured)

---

## Challenge Summary
This challenge focused on a tactical vehicle registration vector, utilizing license plate databases, regional identifier registers, user profile telemetry, and reverse WHOIS registry auditing to track infrastructure and domains.

---

## 1. Background Vehicle Ingress Identification
*   **Methodology:** Analyzed the deployment environment background to isolate and cross-reference a target vehicle registration number using the PlatesMania registry database.
*   **Verification Sources:**
    *   [PlatesMania German Database Registry (Photo ID: 31990210)](https://platesmania.com/de/foto31990210)
*   **Flag Data:** 
    <details>
    <summary>Click to reveal flag</summary>
    <code>osintuk{GERK436}</code>
    </details>

---

## 2. Regional Identifier Extraction
*   **Methodology:** Cross-referenced the prefix code isolated from the vehicle plate in Phase 1 against official German vehicle registration databases to identify the specific geographic origin.
*   **Verification Sources:**
    *   [Wikipedia German Vehicle Registration Plates Directory](https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Germany#:~:text=Germersheim,-GF)
*   **Flag Data:** 
    <details>
    <summary>Click to reveal flag</summary>
    <code>osintuk{Germersheim}</code>
    </details>

---

## 3. Platform User Profiling
*   **Methodology:** Enumerated platform metrics and audited individual account signatures to extract the precise unique identifier assigned to the target user asset.
*   **Verification Sources:**
    *   [PlatesMania User Profile Directory](https://platesmania.com/user96622)
*   **Flag Data:** 
    <details>
    <summary>Click to reveal flag</summary>
    <code>osintuk{96622}</code>
    </details>

---

## 4. Reverse Domain Infrastructure Mapping
*   **Methodology:** Deployed a Reverse WHOIS inquiry vector to analyze all registered web properties associated with a specific timestamp. Filtered the resulting JSON payload via targeted keyword match tracking to isolate the command infrastructure.
*   **Verification Sources:**
    *   [Whoxy Reverse WHOIS Analytical Platform](https://www.whoxy.com/reverse-whois/demo.php)
*   **Flag Data:** 
    <details>
    <summary>Click to reveal flag</summary>
    <code>osintuk{germersheim-cruises-all-inclusive-packages.today}</code>
    </details>

---

