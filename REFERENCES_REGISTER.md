# Verified reference register

Verification date: `2026-08-02`  
Citation style in working draft: numbered/IEEE-like  
Status: **bounded initial set; final group bibliography review still required**

Only sources actually opened in this work session appear below. The register
records the proposal claim each source may support and what it does **not**
support. A URL or source title alone does not authorise copying figures, tables,
data, code, or wording into the assessment.

## R1 - NIST AI RMF 1.0

- **Citation:** National Institute of Standards and Technology, *Artificial
  Intelligence Risk Management Framework (AI RMF 1.0)*, NIST AI 100-1, Jan.
  2023, doi: `10.6028/NIST.AI.100-1`.
- **Primary source:**
  `https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf`
- **Source SHA-256 when checked:**
  `7576edb531d9848825814ee88e28b1795d3a84b435b4b797d3670eafdc4a89f1`
- **Verified content:** title/date/DOI; trustworthiness characteristics; AI RMF
  core functions `GOVERN`, `MAP`, `MEASURE`, and `MANAGE`; lifecycle emphasis
  and separation of building from verification/validation roles.
- **Proposal claim mapping:** lifecycle risk governance, traceability,
  measurement, accountability, and independent checking in Sections 7 and 10.
- **Does not establish:** that this product complies with NIST, is safe, or is
  suitable for any production use.

## R2 - NIST Generative AI Profile

- **Citation:** National Institute of Standards and Technology, *Artificial
  Intelligence Risk Management Framework: Generative Artificial Intelligence
  Profile*, NIST AI 600-1, July 2024, doi: `10.6028/NIST.AI.600-1`.
- **Primary source:**
  `https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf`
- **Source SHA-256 when checked:**
  `6e73620ab6b64e90ef2c04bf0e0d6246185a2f4b1b13cab0df494496cff89b6a`
- **Verified content:** the profile is a GenAI companion to AI RMF 1.0;
  governance, content provenance, pre-deployment testing, and incident
  disclosure are primary considerations; identified risks include
  confabulation, data privacy, human-AI configuration/automation bias,
  information integrity, and information security.
- **Proposal claim mapping:** risk taxonomy, human authority, provenance,
  pre-deployment evaluation, privacy, and limitations in Sections 9 and 10.
- **Does not establish:** that the proposal's controls fully mitigate those
  risks or that every NIST suggested action is in scope.

## R3 - OWASP prompt injection guidance

- **Citation:** OWASP Gen AI Security Project, “LLM01:2025 Prompt Injection,”
  accessed Aug. 2, 2026. `https://genai.owasp.org/llmrisk/llm01-prompt-injection/`
- **Live HTML SHA-256 when checked:**
  `84482723dc0af6194c873cac3c31b7d4dcfc885a02e7a1f49c4aa7dfd9ef2418`
- **Verified content:** direct and indirect prompt injection can alter model
  behaviour; prevention is not presented as foolproof; listed mitigations
  include constraining behaviour, validating expected outputs with deterministic
  code, least privilege, human approval for high-risk actions, segregating
  untrusted content, and adversarial testing.
- **Proposal claim mapping:** prompt-injection risk, strict output schema,
  gateway isolation, no external action, and human-review boundary in Sections
  7 and 10.
- **Does not establish:** that the current string guard prevents every attack.
  The proposal explicitly identifies that limitation.

## R4 - FActScore

- **Citation:** S. Min, K. Krishna, X. Lyu, M. Lewis, W.-t. Yih, P. Koh,
  M. Iyyer, L. Zettlemoyer, and H. Hajishirzi, “FActScore: Fine-grained Atomic
  Evaluation of Factual Precision in Long Form Text Generation,” in
  *Proceedings of EMNLP 2023*, pp. 12076-12100, 2023,
  doi: `10.18653/v1/2023.emnlp-main.741`.
- **Primary source:** `https://aclanthology.org/2023.emnlp-main.741/`
- **Live HTML SHA-256 when checked:**
  `b4e0f6159ebd64682c9c03918411c042dc5594577c49e5a1aa0d67b3a8d893c0`
- **Verified content:** the abstract motivates fine-grained evaluation because
  long-form generations may mix supported and unsupported information and
  describes decomposition into atomic facts checked against a reliable source.
