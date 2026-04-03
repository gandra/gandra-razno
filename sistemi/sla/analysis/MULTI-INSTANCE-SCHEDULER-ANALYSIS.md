# Multi-Instance Scheduler Analysis - Distributed Locking

## 📋 Problem Statement

### Trenutna Situacija

OCI Monitor koristi Spring's `@Scheduled` anotacije za automatsko pokretanje SLA computation-a:

```java
@Component
public class SlaScheduler {

    @Scheduled(cron = "0 5 0 * * *")  // Daily at 00:05
    public void scheduleDailySlas() {
        slaSchedulerService.processPeriodType(SlaPeriodType.DAILY, yesterday, now);
    }

    @Scheduled(cron = "0 10 0 * * MON")  // Weekly Monday 00:10
    public void scheduleWeeklySlas() {
        slaSchedulerService.processPeriodType(SlaPeriodType.WEEKLY, lastWeek, now);
    }

    @Scheduled(cron = "0 15 0 1 * *")  // Monthly 1st at 00:15
    public void scheduleMonthlySlas() {
        slaSchedulerService.processPeriodType(SlaPeriodType.MONTHLY, lastMonth, now);
    }
}
```

### 🚨 Problem u Multi-Instance Setup

Kada se `oci-monitor` pokrene u **više instanci** (horizontal scaling), **svaka instanca** će izvršiti isti scheduled job:

```
Instance 1:  00:05:00 → scheduleDailySlas() → Compute all DAILY SLAs
Instance 2:  00:05:00 → scheduleDailySlas() → Compute all DAILY SLAs  ❌ DUPLICATE!
Instance 3:  00:05:00 → scheduleDailySlas() → Compute all DAILY SLAs  ❌ DUPLICATE!
```

### 💥 Posledice

1. **Duplicate SLA Computations**
   - Isti SLA se računa 3x (broj instanci)
   - Waste CPU/database resources
   - Race conditions u pisanju SlaResult

2. **Duplicate Notifications**
   - Email notifikacije se šalju 3x
   - Webhook notifikacije se šalju 3x
   - Spam recipients

3. **Database Contention**
   - Multiple instances pokušavaju da save isti SlaResult istovremeno
   - Optimistic locking conflicts (`@Version` field)
   - Transaction rollbacks

4. **Inconsistent State**
   - Ako jedna instanca uspe, druge mogu da failuju
   - Partial updates u bazi

### 📊 Scenario Example

```
T = 00:05:00 (CRON trigger)
────────────────────────────────────────────────────

Instance 1:
  └─ SlaScheduler.scheduleDailySlas()
      └─ Process SLA-001: Save SlaResult ✅
      └─ Process SLA-002: Save SlaResult ✅
      └─ Send notification for SLA-001 ✅

Instance 2 (same time):
  └─ SlaScheduler.scheduleDailySlas()
      └─ Process SLA-001: Conflict! ❌ (already saved by Instance 1)
      └─ Process SLA-002: Conflict! ❌
      └─ Send notification for SLA-001 ✅ ❌ DUPLICATE EMAIL!

Instance 3 (same time):
  └─ SlaScheduler.scheduleDailySlas()
      └─ Process SLA-001: Conflict! ❌
      └─ Process SLA-002: Conflict! ❌
      └─ Send notification for SLA-001 ✅ ❌ DUPLICATE EMAIL!

Result:
  ✅ SLA computed once (good)
  ❌ 3x notification emails sent (BAD!)
  ❌ 2x failed computations (waste resources)
```

---

## 🎯 Cilj

Osigurati da **samo jedna instanca** izvršava scheduled job u bilo kom trenutku, dok ostale instance ostaju u **standby** režimu.

**Requirements:**
1. Only one instance executes job
2. Automatic failover if executing instance crashes
3. Minimal latency overhead
4. Uses existing infrastructure (MySQL preferred)
5. Simple configuration
6. Production-proven solution

---

## 🔧 Pristup 1: ShedLock (Spring Native - RECOMMENDED ✅)

### Opis

**ShedLock** je lightweight library dizajniran specifično za distributed locking Spring scheduled tasks. Koristi database (MySQL, PostgreSQL, MongoDB, etc.) ili Redis za koordinaciju.

**Oficijalni repo:** https://github.com/lukas-krecan/ShedLock

### Kako Radi

1. Pre izvršavanja scheduled job-a, instanca pokušava da **zaključa lock u bazi**
2. Ako uspe, izvršava job
3. Ako ne uspe (lock već zauzet), **preskače** izvršavanje
4. Lock se automatski oslobađa nakon `lockAtMostFor` vremena (failsafe)

```
Instance 1:  00:05:00 → Try acquire lock "daily-sla" → ✅ SUCCESS → Execute job
Instance 2:  00:05:00 → Try acquire lock "daily-sla" → ❌ LOCKED  → Skip
Instance 3:  00:05:00 → Try acquire lock "daily-sla" → ❌ LOCKED  → Skip
```

### Implementacija

**1. Dodati ShedLock dependency:**

```xml
<!-- pom.xml -->
<dependency>
    <groupId>net.javacrumbs.shedlock</groupId>
    <artifactId>shedlock-spring</artifactId>
    <version>5.10.0</version>
</dependency>
<dependency>
    <groupId>net.javacrumbs.shedlock</groupId>
    <artifactId>shedlock-provider-jdbc-template</artifactId>
    <version>5.10.0</version>
</dependency>
```

**2. Kreirati lock tabelu:**

