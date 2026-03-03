# 🔁 Recursiveness Implementation Guide

## Face Recognition Security Backend System

> **Last Updated:** March 3, 2026  
> **Project:** Spring Boot Security Backend  
> **Focus:** Recursive Algorithms & Data Structures

---

## 📚 Table of Contents

1. [Introduction to Recursiveness](#introduction-to-recursiveness)
2. [Current System Architecture](#current-system-architecture)
3. [Recursive Opportunities in This Project](#recursive-opportunities-in-this-project)
4. [Implementation Examples](#implementation-examples)
5. [Performance Considerations](#performance-considerations)
6. [Best Practices](#best-practices)

---

## 🎯 Introduction to Recursiveness

**Recursiveness** is a programming technique where a function calls itself to solve a problem by breaking it down into smaller, similar subproblems. In the context of this face recognition security system, recursive algorithms are particularly useful for:

- **Hierarchical data structures** (event trees, alert chains)
- **Traversal operations** (directory trees, nested detection events)
- **State machine transitions** (alert state history)
- **Aggregation logic** (combining multiple detection events)

---

## 🏗️ Current System Architecture

### Domain Model Overview

```
DetectionEvent (Parent)
    │
    ├── Frame (Associated)
    │     └── Face[] (One-to-Many)
    │
    └── Timestamp Chain (Temporal)
          └── Previous Events
                └── Previous Events (recursive chain)
```

### Key Components

- **EventProcessingService**: Processes detection events with semaphore-based concurrency control
- **FrameService**: Manages frame storage and retrieval
- **AlertService**: Handles alert state transitions
- **DetectionEvent**: Core entity representing a detection occurrence

---

## 🔄 Recursive Opportunities in This Project

### 1. **Event Relationship Tree** (High Priority)

**Use Case:** Track parent-child relationships between detection events for grouped scenarios.

**Scenario Example:**

```
Main Detection Event (Person entering)
  │
  ├── Sub-Event: Face detected (confidence: 0.95)
  │     └── Sub-Sub-Event: Gender classified (Male)
  │           └── Sub-Sub-Sub-Event: Age estimated (25-35)
  │
  └── Sub-Event: Tracking started
        └── Sub-Sub-Event: Movement pattern recorded
```

**Implementation Location:** `model/DetectionEvent.java`

```java
@Entity
@Table(name = "detection_events")
public class DetectionEvent {
    // ...existing fields...

    @ManyToOne
    @JoinColumn(name = "parent_event_id")
    private DetectionEvent parentEvent;

    @OneToMany(mappedBy = "parentEvent", cascade = CascadeType.ALL)
    private List<DetectionEvent> childEvents = new ArrayList<>();

    // Recursive method to get entire event tree
    public List<DetectionEvent> getAllDescendants() {
        List<DetectionEvent> descendants = new ArrayList<>();
        collectDescendants(this, descendants);
        return descendants;
    }

    private void collectDescendants(DetectionEvent event, List<DetectionEvent> accumulator) {
        for (DetectionEvent child : event.getChildEvents()) {
            accumulator.add(child);
            collectDescendants(child, accumulator); // RECURSIVE CALL
        }
    }

    // Calculate total confidence across event tree
    public double getTotalTreeConfidence() {
        return calculateTreeConfidence(this);
    }

    private double calculateTreeConfidence(DetectionEvent event) {
        double total = event.getConfidence();
        for (DetectionEvent child : event.getChildEvents()) {
            total += calculateTreeConfidence(child); // RECURSIVE CALL
        }
        return total;
    }
}
```

---

### 2. **Alert State History Chain** (Medium Priority)

**Use Case:** Track alert state transitions over time with backtracking capability.

**Scenario Example:**

```
Current State: CRITICAL_ALERT
  ↓ previous
Warning State: SUSPICIOUS_ACTIVITY
  ↓ previous
Normal State: NO_ENTITIES
  ↓ previous
Startup State: SYSTEM_READY
```

**Implementation Location:** `service/AlertService.java`

```java
@Service
public class AlertService {

    // Inner class for state tracking
    @Data
    public static class AlertState {
        private String state;
        private Instant timestamp;
        private DetectionEvent triggerEvent;
        private AlertState previousState; // Link to previous state

        public AlertState(String state, Instant timestamp, DetectionEvent event) {
            this.state = state;
            this.timestamp = timestamp;
            this.triggerEvent = event;
        }
    }

    private AlertState currentState;

    /**
     * Recursively traverse alert history
     * @return List of all historical states from newest to oldest
     */
    public List<AlertState> getAlertHistory() {
        List<AlertState> history = new ArrayList<>();
        traverseHistory(currentState, history);
        return history;
    }

    private void traverseHistory(AlertState state, List<AlertState> accumulator) {
        if (state == null) {
            return; // BASE CASE: reached the beginning
        }
        accumulator.add(state);
        traverseHistory(state.getPreviousState(), accumulator); // RECURSIVE CALL
    }

    /**
     * Find when system was last in a specific state
     * @param targetState State to search for
     * @return AlertState or null if not found
     */
    public AlertState findLastOccurrenceOfState(String targetState) {
        return searchStateRecursively(currentState, targetState);
    }

    private AlertState searchStateRecursively(AlertState current, String target) {
        if (current == null) {
            return null; // BASE CASE: not found
        }
        if (current.getState().equals(target)) {
            return current; // BASE CASE: found!
        }
        return searchStateRecursively(current.getPreviousState(), target); // RECURSIVE CALL
    }

    /**
     * Count state transitions in history
     */
    public int countStateTransitions() {
        return countTransitionsRecursively(currentState, 0);
    }

    private int countTransitionsRecursively(AlertState state, int count) {
        if (state == null || state.getPreviousState() == null) {
            return count; // BASE CASE
        }
        return countTransitionsRecursively(state.getPreviousState(), count + 1); // RECURSIVE CALL
    }
}
```

---

### 3. **Frame Storage Directory Tree** (Medium Priority)

**Use Case:** Organize frames in hierarchical directory structure by date/camera.

**Directory Structure:**

```
frames/
  ├── 2026/
  │   ├── 03/
  │   │   ├── 03/
  │   │   │   ├── camera-1/
  │   │   │   │   ├── frame-001.jpg
  │   │   │   │   └── frame-002.jpg
  │   │   │   └── camera-2/
  │   │   │       └── frame-001.jpg
```

**Implementation Location:** `service/FrameService.java`

```java
@Service
public class FrameService {

    /**
     * Recursively delete all frames in directory tree
     * @param directory Root directory to delete
     * @return Number of files deleted
     */
    public int deleteFrameDirectoryRecursively(Path directory) {
        return deleteDirectoryContents(directory);
    }

    private int deleteDirectoryContents(Path path) {
        int deletedCount = 0;

        if (!Files.exists(path)) {
            return 0; // BASE CASE: path doesn't exist
        }

        try {
            if (Files.isDirectory(path)) {
                // RECURSIVE CASE: process subdirectories first
                try (DirectoryStream<Path> entries = Files.newDirectoryStream(path)) {
                    for (Path entry : entries) {
                        deletedCount += deleteDirectoryContents(entry); // RECURSIVE CALL
                    }
                }
                // Delete the now-empty directory
                Files.delete(path);
                log.debug("Deleted directory: {}", path);
            } else {
                // BASE CASE: delete file
                Files.delete(path);
                deletedCount++;
                log.debug("Deleted file: {}", path);
            }
        } catch (IOException e) {
            log.error("Error deleting: {}", path, e);
        }

        return deletedCount;
    }

    /**
     * Recursively count frames in directory tree
     * @param directory Root directory
     * @return Total frame count
     */
    public long countFramesRecursively(Path directory) {
        return countFilesInDirectory(directory);
    }

    private long countFilesInDirectory(Path path) {
        if (!Files.exists(path) || !Files.isDirectory(path)) {
            return 0; // BASE CASE
        }

        long count = 0;
        try (DirectoryStream<Path> entries = Files.newDirectoryStream(path)) {
            for (Path entry : entries) {
                if (Files.isDirectory(entry)) {
                    count += countFilesInDirectory(entry); // RECURSIVE CALL
                } else {
                    count++; // Count this file
                }
            }
        } catch (IOException e) {
            log.error("Error counting files in: {}", path, e);
        }

        return count;
    }

    /**
     * Recursively find all frames matching a pattern
     */
    public List<Path> findFramesByPatternRecursively(Path root, String pattern) {
        List<Path> matches = new ArrayList<>();
        searchFiles(root, pattern, matches);
        return matches;
    }

    private void searchFiles(Path dir, String pattern, List<Path> accumulator) {
        if (!Files.exists(dir) || !Files.isDirectory(dir)) {
            return; // BASE CASE
        }

        try (DirectoryStream<Path> entries = Files.newDirectoryStream(dir)) {
            for (Path entry : entries) {
                if (Files.isDirectory(entry)) {
                    searchFiles(entry, pattern, accumulator); // RECURSIVE CALL
                } else if (entry.getFileName().toString().matches(pattern)) {
                    accumulator.add(entry);
                }
            }
        } catch (IOException e) {
            log.error("Error searching files in: {}", dir, e);
        }
    }
}
```

---

### 4. **Detection Event Aggregation** (Low Priority)

**Use Case:** Aggregate statistics across nested detection events.

**Implementation Location:** `service/DetectionEventService.java`

```java
@Service
public class DetectionEventService {

    /**
     * Aggregate confidence scores across entire event tree
     */
    public DetectionEventStatistics aggregateEventTree(Long rootEventId) {
        DetectionEvent root = eventRepository.findById(rootEventId)
            .orElseThrow(() -> new ResourceNotFoundException("Event not found"));

        return computeTreeStatistics(root);
    }

    private DetectionEventStatistics computeTreeStatistics(DetectionEvent event) {
        // BASE CASE: leaf node
        if (event.getChildEvents() == null || event.getChildEvents().isEmpty()) {
            return new DetectionEventStatistics(
                1,                      // count
                event.getConfidence(),  // totalConfidence
                event.getConfidence(),  // maxConfidence
                event.getConfidence()   // minConfidence
            );
        }

        // RECURSIVE CASE: aggregate children
        DetectionEventStatistics stats = new DetectionEventStatistics(1,
            event.getConfidence(),
            event.getConfidence(),
            event.getConfidence());

        for (DetectionEvent child : event.getChildEvents()) {
            DetectionEventStatistics childStats = computeTreeStatistics(child); // RECURSIVE CALL
            stats = stats.merge(childStats);
        }

        return stats;
    }

    @Data
    @AllArgsConstructor
    public static class DetectionEventStatistics {
        private int count;
        private double totalConfidence;
        private double maxConfidence;
        private double minConfidence;

        public double getAverageConfidence() {
            return count > 0 ? totalConfidence / count : 0.0;
        }

        public DetectionEventStatistics merge(DetectionEventStatistics other) {
            return new DetectionEventStatistics(
                this.count + other.count,
                this.totalConfidence + other.totalConfidence,
                Math.max(this.maxConfidence, other.maxConfidence),
                Math.min(this.minConfidence, other.minConfidence)
            );
        }
    }
}
```

---

### 5. **Recursive Backtracking for Alert Patterns** (Advanced)

**Use Case:** Find sequence of events that led to critical alert.

**Implementation Location:** `service/AlertService.java`

```java
@Service
public class AlertService {

    /**
     * Find all paths in event history that match a specific pattern
     * Example: Find all sequences that escalated from NORMAL -> WARNING -> CRITICAL
     */
    public List<List<AlertState>> findAlertPatterns(List<String> pattern) {
        List<List<AlertState>> allPaths = new ArrayList<>();
        List<AlertState> currentPath = new ArrayList<>();

        findPatternRecursively(currentState, pattern, 0, currentPath, allPaths);

        return allPaths;
    }

    private void findPatternRecursively(
            AlertState current,
            List<String> pattern,
            int patternIndex,
            List<AlertState> currentPath,
            List<List<AlertState>> allPaths) {

        if (current == null) {
            return; // BASE CASE: reached end of history
        }

        // Check if current state matches pattern
        if (current.getState().equals(pattern.get(patternIndex))) {
            currentPath.add(current);

            // BASE CASE: complete pattern found!
            if (patternIndex == pattern.size() - 1) {
                allPaths.add(new ArrayList<>(currentPath)); // Save copy
            } else {
                // RECURSIVE CASE: continue searching for next pattern element
                findPatternRecursively(
                    current.getPreviousState(),
                    pattern,
                    patternIndex + 1,
                    currentPath,
                    allPaths
                );
            }

            // BACKTRACK
            currentPath.remove(currentPath.size() - 1);
        }

        // Try searching from previous state (explore other paths)
        findPatternRecursively(
            current.getPreviousState(),
            pattern,
            patternIndex,
            currentPath,
            allPaths
        );
    }
}
```

---

## ⚡ Performance Considerations

### Stack Overflow Prevention

**Problem:** Deep recursion can cause stack overflow with Java's default stack size.

**Solution:**

```java
// For deep recursion, use iterative approach with explicit stack
public List<DetectionEvent> getAllDescendantsIterative() {
    List<DetectionEvent> descendants = new ArrayList<>();
    Stack<DetectionEvent> stack = new Stack<>();
    stack.push(this);

    while (!stack.isEmpty()) {
        DetectionEvent current = stack.pop();
        descendants.add(current);

        // Add children in reverse order to maintain traversal order
        List<DetectionEvent> children = current.getChildEvents();
        for (int i = children.size() - 1; i >= 0; i--) {
            stack.push(children.get(i));
        }
    }

    return descendants;
}
```

### Tail Call Optimization

**Java doesn't optimize tail calls**, so consider iterative alternatives for performance-critical paths:

```java
// Recursive (tail call - NOT optimized in Java)
private int countRecursive(AlertState state, int acc) {
    if (state == null) return acc;
    return countRecursive(state.getPreviousState(), acc + 1);
}

// Iterative (better performance)
private int countIterative(AlertState state) {
    int count = 0;
    while (state != null) {
        count++;
        state = state.getPreviousState();
    }
    return count;
}
```

### Memoization for Repeated Calculations

```java
@Service
public class EventProcessingService {

    // Cache for tree statistics
    private final Map<Long, DetectionEventStatistics> statsCache = new ConcurrentHashMap<>();

    public DetectionEventStatistics getTreeStatistics(Long eventId) {
        return statsCache.computeIfAbsent(eventId, id -> {
            DetectionEvent event = repository.findById(id).orElseThrow();
            return computeTreeStatisticsRecursively(event);
        });
    }
}
```

---

## 🎯 Best Practices

### 1. **Always Define Base Case First**

```java
// ✅ GOOD: Clear base case
private void traverse(Node node) {
    if (node == null) return; // BASE CASE FIRST
    process(node);
    traverse(node.getLeft());
    traverse(node.getRight());
}

// ❌ BAD: No clear base case
private void traverse(Node node) {
    process(node); // Will crash on null!
    traverse(node.getLeft());
}
```

### 2. **Limit Recursion Depth**

```java
private static final int MAX_DEPTH = 100;

private void traverseWithLimit(Node node, int depth) {
    if (node == null || depth > MAX_DEPTH) {
        if (depth > MAX_DEPTH) {
            log.warn("Maximum recursion depth exceeded!");
        }
        return;
    }
    // ...recursive logic
    traverseWithLimit(node.getNext(), depth + 1);
}
```

### 3. **Use Iterative for Performance-Critical Code**

Use recursion for **clarity and maintainability**, not performance. For hot paths (called frequently), prefer iterative solutions.

### 4. **Document Time and Space Complexity**

```java
/**
 * Recursively aggregate event tree statistics
 *
 * Time Complexity: O(n) where n = total events in tree
 * Space Complexity: O(h) where h = height of tree (call stack)
 *
 * @param event Root event
 * @return Aggregated statistics
 */
private Stats computeStats(DetectionEvent event) {
    // ...implementation
}
```

---

## 📊 When to Use Recursion vs. Iteration

| Use Recursion When...                      | Use Iteration When...         |
| ------------------------------------------ | ----------------------------- |
| Working with tree/graph structures         | Working with flat lists       |
| Problem naturally divides into subproblems | Simple sequential processing  |
| Code clarity is priority                   | Performance is critical       |
| Depth is bounded (< 1000 levels)           | Handling very deep structures |
| Backtracking is needed                     | Memory is constrained         |

---

## 🚀 Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

- [ ] Add parent-child relationship to `DetectionEvent` entity
- [ ] Implement basic tree traversal methods
- [ ] Add unit tests for recursive functions

### Phase 2: Alert History (Week 3-4)

- [ ] Create `AlertState` model with previous state link
- [ ] Implement recursive state history traversal
- [ ] Add pattern matching with backtracking

### Phase 3: File System Operations (Week 5-6)

- [ ] Implement recursive directory operations in `FrameService`
- [ ] Add recursive file search and cleanup
- [ ] Performance testing with large file trees

### Phase 4: Optimization (Week 7-8)

- [ ] Add memoization for expensive calculations
- [ ] Convert performance-critical recursions to iteration
- [ ] Load testing and stack depth analysis

---

## 📝 Testing Recursive Functions

```java
@SpringBootTest
class RecursiveAlgorithmsTest {

    @Test
    void testEventTreeTraversal() {
        // Arrange: Create tree
        DetectionEvent root = new DetectionEvent();
        DetectionEvent child1 = new DetectionEvent();
        DetectionEvent child2 = new DetectionEvent();
        root.addChild(child1);
        root.addChild(child2);

        // Act: Traverse recursively
        List<DetectionEvent> descendants = root.getAllDescendants();

        // Assert
        assertEquals(2, descendants.size());
        assertTrue(descendants.contains(child1));
        assertTrue(descendants.contains(child2));
    }

    @Test
    void testRecursionDepthLimit() {
        // Arrange: Create deep chain
        AlertState root = new AlertState("ROOT", Instant.now(), null);
        AlertState current = root;
        for (int i = 0; i < 150; i++) {
            AlertState next = new AlertState("STATE_" + i, Instant.now(), null);
            next.setPreviousState(current);
            current = next;
        }

        // Act & Assert: Should handle gracefully
        assertDoesNotThrow(() -> alertService.getAlertHistory());
    }
}
```

---

## 🎓 Conclusion

Recursiveness adds powerful capabilities to this face recognition security backend:

1. **Event Hierarchies**: Model complex detection scenarios with parent-child relationships
2. **Alert State Tracking**: Maintain complete history with backtracking capabilities
3. **File System Operations**: Efficient cleanup and search operations
4. **Pattern Detection**: Find sequences that led to critical alerts

Always balance **code clarity** with **performance** when choosing recursive vs. iterative approaches. For this security system with bounded data structures (limited event depth, manageable file trees), recursion provides elegant solutions without significant performance penalties.

---

## 📚 Additional Resources

- [Java Recursion Best Practices](https://docs.oracle.com/javase/tutorial/java/javaOO/methods.html)
- [Spring Boot Performance Tuning](https://spring.io/blog/2020/06/15/what-s-new-in-spring-boot-2-3)
- [Algorithm Complexity Analysis](https://www.bigocheatsheet.com/)

---

**Author:** Spring Boot Security Backend Team  
**Version:** 1.0.0  
**Last Updated:** March 3, 2026
