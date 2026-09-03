package com.antarctica.digitaltwin.controller;

import com.antarctica.digitaltwin.simulator.v4.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.io.IOException; import java.time.LocalDate; import java.util.*;

/** Standalone V4 digital-twin API. It has no ML dependency. */
@RestController @RequestMapping("/simulation/v4")
public class SimulationV4Controller {
    private final SimulationV4Service service; public SimulationV4Controller(SimulationV4Service service){this.service=service;}
    @PostMapping("/stations/{id}") public StationState create(@PathVariable String id,@RequestParam(defaultValue="2024-01-01") LocalDate start,@RequestParam(defaultValue="42") long seed){return service.create(id,start,seed);}
    @GetMapping("/stations/{id}") public StationState state(@PathVariable String id){return service.state(id);}
    @PostMapping("/stations/{id}/step") public SimulationSnapshot step(@PathVariable String id){return service.step(id);}
    @PostMapping("/stations/{id}/run") public List<SimulationSnapshot> run(@PathVariable String id,@RequestParam int days){return service.run(id,days);}
    @PostMapping("/stations/{id}/save") public Map<String,String> save(@PathVariable String id)throws IOException{service.save(id);return Map.of("status","saved");}
    @PostMapping("/stations/{id}/load") public StationState load(@PathVariable String id)throws IOException{return service.load(id);}
    @PostMapping("/stations/{id}/export") public Map<String,String> export(@PathVariable String id,@RequestParam(defaultValue="365") int days)throws IOException{return Map.of("path",service.exportCsv(id,days).toString());}
}