```sql
-- V13__create_shedlock_table.sql
CREATE TABLE shedlock (
    name VARCHAR(64) NOT NULL PRIMARY KEY,
    lock_until TIMESTAMP(3) NOT NULL,
    locked_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    locked_by VARCHAR(255) NOT NULL,
    INDEX idx_lock_until (lock_until)
) ENGINE=InnoDB;

-- name: Unique lock identifier (e.g., "daily-sla-scheduler")
-- lock_until: When lock expires (automatic failover if instance crashes)
-- locked_at: When lock was acquired (debugging)
-- locked_by: Which instance acquired lock (hostname)
```

**3. ShedLock Configuration:**

```java
@Configuration
@EnableScheduling
@EnableSchedulerLock(defaultLockAtMostFor = "PT10M") // Max lock duration: 10 minutes
public class SchedulerConfig {

    /**
     * ShedLock provider using MySQL database.
     * Uses existing DataSource (no additional infrastructure needed).
     */
    @Bean
    public LockProvider lockProvider(DataSource dataSource) {
        return new JdbcTemplateLockProvider(JdbcTemplateLockProvider.Configuration.builder()
                .withJdbcTemplate(new JdbcTemplate(dataSource))
                .usingDbTime() // Use database time (not application server time)
                .build()
        );
    }
}
```

**4. Annotate Scheduled Methods:**

```java
@Component
@Slf4j
@RequiredArgsConstructor
public class SlaScheduler {

    private final SchedulerToggleService schedulerToggleService;
    private final SlaSchedulerService slaSchedulerService;

    /**
     * Schedule DAILY SLA computations.
     * Executes every day at 00:05.
     *
     * ShedLock ensures only ONE instance executes this at a time.
     *
     * @SchedulerLock parameters:
     * - name: Unique lock identifier
     * - lockAtMostFor: Max lock duration (failsafe if instance crashes)
     * - lockAtLeastFor: Min lock duration (prevents re-execution if job finishes quickly)
     */
    @Scheduled(cron = "0 5 0 * * *")
    @SchedulerLock(
        name = "daily-sla-scheduler",
        lockAtMostFor = "PT10M",   // Lock expires after 10 minutes (failover)
        lockAtLeastFor = "PT1M"    // Hold lock for at least 1 minute (prevents rapid re-execution)
    )
    public void scheduleDailySlas() {
        if (!schedulerToggleService.isTaskEnabled("sla.scheduled.daily")) {
            log.info("SlaScheduler:: Daily SLA scheduler is disabled. Skipping execution.");
            return;
        }

        log.info("=== DAILY SLA Scheduler Started (Instance: {}) ===", getInstanceId());

        LocalDateTime now = LocalDateTime.now();
        LocalDate yesterday = LocalDate.now().minusDays(1);

        try {
            slaSchedulerService.processPeriodType(SlaPeriodType.DAILY, yesterday, now);
            log.info("=== DAILY SLA Scheduler Completed Successfully ===");
        } catch (Exception e) {
            log.error("=== DAILY SLA Scheduler Failed: {} ===", e.getMessage(), e);
        }
    }

    @Scheduled(cron = "0 10 0 * * MON")
    @SchedulerLock(
        name = "weekly-sla-scheduler",
        lockAtMostFor = "PT10M",
        lockAtLeastFor = "PT1M"
    )
    public void scheduleWeeklySlas() {
        if (!schedulerToggleService.isTaskEnabled("sla.scheduled.weekly")) {
            log.info("SlaScheduler:: Weekly SLA scheduler is disabled. Skipping execution.");
            return;
        }

        log.info("=== WEEKLY SLA Scheduler Started (Instance: {}) ===", getInstanceId());

        LocalDateTime now = LocalDateTime.now();
        LocalDate lastWeek = LocalDate.now().minusWeeks(1);

        try {
            slaSchedulerService.processPeriodType(SlaPeriodType.WEEKLY, lastWeek, now);
            log.info("=== WEEKLY SLA Scheduler Completed Successfully ===");
        } catch (Exception e) {
            log.error("=== WEEKLY SLA Scheduler Failed: {} ===", e.getMessage(), e);
        }
    }

    @Scheduled(cron = "0 15 0 1 * *")
    @SchedulerLock(
        name = "monthly-sla-scheduler",
        lockAtMostFor = "PT30M",  // Monthly jobs may take longer
        lockAtLeastFor = "PT2M"
    )
    public void scheduleMonthlySlas() {
        if (!schedulerToggleService.isTaskEnabled("sla.scheduled.monthly")) {
            log.info("SlaScheduler:: Monthly SLA scheduler is disabled. Skipping execution.");
            return;
        }

        log.info("=== MONTHLY SLA Scheduler Started (Instance: {}) ===", getInstanceId());

        LocalDateTime now = LocalDateTime.now();
        LocalDate lastMonth = LocalDate.now().minusMonths(1);

        try {
            slaSchedulerService.processPeriodType(SlaPeriodType.MONTHLY, lastMonth, now);
            log.info("=== MONTHLY SLA Scheduler Completed Successfully ===");
        } catch (Exception e) {
            log.error("=== MONTHLY SLA Scheduler Failed: {} ===", e.getMessage(), e);
        }
    }

    /**
     * Get instance identifier for logging.
     */
    private String getInstanceId() {
        try {
            return InetAddress.getLocalHost().getHostName();
        } catch (Exception e) {
            return "unknown";
        }
    }
}
```

**5. Application Properties (Optional tuning):**

