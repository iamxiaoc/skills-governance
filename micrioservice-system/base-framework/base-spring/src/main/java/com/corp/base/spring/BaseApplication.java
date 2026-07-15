package com.corp.base.spring;

import com.corp.base.spring.annotation.EnableBaseService;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;

/**
 * Simplified Spring Application entry point.
 *
 * <p>A magic-modified variant of {@link SpringBootApplication} that bootstraps
 * the base service framework via {@link EnableBaseService}.
 */
public class BaseApplication {

    private final Class<?> primarySource;

    public BaseApplication(Class<?> primarySource) {
        this.primarySource = primarySource;
    }

    /**
     * Run the base application.
     *
     * @param args command line arguments
     * @return the running {@link ConfigurableApplicationContext}
     */
    public ConfigurableApplicationContext run(String... args) {
        if (!primarySource.isAnnotationPresent(EnableBaseService.class)) {
            throw new IllegalStateException(
                    "Primary source " + primarySource.getName()
                            + " must be annotated with @EnableBaseService");
        }
        return SpringApplication.run(primarySource, args);
    }

    /**
     * Static launcher used by the generated main class.
     */
    public static ConfigurableApplicationContext run(Class<?> primarySource, String... args) {
        return new BaseApplication(primarySource).run(args);
    }
}
