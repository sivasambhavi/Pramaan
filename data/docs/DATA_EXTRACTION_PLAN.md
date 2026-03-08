# PRAMAAN MVP Data Review & Extraction Plan

## 1. Overview
The PRAMAAN MVP requires seed data mapped to a specific ontology: **Regions, Schemes, Actors, Assets, Beneficiaries, Evidence**, and **Events**. 

Based on my scan of the repository (`e:\Pramaan`), here is what we can extract from the existing files to populate your Delhi/Shahdara ward data, and what is currently missing.

---

## 2. What We Can Extract from Existing Files

### A. Regions Table
**File:** `f1a46aa8-123b-41f9-b267-31da999081ba.csv` (Delhi Census & Amenities Geo-data)
**File:** `c16ccda1-eb93-40d9-8f78-b2f0327fcaca (1).csv` (Delhi Ward Population Data)
**File:** `New_colony_ward_zone_mapping.pdf` (Colony to Ward Mapping)
*   **What we have:** We have a rich dataset of Delhi geographic regions (`District Name`, `Sub-district Name`, `Town Name`, `Ward Number`), including **Shahdara** (Zone/District). 
*   **What we will extract:** We can generate a `regions.csv` that contains wards, town names, and population figures. We will focus the export on Shahdara and 2-3 other zones.

### B. Actors Table
**File:** `sh_north_zone_duty_roaster_of_mali_2512011212291229.xlsx` (Shahdara North Zone Duty Roster)
**File:** `beat_list_shn_2511141026251125.xlsx` (Beat List)
*   **What we have:** Names of government employees ("Malis", Safai Karamcharis, Inspectors, etc.), their employee IDs, mobile numbers, zones, and designated beats/wards.
*   **What we will extract:** We can generate `actors.csv` using these employee names, attaching them as `Actors` associated with the execution/maintenance of assets in the Shahdara region.

### C. Assets (High-Level / Aggregated)
**File:** `sbm_toilets.json` (Swachh Bharat Mission Toilets metadata)
**File:** `f1a46aa8-123b-41f9-b267-31da999081ba.csv` (Amenities like `Drinking water facilities`, `No of Primary Schools`, `Roads (in kms)`)
*   **What we have:** State-level counts of Swachh Bharat Toilets (from the API call we made earlier) and municipal-level counts of basic amenities (from the census file).
*   **What we will extract:** We can't extract specific hyper-local assets (e.g., "Drain in Gali 7") from this, but we *can* extract macro-assets (e.g., "Number of Primary Schools = 5 in Shahdara") as placeholder assets.

### D. Schemes (High-Level)
**File:** `statewise_allocation.json`
**File:** `sbm_toilets.json`
*   **What we have:** We know of at least three schemes based on your API fetches today: "AMRUT" (Storm Water Drains), "Credit Guarantee Scheme", and "Swachh Bharat Mission (Urban)".
*   **What we will extract:** We can generate `schemes.csv` populated with these three schemes.

---

## 3. What is MISSING (Data You Need to Get/Mock)
To fulfill the specific criteria in **PRD 1** ("Identify 3–5 physical assets in that ward... For each asset, construct complete delivery chains"), the repository currently lacks hyper-local, entity-linked proof.

You will need to acquire or mock the following to complete the CSVs:

1. **Specific Physical Assets (`assets.csv`):**
   *   We need 3-5 *specific* physical constructions (e.g., "Gali No. 7 Drain", "Streetlight Pole #45 outside H-Block"). The amenities CSV only gives us totals (e.g., "15 primary schools"). You need to mock 5 specific asset IDs/names.
2. **Asset-Actor Linkage:**
   *   While we have the names of the Malis (gardeners/sweepers) from the duty roster, we need to map which specific actor built or maintains which specific asset.
3. **Evidence (`evidence.csv`):**
   *   We need mock URLs to "before" and "after" photos for these 5 assets.
4. **Beneficiaries (`beneficiaries.csv`):**
   *   We need mock names of citizens (e.g., "Ramesh Kumar") who live in the specific Gali where the asset was built.

---

## 4. Next Steps & Recommendation

**Recommendation:** Since you want to stick with **Python + Pandas (Option A)**, I recommend writing an ETL script that:
1.  Takes the real Shahdara geography from your tables to create `regions.csv`.
2.  Takes the real employee names from the Shahdara Duty Roster to create `actors.csv`.
3.  Injects 5 **mocked** hyper-local assets (as requested by PRD 1) into Shahdara, tagging the real employees to them.
4.  Generates the remaining mocked CSVs (`evidence.csv`, `beneficiaries.csv`) to complete the referential integrity.

Would you like me to go ahead and write this Python ETL script (`generate_seed_data.py`) to automatically generate these 6 CSV files in your `/data` folder based on this hybrid (Real Data + Mock Data) approach?