```properties
# oci-monitor/src/main/resources/application.properties

# ShedLock configuration (all defaults are good, but can be customized)
# shedlock.defaults.lock-at-most-for=PT10M
# shedlock.defaults.lock-at-least-for=PT1M
```

### Kako Radi - Timeline

```
T = 00:05:00 (CRON triggers on all instances)
────────────────────────────────────────────────────

Instance 1 (oci-monitor-pod-1):
  00:05:00.001 → @SchedulerLock tries to INSERT into shedlock table
  00:05:00.002 → ✅ SUCCESS (first to acquire lock)
  00:05:00.003 → Log: "DAILY SLA Scheduler Started (Instance: oci-monitor-pod-1)"
  00:05:00.004 → Execute scheduleDailySlas()
  00:05:01.500 → Processing SLA definitions...
  00:10:30.000 → Job completes
  00:10:30.001 → Lock automatically released

Instance 2 (oci-monitor-pod-2):
  00:05:00.001 → @SchedulerLock tries to INSERT into shedlock table
  00:05:00.002 → ❌ FAIL (lock already acquired by Instance 1)
  00:05:00.003 → Log: "Could not acquire lock for daily-sla-scheduler, skipping"
  00:05:00.004 → Method returns without executing
  00:05:00.005 → Instance stays idle until next CRON trigger

Instance 3 (oci-monitor-pod-3):
  00:05:00.001 → @SchedulerLock tries to INSERT into shedlock table
  00:05:00.002 → ❌ FAIL (lock already acquired by Instance 1)
  00:05:00.003 → Log: "Could not acquire lock for daily-sla-scheduler, skipping"
  00:05:00.004 → Method returns without executing
  00:05:00.005 → Instance stays idle until next CRON trigger

Result:
  ✅ Only Instance 1 executes job
  ✅ No duplicate computations
  ✅ No duplicate notifications
  ✅ Instances 2 & 3 stay in standby
```

### Failover Scenario

```
Instance 1 crashes at 00:07:00 (middle of job execution)
────────────────────────────────────────────────────

T = 00:07:00 → Instance 1 crashes (lock still in database)

T = 00:15:00 → Lock expires (lockAtMostFor = 10 minutes)
             → Lock record automatically becomes stale

Next CRON cycle (01:05:00):
  Instance 2 → Tries to acquire lock
            → ✅ SUCCESS (stale lock cleaned up)
            → Executes job

Result:
  ✅ Automatic failover after lockAtMostFor expires
  ✅ No manual intervention needed
  ⚠️ Max 10 minute delay before failover (acceptable for daily jobs)
```

### Lock Cleanup (Automatic)

ShedLock automatski čisti stale locks:

```sql
-- Before acquiring lock, ShedLock executes:
UPDATE shedlock
SET lock_until = ?, locked_at = ?, locked_by = ?
WHERE name = ?
  AND lock_until <= NOW(); -- Only update if lock expired

-- If UPDATE affects 0 rows → lock is held by another instance
-- If UPDATE affects 1 row → lock acquired successfully
```

### Prednosti ✅

1. **Spring Native**: Dizajniran specifično za Spring `@Scheduled`
2. **Simple Configuration**: 1 dependency + 1 table + 1 annotation
3. **Uses Existing MySQL**: Ne traži dodatnu infrastrukturu (Redis, ZooKeeper, etc.)
4. **Automatic Failover**: Stale locks se automatski oslobađaju nakon `lockAtMostFor`
5. **Production Proven**: Koristi ga Netflix, Spotify, i hiljade drugih kompanija
6. **Lightweight**: Minimalan overhead (~5-10ms per lock attempt)
7. **Database Time**: Koristi DB time (ne application server time) → clock drift safe
8. **Multiple Lock Backends**: Ako jednom želite Redis, samo promenite provider
9. **No Leader Election**: Nema complex leader election protokola
10. **Debugging Friendly**: Lock state je visible u `shedlock` tabeli

### Mane ⚠️

1. **Database Dependency**: Svaki lock attempt = 1 database query (minimal overhead)
2. **Lock Granularity**: Lock je per-method (ne može fine-grained lock unutar metode)
3. **Not Real-Time**: `lockAtMostFor` delay za failover (ali za scheduled jobs je OK)
4. **Manual Cleanup**: Stare lock records ostaju u tabeli (može se dodati cleanup job)

### Kada Koristiti

- ✅ **Default choice** za Spring scheduled tasks
- ✅ Kada već koristite MySQL/PostgreSQL
- ✅ Simple horizontal scaling
- ✅ Ne želite dodatnu infrastrukturu (Redis, ZooKeeper)
- ✅ Production-ready solution sa minimalnim setup-om

---

## 🔧 Pristup 2: Redis Distributed Lock (Redisson)

### Opis

Redis može da se koristi kao distributed lock manager kroz **Redisson** library koja implementira industry-standard locking patterns.

### Implementacija

**1. Dodati Redisson dependency:**

```xml
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson-spring-boot-starter</artifactId>
    <version>3.24.3</version>
</dependency>
```

**2. Redis Configuration:**

```java
@Configuration
public class RedissonConfig {

    @Bean
    public RedissonClient redissonClient() {
        Config config = new Config();
        config.useSingleServer()
                .setAddress("redis://localhost:6379")
                .setConnectionPoolSize(10)
                .setConnectionMinimumIdleSize(2);

        return Redisson.create(config);
    }
}
```

**3. Custom Lock Annotation:**

