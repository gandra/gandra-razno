# Breach Resolution API Analysis - SLA Breach Management

## 📋 Problem Statement

### Trenutna Situacija

Trenutno, `SlaBreach` entitet ima fields za resolution i acknowledgement:

```java
@Entity
@Table(name = "sla_breach")
public class SlaBreach extends BaseEntity {
    // Resolution fields
    private Boolean isResolved = false;
    private LocalDateTime resolvedAt;
    private String resolvedBy;
    private String resolutionNotes;

    // Acknowledgment fields
    private Boolean isAcknowledged = false;
    private LocalDateTime acknowledgedAt;
    private String acknowledgedBy;
    private String acknowledgmentNotes;

    // Business logic methods (exist but not exposed via API)
    public void markAsResolved(String resolvedBy, String notes) { ... }
    public void acknowledge(String acknowledgedBy, String notes) { ... }
}
```

**Ali:**
- ❌ **Nema REST API** za acknowledge/resolve breaches
- ❌ **Nema UI** gde ops tim može da upravlja breachovima
- ❌ **Nema workflow** za breach lifecycle management
- ❌ **Nema reporting** za breach metrics (MTTA, MTTR, etc.)

### 🚨 Problemi

1. **Manual database updates**: Ops tim mora direktno da menja bazu
2. **No audit trail**: Nema jasnog history-ja ko je šta uradio
3. **No notifications**: Niko se ne notifikuje kad je breach resolved
4. **No metrics**: Nema KPI-eva (Mean Time To Acknowledge, Mean Time To Resolve)
5. **No escalation**: Nema automatske escalation-a za unacknowledged breaches

---

## 🎯 Cilj

Kreirati kompletan Breach Management API koji omogućava:

1. **Lifecycle Management**: Acknowledge → Investigate → Resolve
2. **Audit Trail**: Ko, kada, zašto
3. **Notifications**: Notifikacije stakeholder-ima
4. **Metrics & Reporting**: MTTA, MTTR, breach trends
5. **Escalation**: Automatska escalation za critical breaches
6. **Comments/Notes**: Communication thread za breach investigation

---

## 🏗️ Breach Lifecycle States

### State Machine

```
         ┌─────────────┐
         │   DETECTED  │ (initial state)
         └──────┬──────┘
                │
                │ acknowledge()
                ▼
         ┌─────────────┐
         │ACKNOWLEDGED │
         └──────┬──────┘
                │
                │ startInvestigation()
                ▼
         ┌─────────────┐
         │INVESTIGATING│
         └──────┬──────┘
                │
                │ resolve()
                ▼
         ┌─────────────┐
         │  RESOLVED   │ (terminal state)
         └─────────────┘
```

### State Transitions

| From State | Action | To State | Trigger |
|------------|--------|----------|---------|
| DETECTED | acknowledge() | ACKNOWLEDGED | Ops team acknowledges breach |
| ACKNOWLEDGED | startInvestigation() | INVESTIGATING | Ops starts root cause analysis |
| INVESTIGATING | resolve() | RESOLVED | Issue fixed, breach closed |
| DETECTED | resolve() | RESOLVED | Quick fix (skip investigation) |

---

## 🔧 Pristup 1: Simple REST API (Minimal ✅)

### Opis

Minimalistički pristup - samo basic CRUD operacije za acknowledge i resolve.

### Implementacija

**1. Create BreachManagementController:**

