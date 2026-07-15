package com.corp.base.middleware.datasource;

import com.corp.monitor.MonitorUtils;

import javax.sql.DataSource;
import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.SQLException;
import java.sql.SQLFeatureNotSupportedException;
import java.util.concurrent.atomic.AtomicLong;
import java.util.logging.Logger;

/**
 * Wrapper around {@link com.zaxxer.hikari.HikariDataSource} that adds SQL
 * monitoring and slow-query logging.
 *
 * <p>Designed as a drop-in replacement: existing code depends on
 * {@link DataSource} only.
 */
public class CustomDataSource implements DataSource {

    private final com.zaxxer.hikari.HikariDataSource delegate;

    /** Threshold in millis above which a borrowed connection is logged as slow. */
    private long slowSqlThresholdMillis = 500L;

    private final AtomicLong borrowCount = new AtomicLong();
    private final AtomicLong slowCount = new AtomicLong();

    public CustomDataSource(com.zaxxer.hikari.HikariDataSource delegate) {
        this.delegate = delegate;
    }

    public CustomDataSource(DataSourcePoolConfig config) {
        this.delegate = config.buildHikariDataSource();
    }

    @Override
    public Connection getConnection() throws SQLException {
        long start = System.currentTimeMillis();
        Connection conn = delegate.getConnection();
        long elapsed = System.currentTimeMillis() - start;
        borrowCount.incrementAndGet();
        MonitorUtils.increment("datasource.connection.borrow");
        if (elapsed > slowSqlThresholdMillis) {
            slowCount.incrementAndGet();
            // Slow acquisition logging — keep simple to avoid noise.
            System.getLogger("SlowDataSource")
                    .log(System.Logger.Level.WARNING,
                            "Slow connection acquisition: " + elapsed + "ms");
        }
        return new ConnectionMonitor(conn, slowSqlThresholdMillis);
    }

    @Override
    public Connection getConnection(String username, String password) throws SQLException {
        long start = System.currentTimeMillis();
        Connection conn = delegate.getConnection(username, password);
        long elapsed = System.currentTimeMillis() - start;
        borrowCount.incrementAndGet();
        MonitorUtils.increment("datasource.connection.borrow");
        if (elapsed > slowSqlThresholdMillis) {
            slowCount.incrementAndGet();
        }
        return new ConnectionMonitor(conn, slowSqlThresholdMillis);
    }

    public long getBorrowCount() {
        return borrowCount.get();
    }

    public long getSlowCount() {
        return slowCount.get();
    }

    public void setSlowSqlThresholdMillis(long slowSqlThresholdMillis) {
        this.slowSqlThresholdMillis = slowSqlThresholdMillis;
    }

    public void close() {
        if (delegate != null && !delegate.isClosed()) {
            delegate.close();
        }
    }

    // ---------- pure delegation below ----------
    @Override public PrintWriter getLogWriter() { return delegate.getLogWriter(); }
    @Override public void setLogWriter(PrintWriter out) { delegate.setLogWriter(out); }
    @Override public void setLoginTimeout(int seconds) { delegate.setLoginTimeout(seconds); }
    @Override public int getLoginTimeout() { return delegate.getLoginTimeout(); }
    @Override public Logger getParentLogger() throws SQLFeatureNotSupportedException {
        return delegate.getParentLogger();
    }
    @Override public <T> T unwrap(Class<T> iface) throws SQLException {
        if (iface.isInstance(this)) {
            return iface.cast(this);
        }
        return delegate.unwrap(iface);
    }
    @Override public boolean isWrapperFor(Class<?> iface) throws SQLException {
        return iface.isInstance(this) || delegate.isWrapperFor(iface);
    }

    /** Lightweight connection proxy that tracks statement execution time. */
    static class ConnectionMonitor extends java.sql.Wrapper {
        private final java.sql.Connection delegate;
        private final long slowThresholdMillis;

        ConnectionMonitor(java.sql.Connection delegate, long slowThresholdMillis) {
            super(delegate, "java.sql.Connection");
            this.delegate = delegate;
            this.slowThresholdMillis = slowThresholdMillis;
        }

        @Override
        public java.sql.Statement createStatement() throws SQLException {
            java.sql.Statement stmt = delegate.createStatement();
            return new StatementMonitor(stmt, slowThresholdMillis);
        }

        @Override
        public java.sql.PreparedStatement prepareStatement(String sql) throws SQLException {
            java.sql.PreparedStatement ps = delegate.prepareStatement(sql);
            return new StatementMonitor(ps, slowThresholdMillis);
        }

        @Override
        public java.sql.CallableStatement prepareCall(String sql) throws SQLException {
            java.sql.CallableStatement cs = delegate.prepareCall(sql);
            return new StatementMonitor(cs, slowThresholdMillis);
        }

        public java.sql.Connection getDelegate() {
            return delegate;
        }
    }

    /** Statement wrapper that logs slow SQL statements. */
    static class StatementMonitor extends java.sql.Wrapper {
        private final java.sql.Statement delegate;
        private final long slowThresholdMillis;

        StatementMonitor(java.sql.Statement delegate, long slowThresholdMillis) {
            super(delegate, "java.sql.Statement");
            this.delegate = delegate;
            this.slowThresholdMillis = slowThresholdMillis;
        }

        @Override
        public boolean execute(String sql) throws SQLException {
            long start = System.currentTimeMillis();
            boolean rs = delegate.execute(sql);
            logIfSlow("execute", sql, start);
            return rs;
        }

        @Override
        public java.sql.ResultSet executeQuery(String sql) throws SQLException {
            long start = System.currentTimeMillis();
            java.sql.ResultSet rs = delegate.executeQuery(sql);
            logIfSlow("query", sql, start);
            return rs;
        }

        @Override
        public int executeUpdate(String sql) throws SQLException {
            long start = System.currentTimeMillis();
            int rows = delegate.executeUpdate(sql);
            logIfSlow("update", sql, start);
            return rows;
        }

        private void logIfSlow(String op, String sql, long start) {
            long elapsed = System.currentTimeMillis() - start;
            if (elapsed > slowThresholdMillis) {
                System.getLogger("SlowSql")
                        .log(System.Logger.Level.WARNING,
                                String.format("Slow %s [%dms]: %s", op, elapsed, sql));
            }
        }
    }

    // ---------- Wrapper helper base class ----------
    /** Minimal Wrapper helper used to forward unrelated methods to the delegate. */
    static class Wrapper implements java.sql.Wrapper {
        protected final java.sql.Wrapper delegate;
        private final String description;

        Wrapper(java.sql.Wrapper delegate, String description) {
            this.delegate = delegate;
            this.description = description;
        }

        @Override
        public <T> T unwrap(Class<T> iface) throws SQLException {
            if (iface.isInstance(delegate)) {
                return iface.cast(delegate);
            }
            throw new SQLException(description + " not a wrapper for " + iface);
        }

        @Override
        public boolean isWrapperFor(Class<?> iface) throws SQLException {
            return iface.isInstance(delegate);
        }

        public java.sql.Wrapper getDelegate() {
            return delegate;
        }
    }
}