- **Proposal claim mapping:** claim-level rather than whole-document evaluation
  rationale in Sections 3, 4, and 9.
- **Does not establish:** that this project implements FActScore, uses its data,
  or reproduces its reported experiments. It does none of those things.

## R5 - RAGAs

- **Citation:** S. Es, J. James, L. Espinosa Anke, and S. Schockaert, “RAGAs:
  Automated Evaluation of Retrieval Augmented Generation,” in *Proceedings of
  the 18th EACL: System Demonstrations*, pp. 150-158, 2024,
  doi: `10.18653/v1/2024.eacl-demo.16`.
- **Primary source:** `https://aclanthology.org/2024.eacl-demo.16/`
- **Live HTML SHA-256 when checked:**
  `5b7735b18e3fd574424f946bd9776509b61134c09edcd95c973595f71c6477db`
- **Verified content:** the abstract distinguishes retrieval relevance, faithful
  use of retrieved passages, and generation quality as different RAG evaluation
  dimensions and introduces a metric suite.
- **Proposal claim mapping:** need for multi-dimensional evaluation rather than
  one aggregate score in Sections 3 and 9.
- **Does not establish:** that this product is RAGAs-compatible, implements its
  metrics, or inherits its validity.

## R6 - scikit-learn TF-IDF technical documentation

- **Citation:** scikit-learn developers, “`TfidfVectorizer`,” *scikit-learn API
  Reference*, accessed Aug. 2, 2026.
  `https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html`
- **Live HTML SHA-256 when checked:**
  `1fb18ded230cd46cae01e9dec8c839815ec09f394296b0f252c398cb74f6c5de`
- **Verified content:** the API converts raw documents to TF-IDF feature
  matrices and is equivalent to a count vectorizer followed by a TF-IDF
  transformer; documented normalisation supports cosine use through a dot
  product under L2 normalisation.
- **Proposal claim mapping:** selected local retrieval component in Section 7.
- **Does not establish:** semantic retrieval quality or the project's final
  performance.

## R7 - pytest technical documentation

- **Citation:** pytest developers, “pytest documentation,” accessed Aug. 2,
  2026. `https://docs.pytest.org/en/stable/`
- **Live HTML SHA-256 when checked:**
  `96781e73a1f051ae4f2edbb67386e38be9d3aece38ac6d4b15bc7e0a2e190857`
- **Verified content:** official stable documentation surface for the selected
  Python testing framework.
- **Proposal claim mapping:** selected test tool and reproduction method in
  Sections 7 and 9.
- **Does not establish:** that any project test passed; local test output is the
  evidence for that claim.

## Claim-to-source map

| Proposal claim | Source(s) | Boundary |
|---|---|---|
| Long outputs can mix supported and unsupported units, motivating claim-level review | R4 | Conceptual motivation only; no FActScore implementation/data reuse |
| Retrieval relevance, evidence use, and output quality should not collapse into one measure | R5 | Metric-design motivation only; project metrics are independently defined |
| AI risk work should be governed, contextualised, measured, and managed across a lifecycle | R1 | Framework informs risk process; no compliance claim |
| GenAI-specific risks include confabulation, privacy, automation bias/human-AI configuration, integrity, and security | R2 | Selected risks are scoped to this product |
| Prompt injection requires architectural and deterministic controls plus human oversight; a string filter is insufficient | R3 | Current controls reduce impact but are not foolproof |
| Local baseline retrieval uses a documented TF-IDF vectoriser | R6 | Implementation/tests establish actual use and behaviour |
| pytest is the selected test runner | R7 | Project transcripts establish the pass count |

## Final bibliography gate

- [ ] Actual group chooses and applies one citation style consistently.
- [ ] Each member opens every source cited in their section.
- [ ] Inline citation is attached to the exact supported claim.
- [ ] No source is used to imply implementation, safety, performance, or
  compliance that it does not establish.
- [ ] External figures/tables/data are omitted unless licence, attribution, and
  course rules are verified; original project diagrams are preferred.
- [ ] Canvas Proposal brief and Lab 1 are cited as course sources where required.
- [ ] URLs, DOIs, authors, titles, venue, pages, and access dates are rechecked
  before final PDF generation.
- [ ] Any later source is added to this register with the same claim/boundary
  fields before it enters the Proposal.