```java
@RestController
@RequestMapping("/api/sla/breaches")
@RequiredArgsConstructor
@Slf4j
public class BreachManagementController {

    private final BreachManagementService breachManagementService;

    /**
     * Acknowledge a breach.
     * POST /api/sla/breaches/{breachId}/acknowledge
     */
    @PostMapping("/{breachId}/acknowledge")
    public ResponseEntity<SlaBreachDto> acknowledgeBreach(
            @PathVariable UUID breachId,
            @RequestBody @Valid AcknowledgeBreachRequest request) {

        log.info("Acknowledging breach: {}", breachId);

        SlaBreach breach = breachManagementService.acknowledgeBreach(
                breachId,
                request.getAcknowledgedBy(),
                request.getNotes()
        );

        SlaBreachDto dto = breachMapper.toDto(breach);
        return ResponseEntity.ok(dto);
    }

    /**
     * Resolve a breach.
     * POST /api/sla/breaches/{breachId}/resolve
     */
    @PostMapping("/{breachId}/resolve")
    public ResponseEntity<SlaBreachDto> resolveBreach(
            @PathVariable UUID breachId,
            @RequestBody @Valid ResolveBreachRequest request) {

        log.info("Resolving breach: {}", breachId);

        SlaBreach breach = breachManagementService.resolveBreach(
                breachId,
                request.getResolvedBy(),
                request.getResolutionNotes()
        );

        SlaBreachDto dto = breachMapper.toDto(breach);
        return ResponseEntity.ok(dto);
    }

    /**
     * Get breach details.
     * GET /api/sla/breaches/{breachId}
     */
    @GetMapping("/{breachId}")
    public ResponseEntity<SlaBreachDto> getBreachDetails(@PathVariable UUID breachId) {
        SlaBreach breach = breachManagementService.getBreachById(breachId);
        SlaBreachDto dto = breachMapper.toDto(breach);
        return ResponseEntity.ok(dto);
    }

    /**
     * List all breaches with filters.
     * GET /api/sla/breaches?status=UNRESOLVED&severity=CRITICAL
     */
    @GetMapping
    public ResponseEntity<List<SlaBreachDto>> listBreaches(
            @RequestParam(required = false) BreachStatus status,
            @RequestParam(required = false) String severity,
            @RequestParam(required = false) UUID slaDefinitionId) {

        List<SlaBreach> breaches = breachManagementService.listBreaches(
                status, severity, slaDefinitionId
        );

        List<SlaBreachDto> dtos = breaches.stream()
                .map(breachMapper::toDto)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }
}
```

**2. Request DTOs:**

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AcknowledgeBreachRequest {

    @NotBlank(message = "acknowledgedBy is required")
    private String acknowledgedBy;

    @Size(max = 1000, message = "Notes max 1000 characters")
    private String notes;
}

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ResolveBreachRequest {

    @NotBlank(message = "resolvedBy is required")
    private String resolvedBy;

    @NotBlank(message = "resolutionNotes is required")
    @Size(max = 2000, message = "Resolution notes max 2000 characters")
    private String resolutionNotes;
}
```

**3. BreachManagementService:**

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class BreachManagementService {

    private final SlaBreachRepository breachRepository;

    @Transactional
    public SlaBreach acknowledgeBreach(UUID breachId, String acknowledgedBy, String notes) {
        SlaBreach breach = breachRepository.findById(breachId)
                .orElseThrow(() -> new ResourceNotFoundException("Breach not found: " + breachId));

        if (breach.getIsAcknowledged()) {
            throw new IllegalStateException("Breach already acknowledged");
        }

        if (breach.getIsResolved()) {
            throw new IllegalStateException("Cannot acknowledge resolved breach");
        }

        // Use existing business logic method
        breach.acknowledge(acknowledgedBy, notes);

        SlaBreach saved = breachRepository.save(breach);

        log.info("✅ Breach {} acknowledged by {}", breachId, acknowledgedBy);

        return saved;
    }

    @Transactional
    public SlaBreach resolveBreach(UUID breachId, String resolvedBy, String notes) {
        SlaBreach breach = breachRepository.findById(breachId)
                .orElseThrow(() -> new ResourceNotFoundException("Breach not found: " + breachId));

        if (breach.getIsResolved()) {
            throw new IllegalStateException("Breach already resolved");
        }

        // Use existing business logic method
        breach.markAsResolved(resolvedBy, notes);

        SlaBreach saved = breachRepository.save(breach);

        log.info("✅ Breach {} resolved by {}", breachId, resolvedBy);

        return saved;
    }

    @Transactional(readOnly = true)
    public SlaBreach getBreachById(UUID breachId) {
        return breachRepository.findById(breachId)
                .orElseThrow(() -> new ResourceNotFoundException("Breach not found: " + breachId));
    }

    @Transactional(readOnly = true)
    public List<SlaBreach> listBreaches(BreachStatus status, String severity, UUID slaDefinitionId) {
        // Use repository filters
        if (status == BreachStatus.UNRESOLVED) {
            return breachRepository.findByIsResolvedFalse();
        } else if (status == BreachStatus.UNACKNOWLEDGED) {
            return breachRepository.findByIsAcknowledgedFalseAndIsResolvedFalse();
        }

        return breachRepository.findAll();
    }
}
```

**4. Repository queries:**

