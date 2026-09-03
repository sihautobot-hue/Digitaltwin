package com.antarctica.digitaltwin.simulator.v4;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;
import java.io.IOException;
import java.nio.file.*;

/** Explicit local checkpoint store. A caller controls when state is persisted. */
@Component
public class StateStore {
    private final ObjectMapper mapper = new ObjectMapper().findAndRegisterModules();
    private final Path root = Paths.get("simulation-state-v4");
    public void save(String name, StationState state) throws IOException { Files.createDirectories(root); mapper.writeValue(root.resolve(safe(name)+".json").toFile(), state); }
    public StationState load(String name) throws IOException { return mapper.readValue(root.resolve(safe(name)+".json").toFile(), StationState.class); }
    private String safe(String value) { return value.replaceAll("[^A-Za-z0-9_-]", "_"); }
}