```java
@Aspect
@Component
@Slf4j
@RequiredArgsConstructor
public class DistributedLockAspect {

    private final RedissonClient redissonClient;

    @Around("@annotation(distributedLock)")
    public Object executeWithLock(ProceedingJoinPoint joinPoint, DistributedLock distributedLock)
            throws Throwable {

        String lockKey = distributedLock.key();
        long waitTime = distributedLock.waitTime();
        long leaseTime = distributedLock.leaseTime();
        TimeUnit timeUnit = distributedLock.timeUnit();

        RLock lock = redissonClient.getLock(lockKey);

        boolean acquired = false;
        try {
            // Try to acquire lock with timeout
            acquired = lock.tryLock(waitTime, leaseTime, timeUnit);

            if (!acquired) {
                log.info("Could not acquire lock '{}', skipping execution", lockKey);
                return null; // Skip execution
            }

            log.info("✅ Lock '{}' acquired by {}", lockKey, getInstanceId());

            // Execute scheduled method
            return joinPoint.proceed();

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.error("Lock acquisition interrupted for '{}'", lockKey);
            return null;
        } finally {
            if (acquired && lock.isHeldByCurrentThread()) {
                lock.unlock();
                log.info("Lock '{}' released by {}", lockKey, getInstanceId());
            }
        }
    }

    private String getInstanceId() {
        try {
            return InetAddress.getLocalHost().getHostName();
        } catch (Exception e) {
            return "unknown";
        }
    }
}

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface DistributedLock {
    String key();
    long waitTime() default 0; // Don't wait if lock unavailable
    long leaseTime() default 10; // Lock expires after 10 minutes
    TimeUnit timeUnit() default TimeUnit.MINUTES;
}
```

**4. Annotate Scheduled Methods:**

```java
@Scheduled(cron = "0 5 0 * * *")
@DistributedLock(key = "daily-sla-scheduler", leaseTime = 10, timeUnit = TimeUnit.MINUTES)
public void scheduleDailySlas() {
    // ... existing logic ...
}
```

### Prednosti ✅

1. **Fast**: Redis je in-memory, lock acquisition je brži (~1-2ms vs ~5-10ms database)
2. **Real-Time Failover**: Lock automatski expires ako instance crashes
3. **Rich Features**: Redisson pruža advanced locking patterns (fair locks, read-write locks, etc.)
4. **Centralized**: Redis može da se koristi za druge stvari (caching, rate limiting)
5. **Battle-Tested**: Redis locking je industry standard

### Mane ⚠️

1. **Additional Infrastructure**: Zahteva Redis server (deployment, monitoring, backup)
2. **Single Point of Failure**: Ako Redis padne, locking ne radi (može se mitigirati Redis Sentinel/Cluster)
3. **Operational Overhead**: Još jedan service za maintain
4. **Network Dependency**: Extra network hop za svaki lock attempt
5. **More Complex**: Više konfiguracije nego ShedLock

### Kada Koristiti

- ✅ Već koristite Redis za caching
- ✅ Potreban je fast lock acquisition (< 5ms)
- ✅ Potrebni su advanced locking patterns
- ✅ High-frequency locking (thousands per second)

---

## 🔧 Pristup 3: Database Advisory Locks (MySQL)

### Opis

MySQL ima built-in **advisory lock** funkcije koje se mogu koristiti za distributed locking bez dodatnih tabela.

**MySQL Functions:**
- `GET_LOCK(lock_name, timeout)` - Acquire lock
- `RELEASE_LOCK(lock_name)` - Release lock
- `IS_FREE_LOCK(lock_name)` - Check if lock is free

### Implementacija

```java
@Component
@Slf4j
@RequiredArgsConstructor
public class MysqlAdvisoryLockService {

    private final JdbcTemplate jdbcTemplate;

    /**
     * Try to acquire MySQL advisory lock.
     *
     * @param lockName Unique lock identifier
     * @param timeoutSeconds How long to wait for lock (0 = no wait)
     * @return true if lock acquired, false otherwise
     */
    public boolean acquireLock(String lockName, int timeoutSeconds) {
        try {
            Integer result = jdbcTemplate.queryForObject(
                    "SELECT GET_LOCK(?, ?)",
                    Integer.class,
                    lockName,
                    timeoutSeconds
            );

            // GET_LOCK returns:
            // 1 = lock acquired
            // 0 = timeout (lock held by another connection)
            // NULL = error
            return result != null && result == 1;

        } catch (Exception e) {
            log.error("Failed to acquire lock '{}': {}", lockName, e.getMessage());
            return false;
        }
    }

    /**
     * Release MySQL advisory lock.
     */
    public boolean releaseLock(String lockName) {
        try {
            Integer result = jdbcTemplate.queryForObject(
                    "SELECT RELEASE_LOCK(?)",
                    Integer.class,
                    lockName
            );

            // RELEASE_LOCK returns:
            // 1 = lock released
            // 0 = lock not held by this connection
            // NULL = lock doesn't exist
            return result != null && result == 1;

        } catch (Exception e) {
            log.error("Failed to release lock '{}': {}", lockName, e.getMessage());
            return false;
        }
    }
}
```

**Custom Lock Aspect:**

