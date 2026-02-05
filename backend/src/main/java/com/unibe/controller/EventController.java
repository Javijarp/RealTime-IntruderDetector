import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/events")
public class EventController {

    private final DetectionService detectionService;

    @Autowired
    public EventController(DetectionService detectionService) {
        this.detectionService = detectionService;
    }

    @PostMapping
    public ResponseEntity<DetectionEvent> createEvent(@RequestBody DetectionEvent event) {
        DetectionEvent createdEvent = detectionService.saveEvent(event);
        return ResponseEntity.ok(createdEvent);
    }

    @GetMapping
    public ResponseEntity<List<DetectionEvent>> getAllEvents() {
        List<DetectionEvent> events = detectionService.getAllEvents();
        return ResponseEntity.ok(events);
    }
}