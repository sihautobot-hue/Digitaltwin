package com.antarctica.digitaltwin.simulator.v4;

import org.springframework.stereotype.Service;
import java.io.*;
import java.nio.file.*;
import java.time.LocalDate;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class SimulationV4Service {
    private final SimulationConfig config=new SimulationConfig(); private final StatefulSimulationEngine engine=new StatefulSimulationEngine(config);
    private final StateStore store; private final Map<String,StationState> states=new ConcurrentHashMap<>();
    public SimulationV4Service(StateStore store){this.store=store;}
    public StationState create(String id, LocalDate start, long seed){StationState s=StationState.initial(id,start,seed,config);states.put(id,s);return s;}
    public StationState state(String id){return require(id);}
    public SimulationSnapshot step(String id){return engine.step(require(id));}
    public List<SimulationSnapshot> run(String id,int days){if(days<1||days>20_000)throw new IllegalArgumentException("days must be 1..20000");List<SimulationSnapshot> out=new ArrayList<>();for(int i=0;i<days;i++)out.add(step(id));return out;}
    public void save(String id) throws IOException{store.save(id,require(id));}
    public StationState load(String id) throws IOException{StationState s=store.load(id);states.put(id,s);return s;}
    public Path exportCsv(String id,int days) throws IOException {List<SimulationSnapshot> rows=run(id,days);Path p=Paths.get("simulation-state-v4",id+"-daily.csv");Files.createDirectories(p.getParent());try(BufferedWriter w=Files.newBufferedWriter(p)){w.write("date,station_id,temperature_c,wind_speed_kmh,solar_generation_kw,wind_generation_kw,total_load_kw,generator_output_kw,generator_runtime_hours,fuel_stock_liters,fuel_consumed_today_liters,battery_soc_percent,total_population,mission,food_days,medical_kits,critical_spares,generator_health_percent,equipment_health_percent,storm,generator_failed\n");for(SimulationSnapshot x:rows)w.write(String.format(Locale.ROOT,"%s,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%d,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%s,%s%n",x.date(),x.stationId(),x.temperatureC(),x.windSpeedKmh(),x.solarGenerationKw(),x.windGenerationKw(),x.totalLoadKw(),x.generatorOutputKw(),x.generatorRuntimeHours(),x.fuelStockLitres(),x.fuelConsumedLitres(),x.batterySocPercent(),x.totalPopulation(),x.mission(),x.foodDays(),x.medicalKits(),x.criticalSpares(),x.generatorHealthPercent(),x.equipmentHealthPercent(),x.storm(),x.generatorFailed()));}return p;}
    private StationState require(String id){StationState s=states.get(id);if(s==null)throw new NoSuchElementException("No V4 station instance: "+id);return s;}
}