```java
@Repository
public interface SlaBreachRepository extends JpaRepository<SlaBreach, UUID> {

    List<SlaBreach> findByIsResolvedFalse();

    List<SlaBreach> findByIsAcknowledgedFalseAndIsResolvedFalse();

    List<SlaBreach> findBySeverityAndIsResolvedFalse(String severity);

    @Query("SELECT sb FROM SlaBreach sb " +
           "WHERE sb.slaResult.slaDefinition.id = :definitionId " +
           "AND sb.isResolved = false")
    List<SlaBreach> findUnresolvedByDefinitionId(@Param("definitionId") UUID definitionId);
}
```

### Prednosti ✅

1. **Quick implementation**: 2-3 sata rada
2. **Simple**: Nema complex state machine
3. **Uses existing entity logic**: Koristi postojeće `SlaBreach` metode
4. **RESTful**: Standard REST API pattern

### Mane ⚠️

1. **No workflow**: Ne podržava kompleksnije workflow-e
2. **No state validation**: Minimalna validacija state transitions
3. **No notifications**: Ne notifikuje stakeholder-e
4. **No audit trail**: Minimalan audit (samo ko i kada)

### Kada koristiti

- **MVP**: Quick solution za immediate need
- **Simple use case**: Ops tim samo treba da close breaches
- **Small team**: Mali tim, manual coordination

---

## 🔧 Pristup 2: State Machine sa Workflow (Recommended ✅)

### Opis

Implementacija pravog state machine-a sa validacijom transitions i workflow support.

### Implementacija

**1. Breach State Enum:**

```java
public enum BreachState {
    DETECTED("Detected", "Breach detected, awaiting acknowledgement"),
    ACKNOWLEDGED("Acknowledged", "Breach acknowledged by ops team"),
    INVESTIGATING("Investigating", "Root cause analysis in progress"),
    RESOLVED("Resolved", "Breach resolved and closed");

    private final String displayName;
    private final String description;

    BreachState(String displayName, String description) {
        this.displayName = displayName;
        this.description = description;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getDescription() {
        return description;
    }

    /**
     * Valid transitions from current state.
     */
    public List<BreachState> getValidTransitions() {
        return switch (this) {
            case DETECTED -> List.of(ACKNOWLEDGED, RESOLVED);
            case ACKNOWLEDGED -> List.of(INVESTIGATING, RESOLVED);
            case INVESTIGATING -> List.of(RESOLVED);
            case RESOLVED -> List.of(); // Terminal state
        };
    }

    public boolean canTransitionTo(BreachState targetState) {
        return getValidTransitions().contains(targetState);
    }
}
```

**2. Update SlaBreach entity:**

```java
@Entity
@Table(name = "sla_breach")
public class SlaBreach extends BaseEntity {

    // ... existing fields ...

    /**
     * Breach lifecycle state.
     * Replaces isAcknowledged/isResolved boolean flags with proper state machine.
     */
    @Column(name = "state", nullable = false, length = 20)
    @Enumerated(EnumType.STRING)
    private BreachState state = BreachState.DETECTED;

    /**
     * Assigned to user (for tracking responsibility).
     */
    @Column(name = "assigned_to", length = 255)
    private String assignedTo;

    /**
     * Current state entered at timestamp.
     */
    @Column(name = "state_changed_at")
    private LocalDateTime stateChangedAt;

    // State transition method
    public void transitionTo(BreachState newState, String performedBy, String notes) {
        if (!this.state.canTransitionTo(newState)) {
            throw new IllegalStateException(
                String.format("Invalid state transition from %s to %s", this.state, newState)
            );
        }

        this.state = newState;
        this.stateChangedAt = LocalDateTime.now();
        this.updatedBy = performedBy;

        // Update legacy flags for backward compatibility
        if (newState == BreachState.ACKNOWLEDGED) {
            this.isAcknowledged = true;
            this.acknowledgedAt = LocalDateTime.now();
            this.acknowledgedBy = performedBy;
            this.acknowledgmentNotes = notes;
        } else if (newState == BreachState.RESOLVED) {
            this.isResolved = true;
            this.resolvedAt = LocalDateTime.now();
            this.resolvedBy = performedBy;
            this.resolutionNotes = notes;
        }
    }

    public boolean canTransitionTo(BreachState targetState) {
        return this.state.canTransitionTo(targetState);
    }

    public List<BreachState> getAvailableTransitions() {
        return this.state.getValidTransitions();
    }
}
```

