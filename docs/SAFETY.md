# Safety

Safety screening is deterministic and runs before plan generation. Structured chest-pain, fainting/dizziness, and unusual-shortness-of-breath flags, plus equivalent red-flag text, block normal training. Recent injury and movement-pain details are normalized into blocked/caution tags before exercise filtering. Contraindications exclude an exercise; restriction tags select a lower dose, pain-free range, or safe alternative. Cautionary restrictions produce conservative guidance rather than a free-form AI diagnosis.

Safety has higher priority than streak, XP, motivation, or any model output. A blocked user can be stored so the UI can explain the result, but normal plan generation returns a conflict until a suitable professional review has occurred.

This is a fitness product for healthy adults, not a medical diagnosis or rehabilitation service.
