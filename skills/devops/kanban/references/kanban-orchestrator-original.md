# kanban-orchestrator (original content — absorbed into `kanban` umbrella)

The orchestrator skill managed board state via filesystem, detected ready items, assigned to workers, handled completion callbacks, and updated board status (todo → in_progress → review → done). It included WIP limits, lane configuration, and the full orchestration loop. Absorbed into the `kanban` umbrella skill's Orchestrator section.

## Key preserved patterns

- Board format in YAML with lanes, wip_limits, cards
- Orchestration loop: read → check → assign → poll → move → repeat
- Completion callback handling
- Priority and dependency resolution
