# E03 summary (41 tasks, 240 hidden-truth cases, tau = 0.05)

Nominal-design consequence class per dimension: {"2D": {"large_loss": 16, "infeasible": 10, "consequential": 3, "harmless": 5}, "3D": {"infeasible": 2, "large_loss": 2, "consequential": 3}}

| policy | tasks | mean questions | non-mandatory questions (total) | releases | pool-unsafe releases (cases) | selected-truth exceedances | tasks with a pool-unsafe release | reference bundles per case (case-weighted / task-weighted) |
|---|---|---|---|---|---|---|---|---|
| CGC | 41 | 1.70 | 334 | 232 | 0 | 0 | 0 | 11.19 / 5.85 |
| CGC_S | 41 | 1.84 | 368 | 224 | 0 | 0 | 0 | 5.38 / 3.88 |
| CGC_S_a0 | 41 | 1.89 | 380 | 224 | 0 | 0 | 0 | 5.38 / 3.88 |
| CGC_a0 | 41 | 1.71 | 336 | 232 | 0 | 0 | 0 | 11.19 / 5.85 |
| H_lazy | 41 | 1.78 | 353 | 232 | 0 | 0 | 0 | 5.90 / 4.04 |
| ask_all | 41 | 2.52 | 531 | 240 | 0 | 0 | 0 | 1.00 / 1.00 |
| ask_all_a0 | 41 | 2.52 | 531 | 240 | 0 | 0 | 0 | 1.00 / 1.00 |
| full_H | 41 | 1.70 | 333 | 232 | 0 | 0 | 0 | 11.19 / 5.85 |
| mandatory_only | 41 | 0.31 | 0 | 240 | 219 | 155 | 36 | 1.00 / 1.00 |
| no_ask | 41 | 0.00 | 0 | 240 | 219 | 155 | 36 | 1.00 / 1.00 |
| no_ask_a0 | 41 | 0.00 | 0 | 240 | 219 | 155 | 36 | 1.00 / 1.00 |
| oracle | 41 | 1.71 | 337 | 240 | 0 | 0 | 0 | 11.19 / 5.85 |
| oracle_a0 | 41 | 1.72 | 339 | 240 | 0 | 0 | 0 | 11.19 / 5.85 |
| robust | 22 | 0.22 | 0 | 105 | 58 | 38 | 10 | 8.55 / 5.77 |
| robust_then_H | 41 | 1.60 | 309 | 232 | 0 | 0 | 0 | 11.63 / 6.39 |

| task | dim | readings | class | nominal worst loss | max ref gap | max noise |
|---|---|---|---|---|---|---|
| L01 | 2 | 6 | large_loss | 3.69e+04 | 6.66e-16 | 0.0051 |
| L04 | 2 | 30 | infeasible | inf | 0.00252 | 0.013 |
| L05 | 2 | 4 | infeasible | inf | 4.44e-16 | 0.00032 |
| L07 | 2 | 2 | consequential | 1.07 | 0 | 0.00023 |
| L08 | 2 | 3 | infeasible | inf | 0 | 0.0019 |
| L09 | 2 | 3 | large_loss | 2.44e+05 | 2.22e-16 | 0.0012 |
| L11 | 2 | 9 | large_loss | 159 | 0.0286 | 0.025 |
| L02 | 3 | 8 | infeasible | inf | 0.000695 | 0.014 |
| L06 | 3 | 6 | large_loss | 13.2 | 4.66e-15 | 0.001 |
| L12 | 3 | 8 | infeasible | inf | 4.88e-15 | 0.0022 |
| L13 | 2 | 3 | large_loss | 1.5e+05 | 0 | 0.0025 |
| L14 | 2 | 3 | large_loss | 4.95e+03 | 0 | 0.0017 |
| L15 | 2 | 2 | large_loss | 6.23e+04 | 0 | 0.0055 |
| L16 | 2 | 9 | harmless | 0.0216 | 0.000119 | 0.0028 |
| L17 | 2 | 5 | large_loss | 34.9 | 6.66e-16 | 0.0028 |
| L18 | 2 | 3 | harmless | 0.0479 | 0.000221 | 0.002 |
| L19 | 2 | 2 | large_loss | 7.62e+04 | 0 | 0.00058 |
| L20 | 2 | 8 | infeasible | inf | 0 | 0.0047 |
| L21 | 2 | 3 | consequential | 4.49 | 2.22e-16 | 0.0015 |
| L22 | 2 | 18 | large_loss | 1.99e+05 | 9.36e-05 | 0.0043 |
| L23 | 2 | 3 | infeasible | inf | 0 | 0.00022 |
| L25 | 2 | 4 | large_loss | 3.39e+05 | 0 | 0.0023 |
| L27 | 2 | 2 | large_loss | 1.82e+05 | 0 | 0.0028 |
| L28 | 2 | 3 | infeasible | inf | 2.22e-16 | 0.0016 |
| L29 | 2 | 2 | infeasible | inf | 0 | 0.0011 |
| L30 | 2 | 1 | harmless | -9.1e-05 | 0 | 9.1e-05 |
| L31 | 2 | 2 | harmless | 0.0478 | 0 | 0.0015 |
| L24 | 3 | 6 | consequential | 0.0559 | 7.99e-15 | 0.00045 |
| L33 | 3 | 4 | consequential | 2.8 | 6.35e-14 | 0.0059 |
| L34 | 3 | 2 | large_loss | 20.8 | 0 | 0.0031 |
| L35 | 3 | 2 | consequential | 0.0821 | 4.44e-14 | 0.041 |
| L36 | 2 | 9 | consequential | 0.121 | 0.00507 | 0.0018 |
| L37 | 2 | 12 | infeasible | inf | 0.00163 | 0.0019 |
| L38 | 2 | 16 | large_loss | 7.33e+05 | 4.44e-16 | 0.0075 |
| L39 | 2 | 2 | infeasible | inf | 0 | 0.011 |
| L40 | 2 | 4 | large_loss | 8.89e+04 | 2.66e-15 | 0.0047 |
| L41 | 2 | 3 | large_loss | 3.97e+03 | 2.22e-16 | 0.0029 |
| L42 | 2 | 4 | large_loss | 2.5e+04 | 0 | 0.0026 |
| L43 | 2 | 6 | harmless | 0.00292 | 2.22e-16 | 5.3e-05 |
| L44 | 2 | 2 | large_loss | 5.14e+04 | 4.44e-16 | 0.0021 |
| L45 | 2 | 16 | infeasible | inf | 0.00362 | 0.00017 |
