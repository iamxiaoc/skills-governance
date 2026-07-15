package com.corp.base.common.utils;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * Collection utilities complementing {@link java.util.Collections} and Guava.
 */
public final class CollectionUtils {

    private CollectionUtils() {
    }

    // ---------- emptiness ----------
    public static boolean isEmpty(Collection<?> c) {
        return c == null || c.isEmpty();
    }

    public static boolean isEmpty(Map<?, ?> m) {
        return m == null || m.isEmpty();
    }

    public static boolean isNotEmpty(Collection<?> c) {
        return !isEmpty(c);
    }

    public static boolean isNotEmpty(Map<?, ?> m) {
        return !isEmpty(m);
    }

    // ---------- set operations ----------
    @SafeVarargs
    public static <T> Set<T> union(Collection<? extends T>... collections) {
        Set<T> result = new LinkedHashSet<>();
        if (collections == null) {
            return result;
        }
        for (Collection<? extends T> c : collections) {
            if (c != null) {
                result.addAll(c);
            }
        }
        return result;
    }

    public static <T> Set<T> intersect(Collection<? extends T> a, Collection<? extends T> b) {
        if (isEmpty(a) || isEmpty(b)) {
            return new LinkedHashSet<>();
        }
        Set<T> left = new LinkedHashSet<>(a);
        Set<T> right = new HashSet<>(b);
        left.retainAll(right);
        return left;
    }

    public static <T> Set<T> diff(Collection<? extends T> a, Collection<? extends T> b) {
        if (isEmpty(a)) {
            return new LinkedHashSet<>();
        }
        Set<T> result = new LinkedHashSet<>(a);
        if (isNotEmpty(b)) {
            result.removeAll(b);
        }
        return result;
    }

    // ---------- transformation ----------
    public static <T, R> List<R> map(List<T> source, Function<T, R> mapper) {
        if (isEmpty(source)) {
            return new ArrayList<>();
        }
        return source.stream()
                .filter(Objects::nonNull)
                .map(mapper)
                .collect(Collectors.toList());
    }

    public static <T, K> Map<K, T> toMap(List<T> source, Function<T, K> keyExtractor) {
        if (isEmpty(source)) {
            return new LinkedHashMap<>();
        }
        return source.stream()
                .filter(Objects::nonNull)
                .collect(Collectors.toMap(
                        keyExtractor,
                        Function.identity(),
                        (a, b) -> b,
                        LinkedHashMap::new));
    }

    public static <T, K> Map<K, List<T>> groupBy(List<T> source, Function<T, K> classifier) {
        if (isEmpty(source)) {
            return new LinkedHashMap<>();
        }
        return source.stream()
                .filter(Objects::nonNull)
                .collect(Collectors.groupingBy(
                        classifier,
                        LinkedHashMap::new,
                        Collectors.toList()));
    }

    // ---------- partitioning ----------
    public static <T> List<List<T>> partition(List<T> source, int batchSize) {
        if (isEmpty(source) || batchSize <= 0) {
            return Collections.emptyList();
        }
        List<List<T>> result = new ArrayList<>();
        for (int i = 0; i < source.size(); i += batchSize) {
            result.add(new ArrayList<>(source.subList(i, Math.min(i + batchSize, source.size()))));
        }
        return result;
    }

    // ---------- safe helpers ----------
    @SafeVarargs
    public static <T> List<T> asList(T... items) {
        if (items == null || items.length == 0) {
            return new ArrayList<>();
        }
        return new ArrayList<>(Arrays.asList(items));
    }

    public static <T> List<T> unmodifiable(List<T> list) {
        if (list == null) {
            return Collections.emptyList();
        }
        return Collections.unmodifiableList(list);
    }

    public static <K, V> Map<K, V> unmodifiable(Map<K, V> map) {
        if (map == null) {
            return Collections.emptyMap();
        }
        return Collections.unmodifiableMap(map);
    }

    /**
     * Return a new map containing only entries whose keys are in {@code keys}.
     */
    public static <K, V> Map<K, V> filterByKeys(Map<K, V> source, Collection<K> keys) {
        if (isEmpty(source) || isEmpty(keys)) {
            return new HashMap<>();
        }
        Map<K, V> result = new LinkedHashMap<>();
        for (K k : keys) {
            V v = source.get(k);
            if (v != null) {
                result.put(k, v);
            }
        }
        return result;
    }
}
