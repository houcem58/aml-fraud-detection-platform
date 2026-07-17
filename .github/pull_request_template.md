## Summary

<!-- What does this PR change and why? -->

## Type of change

- [ ] Bug fix
- [ ] New scoring component or rule
- [ ] Fusion weight recalibration
- [ ] Regulatory threshold update (BCT / ACPR / FinCEN)
- [ ] RLHF / model retraining change
- [ ] Demo script improvement
- [ ] Documentation update
- [ ] CI pipeline change

## Model impact

<!-- If this changes scoring logic, document the expected impact on the test set metrics -->

| Metric | Before | After |
|---|---|---|
| AUC-ROC | | |
| F1 (BLOCK) | | |
| FPR | | |

## Checklist

- [ ] Demo script runs cleanly: `python demo/examples/01_single_transaction.py`
- [ ] If changing fusion weights: ADR updated or new ADR in `docs/decisions/`
- [ ] If changing regulatory thresholds: compliance reference cited
- [ ] If changing RLHF pipeline: validation gate behaviour documented
- [ ] `docs/ModelCard.md` updated if metrics changed
- [ ] No PII or real transaction data included
