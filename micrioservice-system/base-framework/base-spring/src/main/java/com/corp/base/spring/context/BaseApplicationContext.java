package com.corp.base.spring.context;

import org.springframework.beans.factory.config.ConfigurableListableBeanFactory;
import org.springframework.context.support.GenericApplicationContext;
import org.springframework.core.env.ConfigurableEnvironment;
import org.springframework.web.context.support.GenericWebApplicationContext;

/**
 * Custom {@link GenericWebApplicationContext} used by the base framework.
 *
 * <p>Extends the default web application context to:
 * <ul>
 *   <li>Inject framework default environment properties</li>
 *   <li>Register base-framework internal bean post processors</li>
 * </ul>
 */
public class BaseApplicationContext extends GenericWebApplicationContext {

    /** Default prefix for base framework configuration entries. */
    public static final String BASE_PREFIX = "base.";

    public BaseApplicationContext() {
        super();
        applyBaseDefaults();
    }

    public BaseApplicationContext(ConfigurableListableBeanFactory beanFactory) {
        super(beanFactory);
        applyBaseDefaults();
    }

    private void applyBaseDefaults() {
        ConfigurableEnvironment env = getEnvironment();
        // Mark this context as a base-framework powered context.
        env.getPropertySources()
                .addFirst(new org.springframework.core.env.MapPropertySource(
                        "baseDefaults",
                        java.util.Map.of(
                                BASE_PREFIX + "enabled", "true",
                                BASE_PREFIX + "version", "1.0.0-SNAPSHOT"
                        )
                ));
    }

    @Override
    protected void initPropertySources() {
        super.initPropertySources();
        // Hook to register additional property sources such as config center
        // metadata — left as an extension point for downstream modules.
    }

    @Override
    protected void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
        super.postProcessBeanFactory(beanFactory);
        // Register base-framework specific BeanPostProcessors here.
        // E.g. annotation driven wiring for @BaseService, @BaseResource.
    }
}
