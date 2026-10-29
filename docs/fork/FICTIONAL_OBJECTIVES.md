# Free-form fictional objectives

Updated after F2.8.2 at the user's request.

Create and Update no longer apply keyword/content filters to the premise, motivation, next development or transition condition. References to numbers, BPM, imagined equipment actions, medical storylines and other fictional developments are accepted as story text. The drawer guidance reflects this behavior.

Objective text remains fallible fictional context, separate from canonical observations. It cannot execute hardware actions or supply verified telemetry. Existing read-only architecture and operational-response grounding remain intact.

The required premise, existing field-length limits (240 characters for the premise; 180 for each other field), request/schema limits, lifecycle rules, model isolation, persistence settings and context budgets remain. General Story Memory excerpt filtering is a separate mechanism and was not broadly changed; its existing user-plan fallback no longer calls the removed objective-content validator.

Regression validation: 469 Python tests and 37 companion JavaScript tests pass. The same three socket-dependent Python cases remain unavailable in the sandbox. Added coverage checks formerly rejected text in each objective field, Create/Update, compiler inclusion as fiction, unchanged canonical facts and retained read-only authority. Upstream-file integrity verification passes. No service was restarted, model rebuilt or conversation data edited.

To activate the changed backend in the installed desktop stack, manually restart only the observer and reload the UI:

```sh
systemctl --user restart edgeloop-ai-observer.service
```
