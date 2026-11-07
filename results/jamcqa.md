# JamC-QA (v1.0 test, 2,309 questions, 3-shot, temperature 0, `max_tokens` 8, thinking off)

Runner: `bench/jamcqa_resume.py`, one request at a time.

| | Split engine 0.2.10 | Layer split 0.1.56 | Split engine 0.2.11 |
|---|---|---|---|
| Accuracy | 64.96% (1500) | 65.09% (1503) | 64.79% (1496) |
| Unparsed / cut by length / empty | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| Mean seconds per question | 2.28 | 1.46 | 2.18 |
| Run time | about 88 min | about 56 min | not recorded (the run was paused once) |

- 0.2.10 split engine vs layer split: 96.3% of the questions (2,223) have the same correct/incorrect outcome; 32 are right only on the split engine, 35 only on the layer split; exact McNemar p = 0.81.
- 0.2.10 vs 0.2.11 on the split engine: 98.09% same outcome (1,476 right in both, 789 wrong in both); 24 right only on 0.2.10, 20 only on 0.2.11; exact McNemar p = 0.652. Same answer choice on 97.40%.
- The standard error of an accuracy near 65% over 2,309 questions is about 1.0 point, so none of these differences is significant.
- A JamC-QA question is a long 3-shot prompt with a few output tokens, so the run time is dominated by prompt reading; this is why the split engine is slower here (same effect as on short ShareGPT answers).

Per-category accuracy (%, split engine 0.2.10 / layer split): culture 65.94 / 65.94, custom 71.5 / 74.0, regional_identity 58.19 / 58.44, geography 59.56 / 58.46, history 73.18 / 74.34, government 67.27 / 67.27, law 60.54 / 59.87, healthcare 75.0 / 70.83 (healthcare has 48 questions, custom 200). `json/` has the summary files.