```java
@Aspect
@Component
@Slf4j
@RequiredArgsConstructor
public class AdvisoryLockAspect {

    private final MysqlAdvisoryLockService lockService;

    @Around("@annotation(advisoryLock)")
    public Object executeWithLock(ProceedingJoinPoint joinPoint, AdvisoryLock advisoryLock)
            throws Throwable {

        String lockName = advisoryLock.lockName();
        int timeout = advisoryLock.timeout();

        boolean acquired = lockService.acquireLock(lockName, timeout);

        if (!acquired) {
            log.info("Could not acquire advisory lock '{}', skipping execution", lockName);
            return null;
        }

        try {
            log.info("✅ Advisory lock '{}' acquired", lockName);
            return joinPoint.proceed();
        } finally {
            lockService.releaseLock(lockName);
            log.info("Advisory lock '{}' released", lockName);
        }
    }
}

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface AdvisoryLock {
    String lockName();
    int timeout() default 0; // No wait
}
```

**Usage:**

```java
@Scheduled(cron = "0 5 0 * * *")
@AdvisoryLock(lockName = "daily-sla-scheduler")
public void scheduleDailySlas() {
    // ... existing logic ...
}
```

### Prednosti ✅

1. **No Additional Table**: Koristi MySQL built-in funkcionalnost
2. **Fast**: Lock je in-memory u MySQL serveru
3. **Automatic Cleanup**: Lock se automatski release-uje kada connection zatvori
4. **Simple**: Nema external dependencies

### Mane ⚠️

1. **Connection-Based**: Lock je vezan za database connection (mora se držati connection otvoren tokom job-a)
2. **No Automatic Failover**: Lock se ne release-uje ako instanca crashuje bez closing connection
3. **Connection Pool Issues**: Može da exhaustuje connection pool za long-running jobs
4. **MySQL Specific**: Ne radi sa PostgreSQL (ima drugačije funkcije)
5. **Less Visible**: Lock state nije visible u database tabeli (teže debug-ovati)

### Kada Koristiti

- ⚠️ **NOT RECOMMENDED** za scheduled tasks
- ✅ Može se koristiti za short-lived critical sections
- ✅ Kada ne želite dodatnu tabelu

---

## 🔧 Pristup 4: Quartz Scheduler (Cluster Mode)

### Opis

**Quartz** je enterprise-grade job scheduling library sa built-in cluster support. Automatski koordinira job execution preko više instanci.

### Implementacija

**1. Dodati Quartz dependency:**

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-quartz</artifactId>
</dependency>
```

**2. Quartz Configuration:**

```java
@Configuration
public class QuartzConfig {

    @Bean
    public SchedulerFactoryBean schedulerFactoryBean(DataSource dataSource) {
        SchedulerFactoryBean factory = new SchedulerFactoryBean();
        factory.setDataSource(dataSource);
        factory.setQuartzProperties(quartzProperties());
        return factory;
    }

    private Properties quartzProperties() {
        Properties properties = new Properties();

        // Cluster configuration
        properties.setProperty("org.quartz.scheduler.instanceName", "OciMonitorScheduler");
        properties.setProperty("org.quartz.scheduler.instanceId", "AUTO");

        // Enable clustering
        properties.setProperty("org.quartz.jobStore.isClustered", "true");
        properties.setProperty("org.quartz.jobStore.clusterCheckinInterval", "20000");

        // Use JDBC job store
        properties.setProperty("org.quartz.jobStore.class", "org.quartz.impl.jdbcjobstore.JobStoreTX");
        properties.setProperty("org.quartz.jobStore.driverDelegateClass",
                "org.quartz.impl.jdbcjobstore.StdJDBCDelegate");
        properties.setProperty("org.quartz.jobStore.tablePrefix", "QRTZ_");

        return properties;
    }
}
```

**3. Create Quartz Tables:**

```sql
-- Quartz provides SQL scripts for table creation
-- Download from: https://github.com/quartz-scheduler/quartz/tree/main/quartz-core/src/main/resources/org/quartz/impl/jdbcjobstore

-- Creates tables: QRTZ_JOB_DETAILS, QRTZ_TRIGGERS, QRTZ_LOCKS, etc.
```

**4. Define Quartz Job:**

```java
@Component
@DisallowConcurrentExecution // Prevents concurrent execution
public class DailySlaJob extends QuartzJobBean {

    @Autowired
    private SlaSchedulerService slaSchedulerService;

    @Override
    protected void executeInternal(JobExecutionContext context) throws JobExecutionException {
        log.info("=== DAILY SLA Job Started (Instance: {}) ===", getInstanceId());

        LocalDateTime now = LocalDateTime.now();
        LocalDate yesterday = LocalDate.now().minusDays(1);

        try {
            slaSchedulerService.processPeriodType(SlaPeriodType.DAILY, yesterday, now);
            log.info("=== DAILY SLA Job Completed Successfully ===");
        } catch (Exception e) {
            log.error("=== DAILY SLA Job Failed: {} ===", e.getMessage(), e);
            throw new JobExecutionException(e);
        }
    }

    private String getInstanceId() {
        try {
            return InetAddress.getLocalHost().getHostName();
        } catch (Exception e) {
            return "unknown";
        }
    }
}
```

**5. Schedule Job:**

```java
@Configuration
public class QuartzJobConfig {

    @Bean
    public JobDetail dailySlaJobDetail() {
        return JobBuilder.newJob(DailySlaJob.class)
                .withIdentity("dailySlaJob", "slaGroup")
                .storeDurably()
                .build();
    }

