# Synthetic corpus — Planta Fotovoltaica Los Almendros

> **Every document in this folder is fictional.**
>
> This project is a public reconstruction of a RAG system that the author built and runs
> in production at a renewable energy company. That production system is fed with the
> company's **private** documentation — studies, permitting projects, construction and
> quality records, O&M documents — which is confidential and cannot be published.
>
> None of that documentation is here, and none of it was used to write this corpus.
> "Los Almendros", its owner, its equipment brands (Solvanta, TrakLine, NovaPanel), its
> figures, dates, incidents and non-conformities were invented for this repository so that
> the pipeline can be shown and evaluated in public. Any resemblance to a real plant,
> company or product is coincidental.

## What the corpus imitates

The documents follow the *structure* of the documentation a utility-scale PV project
produces across its life cycle, because that is what engineers actually search through:
numbered procedures, tables of set-points and tolerances, inspection plans with hold
points, and reports that refer to each other.

| Phase | Documents |
|---|---|
| `1-estudios-previos` | Geotechnical study and pile test campaign; topographic and hydrological study |
| `2-ingenieria-y-tramitacion` | Permitting project (Proyecto Técnico Administrativo, PTA); grid connection requirements |
| `3-construccion` | Civil works design report; pile driving procedure; commissioning test protocol |
| `4-calidad` | Inspection and test plans (PPI) for piling and structure, and for trenches and cabling; a non-conformity report |
| `5-operacion-y-mantenimiento` | O&M manual; inverter datasheet; SCADA alarm codes; tracker maintenance; module cleaning; an incident report; a monthly performance report |

## Cross-references on purpose

The documents are written to reference each other the way real project documentation
does, so that retrieval is tested on connections, not just keywords. For example:

- The geotechnical study recommends a follow-up survey in the north zone. The
  non-conformity NC-2023-041 records that the survey was skipped and the piles hit
  cemented gravel there.
- The incident report INC-2024-017 traces blown string fuses to badly crimped
  connectors. The trench and cabling PPI is revised in response, and the O&M manual
  raises the minimum fuse stock.
- Thresholds such as the 60 km/h tracker stow limit appear in more than one document,
  which is why the evaluation accepts more than one correct document for some questions.

Figures are chosen to be physically plausible for a 50 MWp single-axis tracker plant in
southern Spain and are internally consistent (module, string, row and pile counts all
agree), but they must not be used as engineering guidance.
