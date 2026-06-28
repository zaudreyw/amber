# Tool-usage summary (406 tasks)

- Eval root: `/home/matt/sci/repo3/data/eval`
- Skipped (no events.jsonl / parse error): 0
- Agent keys: claude_code_no_plugin, claude_code_repo3_plugin, claude_code_repo3_plugin_m1u, claude_code_repo3_plugin_nohook

## Total tool calls per agent

| agent | n_tasks | attempted | succeeded | errored | mean_att/task | err_rate |
|---|---:|---:|---:|---:|---:|---:|
| claude_code_no_plugin | 46 | 6309 | 6036 | 273 | 137.15 | 0.043 |
| claude_code_repo3_plugin | 17 | 3740 | 3681 | 59 | 220.0 | 0.016 |
| claude_code_repo3_plugin_m1u | 17 | 1226 | 1218 | 8 | 72.12 | 0.007 |
| claude_code_repo3_plugin_nohook | 17 | 906 | 890 | 16 | 53.29 | 0.018 |

## Most-used tools (across all agents)

| tool_name | attempted | succeeded | errored | n_tasks | error_rate |
|---|---:|---:|---:|---:|---:|
| `Read` | 2922 | 2795 | 127 | 46 | 0.043 |
| `Bash` | 2602 | 2523 | 79 | 45 | 0.03 |
| `Write` | 1488 | 1459 | 29 | 45 | 0.019 |
| `mcp__geos-rag__search_schema` | 1162 | 1155 | 7 | 20 | 0.006 |
| `mcp__geos-rag__search_technical` | 1140 | 1132 | 8 | 19 | 0.007 |
| `TodoWrite` | 877 | 876 | 1 | 45 | 0.001 |
| `Edit` | 492 | 458 | 34 | 41 | 0.069 |
| `Grep` | 445 | 443 | 2 | 40 | 0.004 |
| `mcp__geos-rag__search_navigator` | 435 | 385 | 50 | 34 | 0.115 |
| `Glob` | 414 | 414 | 0 | 41 | 0.0 |
| `WebSearch` | 138 | 138 | 0 | 4 | 0.0 |
| `Agent` | 42 | 40 | 2 | 19 | 0.048 |
| `WebFetch` | 15 | 7 | 8 | 4 | 0.533 |
| `AskUserQuestion` | 9 | 0 | 9 | 4 | 1.0 |

## Tools with elevated error rates (>=10% error, >=10 attempts)

| tool_name | attempted | errored | error_rate |
|---|---:|---:|---:|
| `mcp__geos-rag__search_navigator` | 435 | 50 | 0.115 |
| `WebFetch` | 15 | 8 | 0.533 |

## Plug vs no-plug averages

| plug_bucket | tool_name | attempted | n_tasks | mean/task |
|---|---|---:|---:|---:|
| no_plugin | `Read` | 1999 | 46 | 43.46 |
| plugin | `Read` | 923 | 17 | 54.29 |
| no_plugin | `Bash` | 1924 | 45 | 42.76 |
| plugin | `Bash` | 678 | 17 | 39.88 |
| no_plugin | `Write` | 591 | 45 | 13.13 |
| plugin | `Write` | 897 | 17 | 52.76 |
| no_plugin | `mcp__geos-rag__search_schema` | 5 | 5 | 1.0 |
| plugin | `mcp__geos-rag__search_schema` | 1157 | 17 | 68.06 |
| no_plugin | `mcp__geos-rag__search_technical` | 8 | 6 | 1.33 |
| plugin | `mcp__geos-rag__search_technical` | 1132 | 17 | 66.59 |
| no_plugin | `TodoWrite` | 528 | 45 | 11.73 |
| plugin | `TodoWrite` | 349 | 17 | 20.53 |
| no_plugin | `Edit` | 259 | 41 | 6.32 |
| plugin | `Edit` | 233 | 16 | 14.56 |
| no_plugin | `Grep` | 410 | 40 | 10.25 |
| plugin | `Grep` | 35 | 10 | 3.5 |
| no_plugin | `mcp__geos-rag__search_navigator` | 49 | 34 | 1.44 |
| plugin | `mcp__geos-rag__search_navigator` | 386 | 17 | 22.71 |
| no_plugin | `Glob` | 335 | 41 | 8.17 |
| plugin | `Glob` | 79 | 16 | 4.94 |
| no_plugin | `WebSearch` | 138 | 4 | 34.5 |
| no_plugin | `Agent` | 42 | 19 | 2.21 |

## Discrepancies (events.jsonl attempted vs status.json per_tool_counts)

18 (agent,run,task,tool) rows disagree. Top mismatches by frequency:

| agent | tool_name | n_disagreements | total_delta |
|---|---|---:|---:|
| claude_code_repo3_plugin | `Bash` | 2 | 25 |
| claude_code_repo3_plugin | `Edit` | 2 | 10 |
| claude_code_repo3_plugin | `TodoWrite` | 2 | 11 |
| claude_code_repo3_plugin | `Read` | 2 | 24 |
| claude_code_repo3_plugin | `mcp__geos-rag__search_navigator` | 2 | 2 |
| claude_code_repo3_plugin | `Write` | 2 | 5 |
| claude_code_repo3_plugin | `mcp__geos-rag__search_schema` | 2 | 11 |
| claude_code_repo3_plugin | `mcp__geos-rag__search_technical` | 2 | 2 |
| claude_code_repo3_plugin | `Glob` | 1 | 2 |
| claude_code_repo3_plugin | `Grep` | 1 | 3 |

Full list: `scripts/analysis/out_4cond/tool_usage/tool_usage_discrepancies.csv`

## Output files

- `scripts/analysis/out_4cond/tool_usage/tool_usage_per_run.csv`
- `scripts/analysis/out_4cond/tool_usage/tool_usage_by_agent.csv`
- `scripts/analysis/out_4cond/tool_usage/tool_usage_by_agent_pivot_attempted.csv`
- `scripts/analysis/out_4cond/tool_usage/tool_usage_by_agent_pivot_succeeded.csv`
- `scripts/analysis/out_4cond/tool_usage/tool_usage_discrepancies.csv`
