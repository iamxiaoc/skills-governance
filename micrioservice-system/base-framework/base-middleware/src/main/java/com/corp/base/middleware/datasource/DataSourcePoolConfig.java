package com.corp.base.middleware.datasource;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;

/**
 * Configuration object for the {@link CustomDataSource} / Hikari pool.
 *
 * <p>Properties mirror HikariCP's well-known names so that this class can be
 * bound directly from {@code application.yml} via {@code @ConfigurationProperties}.
 */
public class DataSourcePoolConfig {

    private String jdbcUrl;
    private String driverClassName;
    private String username;
    private String password;
    private String poolName = "base-hikari-pool";

    private int maximumPoolSize = 10;
    private int minimumIdle = 2;
    private long connectionTimeoutMillis = 30000L;
    private long idleTimeoutMillis = 600000L;
    private long maxLifetimeMillis = 1800000L;
    private long connectionTestQueryTimeoutSeconds = 5L;
    private String connectionTestQuery;

    /** Build a configured {@link HikariDataSource}. */
    public HikariDataSource buildHikariDataSource() {
        HikariConfig cfg = new HikariConfig();
        cfg.setPoolName(poolName);
        cfg.setJdbcUrl(jdbcUrl);
        if (driverClassName != null) {
            cfg.setDriverClassName(driverClassName);
        }
        cfg.setUsername(username);
        cfg.setPassword(password);
        cfg.setMaximumPoolSize(maximumPoolSize);
        cfg.setMinimumIdle(minimumIdle);
        cfg.setConnectionTimeout(connectionTimeoutMillis);
        cfg.setIdleTimeout(idleTimeoutMillis);
        cfg.setMaxLifetime(maxLifetimeMillis);
        if (connectionTestQuery != null && !connectionTestQuery.isEmpty()) {
            cfg.setConnectionTestQuery(connectionTestQuery);
        }
        return new HikariDataSource(cfg);
    }

    // ---------- getters / setters ----------
    public String getJdbcUrl() { return jdbcUrl; }
    public void setJdbcUrl(String jdbcUrl) { this.jdbcUrl = jdbcUrl; }

    public String getDriverClassName() { return driverClassName; }
    public void setDriverClassName(String driverClassName) { this.driverClassName = driverClassName; }

    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }

    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }

    public String getPoolName() { return poolName; }
    public void setPoolName(String poolName) { this.poolName = poolName; }

    public int getMaximumPoolSize() { return maximumPoolSize; }
    public void setMaximumPoolSize(int maximumPoolSize) { this.maximumPoolSize = maximumPoolSize; }

    public int getMinimumIdle() { return minimumIdle; }
    public void setMinimumIdle(int minimumIdle) { this.minimumIdle = minimumIdle; }

    public long getConnectionTimeoutMillis() { return connectionTimeoutMillis; }
    public void setConnectionTimeoutMillis(long connectionTimeoutMillis) { this.connectionTimeoutMillis = connectionTimeoutMillis; }

    public long getIdleTimeoutMillis() { return idleTimeoutMillis; }
    public void setIdleTimeoutMillis(long idleTimeoutMillis) { this.idleTimeoutMillis = idleTimeoutMillis; }

    public long getMaxLifetimeMillis() { return maxLifetimeMillis; }
    public void setMaxLifetimeMillis(long maxLifetimeMillis) { this.maxLifetimeMillis = maxLifetimeMillis; }

    public long getConnectionTestQueryTimeoutSeconds() { return connectionTestQueryTimeoutSeconds; }
    public void setConnectionTestQueryTimeoutSeconds(long connectionTestQueryTimeoutSeconds) { this.connectionTestQueryTimeoutSeconds = connectionTestQueryTimeoutSeconds; }

    public String getConnectionTestQuery() { return connectionTestQuery; }
    public void setConnectionTestQuery(String connectionTestQuery) { this.connectionTestQuery = connectionTestQuery; }
}
