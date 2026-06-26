# InsureTrust AI: Multimodal Anomaly Detection Pipeline

An end-to-end Machine Learning pipeline designed for risk evaluation and anomaly detection in insurance contexts. This architecture demonstrates a multimodal approach, fusing linguistic features extracted from text inputs with tabular metadata to predict high-risk anomalies.

> **Note on Confidentiality:** This repository serves as a sanitized, public Proof-of-Concept (PoC). The underlying production models and proprietary training data are omitted to comply with previous organizational commitments and non-disclosure agreements. This architecture utilizes synthetic datasets to demonstrate core structural design, fine-tuning mechanisms, and evaluation logic.

---

## 🚀 Key Features

*   **Multimodal Data Fusion:** Combines unstructured textual risk signals with structured operational metadata.
*   **Custom NLP Fine-Tuning:** Features a specialized Transformer-based architecture (fine-tuned backbone) adapted for domain-specific semantic extraction.
*   **Optimized Tabular Classification:** Implements a custom-configured XGBoost framework optimized via hyperparameter tuning to handle multi-modal feature vectors.
*   **Imbalanced Class Evaluation:** A dedicated validation suite built specifically to address severe class imbalances inherent in anomaly and fraud detection workflows.

---

## 📂 Repository Structure

```text
├── data/
│   └── mock_data.csv         # Synthetic dataset for pipeline validation
├── models/
│   ├── nlp_backbone.py       # Custom NLP architecture/fine-tuning wrapper
│   └── xgboost_model.py      # XGBoost classifier & hyperparameter configuration
├── train_pipeline.py         # End-to-end training and feature fusion pipeline
├── eval_metrics.py           # Evaluation framework (PR-AUC, Macro-F1, threshold tuning)
├── requirements.txt          # Project dependencies
└── README.md
