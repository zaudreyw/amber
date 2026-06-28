# Tool-usage summary (908 tasks)

- Eval root: `/home/matt/sci/repo3/data/eval`
- Skipped (no events.jsonl / parse error): 0
- Agent keys: claude_code_no_plugin, claude_code_repo3_plugin, claude_code_repo3_plugin_gmem, claude_code_repo3_plugin_gmemsilent, claude_code_repo3_plugin_gmemsilent_nohook, claude_code_repo3_plugin_m1g, claude_code_repo3_plugin_m1u, claude_code_repo3_plugin_m3g, claude_code_repo3_plugin_m4g, claude_code_repo3_plugin_m4u, claude_code_repo3_plugin_m_placebo, claude_code_repo3_plugin_mem, claude_code_repo3_plugin_memshort, claude_code_repo3_plugin_memws, claude_code_repo3_plugin_nohook, claude_code_repo3_plugin_noop, claude_code_repo3_plugin_noop_nohook, claude_code_repo3_plugin_tree

## Total tool calls per agent

| agent | n_tasks | attempted | succeeded | errored | mean_att/task | err_rate |
|---|---:|---:|---:|---:|---:|---:|
| claude_code_no_plugin | 46 | 6284 | 6014 | 270 | 136.61 | 0.043 |
| claude_code_repo3_plugin | 17 | 3740 | 3681 | 59 | 220.0 | 0.016 |
| claude_code_repo3_plugin_gmemsilent | 17 | 2571 | 2543 | 28 | 151.24 | 0.011 |
| claude_code_repo3_plugin_m_placebo | 17 | 1538 | 1515 | 23 | 90.47 | 0.015 |
| claude_code_repo3_plugin_gmem | 17 | 1327 | 1281 | 46 | 78.06 | 0.035 |
| claude_code_repo3_plugin_m1g | 17 | 1297 | 1272 | 25 | 76.29 | 0.019 |
| claude_code_repo3_plugin_m1u | 17 | 1226 | 1218 | 8 | 72.12 | 0.007 |
| claude_code_repo3_plugin_m4g | 17 | 1202 | 1202 | 0 | 70.71 | 0.0 |
| claude_code_repo3_plugin_m4u | 17 | 1109 | 1103 | 6 | 65.24 | 0.005 |
| claude_code_repo3_plugin_nohook | 17 | 906 | 890 | 16 | 53.29 | 0.018 |
| claude_code_repo3_plugin_gmemsilent_nohook | 17 | 892 | 882 | 10 | 52.47 | 0.011 |
| claude_code_repo3_plugin_memws | 17 | 667 | 642 | 25 | 39.24 | 0.037 |
| claude_code_repo3_plugin_memshort | 17 | 628 | 614 | 14 | 36.94 | 0.022 |
| claude_code_repo3_plugin_m3g | 17 | 611 | 582 | 29 | 35.94 | 0.047 |
| claude_code_repo3_plugin_tree | 17 | 604 | 589 | 15 | 35.53 | 0.025 |
| claude_code_repo3_plugin_mem | 17 | 561 | 548 | 13 | 33.0 | 0.023 |
| claude_code_repo3_plugin_noop_nohook | 4 | 380 | 375 | 5 | 95.0 | 0.013 |
| claude_code_repo3_plugin_noop | 4 | 352 | 348 | 4 | 88.0 | 0.011 |

## Most-used tools (across all agents)

| tool_name | attempted | succeeded | errored | n_tasks | error_rate |
|---|---:|---:|---:|---:|---:|
| `Read` | 5320 | 5108 | 212 | 46 | 0.04 |
| `Bash` | 4177 | 4047 | 130 | 45 | 0.031 |
| `mcp__geos-rag__search_schema` | 3925 | 3905 | 20 | 20 | 0.005 |
| `mcp__geos-rag__search_technical` | 3503 | 3486 | 17 | 19 | 0.005 |
| `Write` | 3497 | 3435 | 62 | 45 | 0.018 |
| `TodoWrite` | 1726 | 1724 | 2 | 45 | 0.001 |
| `mcp__geos-rag__search_navigator` | 1359 | 1308 | 51 | 34 | 0.038 |
| `Edit` | 971 | 905 | 66 | 41 | 0.068 |
| `Glob` | 606 | 606 | 0 | 41 | 0.0 |
| `Grep` | 573 | 571 | 2 | 40 | 0.003 |
| `WebSearch` | 138 | 138 | 0 | 4 | 0.0 |
| `Agent` | 43 | 41 | 2 | 19 | 0.047 |
| `WebFetch` | 24 | 7 | 17 | 7 | 0.708 |
| `mcp__memory__memory_lookup` | 18 | 18 | 0 | 17 | 0.0 |
| `AskUserQuestion` | 15 | 0 | 15 | 4 | 1.0 |

