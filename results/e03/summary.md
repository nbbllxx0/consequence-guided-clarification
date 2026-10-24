# E03 summary (36 tasks, 134 hidden-truth cases, tau = 0.05)

Nominal-design consequence class per dimension: {"2D": {"large_loss": 12, "harmless": 10, "infeasible": 7}, "3D": {"large_loss": 3, "consequential": 4}}

| policy | tasks | mean questions | non-mandatory questions (total) | releases | pool-unsafe releases (cases) | selected-truth exceedances | tasks with a pool-unsafe release | reference bundles per case (case-weighted / task-weighted) |
|---|---|---|---|---|---|---|---|---|
| CGC | 36 | 1.08 | 103 | 134 | 0 | 0 | 0 | 6.10 / 3.72 |
| CGC_S | 36 | 1.08 | 103 | 134 | 0 | 0 | 0 | 3.84 / 3.03 |
| CGC_S_a0 | 36 | 1.10 | 105 | 134 | 0 | 0 | 0 | 3.84 / 3.03 |
| CGC_a0 | 36 | 1.10 | 105 | 134 | 0 | 0 | 0 | 6.10 / 3.72 |
| H_lazy | 36 | 1.08 | 103 | 134 | 0 | 0 | 0 | 3.85 / 3.06 |
| ask_all | 36 | 1.72 | 188 | 134 | 0 | 0 | 0 | 1.00 / 1.00 |
| ask_all_a0 | 36 | 1.72 | 188 | 134 | 0 | 0 | 0 | 1.00 / 1.00 |
| full_H | 36 | 1.08 | 103 | 134 | 0 | 0 | 0 | 6.10 / 3.72 |
| mandatory_only | 36 | 0.31 | 0 | 134 | 101 | 65 | 26 | 1.00 / 1.00 |
| no_ask | 36 | 0.00 | 0 | 134 | 101 | 65 | 26 | 1.00 / 1.00 |
| no_ask_a0 | 36 | 0.00 | 0 | 134 | 101 | 65 | 26 | 1.00 / 1.00 |
| oracle | 36 | 1.08 | 103 | 134 | 0 | 0 | 0 | 6.10 / 3.72 |
| oracle_a0 | 36 | 1.10 | 105 | 134 | 0 | 0 | 0 | 6.10 / 3.72 |
| robust | 23 | 0.18 | 0 | 98 | 34 | 32 | 6 | 8.06 / 5.26 |
| robust_then_H | 36 | 0.86 | 73 | 134 | 0 | 0 | 0 | 6.84 / 4.36 |

| task | dim | readings | class | nominal worst loss | max ref gap | max noise |
|---|---|---|---|---|---|---|
| L01 | 2 | 6 | large_loss | 3.69e+04 | 6.66e-16 | 0.0051 |
| L04 | 2 | 5 | large_loss | 6.28e+03 | 2.22e-16 | 0.013 |
| L05 | 2 | 2 | harmless | -9.14e-05 | 4.44e-16 | 9.1e-05 |
| L07 | 2 | 1 | harmless | -0.000227 | 0 | 0.00023 |
| L08 | 2 | 3 | infeasible | inf | 0 | 0.0019 |
| L09 | 2 | 3 | large_loss | 2.44e+05 | 2.22e-16 | 0.0012 |
| L11 | 2 | 3 | large_loss | 159 | 0.0286 | 0.025 |
| L02 | 3 | 3 | large_loss | 79.5 | 1.27e-14 | 0.014 |
| L06 | 3 | 6 | large_loss | 13.2 | 4.66e-15 | 0.001 |
| L12 | 3 | 4 | consequential | 0.905 | 2.66e-15 | 0.0014 |
| L13 | 2 | 3 | large_loss | 1.5e+05 | 0 | 0.0025 |
| L14 | 2 | 3 | large_loss | 4.95e+03 | 0 | 0.0017 |
| L15 | 2 | 2 | large_loss | 6.23e+04 | 0 | 0.0055 |
| L16 | 2 | 9 | harmless | 0.0216 | 0.000119 | 0.0028 |
| L18 | 2 | 3 | harmless | 0.0479 | 0.000221 | 0.002 |
| L20 | 2 | 2 | harmless | 0.0162 | 0 | 0.00039 |
| L21 | 2 | 2 | harmless | 0.0108 | 2.22e-16 | 0.0015 |
| L22 | 2 | 18 | large_loss | 1.84e+05 | 9.36e-05 | 0.0043 |
| L23 | 2 | 2 | infeasible | inf | 0 | 0.00022 |
| L25 | 2 | 4 | large_loss | 3.39e+05 | 0 | 0.0023 |
| L28 | 2 | 3 | infeasible | inf | 2.22e-16 | 0.0016 |
| L29 | 2 | 2 | infeasible | inf | 0 | 0.0011 |
| L30 | 2 | 1 | harmless | -9.1e-05 | 0 | 9.1e-05 |
| L31 | 2 | 1 | harmless | -0.00153 | 0 | 0.0015 |
| L24 | 3 | 6 | consequential | 0.0559 | 7.99e-15 | 0.00045 |
| L33 | 3 | 2 | consequential | 2.8 | 1.11e-14 | 0.0059 |
| L34 | 3 | 2 | large_loss | 20.8 | 0 | 0.0031 |
| L35 | 3 | 2 | consequential | 0.0821 | 4.44e-14 | 0.041 |
| L36 | 2 | 6 | harmless | 0.0172 | 0.00507 | 0.0018 |
| L37 | 2 | 4 | infeasible | inf | 0.00104 | 0.0013 |
| L38 | 2 | 4 | large_loss | 1.84e+04 | 0 | 0.0014 |
| L39 | 2 | 2 | infeasible | inf | 0 | 0.011 |
| L41 | 2 | 3 | large_loss | 3.97e+03 | 2.22e-16 | 0.0029 |
| L43 | 2 | 6 | harmless | 0.00292 | 2.22e-16 | 5.3e-05 |
| L44 | 2 | 2 | large_loss | 5.14e+04 | 4.44e-16 | 0.0021 |
| L45 | 2 | 4 | infeasible | inf | 0.00113 | 0.00012 |
