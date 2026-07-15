package com.corp.base.security.config;

import com.corp.base.security.filter.SecurityFilter;
import com.corp.base.security.filter.XssFilter;
import jakarta.servlet.Filter;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.autoconfigure.condition.ConditionalOnWebApplication;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.core.Ordered;

import java.util.HashMap;
import java.util.Map;

/**
 * Auto-configuration that registers the base security filters when running in
 * a servlet web application.
 *
 * <p>Each filter can be turned off individually via properties under the
 * {@code base.security.*} namespace.
 */
@AutoConfiguration
@ConditionalOnWebApplication(type = ConditionalOnWebApplication.Type.SERVLET)
@ConditionalOnClass({Filter.class, jakarta.servlet.http.HttpServletRequest.class})
public class SecurityAutoConfiguration {

    /** Default filter orders; XSS runs before the generic security filter. */
    public static final int XSS_FILTER_ORDER = Ordered.HIGHEST_PRECEDENCE + 20;
    public static final int SECURITY_FILTER_ORDER = Ordered.HIGHEST_PRECEDENCE + 30;

    /**
     * Register the {@link SecurityFilter}.
     */
    @Bean
    @ConditionalOnMissingBean(SecurityFilter.class)
    @ConditionalOnProperty(prefix = "base.security.filter", name = "enabled", havingValue = "true", matchIfMissing = true)
    public FilterRegistrationBean<SecurityFilter> securityFilterRegistration(SecurityFilter filter) {
        FilterRegistrationBean<SecurityFilter> reg = new FilterRegistrationBean<>(filter);
        reg.setName("baseSecurityFilter");
        reg.setOrder(SECURITY_FILTER_ORDER);
        reg.addUrlPatterns("/*");
        Map<String, String> params = new HashMap<>();
        params.put("maxContentLengthMb", "10");
        reg.setInitParameters(params);
        return reg;
    }

    @Bean
    @ConditionalOnMissingBean
    @ConditionalOnProperty(prefix = "base.security.filter", name = "enabled", havingValue = "true", matchIfMissing = true)
    public SecurityFilter securityFilter() {
        return new SecurityFilter();
    }

    /**
     * Register the {@link XssFilter}.
     */
    @Bean
    @ConditionalOnMissingBean(XssFilter.class)
    @ConditionalOnProperty(prefix = "base.security.xss", name = "enabled", havingValue = "true", matchIfMissing = true)
    public FilterRegistrationBean<XssFilter> xssFilterRegistration(XssFilter filter) {
        FilterRegistrationBean<XssFilter> reg = new FilterRegistrationBean<>(filter);
        reg.setName("baseXssFilter");
        reg.setOrder(XSS_FILTER_ORDER);
        reg.addUrlPatterns("/*");
        return reg;
    }

    @Bean
    @ConditionalOnMissingBean
    @ConditionalOnProperty(prefix = "base.security.xss", name = "enabled", havingValue = "true", matchIfMissing = true)
    public XssFilter xssFilter() {
        return new XssFilter();
    }
}
