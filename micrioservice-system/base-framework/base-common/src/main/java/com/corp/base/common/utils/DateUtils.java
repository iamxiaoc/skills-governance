package com.corp.base.common.utils;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Date;
import java.util.Locale;
import java.util.Objects;
import java.util.TimeZone;

/**
 * Date utilities built on top of {@link java.time} and {@link SimpleDateFormat}.
 *
 * <p>Default time-zone is Asia/Shanghai; override via {@link #setDefaultTimeZone(TimeZone)}.
 */
public final class DateUtils {

    public static final String PATTERN_DATE = "yyyy-MM-dd";
    public static final String PATTERN_DATETIME = "yyyy-MM-dd HH:mm:ss";
    public static final String PATTERN_TIMESTAMP = "yyyy-MM-dd HH:mm:ss.SSS";

    private static TimeZone defaultTimeZone = TimeZone.getTimeZone("Asia/Shanghai");
    private static final ZoneId DEFAULT_ZONE = defaultTimeZone.toZoneId();

    private DateUtils() {
    }

    public static void setDefaultTimeZone(TimeZone tz) {
        defaultTimeZone = Objects.requireNonNull(tz);
    }

    // ---------- formatting ----------
    public static String formatDate(Date date) {
        return format(date, PATTERN_DATE);
    }

    public static String formatDateTime(Date date) {
        return format(date, PATTERN_DATETIME);
    }

    public static String format(Date date, String pattern) {
        if (date == null) {
            return null;
        }
        return new SimpleDateFormat(pattern, Locale.getDefault()).format(date);
    }

    public static String format(LocalDateTime ldt, String pattern) {
        if (ldt == null) {
            return null;
        }
        return ldt.format(DateTimeFormatter.ofPattern(pattern));
    }

    // ---------- parsing ----------
    public static Date parseDate(String text) throws ParseException {
        return parse(text, PATTERN_DATE);
    }

    public static Date parseDateTime(String text) throws ParseException {
        return parse(text, PATTERN_DATETIME);
    }

    public static Date parse(String text, String pattern) throws ParseException {
        if (text == null || text.isEmpty()) {
            return null;
        }
        SimpleDateFormat sdf = new SimpleDateFormat(pattern, Locale.getDefault());
        sdf.setTimeZone(defaultTimeZone);
        sdf.setLenient(false);
        return sdf.parse(text);
    }

    public static LocalDateTime parseLocalDateTime(String text, String pattern) {
        if (text == null || text.isEmpty()) {
            return null;
        }
        return LocalDateTime.parse(text, DateTimeFormatter.ofPattern(pattern));
    }

    // ---------- conversions ----------
    public static LocalDateTime toLocalDateTime(Date date) {
        if (date == null) {
            return null;
        }
        Instant instant = date.toInstant();
        return LocalDateTime.ofInstant(instant, DEFAULT_ZONE);
    }

    public static Date toDate(LocalDateTime ldt) {
        if (ldt == null) {
            return null;
        }
        return Date.from(ldt.atZone(DEFAULT_ZONE).toInstant());
    }

    public static LocalDate toLocalDate(Date date) {
        return toLocalDateTime(date) == null ? null : toLocalDateTime(date).toLocalDate();
    }

    // ---------- arithmetic ----------
    public static Date plusDays(Date date, long days) {
        if (date == null) {
            return null;
        }
        return toDate(toLocalDateTime(date).plusDays(days));
    }

    public static Date minusDays(Date date, long days) {
        return plusDays(date, -days);
    }

    public static Date plusHours(Date date, long hours) {
        if (date == null) {
            return null;
        }
        return toDate(toLocalDateTime(date).plusHours(hours));
    }

    public static long diffInDays(Date from, Date to) {
        if (from == null || to == null) {
            return 0L;
        }
        long ms = to.getTime() - from.getTime();
        return ms / (24L * 60L * 60L * 1000L);
    }

    public static long diffInHours(Date from, Date to) {
        if (from == null || to == null) {
            return 0L;
        }
        return (to.getTime() - from.getTime()) / (60L * 60L * 1000L);
    }

    /**
     * Current time as a {@link Date}.
     */
    public static Date now() {
        return new Date();
    }

    /**
     * Epoch millis for the given {@link LocalDateTime} in the default zone.
     */
    public static long toEpochMilli(LocalDateTime ldt) {
        if (ldt == null) {
            return 0L;
        }
        return ldt.atZone(DEFAULT_ZONE).toInstant().toEpochMilli();
    }
}