    @Bean
    public Trigger dailySlaJobTrigger() {
        return TriggerBuilder.newTrigger()
                .forJob(dailySlaJobDetail())
                .withIdentity("dailySlaJobTrigger", "slaGroup")
                .withSchedule(CronScheduleBuilder.cronSchedule("0 5 0 * * ?"))
                .build();
    }
}
```

### Prednosti ✅

1. **Enterprise-Grade**: Industry standard za complex scheduling
2. **Built-In Clustering**: Automatic coordination bez custom code
3. **Rich Features**: Mis-fire handling, job persistence, pause/resume, etc.
4. **Automatic Failover**: Ako instanca crashuje, drugi instance preuzimaju jobs
5. **Job Monitoring**: Built-in UI/API za monitoring job execution
6. **Persistence**: Jobs se čuvaju u bazi (survive app restarts)

### Mane ⚠️

1. **High Complexity**: 11 tabela u bazi, kompleksna konfiguracija
2. **Overkill**: Previše features za simple scheduled tasks
3. **Migration Effort**: Mora da se refaktorisu svi `@Scheduled` metodi u Quartz jobs
4. **Learning Curve**: Tim mora da nauči Quartz API
5. **Database Schema**: Quartz tabele su complex (QRTZ_*)

### Kada Koristiti

- ✅ Complex scheduling requirements (dynamic schedules, job chains, etc.)
- ✅ Need web UI for job management
- ✅ Already using Quartz
- ⚠️ **NOT RECOMMENDED** za simple scheduled tasks

---

## 🔧 Pristup 5: Leader Election Pattern (Spring Cloud)

### Opis

Leader election pattern: jedna instanca postaje **leader** i izvršava sve scheduled tasks, dok ostale su **followers** u standby režimu.

Može se implementirati sa:
- **Spring Cloud Kubernetes** (leader election via ConfigMap)
- **Spring Cloud Consul**
- **Apache Curator** (ZooKeeper)

### Implementacija (Kubernetes)

**1. Dependency:**

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-kubernetes-client-leader</artifactId>
</dependency>
```

**2. Enable Leader Election:**

```java
@Configuration
@EnableKubernetesLeaderElection
public class LeaderElectionConfig {
    // Auto-configures leader election
}
```

**3. Conditional Scheduled Execution:**

```java
@Component
@Slf4j
@RequiredArgsConstructor
public class SlaScheduler {

    private final LeaderElectionContext leaderElectionContext;
    private final SlaSchedulerService slaSchedulerService;

    @Scheduled(cron = "0 5 0 * * *")
    public void scheduleDailySlas() {
        // Only execute if this instance is the leader
        if (!leaderElectionContext.isLeader()) {
            log.debug("Not the leader, skipping DAILY SLA execution");
            return;
        }

        log.info("=== DAILY SLA Scheduler Started (Leader Instance) ===");

        LocalDateTime now = LocalDateTime.now();
        LocalDate yesterday = LocalDate.now().minusDays(1);

        try {
            slaSchedulerService.processPeriodType(SlaPeriodType.DAILY, yesterday, now);
            log.info("=== DAILY SLA Scheduler Completed Successfully ===");
        } catch (Exception e) {
            log.error("=== DAILY SLA Scheduler Failed: {} ===", e.getMessage(), e);
        }
    }
}
```

### Prednosti ✅

1. **True Leader Election**: Jedna instanca je leader za sve scheduled tasks
2. **Fast Failover**: Leader re-election dešava brzo (seconds)
3. **Cloud-Native**: Integrates sa Kubernetes, Consul, etc.
4. **No Database Overhead**: Leader election via ConfigMap (Kubernetes)

### Mane ⚠️

1. **Infrastructure Dependency**: Zahteva Kubernetes, Consul, ili ZooKeeper
2. **Complexity**: Leader election protokol je kompleksan
3. **All-or-Nothing**: Leader izvršava SVE jobs (nije per-job granularity kao ShedLock)
4. **Resource Waste**: Follower instances su idle (ne izvršavaju ništa)
5. **Lock-In**: Vezuje vas za specifičan cloud/orchestration platform

### Kada Koristiti

- ✅ Već deployujete na Kubernetes
- ✅ Imate mnogo različitih scheduled tasks
- ✅ Želite single leader za sve tasks
- ⚠️ Ne preporučujem za simple use case

---

## 📊 Detaljno Poređenje

| Feature | ShedLock | Redis (Redisson) | MySQL Advisory | Quartz Cluster | Leader Election |
|---------|----------|------------------|----------------|----------------|-----------------|
| **Setup Complexity** | ⭐ Very Easy | ⭐⭐ Medium | ⭐⭐ Medium | ⭐⭐⭐⭐ Very Hard | ⭐⭐⭐ Hard |
| **Infrastructure** | MySQL (existing) | ❌ Redis required | MySQL (existing) | MySQL (existing) | ❌ K8s/Consul required |
| **Lock Acquisition Speed** | 5-10ms | 1-2ms | 2-5ms | 10-20ms | 50-100ms (election) |
| **Automatic Failover** | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes (fast) |
| **Per-Job Granularity** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No (all-or-nothing) |
| **Database Overhead** | 1 query/lock | None | 1 query/lock | High (11 tables) | None |
| **Production Proven** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Debugging** | ⭐⭐⭐⭐⭐ Easy | ⭐⭐⭐ Medium | ⭐⭐ Hard | ⭐⭐⭐⭐ Easy | ⭐⭐⭐ Medium |
| **Migration Effort** | 1-2h | 2-4h | 2-4h | 8-16h | 4-8h |
| **Operational Overhead** | ⭐ Very Low | ⭐⭐⭐ Medium | ⭐ Very Low | ⭐⭐⭐⭐ High | ⭐⭐⭐ Medium |
| **Spring Integration** | ⭐⭐⭐⭐⭐ Native | ⭐⭐⭐ Good | ⭐⭐⭐ Manual | ⭐⭐⭐⭐ Good | ⭐⭐⭐⭐ Native |