**3. Migration:**

```sql
-- V11__add_breach_state_machine.sql
ALTER TABLE sla_breach
    ADD COLUMN state VARCHAR(20) NOT NULL DEFAULT 'DETECTED',
    ADD COLUMN assigned_to VARCHAR(255),
    ADD COLUMN state_changed_at DATETIME,
    ADD INDEX idx_breach_state (state),
    ADD INDEX idx_breach_assigned (assigned_to);

-- Migrate existing data
UPDATE sla_breach
SET state = CASE
    WHEN is_resolved = true THEN 'RESOLVED'
    WHEN is_acknowledged = true THEN 'ACKNOWLEDGED'
    ELSE 'DETECTED'
END,
state_changed_at = COALESCE(resolved_at, acknowledged_at, detected_at);
```

**4. Enhanced Service:**

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class BreachManagementService {

    private final SlaBreachRepository breachRepository;
    private final BreachStateTransitionRepository transitionRepository;
    private final ApplicationEventPublisher eventPublisher;

    /**
     * Transition breach to new state.
     * Generic method that handles all state transitions.
     */
    @Transactional
    public SlaBreach transitionBreachState(
            UUID breachId,
            BreachState targetState,
            String performedBy,
            String notes) {

        SlaBreach breach = breachRepository.findById(breachId)
                .orElseThrow(() -> new ResourceNotFoundException("Breach not found: " + breachId));

        BreachState previousState = breach.getState();

        // Validate transition
        if (!breach.canTransitionTo(targetState)) {
            throw new IllegalStateException(
                String.format("Cannot transition breach %s from %s to %s. Valid transitions: %s",
                    breachId, previousState, targetState,
                    breach.getAvailableTransitions())
            );
        }

        // Perform transition
        breach.transitionTo(targetState, performedBy, notes);

        // Save breach
        SlaBreach saved = breachRepository.save(breach);

        // Save transition history
        BreachStateTransition transition = BreachStateTransition.builder()
                .breach(saved)
                .fromState(previousState)
                .toState(targetState)
                .performedBy(performedBy)
                .notes(notes)
                .transitionedAt(LocalDateTime.now())
                .build();

        transitionRepository.save(transition);

        // Publish event for notifications/audit
        eventPublisher.publishEvent(new BreachStateChangedEvent(
                this, breachId, previousState, targetState, performedBy
        ));

        log.info("✅ Breach {} transitioned from {} to {} by {}",
                breachId, previousState, targetState, performedBy);

        return saved;
    }

    /**
     * Convenience methods for common transitions.
     */
    public SlaBreach acknowledgeBreach(UUID breachId, String acknowledgedBy, String notes) {
        return transitionBreachState(breachId, BreachState.ACKNOWLEDGED, acknowledgedBy, notes);
    }

    public SlaBreach startInvestigation(UUID breachId, String investigator, String notes) {
        return transitionBreachState(breachId, BreachState.INVESTIGATING, investigator, notes);
    }

    public SlaBreach resolveBreach(UUID breachId, String resolvedBy, String notes) {
        return transitionBreachState(breachId, BreachState.RESOLVED, resolvedBy, notes);
    }

    /**
     * Assign breach to user.
     */
    @Transactional
    public SlaBreach assignBreach(UUID breachId, String assignedTo, String assignedBy) {
        SlaBreach breach = breachRepository.findById(breachId)
                .orElseThrow(() -> new ResourceNotFoundException("Breach not found: " + breachId));

        breach.setAssignedTo(assignedTo);
        breach.setUpdatedBy(assignedBy);
        breach.setUpdatedAt(LocalDateTime.now());

        SlaBreach saved = breachRepository.save(breach);

        eventPublisher.publishEvent(new BreachAssignedEvent(
                this, breachId, assignedTo, assignedBy
        ));

        log.info("✅ Breach {} assigned to {} by {}", breachId, assignedTo, assignedBy);

        return saved;
    }

    /**
     * Get breach state transition history.
     */
    @Transactional(readOnly = true)
    public List<BreachStateTransition> getBreachHistory(UUID breachId) {
        return transitionRepository.findByBreachIdOrderByTransitionedAtAsc(breachId);
    }
}
```

**5. State Transition History Entity:**

```java
@Entity
@Table(name = "breach_state_transition", indexes = {
    @Index(name = "idx_transition_breach", columnList = "breach_id"),
    @Index(name = "idx_transition_time", columnList = "transitioned_at")
})
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class BreachStateTransition {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @UuidGenerator
    @JdbcTypeCode(SqlTypes.CHAR)
    @Column(name = "id", updatable = false, nullable = false, columnDefinition = "char(36)")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "breach_id", nullable = false)
    private SlaBreach breach;

    @Column(name = "from_state", nullable = false, length = 20)
    @Enumerated(EnumType.STRING)
    private BreachState fromState;

    @Column(name = "to_state", nullable = false, length = 20)
    @Enumerated(EnumType.STRING)
    private BreachState toState;

    @Column(name = "performed_by", nullable = false, length = 255)
    private String performedBy;

    @Column(name = "notes", length = 2000)
    private String notes;

    @Column(name = "transitioned_at", nullable = false)
    private LocalDateTime transitionedAt;
}
```

**6. Enhanced Controller:**

```java
@RestController
@RequestMapping("/api/sla/breaches")
@RequiredArgsConstructor
@Slf4j
public class BreachManagementController {

