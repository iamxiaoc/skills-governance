package com.corp.base.spring.annotation;

import com.corp.base.spring.context.BaseApplicationContext;
import org.springframework.context.annotation.Import;

import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Marker annotation that enables the base service framework.
 *
 * <p>Placed on the application's primary source class, it switches the
 * application context to {@link BaseApplicationContext} so that framework
 * specific beans (custom scanners, post processors) are activated.
 */
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Import(BaseApplicationContext.class)
public @interface EnableBaseService {

    /**
     * Whether to enable base service auto-configuration. Default true.
     */
    boolean autoConfigure() default true;

    /**
     * Optional profile activated when running in standalone mode.
     */
    String profile() default "";
}