---

## 🎯 Finalna Preporuka

### **Pristup 1: ShedLock** ✅✅✅ (STRONGLY RECOMMENDED)

**Razlozi:**

1. **Perfect Fit**: Dizajniran specifično za vaš use case (Spring `@Scheduled` tasks)
2. **Zero Infrastructure**: Koristi existing MySQL - nema Redis, ZooKeeper, itd.
3. **Simple**: 1 dependency + 1 SQL table + 1 annotation = DONE
4. **Production Proven**: Netflix, Spotify, Twitter, i hiljade drugih koriste
5. **Low Overhead**: ~5-10ms per lock attempt (negligible)
6. **Automatic Cleanup**: Stale locks se automatski oslobađaju
7. **Debuggable**: Lock state je visible u `shedlock` tabeli
8. **Future-Proof**: Može lako da se promeni backend (Redis, MongoDB, etc.)

### Implementation Effort: **1-2 sata**

**Migration Checklist:**
- [ ] Add ShedLock dependencies (2 lines in pom.xml)
- [ ] Create `shedlock` table (Flyway migration)
- [ ] Configure `LockProvider` bean (5 lines)
- [ ] Add `@SchedulerLock` to scheduled methods (3 annotations)
- [ ] Test locally sa multiple instances
- [ ] Deploy i verify logs

### Alternative (Ako već koristite Redis):

**Pristup 2: Redis (Redisson)** može biti bolji izbor AKO:
- ✅ Već imate Redis u production-u
- ✅ Koristite Redis za caching
- ✅ Trebaju vam brzine < 5ms lock acquisition

Ali za majority use cases, **ShedLock je superioran izbor**.

---

## 🧪 Testing Strategy

### Local Testing (Multiple Instances)

**Option 1: Multiple Spring Boot Applications**

```bash
# Terminal 1 - Instance 1
cd oci-monitor
mvn spring-boot:run -Dspring-boot.run.profiles=local -Dserver.port=8082

# Terminal 2 - Instance 2
cd oci-monitor
mvn spring-boot:run -Dspring-boot.run.profiles=local -Dserver.port=8083

# Terminal 3 - Instance 3
cd oci-monitor
mvn spring-boot:run -Dspring-boot.run.profiles=local -Dserver.port=8084
```

**Verify:**
- Check logs - samo jedna instanca bi trebalo da executes scheduled job
- Check `shedlock` tabela - vidi koje instanca drži lock
- Zaustavi executing instance - verify failover na drugu instancu

**Option 2: Docker Compose**

```yaml
# docker-compose-test-multi-instance.yml
version: '3.7'
services:
  oci-monitor-1:
    image: oci.monitor:local
    environment:
      - SPRING_PROFILES_ACTIVE=local
      - SERVER_PORT=8082
    ports:
      - "8082:8082"

  oci-monitor-2:
    image: oci.monitor:local
    environment:
      - SPRING_PROFILES_ACTIVE=local
      - SERVER_PORT=8083
    ports:
      - "8083:8083"

  oci-monitor-3:
    image: oci.monitor:local
    environment:
      - SPRING_PROFILES_ACTIVE=local
      - SERVER_PORT=8084
    ports:
      - "8084:8084"

  db:
    image: mysql:latest
    # ... shared database ...
```

### Unit Tests

```java
@SpringBootTest
@TestPropertySource(properties = {
    "spring.scheduled.enabled=false" // Disable auto-scheduling
})
class ShedLockIntegrationTest {

    @Autowired
    private LockProvider lockProvider;

    @Test
    void testLockAcquisition() {
        String lockName = "test-lock";
        Instant lockAtMostUntil = Instant.now().plus(Duration.ofMinutes(10));
        Instant lockAtLeastUntil = Instant.now().plus(Duration.ofMinutes(1));

        // First acquisition should succeed
        Optional<SimpleLock> lock1 = lockProvider.lock(new LockConfiguration(
                lockName, lockAtMostUntil, lockAtLeastUntil
        ));
        assertThat(lock1).isPresent();

        // Second acquisition should fail (lock already held)
        Optional<SimpleLock> lock2 = lockProvider.lock(new LockConfiguration(
                lockName, lockAtMostUntil, lockAtLeastUntil
        ));
        assertThat(lock2).isEmpty();

        // Release lock
        lock1.get().unlock();

        // Third acquisition should succeed (lock released)
        Optional<SimpleLock> lock3 = lockProvider.lock(new LockConfiguration(
                lockName, lockAtMostUntil, lockAtLeastUntil
        ));
        assertThat(lock3).isPresent();
        lock3.get().unlock();
    }

    @Test
    void testLockExpiration() throws InterruptedException {
        String lockName = "expiring-lock";
        Instant lockAtMostUntil = Instant.now().plus(Duration.ofSeconds(2));
        Instant lockAtLeastUntil = Instant.now().plus(Duration.ofSeconds(1));

        // Acquire lock
        Optional<SimpleLock> lock = lockProvider.lock(new LockConfiguration(
                lockName, lockAtMostUntil, lockAtLeastUntil
        ));
        assertThat(lock).isPresent();

        // Wait for lock to expire
        Thread.sleep(3000);

        // Should be able to acquire expired lock
        Optional<SimpleLock> lock2 = lockProvider.lock(new LockConfiguration(
                lockName, lockAtMostUntil, lockAtLeastUntil
        ));
        assertThat(lock2).isPresent();
        lock2.get().unlock();
    }
}
```

