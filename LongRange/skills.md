# Claude Code Skills

Design and development skills installed in this project under `.agents/skills/`. These are invoked during development to guide UI/UX decisions and code quality.

## Installed Skills

| Skill | Folder | Purpose |
|-------|--------|---------|
| Emil Design Engineering | `emil-design-eng` | Emil Kowalski's UI philosophy: `ease-out` transitions, `translateY(-3px)` hover lift on cards, `scale(0.97–0.99)` active states, `translateX(4px)` arrow on hover, nothing animates from nothing |
| Impeccable | `impeccable` | Production-grade frontend design (pbakaus). Provides `craft` (shape-then-build), `teach` (design context setup), and `extract` (pull reusable tokens) modes. Bans generic AI aesthetics, left-border stripes, and emoji icons |
| Stitch Design Taste | `stitch-design-taste` | Design taste and visual judgment patterns from the Stitch design system |
| GPT Taste | `gpt-taste` | Design taste principles focused on avoiding generic AI-generated aesthetics |
| Minimalist UI | `minimalist-ui` | Patterns for clean, uncluttered interfaces — whitespace discipline, reduced visual noise |
| Industrial Brutalist UI | `industrial-brutalist-ui` | Bold, structural UI aesthetic — raw materials, strong type, intentional contrast |
| High-End Visual Design | `high-end-visual-design` | Luxury/refined visual quality standards — typography, spacing, color precision |
| Redesign Existing Projects | `redesign-existing-projects` | Systematic approach to UI redesign without breaking functionality |
| Adapt | `adapt` | Adapts design patterns to new contexts |
| Animate | `animate` | Motion design and animation principles |
| Audit | `audit` | UI/UX audit methodology |
| Bolder | `bolder` | Pushes visual design to be more confident and distinctive |
| Clarify | `clarify` | Improves information hierarchy and clarity |
| Colorize | `colorize` | Color system and palette refinement |
| Critique | `critique` | Structured UI critique using heuristics and persona-based evaluation |
| Delight | `delight` | Micro-interactions and moments that make interfaces feel alive |
| Distill | `distill` | Simplification — removing what isn't essential |
| Layout | `layout` | Page layout and composition patterns |
| Optimize | `optimize` | Performance and rendering optimization for frontend code |
| Overdrive | `overdrive` | Pushes design to maximum expressiveness |
| Polish | `polish` | Final-pass refinement of typography, spacing, and interaction details |
| Quieter | `quieter` | Reduces visual intensity, calms busy interfaces |
| Shape | `shape` | Structural/compositional design decisions |
| Typeset | `typeset` | Typography and text layout |

## Usage

Skills are invoked via `/skill-name` in the Claude Code chat interface, or loaded automatically when their context is relevant to current work. Design skills like `impeccable` require project context (brand, audience, use case) before generating UI code.
