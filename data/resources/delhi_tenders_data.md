# Delhi Tenders Data Summary (NCT of Delhi)

## Utility for PRAMAAN MVP
This dataset is **highly useful** for the PRAMAAN MVP, specifically for populating the **Actor** nodes in our Knowledge Graph. 

In our ontology, an `Actor` is the agency/organization responsible for implementing a scheme or building an asset. This data provides a verified, real-world list of the most active executing agencies in Delhi, along with the scale of their operations (budget/value of tenders).

**How we will use this:**
1. **Actor Nodes:** We can use organizations like *Public Works Department*, *Delhi Jal Board*, *Irrigation and Flood Control*, and *Delhi Urban Shelter Improvement Board* as real `Actor` nodes in our graph.
2. **Budget Validation:** It gives realistic figures for the "Value of Tenders" (e.g., PWD handling ₹7.36 Lakh Crores equivalent/7,36,652 Lakhs), which helps us mock realistic budget allocations for these actors.
3. **Delivery Chains:** When we create a delivery chain for a water project (Asset), we can confidently link it built_by -> *Delhi Jal Board* (Actor).

---

## The Data

| S.No | Organisation Name | No. of Tenders | Value of Tenders (Rs. in Lakhs) |
|---|---|---|---|
| 1 | New Delhi Municipal Council | 2203 | 9,52,679.31 |
| 2 | Public Works Department | 6499 | 7,36,652.53 |
| 3 | Irrigation and Flood Control | 2248 | 3,68,788.58 |
| 4 | Delhi Jal Board | 12180 | 3,38,617.52 |
| 5 | Delhi Transco Limited | 59 | 1,51,409.64 |
| 6 | DSIIDC | 226 | 58,277.67 |
| 7 | Delhi Urban Shelter Improvement Board | 1437 | 49,204.13 |
| 8 | Directorate of Health Services | 15 | 34,606.48 |
| 9 | GGS INDERPRASTHA UNIVERSITY | 110 | 30,125.12 |
| 10 | Department of Forests and Wildlife | 42 | 20,993.82 |
| 11 | Law justice and Legislative Affairs | 2 | 20,659.00 |
| 12 | Department of Education | 7 | 18,017.30 |
| 13 | G B Pant Hospital | 15 | 14,413.43 |
| 14 | Delhi Transport Infrastructure Devlopment Corp Ltd | 79 | 13,639.37 |
| 15 | Delhi Building and Other Construction workers Welf | 1 | 13,512.00 |
| 16 | IPGCL-PPCL | 255 | 13,116.38 |
| 17 | Dy. Conservator of Forests(West) | 69 | 10,152.37 |
| 18 | DTTDC | 56 | 9,756.51 |
| 19 | Delhi Transport Corporation | 58 | 8,261.79 |
| 20 | Food Suply and Consumer affair Deptt | 2 | 6,000.00 |
| 21 | Delhi Agricultural Marketing Board | 73 | 4,940.76 |
| 22 | Delhi Technological University | 80 | 4,567.93 |
| 23 | Institute of Liver and Biliary Sciences | 16 | 3,207.26 |
| 24 | Department of Trg. and Tech.Education | 2 | 3,107.48 |
| 25 | Delhi Pollution Control Committee | 3 | 2,205.00 |
| 26 | Central Jail Tihar | 18 | 2,190.00 |
| 27 | NSIT | 82 | 1,993.05 |
| 28 | Directorate of Ayush | 3 | 1,760.00 |
| 29 | Delhi Pharmaceutical Science and Research University | 17 | 787.69 |
| 30 | Dy. Conservator of Forests (Central) | 4 | 556.27 |
| 31 | General Administration Department | 3 | 530.00 |
| 32 | G T B Hospital | 5 | 490.07 |
| 33 | 132 Eco Task Force | 9 | 446.85 |
| 34 | SCERT(Delhi) | 3 | 395.00 |
| 35 | Delhi State Civil Supplies Corporation LTD | 7 | 360.00 |
| 36 | Acharyashree Bhikshu Govt. Hospital | 3 | 360.00 |
| 37 | National Law University Delhi | 13 | 349.93 |
| 38 | Sanjay Gandhi Memorial Hospital | 1 | 300.00 |
| 39 | State Health Agency | 1 | 270.60 |
| 40 | Indira Gandhi Delhi Technical University For Women | 8 | 210.00 |
| 41 | DDU Hospital | 2 | 180.00 |
| 42 | Maulana Azad Medical College | 2 | 157.05 |
| 43 | Deep Chand Bandhu Hospital , Ashok Vihar | 7 | 150.90 |
| 44 | Ambedkar University Delhi | 12 | 133.22 |
| 45 | Lal Bahadur Shastri Hospital | 2 | 133.00 |
| 46 | Intelligent Communication Systems India Ltd | 2 | 115.00 |
| 47 | Delhi Parks and Gardens Society | 2 | 109.76 |
| 48 | Delhi Judicial Academy | 2 | 93.70 |
| 49 | Delhi Sate Health Mission | 1 | 90.00 |
| 50 | Department of Delhi Archives | 1 | 88.59 |
| 51 | Institute of Human Behaviour and Allied Sciences | 4 | 58.40 |
| 52 | Delhi State Cancer Institute | 6 | 44.36 |
| 53 | Department of Environment | 1 | 40.13 |
| 54 | Revenue Department | 1 | 38.00 |
| 55 | Chacha Nehru Bal Chikitsalaya | 8 | 24.00 |
| 56 | Guru Govind Singh Govt Hospital | 4 | 22.80 |
| 57 | College of Art | 1 | 13.60 |
| 58 | Babu Jagjivan Ram Memorial Hospital | 1 | 10.00 |
| 59 | Attar Saini Jain Eye and General Hospital, Lawrenc | 1 | 8.00 |
| 60 | Bhagwan Mahavir Hospital | 1 | 7.20 |
| 61 | Maulana Azad Institute of Dental Sciences | 1 | 3.60 |
| 62 | Jag Pravesh Chandra Hospital | 1 | 1.80 |
| 63 | Delhi Legislative Assembly Secretariat | 2 | 0.48 |
| 64 | Delhi Society For Prevention of Cruelty to Animals | 2 | 0.00 |
| 65 | Directorate of Information and Publicity | 1 | 0.00 |
| 66 | Deptt of Information Technology | 4 | 0.00 |
| 67 | Delhi Subordinate Service Selection Board | 1 | 0.00 |
| 68 | Delhi State Aids Control Society | 3 | 0.00 |
| 69 | Delhi Khadi and Village Industrial Board | 1 | 0.00 |
| 70 | Delhi Fire Service | 1 | 0.00 |
| 71 | Delhi Consumers Cooperative E Wholesale Store Ltd. | 1 | 0.00 |
| 72 | Office of Comm. of Excise Entt and Luxury Tax | 1 | 0.00 |
| 73 | Animal Husbandry Department GNCTD | 2 | 0.00 |
| 74 | Finance Department | 1 | 0.00 |
