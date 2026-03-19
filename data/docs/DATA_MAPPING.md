# PRAMAAN Strategic Data Mapping (Delhi Case Study)

This document organizes our repository data into **4 Strategic Governance Layers**. This mapping proves that PRAMAAN can ingest fragmented city data and unify it into a single semantic model.

---

## 🏗️ Layer 1: Infrastructure (Water & Sewerage)
*Proves we can model physical city assets and their capacity.*

| Source File | Entity | Key Metrics |
|---|---|---|
| `watercensusmap.kml` | Asset (Water Body) | **897 Geo-tagged assets** with real coordinates and **893 site photo URLs** (Evidence). |
| `watersupplyandsewarage.pdf`| Asset (STP/WTP) | Capacity measurements (MGD) for Okhla, Haiderpur, Rohini plants. |
| `amrut_storm_water_drainage.json`| Asset (Drain) | Number of projects, Total project cost, Completion status. |

---

## 🏠 Layer 2: Housing & Urban Development
*Proves we can model living conditions, slums, and occupancy.*

| Source File | Entity | Key Metrics |
|---|---|---|
| `pmay_housing_data.json` | Asset (House) | `census houses`, `occupied houses`, `housing shortage`. |
| `housingandurbandevelopment.pdf` | Indicator | Slum cluster locations and redevelopment targets. |

---

## 📊 Layer 3: Socio-Economic (Poverty & Demographics)
*Proves we can model human impact and social metrics.*

| Source File | Entity | Key Metrics |
|---|---|---|
| `c16ccda1...csv` | Region (Ward) | Population per DMC Ward (272 Wards). |
| `delhipovertyline.pdf` | Indicator | **Real Poverty Rates (9.91%)** and **Subsidy Impact (₹2,464/mo avg saving)**. |
| `f1a46aa8...csv` | Indicator | Scheduled Caste/Tribe population, Literacy rates, Gender ratio. |

---

## 💰 Layer 4: Government spending (Projects & Actors)
*Proves we can model the full delivery chain from Budget → Agency → Asset.*

| Source File | Entity | Key Metrics |
|---|---|---|
| `delhi_tenders_data.md` | Actor (Agency) | Organisation Name, No. of Tenders, Total Value (₹ Lakhs). |
| `statewise_allocation.json`| Scheme (Funding) | Annual fund releases for AMRUT/SBM (2019-2024). |
| `sh_north_zone...xlsx` | Actor (Personnel) | Real names of frontline maintenance workers (Malis). |

---

## 🚀 The Hackathon Demo Workflow
1. **The Ingestion:** "Our system pulls from these siloed CSVs and JSONs."
2. **The Mapping:** "We normalize them onto the PRAMAAN Urban Ontology."
3. **The Intelligence:** "Now we can ask: *'In wards with high poverty (Social), what is the water capacity (Infra) and which projects are currently being funded (Spending)?'*."

**Most core nodes use REAL DATA. Beneficiaries are partially mocked for demo completeness. Thin domains (ClimateHazard, TechEvent, SocialEvent) are mocked pending real data sourcing.**