    private final BreachManagementService breachManagementService;
    private final BreachMapper breachMapper;

    /**
     * Get available state transitions for breach.
     * GET /api/sla/breaches/{breachId}/transitions
     */
    @GetMapping("/{breachId}/transitions")
    public ResponseEntity<List<BreachStateDto>> getAvailableTransitions(@PathVariable UUID breachId) {
        SlaBreach breach = breachManagementService.getBreachById(breachId);

        List<BreachStateDto> transitions = breach.getAvailableTransitions().stream()
                .map(state -> BreachStateDto.builder()
                        .state(state)
                        .displayName(state.getDisplayName())
                        .description(state.getDescription())
                        .build())
                .collect(Collectors.toList());

        return ResponseEntity.ok(transitions);
    }

    /**
     * Transition breach to new state.
     * POST /api/sla/breaches/{breachId}/transition
     */
    @PostMapping("/{breachId}/transition")
    public ResponseEntity<SlaBreachDto> transitionBreach(
            @PathVariable UUID breachId,
            @RequestBody @Valid BreachTransitionRequest request) {

        SlaBreach breach = breachManagementService.transitionBreachState(
                breachId,
                request.getTargetState(),
                request.getPerformedBy(),
                request.getNotes()
        );

        SlaBreachDto dto = breachMapper.toDto(breach);
        return ResponseEntity.ok(dto);
    }

    /**
     * Assign breach to user.
     * POST /api/sla/breaches/{breachId}/assign
     */
    @PostMapping("/{breachId}/assign")
    public ResponseEntity<SlaBreachDto> assignBreach(
            @PathVariable UUID breachId,
            @RequestBody @Valid AssignBreachRequest request) {

        SlaBreach breach = breachManagementService.assignBreach(
                breachId,
                request.getAssignedTo(),
                request.getAssignedBy()
        );

        SlaBreachDto dto = breachMapper.toDto(breach);
        return ResponseEntity.ok(dto);
    }

