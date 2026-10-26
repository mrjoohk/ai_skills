# Reference: Evaluation Metrics by Domain

## ML / Deep Learning (General)

### Classification
| Metric | Direction | Description | Primary Use |
|---|:---:|---|---|
| Accuracy | ↑ | Overall accuracy rate | Balanced datasets |
| F1-score (macro/micro/weighted) | ↑ | Harmonic mean of Precision & Recall | Imbalanced datasets |
| AUC-ROC | ↑ | Threshold-independent classification performance | Binary classification |
| AUC-PR | ↑ | Precision-Recall curve area | Highly imbalanced |
| MCC | ↑ | Matthews Correlation Coefficient | Imbalanced binary |

### Regression
| Metric | Direction | Description |
|---|:---:|---|
| MAE | ↓ | Mean Absolute Error |
| RMSE | ↓ | Root Mean Squared Error |
| R² | ↑ | Coefficient of determination |
| MAPE | ↓ | Mean Absolute Percentage Error |

### Generation & Representation Learning
| Metric | Direction | Description |
|---|:---:|---|
| FID | ↓ | Fréchet Inception Distance (image generation) |
| IS | ↑ | Inception Score |
| Perplexity | ↓ | Language model uncertainty |

---

## Audio / Speech

### Source Separation
| Metric | Direction | Description | Standard Range |
|---|:---:|---|---|
| SI-SDR (Scale-Invariant SDR) | ↑ | Scale-invariant signal-to-distortion ratio | > 10 dB excellent |
| SDRi (SDR improvement) | ↑ | SDR improvement over input | > 5 dB good |
| SI-SNRi | ↑ | SI-SNR improvement | > 10 dB excellent |

### Speech Quality
| Metric | Direction | Description | Standard Range |
|---|:---:|---|---|
| PESQ (Perceptual Evaluation of Speech Quality) | ↑ | Subjective quality estimation | 1.0–4.5 MOS |
| STOI (Short-Time Objective Intelligibility) | ↑ | Intelligibility | 0–1 |
| DNSMOS | ↑ | Deep Noise Suppression MOS | 1.0–5.0 |
| ViSQOL | ↑ | High-quality audio quality | 1.0–5.0 |

### Automatic Speech Recognition (ASR)
| Metric | Direction | Description |
|---|:---:|---|
| WER (Word Error Rate) | ↓ | Word error rate |
| CER (Character Error Rate) | ↓ | Character error rate |
| MER (Match Error Rate) | ↓ | |

### Speaker Diarization & Recognition
| Metric | Direction | Description |
|---|:---:|---|
| DER (Diarization Error Rate) | ↓ | Speaker diarization error rate |
| EER (Equal Error Rate) | ↓ | Speaker recognition error rate |
| MinDCF | ↓ | Detection Cost Function |

### Localization
| Metric | Direction | Description |
|---|:---:|---|
| MAE (DOA error) | ↓ | Direction estimation error (degrees) |
| ACC@k° | ↑ | Accuracy within k degrees |

---

## NLP / Language Models

### Machine Translation & Summarization
| Metric | Direction | Description |
|---|:---:|---|
| BLEU | ↑ | n-gram precision based (translation) |
| ROUGE-L | ↑ | Longest common subsequence (summarization) |
| BERTScore | ↑ | Embedding similarity |
| METEOR | ↑ | Considers synonyms & morphology |

### Language Model Quality
| Metric | Direction | Description |
|---|:---:|---|
| Perplexity | ↓ | Lower is more fluent |
| BPB (Bits Per Byte) | ↓ | Compression efficiency |

### QA / Reasoning
| Metric | Direction | Description |
|---|:---:|---|
| Exact Match (EM) | ↑ | Complete match rate |
| F1 (token-level) | ↑ | Token-level F1 |

### Benchmark Suites
| Name | Description |
|---|---|
| GLUE / SuperGLUE | General NLP benchmarks |
| MMLU | Multi-domain knowledge & reasoning |
| BIG-Bench | Diverse reasoning tasks |

---

## Metric Selection Guide

### Principles for Selecting Primary Metric
1. Choose the metric most directly connected to the task's final goal
2. Prioritize metrics most widely used in academic papers and industry standards
3. Choose metrics with intuitive interpretation (easier stakeholder communication)

### References for Setting Thresholds
- SOTA papers in the relevant domain
- Public leaderboards (Papers with Code, etc.)
- Domain expert standards (listening tests, user studies)
