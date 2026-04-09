Proposed criteria to qualify competency questions:

## 1. Scope

Question should not require status or state information (such as damper position)
- e.g. rather than "What is upstream of me?", could ask "What is possibly upstream of me?"

## 2. Ambiguity

Question must be unambiguous. There must not be unstated assumptions that are needed to resolve reasonable alternative interpretations. Contextual variabilities must be made explicit.
- e.g. "Of course I don't mean devices that are upstream via the return air duct"
- e.g. "From the perspective of Damper_1, tell me..."

---
#### Discussion

"Upstream" should also be specific of the substance being traced, for a cooling coil it could be air or chilled water.  "How far to look" is another aspect of path traversal, downstream of our chillers is the entire campus chilled water distribution system which is a large number of heat exchangers, valves, differential pressure booster pumps, all kinds of stuff.

---

There is a big difference between "what is upstream of VAV-1" which uses a global viewpoint vs "what is upstream of VAV-1 from the perspective of VAV-1".  Knowing what "perspective" statements are in conflict with the "omnipotent view" might be an interesting query to write.

In terms of #3 the `s223:Context` referenced from a `s223:ContextualStatement` by the `s223:inContext` predicate would need some `s223:asSeenBy` relation in addition to whatever `s223:dependsOn` relationship is provided (which I propose is a relationship between a context and an [ASK](https://www.w3.org/TR/rdf-sparql-query/#ask) query).