### Integration Tests

```java
@SpringBootTest
@Sql("/test-data/sla-definitions.sql")
class SlaSchedulerIntegrationTest {

    @Autowired
    private SlaScheduler slaScheduler;

    @Autowired
    private SlaResultRepository slaResultRepository;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Test
    void testScheduledJobWithLock() {
        // Clear existing results
        slaResultRepository.deleteAll();

        // Manually trigger scheduled method
        slaScheduler.scheduleDailySlas();

        // Verify SLA results were created
        List<SlaResult> results = slaResultRepository.findAll();
        assertThat(results).isNotEmpty();

        // Verify lock was acquired and released
        Integer lockCount = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM shedlock WHERE name = 'daily-sla-scheduler'",
                Integer.class
        );
        assertThat(lockCount).isEqualTo(1);

        // Verify lock is not currently held
        Timestamp lockUntil = jdbcTemplate.queryForObject(
                "SELECT lock_until FROM shedlock WHERE name = 'daily-sla-scheduler'",
                Timestamp.class
        );
        assertThat(lockUntil).isBefore(new Timestamp(System.currentTimeMillis()));
    }
}
```

---

## 📝 Migration Guide (ShedLock)

### Step 1: Add Dependency

```xml
<!-- pom.xml -->
<dependency>
    <groupId>net.javacrumbs.shedlock</groupId>
    <artifactId>shedlock-spring</artifactId>
    <version>5.10.0</version>
</dependency>
<dependency>
    <groupId>net.javacrumbs.shedlock</groupId>
    <artifactId>shedlock-provider-jdbc-template</artifactId>
    <version>5.10.0</version>
</dependency>
```

### Step 2: Create Migration

```sql
-- oci-monitor/src/main/resources/db/migration/dev/V13__create_shedlock_table.sql
CREATE TABLE shedlock (
    name VARCHAR(64) NOT NULL PRIMARY KEY COMMENT 'Unique lock identifier',
    lock_until TIMESTAMP(3) NOT NULL COMMENT 'Lock expiration time',
    locked_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT 'Lock acquisition time',
    locked_by VARCHAR(255) NOT NULL COMMENT 'Instance that holds lock (hostname)',
    INDEX idx_shedlock_lock_until (lock_until)
) ENGINE=InnoDB
COMMENT='ShedLock distributed locking table for scheduled tasks';
```

### Step 3: Configure ShedLock

```java
// oci-monitor/src/main/java/com/sistemisolutions/oci/monitor/config/SchedulerConfig.java
@Configuration
@EnableScheduling
@EnableSchedulerLock(defaultLockAtMostFor = "PT10M")
public class SchedulerConfig {

    @Bean
    public LockProvider lockProvider(DataSource dataSource) {
        return new JdbcTemplateLockProvider(JdbcTemplateLockProvider.Configuration.builder()
                .withJdbcTemplate(new JdbcTemplate(dataSource))
                .usingDbTime()
                .build()
        );
    }
}
```

### Step 4: Annotate Schedulers

```java
// oci-monitor/src/main/java/com/sistemisolutions/oci/monitor/scheduler/SlaScheduler.java
import net.javacrumbs.shedlock.spring.annotation.SchedulerLock;

@Scheduled(cron = "0 5 0 * * *")
@SchedulerLock(
    name = "daily-sla-scheduler",
    lockAtMostFor = "PT10M",
    lockAtLeastFor = "PT1M"
)
public void scheduleDailySlas() {
    // ... existing code ...
}

@Scheduled(cron = "0 10 0 * * MON")
@SchedulerLock(
    name = "weekly-sla-scheduler",
    lockAtMostFor = "PT10M",
    lockAtLeastFor = "PT1M"
)
public void scheduleWeeklySlas() {
    // ... existing code ...
}

@Scheduled(cron = "0 15 0 1 * *")
@SchedulerLock(
    name = "monthly-sla-scheduler",
    lockAtMostFor = "PT30M",
    lockAtLeastFor = "PT2M"
)
public void scheduleMonthlySlas() {
    // ... existing code ...
}
```

### Step 5: Test Locally

```bash
# Run two instances
mvn spring-boot:run -Dserver.port=8082
mvn spring-boot:run -Dserver.port=8083

# Verify logs show only one executes
# Check shedlock table
mysql> SELECT * FROM shedlock;
```

### Step 6: Deploy

- Deploy kao inače
- Monitor logs za lock acquisition messages
- Check `shedlock` tabela u production database

---

## 📚 References

- [ShedLock GitHub](https://github.com/lukas-krecan/ShedLock)
- [ShedLock Spring Boot Integration](https://github.com/lukas-krecan/ShedLock#spring-boot)
- [Redisson Distributed Locks](https://github.com/redisson/redisson/wiki/8.-distributed-locks-and-synchronizers)
- [MySQL GET_LOCK Documentation](https://dev.mysql.com/doc/refman/8.0/en/locking-functions.html)
- [Quartz Scheduler Clustering](http://www.quartz-scheduler.org/documentation/2.4.0-SNAPSHOT/configuration.html#clustering)
- [Spring Cloud Kubernetes Leader Election](https://docs.spring.io/spring-cloud-kubernetes/docs/current/reference/html/#leader-election)

---

**Prepared by:** Claude Code Analysis
**Date:** 2025-11-13
**Version:** 1.0
