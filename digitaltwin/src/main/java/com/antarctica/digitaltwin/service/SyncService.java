package com.antarctica.digitaltwin.service;

import com.antarctica.digitaltwin.dto.SyncRequest;
import com.antarctica.digitaltwin.model.SyncStatus;
import com.antarctica.digitaltwin.repository.SyncRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class SyncService {

    @Autowired
    private SyncRepository syncRepository;

    public SyncStatus getSyncStatus() {
        List<SyncStatus> all = syncRepository.findAll();
        return all.isEmpty() ? getDummySyncStatus() : all.get(0);
    }

    // Simple simulated sync: we just record that a sync happened and how many
    // records were pushed. No real offline queue or conflict resolution —
    // that would be overkill for a hackathon demo.
    public Map<String, Object> performSync(SyncRequest request) {
        List<SyncStatus> all = syncRepository.findAll();
        SyncStatus status = all.isEmpty() ? new SyncStatus() : all.get(0);

        status.setSyncStatus("ONLINE");
        status.setLastSync(LocalDateTime.now());
        status.setPendingRecords(0);
        syncRepository.save(status);

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("sync_status", "SUCCESS");
        response.put("synced_records", request.getRecords());
        response.put("sync_time", LocalDateTime.now());
        return response;
    }

    private SyncStatus getDummySyncStatus() {
        return new SyncStatus(null, "ONLINE", LocalDateTime.now(), 0);
    }
}