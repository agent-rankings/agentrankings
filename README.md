# AgentRankings.ai

A short, hand-picked list of AI agents, with independent benchmark scores where they exist.

## How it works

- `index.html` is the whole site. It reads `data/agents.json` and renders it.
- `data/agents.json` is the only place content lives. Edit it to add, change or remove an agent.
- `scripts/check.py` validates the data. It runs automatically on every change.

## Rules for the data

- Every score needs a source (`benchmark.sourceUrl`) and the date it was checked.
- No source, no score. Agents without a published result are listed without one.
- When you check or change a listing, set its `checked` date and update `meta.lastUpdated`.

## Weekly review

Every Monday a GitHub issue called "Weekly review" opens with a short checklist:
broken links, the four listings most due for a re-check, the benchmark leaderboard
to look at, and room for new agents. It is meant to take about an hour.
Close the issue when you are done. It can also be started by hand under
Actions → Check data → Run workflow.

## Scoring method

- **Coding, v1:** the share of Terminal-Bench 4.0 tasks the agent solved in its best
  published run, with the model it used.
- **Other categories:** not scored yet, because public benchmarks there mostly test
  the underlying models, not the products.
