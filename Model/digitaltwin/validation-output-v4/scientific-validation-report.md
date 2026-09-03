# Antarctic Digital Twin V4.1 — Scientific Validation Report

## Result
PASS WITH DOCUMENTED LIMITATIONS. The 50-year deterministic run completed without an invariant violation. This certification covers the V4 engine classes tested by this dependency-free runner; Spring API and Jackson checkpoint integration require execution in the host application build.

## 1. Architecture validation
Each call follows one ordered daily transition path: weather, population, mission, logistics, power, battery, dispatch/fuel, inventory, maintenance, then bounds validation. Deterministic replay passed for 730 days using identical seed and initial state. Repeated stepping also passed. The engine has no concurrent mutable static state.

## 2. Temporal validation
18250 daily states (50.0 simulated years) were generated. Temperature lag-1 autocorrelation: 0.987. Maximum cumulative-generator-runtime daily increment: 16.06 h. Storm days: 1218; deliveries: 158. State values evolve daily; scheduled maintenance no longer resets the reported cumulative runtime.

## 3. Physical invariant validation
Violations: 0. Battery SoC range: 0.00–100.00%. Minimum fuel: 0.00 L. Maximum generator output: 280.97 kW (rated 420 kW). Maximum wind output: 70.00 kW (rated 70 kW). Unexplained fuel increases: 0. Fuel-limited dispatch was corrected so a dry tank cannot report generated power or fuel use.

## 4. Statistical validation
Internal multi-year stability comparison was used because no Version 1 historical station time-series was found in the V4 module. The supplied figures provide distribution/seasonality inspection; compare against archived field-calibrated data before scientific deployment.

## 5. Scenario validation
Controlled winter storm increased operational load relative to an identical seeded normal state. A fuel-depleted, empty-battery state produced zero generator output and zero fuel consumption. Other operational scenarios should be added as explicit API-level fixtures once a build/test harness is available.

## 6. Software validation
Engine replay and long-run stability passed. Save/load, CSV service export, API behavior, memory leak profiling, and thread safety of simultaneous calls were not executable in this source-only checkout because Spring/Jackson dependencies and a build descriptor are absent.

## 7. CSV compatibility
Generated CSV uses the 21-column V4 service schema in exact declared order, ISO-8601 dates, Locale.ROOT decimals, and no blank numeric fields. It is NOT schema-compatible with the archived Version 1 `station_summary.csv` used by the ML workspace: that file contains substantially more operational, weather, power-flow, logistics, water, connectivity, and risk columns. V4 must provide an explicit adapter/feature-engineering contract before it replaces that dataset for Models 1–6.

## 8. Benchmark
50-year engine run: 0.071 s; 258093 rows/s. CSV/figure output time is not included in engine throughput.

## 9. Known limitations
The snapshot does not expose unserved energy, battery energy flow, shipment quantity, or a per-day generator-runtime field, limiting full energy-balance and event accounting audits. Food inventory is represented as `food_days`; its population scaling requires calibration against the intended unit definition.

## 10. Recommended improvements
Add a Maven/Gradle build and integration tests for checkpoint replay and REST endpoints; publish Models 1–6 schemas; add energy-flow/unserved-load fields; calibrate against archived operational observations before declaring field realism.