## Tools with elevated error rates (>=10% error, >=10 attempts)

| tool_name | attempted | errored | error_rate |
|---|---:|---:|---:|
| `WebFetch` | 24 | 17 | 0.708 |
| `AskUserQuestion` | 15 | 15 | 1.0 |

## Plug vs no-plug averages

| plug_bucket | tool_name | attempted | n_tasks | mean/task |
|---|---|---:|---:|---:|
| no_plugin | `Read` | 1986 | 46 | 43.17 |
| plugin | `Read` | 3334 | 17 | 196.12 |
| no_plugin | `Bash` | 1920 | 45 | 42.67 |
| plugin | `Bash` | 2257 | 17 | 132.76 |
| no_plugin | `mcp__geos-rag__search_schema` | 5 | 5 | 1.0 |
| plugin | `mcp__geos-rag__search_schema` | 3920 | 17 | 230.59 |
| no_plugin | `mcp__geos-rag__search_technical` | 8 | 6 | 1.33 |
| plugin | `mcp__geos-rag__search_technical` | 3495 | 17 | 205.59 |
| no_plugin | `Write` | 591 | 45 | 13.13 |
| plugin | `Write` | 2906 | 17 | 170.94 |
| no_plugin | `TodoWrite` | 527 | 45 | 11.71 |
| plugin | `TodoWrite` | 1199 | 17 | 70.53 |
| no_plugin | `mcp__geos-rag__search_navigator` | 49 | 34 | 1.44 |
| plugin | `mcp__geos-rag__search_navigator` | 1310 | 17 | 77.06 |
| no_plugin | `Edit` | 259 | 41 | 6.32 |
| plugin | `Edit` | 712 | 17 | 41.88 |
| no_plugin | `Glob` | 329 | 41 | 8.02 |
| plugin | `Glob` | 277 | 17 | 16.29 |
| no_plugin | `Grep` | 409 | 40 | 10.22 |
| plugin | `Grep` | 164 | 16 | 10.25 |
| no_plugin | `WebSearch` | 138 | 4 | 34.5 |
| no_plugin | `Agent` | 42 | 19 | 2.21 |
| plugin | `Agent` | 1 | 1 | 1.0 |

## Discrepancies (events.jsonl attempted vs status.json per_tool_counts)

25 (agent,run,task,tool) rows disagree. Top mismatches by frequency:

| agent | tool_name | n_disagreements | total_delta |
|---|---|---:|---:|
| claude_code_repo3_plugin | `Bash` | 2 | 25 |
| claude_code_repo3_plugin | `Edit` | 2 | 10 |
| claude_code_repo3_plugin | `Read` | 2 | 24 |
| claude_code_repo3_plugin | `Write` | 2 | 5 |
| claude_code_repo3_plugin | `TodoWrite` | 2 | 11 |
| claude_code_repo3_plugin | `mcp__geos-rag__search_navigator` | 2 | 2 |
| claude_code_repo3_plugin | `mcp__geos-rag__search_schema` | 2 | 11 |
| claude_code_repo3_plugin | `mcp__geos-rag__search_technical` | 2 | 2 |
| claude_code_repo3_plugin | `Grep` | 1 | 3 |
| claude_code_repo3_plugin | `Glob` | 1 | 2 |
| claude_code_repo3_plugin_m4u | `Bash` | 1 | 3 |
| claude_code_repo3_plugin_m4u | `Glob` | 1 | 1 |
| claude_code_repo3_plugin_m4u | `Read` | 1 | 7 |
| claude_code_repo3_plugin_m4u | `Write` | 1 | 3 |
| claude_code_repo3_plugin_m4u | `mcp__geos-rag__search_navigator` | 1 | 1 |
| claude_code_repo3_plugin_m4u | `mcp__geos-rag__search_schema` | 1 | 9 |
| claude_code_repo3_plugin_m4u | `mcp__geos-rag__search_technical` | 1 | 5 |

Full list: `/home/matt/sci/repo3/scripts/analysis/out/tool_usage/tool_usage_discrepancies.csv`

## Output files

- `/home/matt/sci/repo3/scripts/analysis/out/tool_usage/tool_usage_per_run.csv`
- `/home/matt/sci/repo3/scripts/analysis/out/tool_usage/tool_usage_by_agent.csv`
- `/home/matt/sci/repo3/scripts/analysis/out/tool_usage/tool_usage_by_agent_pivot_attempted.csv`
- `/home/matt/sci/repo3/scripts/analysis/out/tool_usage/tool_usage_by_agent_pivot_succeeded.csv`
- `/home/matt/sci/repo3/scripts/analysis/out/tool_usage/tool_usage_discrepancies.csv`