    /**
     * Get breach state transition history.
     * GET /api/sla/breaches/{breachId}/history
     */
    @GetMapping("/{breachId}/history")
    public ResponseEntity<List<BreachStateTransitionDto>> getBreachHistory(@PathVariable UUID breachId) {
        List<BreachStateTransition> history = breachManagementService.getBreachHistory(breachId);

        List<BreachStateTransitionDto> dtos = history.stream()
                .map(transition -> BreachStateTransitionDto.builder()
                        .id(transition.getId())
                        .fromState(transition.getFromState())
                        .toState(transition.getToState())
                        .performedBy(transition.getPerformedBy())
                        .notes(transition.getNotes())
                        .transitionedAt(transition.getTransitionedAt())
                        .build())
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }
}
```

### Prednosti ✅

1. **Proper state machine**: Validacija svih transitions
2. **Audit trail**: Kompletan history u `breach_state_transition` tabeli
3. **Extensible**: Lako dodati nove states (e.g., ESCALATED)
4. **Event-driven**: Publishes events za notifications
5. **Assignment tracking**: Prati ko je responsible za breach
6. **Backward compatible**: Održava `isAcknowledged`/`isResolved` flags

### Mane ⚠️

1. **More complex**: Više code i tabela
2. **Migration required**: Potrebna migracija postojećih podataka
3. **Learning curve**: Tim mora da razume state machine

### Kada koristiti

- **Production system**: Pravi production-ready solution
- **Complex workflows**: Potrebni multiple states i transitions
- **Audit requirements**: Potreban kompletan audit trail
- **Team collaboration**: Više ljudi upravlja breachovima

---

## 🔧 Pristup 3: Comments & Collaboration Thread

### Opis

Dodavanje comment/note sistema za breach-eve - kao GitHub issues.

### Implementacija

**1. BreachComment Entity:**

```java
@Entity
@Table(name = "breach_comment", indexes = {
    @Index(name = "idx_comment_breach", columnList = "breach_id"),
    @Index(name = "idx_comment_created", columnList = "created_at")
})
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class BreachComment {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @UuidGenerator
    @JdbcTypeCode(SqlTypes.CHAR)
    @Column(name = "id", updatable = false, nullable = false, columnDefinition = "char(36)")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "breach_id", nullable = false)
    private SlaBreach breach;

    @Column(name = "comment_text", nullable = false, length = 5000)
    private String commentText;

    @Column(name = "comment_type", nullable = false, length = 20)
    @Enumerated(EnumType.STRING)
    private CommentType commentType; // COMMENT, ROOT_CAUSE, RESOLUTION, STATUS_UPDATE

    @Column(name = "created_by", nullable = false, length = 255)
    private String createdBy;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "is_internal", nullable = false)
    private Boolean isInternal = false; // Internal notes vs customer-visible
}

public enum CommentType {
    COMMENT("General comment"),
    ROOT_CAUSE("Root cause analysis"),
    RESOLUTION("Resolution details"),
    STATUS_UPDATE("Status update"),
    ESCALATION("Escalation note");

    private final String displayName;

    CommentType(String displayName) {
        this.displayName = displayName;
    }

    public String getDisplayName() {
        return displayName;
    }
}
```

**2. Comment API:**

```java
@RestController
@RequestMapping("/api/sla/breaches/{breachId}/comments")
@RequiredArgsConstructor
public class BreachCommentController {

    private final BreachCommentService commentService;

    /**
     * Add comment to breach.
     * POST /api/sla/breaches/{breachId}/comments
     */
    @PostMapping
    public ResponseEntity<BreachCommentDto> addComment(
            @PathVariable UUID breachId,
            @RequestBody @Valid AddCommentRequest request) {

        BreachComment comment = commentService.addComment(
                breachId,
                request.getCommentText(),
                request.getCommentType(),
                request.getCreatedBy(),
                request.getIsInternal()
        );

        BreachCommentDto dto = commentMapper.toDto(comment);
        return ResponseEntity.status(HttpStatus.CREATED).body(dto);
    }

    /**
     * List all comments for breach.
     * GET /api/sla/breaches/{breachId}/comments
     */
    @GetMapping
    public ResponseEntity<List<BreachCommentDto>> listComments(@PathVariable UUID breachId) {
        List<BreachComment> comments = commentService.getCommentsByBreachId(breachId);

        List<BreachCommentDto> dtos = comments.stream()
                .map(commentMapper::toDto)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }

    /**
     * Update comment.
     * PUT /api/sla/breaches/{breachId}/comments/{commentId}
     */
    @PutMapping("/{commentId}")
    public ResponseEntity<BreachCommentDto> updateComment(
            @PathVariable UUID breachId,
            @PathVariable UUID commentId,
            @RequestBody @Valid UpdateCommentRequest request) {

        BreachComment comment = commentService.updateComment(
                commentId,
                request.getCommentText(),
                request.getUpdatedBy()
        );

        BreachCommentDto dto = commentMapper.toDto(comment);
        return ResponseEntity.ok(dto);
    }

