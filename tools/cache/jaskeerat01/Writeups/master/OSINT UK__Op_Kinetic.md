# OSINT UK CTF Challenge Writeup
**Operation:** Operation Kinetic  
**Target Focus:** Amgueddfa Cymru (St Fagans National Museum of History)  
**Status:** Completed (5/5 Flags Captured)

---

## Challenge Summary
This challenge required targeted reconnaissance of St Fagans National Museum of History using open-source intelligence vectors, including image verification, search engine dorking, policy tracking, and public registry auditing. All discovered intelligence vectors have been cross-referenced with the operational tracking dossier **Op_Kinetic.md**.

---

## 1. Physical Landmark Identification
*   **Methodology:** Visual identification of the functional historic water wheel system located on the museum grounds to extract the specific structure identity.
*   **Verification Sources:**
    *   [Alamy Image Repository (Image ID: 676256053)](https://www.alamy.com/working-water-wheel-at-bompren-corn-mill-st-fagans-national-museum-of-history-cardiff-south-wales-image676256053.html)
    *   [Amgueddfa Cymru Historic Buildings Database (Building ID: 22)](https://museum.wales/collections/historic-buildings/22/Melin-Bompren-Corn-Mill/)
*   **Flag Data:** 
    <details>
    <summary>Click to reveal flag</summary>
    <code>osintuk{Melin_Bompren_Corn_Mill}</code>
    </details>

---

## 2. Operational Change Tracking
*   **Methodology:** Executed target-specific Google dorking (`fagans national museum parking charges`) to isolate historical tariff modifications. Social media public registries confirmed the exact monetary value and implementation date.
*   **Verification Sources:**
    *   [Amgueddfa Cymru Official Visitors Portal](https://museum.wales/stfagans/visit/)
    *   [St Fagans Facebook Communications Registry (Post ID: 852005473625174)](https://www.facebook.com/stfagansmuseum/posts/car-parking-charges-at-st-fagans-will-be-changing-soon-as-of-monday-8-july-2024-/852005473625174/)
*   **Flag Data:** 
    <details>
    <summary>Click to reveal flag</summary>
    <code>osintuk{£7_08072024}</code>
    </details>

---

## 3. Policy & Admissions Baseline
*   **Methodology:** Extracted historical government directive changes via regional policy documents confirming the removal of national museum admission fees post-2001 to find the baseline entry cost.
*   **Verification Sources:**
    *   [Senedd Wales Financial & Policy Guide (PDF Document)](https://senedd.wales/media/todjnezk/bus-guide-3c3c4b220001306c00003ac000000000-english.pdf)
*   **Flag Data:** 
    <details>
    <summary>Click to reveal flag</summary>
    <code>osintuk{£0}</code>
    </details>

---

## 4. Corporate Registry Enumeration
*   **Methodology:** Deployed targeted dorking (`Charity at St Fagans Museum`) to analyze application footprints and isolate the registered charity identifier located within the platform's footer metadata.
*   **Verification Sources:**
    *   [Amgueddfa Cymru Central Donation Portal](https://museum.wales/donate/)
*   **Flag Data:** 
    <details>
    <summary>Click to reveal flag</summary>
    <code>osintuk{525774}</code>
    </details>

---

## 5. Compliance Gap Analysis
*   **Methodology:** Leveraged the corporate registry ID found in Phase 4 to query the UK Charity Commission platform. Audited the financial reporting schedule for the period ending March 2022 to identify the exact number of days late.
*   **Verification Sources:**
    *   [UK Charity Commission Register (Entity 525774 Full Print Registry)](https://register-of-charities.charitycommission.gov.uk/en/charity-search/-/charity-details/525774/full-print#:~:text=Accounts%20and%20annual%20returns)
*   **Flag Data:** 
    <details>
    <summary>Click to reveal flag</summary>
    <code>osintuk{255}</code>
    </details>

---