    /**
     * Delete comment.
     * DELETE /api/sla/breaches/{breachId}/comments/{commentId}
     */
    @DeleteMapping("/{commentId}")
    public ResponseEntity<Void> deleteComment(
            @PathVariable UUID breachId,
            @PathVariable UUID commentId) {

        commentService.deleteComment(commentId);
        return ResponseEntity.noContent().build();
    }
}
```

### Prednosti ✅

1. **Collaboration**: Tim može da komunicira kroz comments
2. **Documentation**: Dokumentuje investigation process
3. **Timeline**: Chronološki history šta se dešavalo
4. **Internal vs external**: Može se razlikovati internal notes od customer-visible

### Mane ⚠️

1. **Additional complexity**: Još jedna tabela i API
2. **UI dependency**: Treba UI za prikaz comments threada

---

## 📊 Poređenje Pristupa

| Feature | Pristup 1 (Simple) | Pristup 2 (State Machine) | Pristup 3 (Comments) |
|---------|-------------------|---------------------------|----------------------|
| **Implementation Time** | 2-3h | 8-10h | 4-6h |
| **Complexity** | ⭐ Low | ⭐⭐⭐ High | ⭐⭐ Medium |
| **State Validation** | ❌ Minimal | ✅ Full | N/A |
| **Audit Trail** | ⭐ Basic | ⭐⭐⭐ Complete | ⭐⭐⭐ Complete |
| **Workflow Support** | ❌ No | ✅ Yes | N/A |
| **Collaboration** | ❌ No | ⭐ Basic | ✅ Full |
| **Assignment Tracking** | ❌ No | ✅ Yes | ❌ No |
| **Notifications** | ❌ No | ✅ Events | ✅ Events |
| **Extensibility** | ⭐ Limited | ⭐⭐⭐ High | ⭐⭐ Medium |

---

## 🎯 Finalna Preporuka

### Kombinovani Pristup: **Pristup 2 + Pristup 3** ✅

**Razlog:**
- **State Machine (Pristup 2)** za lifecycle management i validation
- **Comments (Pristup 3)** za collaboration i documentation

**Implementation Plan:**

**Faza 1 (Week 1)**: State Machine
- [ ] Dodati `BreachState` enum
- [ ] Update `SlaBreach` entity sa `state` field
- [ ] Kreirati migration
- [ ] Implementirati `transitionTo()` logiku
- [ ] Kreirati `BreachStateTransition` entity i repository
- [ ] Implementirati `BreachManagementService`
- [ ] Kreirati API endpoints
- [ ] Unit tests
- [ ] Integration tests

**Faza 2 (Week 2)**: Comments & Collaboration
- [ ] Kreirati `BreachComment` entity
- [ ] Kreirati migration
- [ ] Implementirati `BreachCommentService`
- [ ] Kreirati comment API endpoints
- [ ] Unit tests
- [ ] Integration tests

**Faza 3 (Week 3)**: Metrics & Reporting
- [ ] Implementirati MTTA/MTTR calculations
- [ ] Kreirati breach metrics API
- [ ] Dashboard queries

**Faza 4 (Week 4)**: Notifications & Escalation
- [ ] Event listeners za state changes
- [ ] Notification service integration
- [ ] Escalation scheduler

---

## 🧪 Testing Strategy

### Unit Tests

```java
@Test
void testValidStateTransition() {
    SlaBreach breach = new SlaBreach();
    breach.setState(BreachState.DETECTED);

    breach.transitionTo(BreachState.ACKNOWLEDGED, "john.doe", "Investigating");

    assertThat(breach.getState()).isEqualTo(BreachState.ACKNOWLEDGED);
    assertThat(breach.getIsAcknowledged()).isTrue();
}

@Test
void testInvalidStateTransition_ThrowsException() {
    SlaBreach breach = new SlaBreach();
    breach.setState(BreachState.RESOLVED);

    assertThatThrownBy(() ->
        breach.transitionTo(BreachState.ACKNOWLEDGED, "john.doe", "Try acknowledge")
    ).isInstanceOf(IllegalStateException.class)
     .hasMessageContaining("Invalid state transition");
}
```

### Integration Tests

```java
@SpringBootTest
@Transactional
class BreachManagementServiceTest {

    @Test
    void testAcknowledgeBreach() {
        SlaBreach breach = createTestBreach();

        SlaBreach acknowledged = breachManagementService.acknowledgeBreach(
            breach.getId(),
            "john.doe",
            "Starting investigation"
        );

        assertThat(acknowledged.getState()).isEqualTo(BreachState.ACKNOWLEDGED);

        List<BreachStateTransition> history =
            transitionRepository.findByBreachIdOrderByTransitionedAtAsc(breach.getId());

        assertThat(history).hasSize(1);
        assertThat(history.get(0).getToState()).isEqualTo(BreachState.ACKNOWLEDGED);
    }
}
```

---

## 📚 References

- [State Machine Pattern](https://refactoring.guru/design-patterns/state)
- [REST API Best Practices](https://restfulapi.net/)
- [Event-Driven Architecture](https://martinfowler.com/articles/201701-event-driven.html)
